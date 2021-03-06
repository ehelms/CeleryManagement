import datetime
import itertools
import collections
import re

from django.db.models import Avg, Min, Max, Variance
from django.core.mail import send_mail as django_send_mail

from celery.states import RECEIVED, FAILURE, SUCCESS, PENDING, STARTED, REVOKED
from celery.states import RETRY, READY_STATES, UNREADY_STATES

from celerymanagementapp.models import DispatchedTask
from celerymanagementapp.policy import exceptions, signals, util

#==============================================================================#
class ApiError(exceptions.Error):
    clsname = 'PolicyApiError'
    
class ApiValidatorError(exceptions.Error):
    clsname = 'PolicyApiValidatorError'

class TimeIntervalError(exceptions.Error):
    clsname = 'PolicyTimeIntervalError'


#==============================================================================#
def make_time_interval(arg, now=None):
    now = now or datetime.datetime.now()
    if isinstance(arg, datetime.timedelta):
        result = (now-arg, now)
    elif isinstance(arg, (tuple, list)):
        if len(arg) != 2:
            msg = 'Sequence arguments must have a length of two.'
            raise TimeIntervalError(msg)
        a, b = arg
        if isinstance(a, datetime.timedelta):
            if isinstance(b, datetime.timedelta):
            # (timedelta 'a' before now,  timedelta 'b' before now)
                result = (now-a, now-b)
            else:
            # (timedelta 'a' before time 'b',  time 'b')
                result = (b-a, b)
        elif isinstance(b, datetime.timedelta):
            # (time 'a',  timedelta 'b' after time 'a')
            result = (a, a+b)
        else:
            # (time 'a', time'b')
            result = arg
    else:
        msg =  'Argument must be a datetime.timedelta'
        msg += ' or a sequence of length two.'
        raise TimeIntervalError(msg)
    return (min(result), max(result))

def string_or_sequence(arg):
    if isinstance(arg, basestring):
        arg = [arg]
    return arg
    
def get_filter_seq_arg(field, arg):
    if arg is not None:
        if (isinstance(arg, collections.Iterable) 
           and not isinstance(arg, basestring)):
            return { '{0}__in'.format(field): tuple(arg) }
        else:
            return { field: arg }
    return {}
    
def filter(states=None, interval=None, workers=None, tasks=None, now=None):
    filterargs = {}
    if interval is not None:
        interval = make_time_interval(interval, now)
        filterargs['sent__gte'] = interval[0]
        filterargs['sent__lt'] = interval[1]
    filterargs.update(get_filter_seq_arg('state', states))
    filterargs.update(get_filter_seq_arg('worker__hostname', workers))
    filterargs.update(get_filter_seq_arg('name', tasks))
    return DispatchedTask.objects.filter(**filterargs)
            
#==============================================================================#
def validate_bool(value):
    if not isinstance(value, bool):
        raise ApiValidatorError()
    return value

def validate_string_or_none(value):
    if not isinstance(value, basestring) and value is not None:
        raise ApiValidatorError()
    return value
    
def validate_int(value):
    if not isinstance(value, int):
        raise ApiValidatorError()
    return value
    
def validate_int_or_none(value):
    if not isinstance(value, int) and value is not None:
        raise ApiValidatorError()
    return value

#

TASKAPI_SETTINGS_CONFIG = [
    ('ignore_result', validate_bool),
    ('routing_key', validate_string_or_none),
    ('exchange',  validate_string_or_none),
    ('default_retry_delay', validate_int),
    ('rate_limit', validate_string_or_none),
    ('store_errors_even_if_ignored', validate_bool),
    ('acks_late', validate_bool),
    ('expires', validate_int_or_none),
]



#==============================================================================#
class ItemApi(object):
    assignable_names = set()
    
    def __init__(self, _broadcast, names=None):
        self.names = names or []
        self._broadcast = _broadcast
        self._locked = True
        
    def __setattr__(self, name, val):
        if (not name.startswith('_') and getattr(self, '_locked', False) 
           and name not in self.assignable_names):
            raise ApiError('Cannot assign to item attribute: {0}'.format(name))
        object.__setattr__(self, name, val)
    

class ItemsCollectionApi(object):
    """ A collection of objects accessible by name. 
    
        Use subscript syntax to work with a single item, or use the all() 
        method to work with all items.  You may also use multiple names with 
        subscript syntax by placing them in a tuple.
        
            collection['item'].item_attribute
            collection.all().item_attribute
            collection[('item0','item1','item2',)].item_attribute
            
    """
    ItemApi = None
    
    def __init__(self, connection=None):
        self._locked = True
        self._connection = connection
        
    def __getitem__(self, names):
        if isinstance(names, basestring):
            names = (names, )
        return self._get_item_api(self._broadcast, names)
        
    def all(self):
        return self._get_item_api(self._broadcast, None)
        
    def _get_item_api(self, _broadcast, names):
        return self.ItemApi(_broadcast, names)
        
    def _get_worker_count(self):
        try:
            n = self._worker_count
        except AttributeError:
            n = len(util.get_all_worker_names())
            self._worker_count = n
        return n
        
    def _broadcast(self, *args, **kwargs):
        ##print 'self._connection = {0}'.format(self._connection)
        kwargs['connection'] = self._connection
        if 'destination' in kwargs and isinstance(kwargs['destination'], list):
            kwargs['limit'] = len(kwargs['destination'])
        else:
            kwargs['limit'] = self._get_worker_count()
        return util.broadcast(*args, **kwargs)
        
    def __getattr__(self, name):
        if not name.startswith('_') and name != 'all':
            raise ApiError('Cannot get attribute: {0}'.format(name))
        return object.__getattr__(self, name)
        
    def __setattr__(self, name, val):
        if not name.startswith('_') and getattr(self, '_locked', False):
            msg = 'Cannot assign to item collection attribute: {0}'.format(name)
            raise ApiError(msg)
        object.__setattr__(self, name, val)

#==============================================================================#
class TaskSetting(object):
    def __init__(self, attrname, validator):
        self.attrname = attrname
        self.validator = validator
    
    def __get__(self, taskapi, owner):
        assert taskapi is not None
        if len(taskapi.names) != 1:
            raise ApiError('Cannot retrieve this attribute for multiple tasks.')
        arguments = {'taskname': taskapi.names[0], 'attrname': self.attrname}
        r = taskapi._broadcast('get_task_attribute', arguments=arguments, 
                               reply=True)
        r = util._merge_broadcast_result(r)
        if not r:
            tmpl = 'Unable to retrieve task attribute: {0}.'
            msg = tmpl.format(self.attrname)
            raise ApiError(msg)
        # check that all 'values' are equal
        r = util._condense_broadcast_result(r)
        # check that the value doesn't indicate an error
        if isinstance(r, dict) and 'error' in r:
            tmpl = 'Error occurred while retrieving task attribute: {0}.'
            msg = tmpl.format(self.attrname)
            raise ApiError(msg)
        return r
        
    def __set__(self, taskapi, value):
        value = self.validator(value)
        arguments = {'tasknames': taskapi.names, 'attrname':self.attrname, 
                     'value': value}
        r = taskapi._broadcast('set_task_attribute', arguments=arguments, 
                               reply=True)
        r = util._merge_broadcast_result(r)
        if not r:
            msg = 'Unable to set task attribute: {0}.'.format(self.attrname)
            raise ApiError(msg)
        # check that all 'values' are equal
        r = util._condense_broadcast_result(r)
        # check that the value doesn't indicate an error
        if isinstance(r, dict) and 'error' in r:
            tmpl = 'Error occurred while setting task attribute: {0}.'
            msg = tmpl.format(self.attrname)
            raise ApiError(msg)
        taskapi._on_task_modified(self.attrname, value)
        
        
class TaskApiMeta(type):
    def __new__(self, clsname, bases, attrs):
        config = attrs.pop('settings_config')
        for name, validator in config:
            attrs[name] = TaskSetting(name, validator)
        return type.__new__(self, clsname, bases, attrs)
        

class TaskApi(ItemApi):
    __metaclass__ = TaskApiMeta
    
    settings_config = TASKAPI_SETTINGS_CONFIG
    assignable_names = set(t[0] for t in settings_config)
    
    def __init__(self, _broadcast, names=None, event_dispatcher=None):
        if not names:
            names = util.get_all_registered_tasks()
        self._event_dispatcher = event_dispatcher
        super(TaskApi, self).__init__(_broadcast, names)
        
    def _on_task_modified(self, attrname, value):
        self._event_dispatcher.send(signals.CM_TASK_MODIFIED_EVENT, 
                                    tasknames=self.names, attrname=attrname, 
                                    value=value)
        

class TasksCollectionApi(ItemsCollectionApi):
    ItemApi = TaskApi
    def __init__(self, event_dispatcher, connection=None):
        self._event_dispatcher = event_dispatcher
        super(TasksCollectionApi, self).__init__(connection=connection)
        
    def _get_item_api(self, *args):
        return self.ItemApi(*args, event_dispatcher=self._event_dispatcher)
    
#==============================================================================#
class WorkerPrefetchProxy(object):
    def __init__(self, broadcast, names):
        self.names = names
        self._broadcast = broadcast
    def get(self):
        if len(self.names) != 1:
            msg = 'Cannot retrieve this attribute for multiple workers.'
            raise ApiError(msg)
        r = self._broadcast('stats', destination=self.names, reply=True)
        r = util._merge_broadcast_result(r)
        if not r:
            raise ApiError('Unable to retrieve worker attribute: prefetch.')
        r = util._condense_broadcast_result(r)
        if isinstance(r, dict) and 'error' in r:
            raise ApiError('Error occurred while retrieving worker prefetch.')
        return r['consumer']['prefetch_count']
        
    def increment(self, n=1):
        n = validate_int(n)
        r = self._broadcast('prefetch_increment', arguments={'n':n}, reply=True)
        r = util._merge_broadcast_result(r)
        if not r:
            raise ApiError('Unable to increment prefetch.')
        # check that the value doesn't indicate an error
        for worker_ret in r:
            if isinstance(worker_ret, dict) and 'error' in worker_ret:
                raise ApiError('Error occurred while incrementing prefetch.')
        
    def decrement(self, n=1):
        n = validate_int(n)
        r = self._broadcast('prefetch_decrement', arguments={'n':n}, reply=True)
        r = util._merge_broadcast_result(r)
        if not r:
            raise ApiError('Unable to decrement prefetch.')
        # check that the value doesn't indicate an error
        for worker_ret in r:
            if isinstance(worker_ret, dict) and 'error' in worker_ret:
                raise ApiError('Error occurred while decrementing prefetch.')
                
class WorkerSubprocessesProxy(object):
    def __init__(self, broadcast, names):
        self.names = names
        self._broadcast = broadcast
    def get(self):
        if len(self.names) != 1:
            msg = 'Cannot retrieve this attribute for multiple workers.'
            raise ApiError(msg)
        r = self._broadcast('stats', destination=self.names, reply=True)
        r = util._merge_broadcast_result(r)
        if not r:
            msg = 'Unable to retrieve worker attribute: subprocess pool.'
            raise ApiError(msg)
        r = util._condense_broadcast_result(r)
        if isinstance(r, dict) and 'error' in r:
            msg = 'Error occurred while retrieving worker subprocess pool.'
            raise ApiError(msg)
        return len(r['pool']['processes'])
        
    def increment(self, n=1):
        n = validate_int(n)
        r = self._broadcast('pool_grow', arguments={'n':n}, reply=True)
        r = util._merge_broadcast_result(r)
        if not r:
            raise ApiError('Unable to increment worker subprocess pool.')
        # check that the value doesn't indicate an error
        for worker_ret in r:
            if isinstance(worker_ret, dict) and 'error' in worker_ret:
                msg =  'Error occurred while incrementing '
                msg += 'worker subprocess pool.'
                raise ApiError(msg)
        
    def decrement(self, n=1):
        n = validate_int(n)
        r = self._broadcast('pool_shrink', arguments={'n':n}, reply=True)
        r = util._merge_broadcast_result(r)
        if not r:
            raise ApiError('Unable to decrement worker subprocess pool.')
        # check that the value doesn't indicate an error
        for worker_ret in r:
            if isinstance(worker_ret, dict) and 'error' in worker_ret:
                msg =  'Error occurred while decrementing '
                msg += 'worker subprocess pool.'
                raise ApiError(msg)
                
class WorkerSetting(object):
    def __init__(self, cls):
        self.cls = cls
    def __get__(self, workerapi, owner):
        assert workerapi is not None
        return self.cls(workerapi._broadcast, workerapi.names)
    def __set__(self, workerapi, value):
        raise ApiError('Cannot set attribute')

class WorkerApi(ItemApi):
    assignable_names = set()
    
    def __init__(self, _broadcast, names=None):
        if not names:
            names = util.get_all_worker_names()
        super(WorkerApi, self).__init__(_broadcast, names)
        
    prefetch = WorkerSetting(WorkerPrefetchProxy)
    subprocesses = WorkerSetting(WorkerSubprocessesProxy)
    
class WorkersCollectionApi(ItemsCollectionApi):
    ItemApi = WorkerApi

#==============================================================================#
class StatsApi(object):
    def __init__(self, connection=None):
        pass
        
    ## [PENDING, RECEIVED, STARTED, SUCCESS]
    ## [FAILURE, REVOKED, RETRY]
        
    def tasks_failed(self, interval=None, workers=None, tasknames=None):
        return self.tasks(states=FAILURE, interval=interval, workers=workers, 
                          tasknames=tasknames)
        
    def tasks_succeeded(self, interval=None, workers=None, tasknames=None):
        return self.tasks(states=SUCCESS, interval=interval, workers=workers, 
                          tasknames=tasknames)
        
    def tasks_revoked(self, interval=None, workers=None, tasknames=None):
        return self.tasks(states=REVOKED, interval=interval, workers=workers, 
                          tasknames=tasknames)
        
    def tasks_ready(self, interval=None, workers=None, tasknames=None):
        """ The number of tasks that have finished executing.  They have 
            succeeded, failed, or been revoked. 
        """
        # READY_STATES = SUCCESS | FAILURE | REVOKED
        return self.tasks(states=tuple(READY_STATES), interval=interval, 
                          workers=workers, tasknames=tasknames)
        
    def tasks_unready(self, interval=None, workers=None, tasknames=None):
        """ The number of tasks that are still in progress.  They have been 
            received, started, retried or are pending. 
        """
        # UNREADY_STATES = PENDING | RECEIVED | STARTED | RETRY
        return self.tasks(states=tuple(UNREADY_STATES), interval=interval, 
                          workers=workers, tasknames=tasknames)
        
    def tasks_sent(self, interval=None, workers=None, tasknames=None):
        """ The number of tasks that have been sent.  This is all tasks. """
        return self.tasks(states=tuple(ALL_STATES), interval=interval, 
                          workers=workers, tasknames=tasknames)
                                    
    def tasks(self, states=None, interval=None, workers=None, tasknames=None):
        """ The number of tasks that meet the given conditions.
        
            states: 
                A single Celery Task state or an iterable of many states.
                
            interval: 
                The interval of time in which tasks started.  This can be a 
                single timedelta, or a pair of timedeltas, datetimes, or one of 
                each.  The meanings of each are as follows:
                timedelta
                    The interval of time between now and timedelta before now.
                (timedelta a, timedelta b)
                    The interval of time between timedelta a and timedelta b 
                    before now.
                (datetime a, timedelta b)
                    The interval of time between a and timedelta b after a.
                (timedelta a, datetime b)
                    The interval of time between timedelta a before b and b.
                (datetime a, datetime b)
                    The interval of time between a and b.
                In all cases, the pair is corrected after applying the above 
                changes so that the minimum value is on the left and the 
                maximum is on the right.
                
            workers:
                The name of a worker as a string, or an iterable of such 
                strings.
                
            tasknames:
                The name of a task as a string, or an iterable of such strings.
        """
        return filter(states, interval, workers, tasknames).count()
    
    def mean_waittime(self, states=None, interval=None, workers=None, 
                      tasknames=None):
        qs = filter(states, interval, workers, tasknames).exclude(waittime=None)
        return qs.aggregate(Avg('waittime'))['waittime__avg']
    
    def mean_runtime(self, states=None, interval=None, workers=None, 
                     tasknames=None):
        qs = filter(states, interval, workers, tasknames).exclude(runtime=None)
        return qs.aggregate(Avg('runtime'))['runtime__avg']


#==============================================================================#
def send_email(subject, message, from_email, recipient_list, auth_user=None, 
               auth_password=None):
    """ Send an email using Django's email interface. 
        
        recipient_list:
            A list of emails--each email is a string.
            
        auth_user, auth_password:
            Username and password for the SMTP server.  If they are not 
            provided, Django will use the EMAIL_HOST_USER and 
            EMAIL_HOST_PASSWORD settings, respectively.
    """
    django_send_mail(subject, message, from_email, recipient_list, 
                     auth_user=auth_user, auth_password=auth_password)
                     
#==============================================================================#

_TIME_FMT = r'''
      (\d{1,2}) : (\d{2})                   # HH:MM
      (?: : (\d{2}) (?: \. (\d{0,6}))? )?   # [:SS[.mmmmmm]]
                                            # mmmmmm = microseconds
    '''

_time_fmt = re.compile(_TIME_FMT, re.VERBOSE)

def today(**kwargs):
    """ Return a datetime.datetime object representing today's date.
        
        With no arguments, the time is set to 00:00:00 (midnight).  However, 
        some keyword arguments are offered which can change this behavior.
        
        :keyword offset_days: An integer which can set the date forward or 
                              backward from the current date.
        :keyword timestr: A string representing a time which will be used in 
                          the returned datetime object.  The string's format is 
                          as follows: HH:MM:SS.mmmmmm
                          HH, MM, SS are the minutes, hours, and seconds.
                          mmmmmm is the microseconds, which can be 0-6 digits.
                          The seconds and microseconds are optional.
        :keyword time: A tuple representing a time which will be used in the 
                       returned datetime object.  The elements much be integers 
                       which represent: hours, minutes, seconds, and 
                       microseconds.  The seconds and microseconds are optional.
                       
        If both `timestr` and `time` are provided, only `timestr` will be used.
    """
    if not kwargs:
        return datetime.datetime.today().replace(hour=0, minute=0, second=0, 
                                                 microsecond=0)
    offset_days = kwargs.pop('offset_days',0)
    hour, minute, second, microsecond = 0,0,0,0
    if 'timestr' in kwargs:
        m = _time_fmt.match(kwargs['timestr'].strip())
        if m is None:
            msg = 'Invalid time string.  '
            msg += 'Must have format: HH:MM[:SS[.mmmmmm]] '
            msg += 'where seconds (S) and microseconds (m) are optional.'
            raise ApiError(msg)
        hour, minute, second, microsecond = m.groups(default='0')
        # microsecond must have 6 digits.  Account for user entering shorter 
        # numbers.
        microsecond = '{0:<06}'.format(microsecond[:6]) 
        hour, minute, second = int(hour), int(minute), int(second)
        microsecond = int(microsecond)
    elif 'time' in kwargs:
        # The 'time' tuple may be 2..4 items long.  The last two items default 
        # to 0.  So, append a tuple with 2 zeros to make sure we have at least 
        # 4 items, then slice off the first four items to get our four values.
        time = tuple(kwargs['time']) + (0,0)
        hour, minute, second, microsecond = time[:4]
    _today = datetime.datetime.today() + datetime.timedelta(days=offset_days)
    return _today.replace(hour=hour, minute=minute, second=second, 
                          microsecond=microsecond)
        

#==============================================================================#



