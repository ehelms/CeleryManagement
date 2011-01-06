import datetime
import time
import calendar
import math

from celery.schedules import crontab


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
          }
LOCALS = {}

SCHEDULE_GLOBALS = {}
SCHEDULE_LOCALS = {'crontab': crontab}
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
