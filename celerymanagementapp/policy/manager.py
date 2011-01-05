import datetime
import time

from django.core.exceptions import ObjectDoesNotExist

from celerymanagementapp.models import PolicyModel
from celerymanagementapp.policy import policy

#==============================================================================#
default_time = datetime.datetime(2000,1,1)

class Entry(object):
    def __init__(self, policy, modified, last_run_time=None):
        self.policy = policy
        self.last_run_time = last_run_time or default_time
        self.modified = modified
        
    def is_due(self):
        return self.policy.is_due(self.last_run_time)
        
    def set_last_run_time(self, current_time):
        self.last_run_time = current_time
        
    def update(self, **kwargs):
        self.policy = kwargs.pop('policy', self.policy)
        self.last_run_time = kwargs.pop('last_run_time', self.last_run_time)
        self.modified = kwargs.pop('modified', self.modified)


#==============================================================================#
class Registry(object):
    def __init__(self):
        self.data = {}
        
    def __iter__(self):
        return self.data.itervalues()
        
    def register(self, obj):
        assert obj.enabled
        assert obj.id not in self.data
        policyobj = policy.Policy(source=obj.source, id=obj.id, name=obj.name)
        entry = Entry(policy=policyobj, modified=obj.modified, last_run_time=obj.last_run_time)
        self.data[obj.id] = entry
        
    def reregister(self, obj):
        assert obj.enabled
        entry = self.data[obj.id]
        assert obj.last_run_time is None or obj.last_run_time <= entry.last_run_time
        entry.policy.reinit(source=obj.source, name=obj.name)
        entry.update(modified=obj.modified)
        
    def unregister(self, id):
        del self.data[id]
        
    def refresh(self):
        updated = False
        objects = PolicyModel.objects.all()
        for id,entry in self.data.iteritems():
            try:
                obj = objects.get(id=id)
                if obj.enabled and obj.modified > entry.modified:
                    self.reregister(obj)
                    updated = True
                elif not obj.enabled:
                    self.unregister(id)
                    updated = True
            except ObjectDoesNotExist:
                self.unregister(id)
                updated = True
        
        for obj in objects:
            if obj.enabled and obj.id not in self.data:
                self.register(obj)
                updated = True
        
        return updated
                
    def save(self, id, current_time):
        entry = self.data[id]
        obj = PolicyModel.objects.get(id=id)
        if obj.modified > entry.modified:
            self.reregister(obj)
        obj.last_run_time = entry.last_run_time
        obj.modified, entry.modified = current_time, current_time
        obj.save()
        
    def close(self):
        self.refresh()
        

#==============================================================================#
MIN_LOOP_SLEEP_TIME = 30  # seconds
MAX_LOOP_SLEEP_TIME = 60*2  # seconds

class PolicyMain(object):
    def __init__(self):
        self.registry = Registry()
        #self.next_run_delta = 0
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_value, traceback):
        self.registry.close()
        
    def loop(self):
        print 'cmrun: Starting PolicyMain loop...'
        try:
            while True:
                self.refresh_registry()
                sleeptime = self.run_ready_policies()
                print 'cmrun: Sleeping for {0:.2f} seconds.'.format(sleeptime)
                time.sleep(max(sleeptime,MIN_LOOP_SLEEP_TIME))
        finally:
            self.on_loop_exit()
            
    def on_loop_exit(self):
        print 'cmrun: Exiting PolicyMain loop.'
        
    def refresh_registry(self):
        self.registry.refresh()
        
    def run_ready_policies(self):
        print 'cmrun: Running ready policies...'
        now = datetime.datetime.now()
        modified_ids = []
        run_deltas = []
        # TODO: put try block on inside of loop, so we can continue with other 
        # policies if an exception is thrown.
        try:
            for entry in self.registry:
                is_due, next_run_delta = entry.is_due()
                if is_due:
                    self.run_policy(entry.policy)
                    entry.set_last_run_time(now)
                    modified_ids.append(entry.policy.id)
                run_deltas.append(next_run_delta)
        finally:
            print 'cmrun: Finished running ready policies.'
            now = datetime.datetime.now()
            for id in modified_ids:
                self.registry.save(id, now)
        return min(run_deltas+[MAX_LOOP_SLEEP_TIME])
            
    def run_policy(self, policyobj):
        print 'cmrun: Running policy "{0}"'.format(policyobj.name)
        if policyobj.run_condition():
            policyobj.run_apply()
        
        
#==============================================================================#

def create_policy(name, source=None, schedule_src=None, condition_srcs=None, apply_src=None, enabled=True):
    """ Creates a new policy model object to the database.  If it doesn't 
        compile, an exception will be thrown.
    """
    assert isinstance(name, basestring)  # TODO: make this an exception
    source = policy.combine_sources(source, schedule_src, condition_srcs, apply_src)
    # The following should throw an exception if it fails.
    if not policy.check_source(source):
        raise RuntimeError('Invariant error:  policy.check_source() returned False.')
    model = PolicyModel(name=name, source=source, enabled=enabled)
    model.save()
    return model
    
def save_policy(model):
    """ Saves an existing policy model to the database.  If it doesn't compile, 
        an excecption will be thrown.
    """
    # The following should throw an exception if it fails.
    if not policy.check_source(model.source):
        raise RuntimeError('Invariant error:  policy.check_source() returned False.')
    model.save()
    
#==============================================================================#
    
    

