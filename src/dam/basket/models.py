#
# Licensed under the EUPL, Version 1.0
#
# You may obtain a copy of the License in your language at:
#
# http://ec.europa.eu/idabc/7330
#
# Read also the LICENSE file included in this package for
# more information.
# file dam basket models.py
##########################################################

from django.db import models
from django.contrib.auth.models import User
from dam.workspace.models import Workspace
from dam.repository.models import Item

class Basket(models.Model):
  user = models.ForeignKey(User)
  item = models.ForeignKey(Item)
  workspace = models.ForeignKey(Workspace)

