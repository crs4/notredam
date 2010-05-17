#########################################################################
#
# NotreDAM, Copyright (C) 2009, Sardegna Ricerche.
# Email: labcontdigit@sardegnaricerche.it
# Web: www.notre-dam.org
#
# This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#########################################################################

from django.db import models
from django.contrib.auth.models import User
from dam.workspace.models import DAMWorkspace as Workspace
from dam.repository.models import Item

class Basket(models.Model):
    """
    Implements simple basket per user
    """
    user = models.ForeignKey(User)
    items = models.ManyToManyField(Item)
    workspace = models.ForeignKey(Workspace)

    class Meta:
        unique_together = (("user", "workspace"))

    def get_size(self):
        """
        Returns number of items in basket
        """
        return self.items.all().count()

    def add_items(self, items):
        """
        Add items to a basket
        @param items a list or QuerySet of repository.Item
        """
        if isinstance(items, Item):
            items = [items]

        self.items.add(*items)

    def remove_items(self, items):
        """
        Remove items from a basket
        @param items a list or QuerySet of repository.Item
        """

        if isinstance(items, Item):
            items = [items]

        self.items.remove(*items)

    def item_in_basket(self, item):
        """
        Check if an item is contained in the current basket
        @param item an instance of repository.Item
        """
        return self.items.filter(pk=item.pk).count() > 0
    
    @staticmethod
    def get_basket(user, workspace):
        """
        Returns the basket for the given user and workspace
        @param user an instance of django.contrib.auth.User
        @param workspace an instance of workspace.DAMWorkspace
        """
        basket, created = Basket.objects.get_or_create(user=user, workspace=workspace)

        return basket
        
    @staticmethod    
    def empty_basket(user, workspace):
        """
        Delete the basket for the given user/workspace
        @param user an instance of django.contrib.auth.User
        @param workspace an instance of workspace.DAMWorkspace
        """
        Basket.objects.filter(user=user, workspace=workspace).delete()
    

