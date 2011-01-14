from django.db import models
from mediadart.storage import new_id

class Process(models.Model):
    process_id = models.CharField(max_length=32, primary_key=True, default=new_id)
    pipeline = models.ForeignKey('Pipeline')
    passed = models.IntegerField(default=0)     # number of actions passed
    failures = models.IntegerField(default=0)   # number of actions failed
    total = models.IntegerField(default=0)      # total number of actions to be performed
    started = models.TimeField(auto_now_add=True)

class Pipeline(models.Model):
    key = models.CharField(max_length=32, primary_key=True, default=new_id)
    # upload etc, used to group pipelines that must be run in succession at certain points
    pipe_type = models.CharField(max_length=32, blank=True, default="") 
    params = models.TextField(blank=False)
    description = models.TextField(blank=True)

class ItemSet(models.Model):
    process = models.ForeignKey(Process)
    item_id = models.IntegerField()           # foreign key to Item
    passed = models.IntegerField(default=0)
    failed = models.IntegerField(default=0)
