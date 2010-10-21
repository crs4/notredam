import time
from json import dumps, loads
from django.db import models
from app import processors
from dam.repository.models import Component

class Job(models.Model):
    job_id = models.CharField(max_length=32, primary_key=True, default=new_id)
    component = models.ForeignKey(Component)
    params = models.TextField(default='', blank=True)
