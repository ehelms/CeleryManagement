import time
import datetime
import sys
from celery import states
from celery.events import state as celery_state

class DispatchedTask(celery_state.Task):
    # These fields in _disptask_defaults are added to those defined by 
    # celery.event.state.Task in _defaults.
    _disptask_defaults = {
        'sent': None,
        'failed': None,
        'received': None,
        'started': None,
        'succeeded': None,
        'waittime': None,
        'totaltime': None,
        }
        
    def __init__(self, **fields):
        super(DispatchedTask, self).__init__(**dict(self._disptask_defaults, 
                                                    **fields))
        
    def on_sent(self, timestamp=None, **fields):
        self.sent = timestamp
        if self.received:
            self.waittime = self.received - timestamp
        self.update(states.PENDING, timestamp, fields)

    def on_received(self, timestamp=None, **fields):
        self.received = timestamp
        if self.sent:
            self.waittime = timestamp - self.sent
        if self.succeeded:
            self.runtime = self.succeeded - timestamp
        self.update(states.RECEIVED, timestamp, fields)

    def on_succeeded(self, timestamp=None, **fields):
        self.succeeded = timestamp
        if self.received:
            self.runtime = timestamp - self.received
        self.update(states.SUCCESS, timestamp, fields)
        self.totaltime = self.runtime
        if self.sent:
            self.totaltime = self.succeeded - self.sent
            
class Worker(celery_state.Worker):
    # on start
    # on stop
    pass


class State(celery_state.State):
    def __init__(self):
        super(State, self).__init__()
        self.group_handlers['cm'] = self.null_event
    
    # Overwrite subclass version of this method so we can create DispatchedTasks
    def get_or_create_task(self, uuid):
        """Get or create task by uuid."""
        try:
            return self.tasks[uuid]
        except KeyError:
            task = self.tasks[uuid] = DispatchedTask(uuid=uuid)
            return task
    
    def null_event(self, type, fields):
        pass

