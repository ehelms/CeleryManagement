"""
    Django view functions that return Json data.
"""

import json
import itertools
import socket
import uuid
import tempfile
import os
import subprocess

from django.http import HttpResponse
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse as urlreverse

from celery import signals
from celery.task.control import broadcast, inspect
from djcelery.models import WorkerState

from celerymanagementapp.jsonquery.filter import JsonFilter
from celerymanagementapp.jsonquery.xyquery import JsonXYQuery
from celerymanagementapp.jsonquery.modelmap import JsonTaskModelMap

from celerymanagementapp import tasks
from celerymanagementapp.models import OutOfBandWorkerNode 
from celerymanagementapp.models import RegisteredTaskType, TaskDemoGroup

#==============================================================================#
def _json_from_post(request, allow_empty=False):
    """Return the json content of the given request.  The json must be in the 
       request's POST data."""
    rawjson = request.raw_post_data
    if allow_empty and not rawjson:
        return None
    return json.loads(rawjson)
    
def _json_response(jsondata, **kwargs):
    """Convert a Python structure (such as dict, list, string, etc) into a json 
       bystream which is then returned as a Django HttpResponse."""
    rawjson = json.dumps(jsondata, **kwargs)
    return HttpResponse(rawjson, content_type='application/json')
    
def _update_json_request(json_request, **kwargs):
    """ Merges the keyword arguments with the contents on the json_request 
        dict.  
        
        If 'filter' or 'exclude' are given (whose values should be a list of 
        lists), their values are appended to the values of the same name in the 
        json dict.  Other arguments replace the corresponding values in the 
        dict.
    """
    if 'filter' in kwargs:
        filter = json_request.get('filter',[])
        filter.extend(kwargs.pop('filter'))
        json_request['filter'] = filter
    if 'exclude' in kwargs:
        exclude = json_request.get('exclude',[])
        exclude.extend(kwargs.pop('exclude'))
        json_request['exclude'] = exclude
    json_request.update(dict((k,v) for k,v in kwargs.iteritems() if v is not None))
    return json_request
        
    
def _resolve_name(name):
    """If name is None or 'all', return None.  Otherwise, returns name."""
    if not name or name.lower() == 'all':
        name = None
    return name
        

# Store the list of defined tasks for easy retrieval.  It is updated when a 
# worker starts and when a worker stops.  

class TasknameCache(object):
    """ Cache the list of task names.  The names are also stored in the 
        database.
    """
    RegisteredTaskType = RegisteredTaskType
    def __init__(self):
        self._taskname_cache = []
        self._worker_status_changed = True
        
    def _getnames(self):
        """ Retieve the currently cached list of task names.  If a worker has 
            been started or stopped since the last time this was called, the 
            cache will be refreshed. 
        """
        if self._worker_status_changed:
            self._worker_status_changed = False
            self._update_database()
            self._taskname_cache = self._get_names_from_database()
        return self._taskname_cache
    
    names = property(_getnames)
    
    def _update_database(self):
        """ Update the RegisteredTaskType model with data from the currently 
            running Celery workers. 
        """
        i = inspect()
        workers = i.registered_tasks()
        if workers:
            for workername, tasks in workers.iteritems():
                self.RegisteredTaskType.clear_tasks(workername)
                for taskname in tasks:
                    self.RegisteredTaskType.add_task(taskname, workername)
                    
    def _get_names_from_database(self):
        """ Retrieve the list of task names from the RegisteredTaskType model. 
        """
        qs = self.RegisteredTaskType.objects.all()
        names = list(set(x.name for x in qs))
        names.sort()
        return names
    
    def _on_celery_worker_ready(self):
        """Celery signal handler."""
        self._worker_status_changed = True
        
    def _on_celery_worker_stopping(self):
        """Celery signal handler."""
        self._worker_status_changed = True
    
    
_taskname_cache = TasknameCache()

# Register Celery signal handlers.  This keeps the TasknameCache up-to-date.
signals.worker_ready.connect(
                _taskname_cache._on_celery_worker_ready, 
                dispatch_uid='celerymanagementapp.dataviews.on_worker_ready'
                )
signals.worker_shutdown.connect(
                _taskname_cache._on_celery_worker_stopping, 
                dispatch_uid='celerymanagementapp.dataviews.on_worker_stopping'
                )

    
def get_defined_tasks():
    """Get a list of the currently defined tasks."""
    return _taskname_cache.names
    
def get_defined_tasks_live():
    """ Get the list of defined tasks as reported by Celery right now. """
    i = inspect()
    workers = i.registered_tasks()
    defined = []
    if workers:
        defined = set(x for x in itertools.chain.from_iterable(workers.itervalues()))
        defined = list(defined)
        defined.sort()
    return defined
    
def get_workers_from_database():
    """Get a list of all workers that exist (running or not) in the database."""
    workers = WorkerState.objects.all()
    return [unicode(w) for w in workers]
    
def get_workers_live():
    """ Get the list of workers as reported by Celery right now. """
    i = inspect()
    workersdict = i.ping()
    workers = []
    if workersdict:
        workers = set(workersdict.iterkeys())
        workers.add(socket.gethostname())
        workers = list(workers)
        workers.sort()
    return workers
    
def get_worker_subprocesses(dest=None):
    """ Retrieve the number of subprocesses for each worker.  The return value 
        is a dict where the keys are worker names and the values are the number 
        of subprocesses. 
    """
    stats = {}
    for x in broadcast("stats", destination=dest, reply=True):
        stats.update(x)
    
    workercounts = {}
    for workername in stats.iterkeys():
        procs = stats[workername]['pool']['processes']
        workercounts[workername] = len(procs)
    
    return workercounts
    

#==============================================================================#
def task_xy_dataview(request):
    """ Performs a database query and returns the results of that query.  The 
        result is formatted as json.  The query must be contained in the 
        request's POST content and it must be fin json format.  
        
        See the docs directory form more information on the format of the query 
        and result.
    """
    json_request = _json_from_post(request)
    
    xyquery = JsonXYQuery(JsonTaskModelMap(), json_request)
    json_result = xyquery.do_query()
    
    return _json_response(json_result)

def worker_subprocesses_dataview(request, name=None):
    """ Return the number of sub processes for each worker as a json 
        dictionary.
    """
    name = _resolve_name(name)
    dest = name and [name]
    workercounts = get_worker_subprocesses(dest=dest)
        
    return _json_response(workercounts)

def worker_start(request):
    """Find an available node and start a worker process"""
    active_nodes = OutOfBandWorkerNode.objects.filter(active=True)
    for node in active_nodes:
        output = node.celeryd_status()
        if not output.strip('\n').isdigit():
            node.celeryd_start()
            return _json_response({'status': 'success'})
    return _json_response({'status': 'failure', 'message': 'No Available Worker Nodes'})
    
def pending_task_count_dataview(request, name=None):
    """ Return the number of pending DispatchedTasks for each defined task.  An 
        optional filter and/or exclude may be provided in the POST data as a 
        json query.  The return value is a json dicitonary with task names as 
        the keys.
    """
    name = _resolve_name(name)
    json_request = _json_from_post(request, allow_empty=True) or {}
    tasknames = get_defined_tasks()
    
    filterexp = [['state','PENDING']]
    if name:
        filterexp.append(['name',name])
    segmentize = {'field': 'taskname', 'method': ['values', tasknames],}
    aggregate = [{'field': 'count'}]
    
    json_request = _update_json_request(json_request, filter=filterexp, 
                                        segmentize=segmentize, 
                                        aggregate=aggregate)
    
    xyquery = JsonXYQuery(JsonTaskModelMap(), json_request)
    json_result = xyquery.do_query()
    
    d = json_result['data']
    
    #r = dict((row[0], row[1]['count']) for row in d)
    r = dict((row[0], row[1][0]['methods'][0]['value']) for row in d)
    
    return _json_response(r)
    
def tasks_per_worker_dataview(request, name=None):
    """ Return the number of tasks of each DefinedTask dispatched to each 
        worker.  The return value is a two-level json dictionary where the 
        top-level keys are the task names and the second-level keys are the 
        worker names.
    
        For example:
        
            {
                task1: {
                    worker1: 0,
                    worker2: 5
                }
                task2: {
                    worker1: 18,
                    worker2: 9
                }
            }
            
        An optional filter and/or exclude may be provided in the POST data as a 
        json query.  
    """
    name = _resolve_name(name)
    json_request = _json_from_post(request, allow_empty=True) or {}
    
    filterexp = []
    if name:
        filterexp.append(['name',name])
    json_request = _update_json_request(json_request, filter=filterexp)
    
    modelmap = JsonTaskModelMap()
    jfilter = JsonFilter(modelmap, json_request)
    queryset = modelmap.get_queryset()
    queryset = jfilter(queryset)
    
    tasknames = get_defined_tasks()
    workers = [(unicode(obj), obj.pk) for obj in WorkerState.objects.all()]
    
    r = {}
    
    for wname, wpk in workers:
        worker_queryset = queryset.filter(worker=wpk)
        for taskname in tasknames:
            n = worker_queryset.filter(name=taskname).count()
            if taskname not in r:
                r[taskname] = {}
            r[taskname][wname] = n
    return _json_response(r)
    
def definedtask_list_dataview(request):
    """ Returns a list of DefinedTasks names, formatted as json. """
    tasknames = get_defined_tasks()
    return _json_response(tasknames)
    
def worker_list_dataview(request):
    """ Returns a list of worker names, formatted as json. """
    workernames = get_workers_live()
    return _json_response(workernames)
    
def worker_info_dataview(request, name=None):
    name = _resolve_name(name)
    if name:
        workers = WorkerState.objects.all(hostname=name)
    else:
        workers = WorkerState.objects.all()
    d = dict((unicode(w), {'is_alive': w.is_alive()}) for w in workers)
    return _json_response(d)
    

#==============================================================================#
def validate_task_demo_request(json_request):
    """ Helper to task_demo_dataview.  It validates the Json request. """
    # return (is_valid, msg)
    name = json_request.get('name', None)
    rate = json_request.get('rate', None)
    runfor = json_request.get('runfor', None)
    if not name or not rate or not runfor:
        return False, "The keys: 'name', 'rate', and 'runfor' are all required."
    if not isinstance(rate, (int,float)) or not isinstance(runfor, (int,float)):
        return False, "The keys: 'rate' and 'runfor' must be integers or floats."
    
    kwargs = json_request.get('kwargs', {})
    args = json_request.get('args', [])
    options = json_request.get('options', {})
    
    if not isinstance(kwargs, dict):
        return False, "The key: 'kwargs', if present, must be a dictionary."
    if not isinstance(args, list):
        return False, "The key: 'args', if present, must be a list."
    if not isinstance(options, dict):
        return False, "The key: 'options', if present, must be a dictionary."
    
    defined = get_defined_tasks_live()
    if name not in defined:
        return False, "There is no task by the name: '{0}'.".format(name)
    
    return True, ""
    

def task_demo_dataview(request):
    """ View that launches a single task several times.  This can be used to 
        stress test a particular Celery configuration. 
    
        The request must include the Json request as POST data.
    """
    json_request = _json_from_post(request)
    
    dispatchid = None
    
    # validate request
    is_valid, msg = validate_task_demo_request(json_request)
    if is_valid:
        # save json to temp file
        rawjson = request.raw_post_data
        fd, tmpname = tempfile.mkstemp()
        os.close(fd)
        tmp = open(tmpname, 'wb')
        tmp.write(rawjson)
        tmp.close()
        # generate id
        dispatchid = uuid.uuid4().hex
        ##print 'Launching dispatcher task...'
        tasks.launch_demotasks.apply_async(args=[dispatchid, tmpname])
        ##print 'Dispatcher task launched.'
        
    # prepare response
    response = {
        'uuid': dispatchid,
        'error': not is_valid,
        'msg': msg,
        }
    
    return _json_response(response)
    
def task_demo_status_dataview(request, uuid=None):
    # default values
    response = {
        'completed': False,
        'elapsed': -1.0,
        'tasks_sent': -1,
        'errors_on_send': -1,
        'errors_on_result': -1,
        'uuid_not_found': True,
        }
    try:
        # get object from db
        obj = TaskDemoGroup.objects.get(uuid=uuid)
        response = {
            'completed': obj.completed,
            'elapsed': obj.elapsed,
            'tasks_sent': obj.tasks_sent,
            'errors_on_send': obj.errors_on_send,
            'errors_on_result': obj.errors_on_result,
            'uuid_not_found': False,
            }
    except ObjectDoesNotExist:
        pass
    return _json_response(response)
    
@login_required
def task_demo_test_dataview(request):
    """ Very simple view for testing the task_demo_dataview function.  This is 
        only for testing, not for production code. 
    """
    from django.template import Template
    from django.template import RequestContext
    
    name = 'celerymanagementapp.testutil.tasks.simple_test'
    rate = 2.0
    runfor = 10.0
    
    send = urlreverse('celerymanagementapp.dataviews.task_demo_dataview')
    
    html = """\
    <html>
    <head>
    <script type="text/javascript" src="{{{{ CELERYMANAGEMENTAPP_MEDIA_PREFIX }}}}js/jquery.js" ></script>
    <script>
    
    function json() {{
    var query = '{{"name": "{name}", "rate":{rate}, "runfor":{runfor} }}';
    
    $.post(
        '{send}',
        query,
        function(data) {{
            //alert("Data loaded: " + data);
            //alert(data.data);
            //alert(data.data[0]);
        }},
        'json'
    );
    }}
    
    </script>
    </head>
    <body>
    <table>
      <tr><td>
        <form action="{send}" method="POST">
        {{% csrf_token %}}
        <input type="button" value="Send" onclick="json();"/>
        </form>
      </td></tr>
    </table>
    </body>
    </html>
    """
    html = html.format(send=send, name=name, rate=rate, runfor=runfor)
    t = Template(html)
    c = RequestContext(request)
    return HttpResponse(t.render(c))


#==============================================================================#

