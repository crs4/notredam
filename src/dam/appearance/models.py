from django.db import models

# Create your models here.

class Theme(models.Model):

    name = models.CharField(max_length=64)
    css_file = models.CharField(max_length=128)
    description = models.CharField(max_length=512)
    SetAsCurrent = models.BooleanField(default=False)
    IsDefault = models.BooleanField(default=False)

    def __str__(self):
        return self.name


