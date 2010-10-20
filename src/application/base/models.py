from django.db import models

# Create your models here.


class Rating(models.Model):
    dam_id = models.CharField(max_length=42)
    value = models.FloatField()
    number_of_votes = models.PositiveIntegerField()
    users = models.ManyToManyField('auth.User')
    
    
    
    
