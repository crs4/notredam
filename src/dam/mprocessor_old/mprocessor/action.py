# Create your views here.
import time
from uuid import uuid4
from collections import deque
from json import dumps, loads
from dam.mprocessor import processors  # to be changed
from dam.mprocessor.models import Job
from dam.mprocessor.utils import MemCache


# Create your models here.
def new_id():
    return uuid4().hex

class MemCache:
    """Simple in memory cache for keeping arbitrary objects"""
    def __init__(self, max_entries):
        self.max_entries = max_entries
        self.d = {}
        self.q = deque()

    def __contains__(self, key):
        return key in self.d

    def add(self, key, item):
        if len(self.q) > self.max_entries:
            self.pop()
        self.d[key] = (item, time.time())
        self.q.append(key)

    def pop(self, key=None):
        "Pop the oldest item"
        key = self.q.popleft()
        del self.d[key]

    def delete(self, key):
        "Delete the item and returns the value"
        ret = None
        if key in self.d:
            ret = self.d[key][0]
            del self.d[key]
            self.q.remove(key)
        return ret
    get = delete   # a synonim of delete

    def purge(self, max_age):
        to_be_deleted = 0
        now = time.time()
        for key in self.q:
            if now - self.d[key][1] > max_age:
                to_be_deleted += 1
            else:
                break
        for n in xrange(to_be_deleted):
            self.pop()
        

memcache = MemCache(100)

class ActionError(Exception):
    pass


#
# example of use
# action = Action().set_component(component)\
#                  .push('xmp_embed')\
#                  .push('altro')\
#                  .execute(None)
#

class Action:
    def __init__(self, job_id=None):
        if job_id:
            self.job = memcache.get(job_id) or Job.objects.get(job_id=job_id)
            self.decoded_params = loads(self.job.params)
        else:
            self.job = Job( )
            self.decoded_params = [ ['dummy'] ]    # first function is always discarded

    def push(self, function_name, *function_params):
        self.decoded_params.append([function_name, function_params])
        return self

    def set_component(self, component):
        self.job.component = component
        return self

    def execute(self, data):
        "This changes the state of the job and it is not undoable"
        if not self.job.component:
            raise('Error: executing action with no component')
        self.decoded_params.remove(self.decoded_params[0])
        if self.decoded_params:
            self.job.params = dumps(self.decoded_params)
            self.job.save()
            fname, fparams = self.decoded_params[0]
            func = getattr(processors, fname)
            log.debug('Action.executing: %s' % fname)
            return func(self, data, *fparams)
        else:
            raise ActionError('Attempt to execute an empty action')

    def retire(self):
        self.job.delete()
