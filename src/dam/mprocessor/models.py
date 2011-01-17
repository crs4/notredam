from django.db import models
from mediadart.storage import new_id
from django.contrib.auth.models import User

class Process(models.Model):    
    script = models.ForeignKey('scripts.Script')
    session = models.CharField(max_length=128,null = True, blank = True, unique = True)
    
    passed = models.IntegerField(default=0)     # number of actions passed
    failures = models.IntegerField(default=0)   # number of actions failed
    total = models.IntegerField(default=0)      # total number of actions to be performed
    start_date = models.DateTimeField(auto_now_add = True)
    end_date = models.DateTimeField(null = True, blank = True)
    launched_by = models.ForeignKey(User)
    
class ProcessTarget(models.Model):
    process = models.ForeignKey(Process)
    target_id = models.IntegerField()           # foreign key to Item
    passed = models.IntegerField(default=0)
    failed = models.IntegerField(default=0)

