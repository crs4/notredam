from django.db import models
from mediadart.storage import new_id
from django.contrib.auth.models import User
from mediadart.mqueue.mqclient_async import Proxy

class Process(models.Model):    
    pipeline = models.ForeignKey('scripts.Pipeline')
    session = models.CharField(max_length=128,null = True, blank = True, unique = True)
    workspace = models.ForeignKey('workspace.DAMWorkspace')
    passed = models.IntegerField(default=0)     # number of actions passed
    failures = models.IntegerField(default=0)   # number of actions failed
    total = models.IntegerField(default=0)      # total number of actions to be performed
    start_date = models.DateTimeField(auto_now_add = True)
    end_date = models.DateTimeField(null = True, blank = True)
    launched_by = models.ForeignKey(User)

    def add_params(self, target_id):
        ProcessTarget.objects.create(process = self, target_id = target_id)
        
    def get_num_target_completed(self):
        return ProcessTarget.objects.filter(process = self, passed = self.pipeline.num_actions()).count()
    
    def get_num_target_failed(self):
        return ProcessTarget.objects.filter(process = self, failed__gt = 0).count()

    def run(self):
        Proxy('MProcessor').run(self.pk)        
    
class ProcessTarget(models.Model):
    process = models.ForeignKey(Process)
    target_id = models.IntegerField()           # foreign key to Item
    passed = models.IntegerField(default=0)
    failed = models.IntegerField(default=0)

    def completed(self):
        return self.passed == self.process.pipeline.num_actions()
    