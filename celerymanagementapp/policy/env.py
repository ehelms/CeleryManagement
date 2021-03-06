import datetime
import time
import calendar
import math

from celery.schedules import crontab
from celery import states

from celerymanagementapp.policy import api, signals


#==============================================================================#
class ModuleWrapper(object):
    def __init__(self, module, allow=None, exclude=None):
        if not allow:
            if '__all__' in module.__dict__:
                allow = module.__all__
            else:
                allow = [ s for s in module.__dict__ if not s.startswith('_') ]
        allow = set(allow)
        allow -= set(exclude or [])
        mapping = dict( (k,v) for (k,v) in module.__dict__.iteritems() 
                                        if k in allow )
        object.__setattr__(self, 'data', mapping)
        
    def __getattr__(self, name):
        data = self.__dict__['data'] #super(ModuleWrapper,self).data #object.getattr(self, 'data')
        try:
            return data[name]
        except KeyError:
            msg = "The module object has no attribute '{0}'.".format(name)
            raise AttributeError(msg)
        
    def __setattr__(self, name, value):
        raise AttributeError('Assignment to module objects is not permitted.')

#==============================================================================#
# GLOBALS and LOCALS apply to all sections.  The other dicts apply to the 
# section given in their name.  When policies are run, they will be provided 
# with *copies* of these dicts.

GLOBALS = { 'datetime': ModuleWrapper(datetime, exclude='datetime_CAPI'),
            'time': ModuleWrapper(time), 'calendar': ModuleWrapper(calendar),
            'math': ModuleWrapper(math), 
            'now': datetime.datetime.now, 'today': api.today,
          }
LOCALS = {}

for state in states.ALL_STATES:
    GLOBALS[state] = state

SCHEDULE_GLOBALS = {}
SCHEDULE_LOCALS = { 'crontab': crontab, }
CONDITION_GLOBALS = {}
CONDITION_LOCALS = {}
APPLY_GLOBALS = {}
APPLY_LOCALS = {}

#==============================================================================#
# Merge GLOBALS dict with *_GLOBALS dicts (and likewise for LOCALS)
SCHEDULE_GLOBALS.update(GLOBALS)
SCHEDULE_LOCALS.update(LOCALS)
CONDITION_GLOBALS.update(GLOBALS)
CONDITION_LOCALS.update(LOCALS)
APPLY_GLOBALS.update(GLOBALS)
APPLY_LOCALS.update(LOCALS)

#==============================================================================#
class Env(object):
    """ The environment for an executing a code object.  This provides the 
        locals and globals dicts. 
    """
    def __init__(self, connection=None):
        self._locals = {}
        self._globals = {}
        self._connection = connection
        
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        self.destroy()
    def destroy(self):
        pass
    
    @property
    def globals(self):
        return self._globals
    @property
    def locals(self):
        return self._locals
        
        
class ScheduleEnv(Env):
    def __init__(self, connection=None):
        super(ScheduleEnv, self).__init__(connection=connection)
        self._locals.update(SCHEDULE_LOCALS)
        self._globals.update(SCHEDULE_GLOBALS)
        
class ConditionEnv(Env):
    def __init__(self, connection=None):
        super(ConditionEnv, self).__init__(connection=connection)
        self._locals.update(CONDITION_LOCALS)
        self._globals.update(CONDITION_GLOBALS)
        xglobals = {
            'stats':    api.StatsApi(connection=connection),
            }
        self._globals.update(xglobals)
        
class ApplyEnv(Env):
    def __init__(self, connection=None):
        super(ApplyEnv, self).__init__(connection=connection)
        self._dispatcher = signals.Dispatcher()
        self._locals.update(APPLY_LOCALS)
        self._globals.update(APPLY_GLOBALS)
        xglobals = {
            'tasks':    api.TasksCollectionApi(self._dispatcher, 
                                               connection=connection),
            'workers':  api.WorkersCollectionApi(connection=connection), 
            'stats':    api.StatsApi(connection=connection),
            'send_email': api.send_email,
            }
        self._globals.update(xglobals)
        
    def destroy(self):
        self._dispatcher.close()

#==============================================================================#


