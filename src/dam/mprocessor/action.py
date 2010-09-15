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


class Action:
    def __init__(self, job_id=None):
        self.job_id = job_id
        self.decoded_params = None
        if job_id:
            self.job = memcache.get(job_id) or Job.objects.get(job_id=job_id)
        else:
            self.job = Job( )

    def start(self, component, function_list):
        if self.job_id:
            raise ActionError('Error: staring a persisted action')
        self.job_id = self.job.id
        self.job.component = component
        self.job.params = dumps(function_list)
        self.job.save()
        self.execute()

    def execute(self):
        self.decoded_params = self.decoded_params or loads(self.job.params)
        if not self.decoded_params:
            return self.end_action()
        fname = self.decoded_params[-1]
        f = getattr(processors, fname)
        try:
            return f(self.job.component, self.job.job_id)
        except Exception ,e:
            log.error('Action.execute: error %s' % str(e))
            return

    def pop(self):
        self.decoded_params = self.decoded_params or loads(self.job.params)
        self.decoded_params.pop()
        self.job.params = dumps(self.decoded_params)
        self.job.save()

    def retire(self):
        self.job.delete()
