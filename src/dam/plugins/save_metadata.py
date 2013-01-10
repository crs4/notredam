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

from django.core.management import setup_environ
import dam.settings as settings
setup_environ(settings)
from django.db.models.loading import get_models
get_models()


from dam.repository.models import Item

def save_metadata(item, metadata_namespace, metadata_name, metadata_value):
    item.set_metadata(metadata_namespace, metadata_name, metadata_value)
        

def run(workspace, item_id, metadata_namespace, metadata_name, metadata_value):
    item = Item.objects.get(pk = item_id)
    save_metadata(item, metadata_namespace, metadata_name, metadata_value)


def test():
    print 'test'
    item = Item.objects.all()[0]
    workspace = item.workspaces.all()[0]
    d = run(workspace,
            item.pk,
             metadata_namespace = 'dublin core',
        metadata_name = 'subject',
        metadata_value = ['test1', 'test2']
            )
    d.addBoth(print_result)

    
    
    

    
