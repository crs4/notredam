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

import sys
import os
import re

from dam.metadata.models import MetadataProperty, MetadataValue
from dam.core.dam_metadata.models import XMPStructure

def reset_modified_flag(comp):

    """
    Reset flags modified in Component and in its metadata
    """
    comp_metadata = comp.metadata.filter(modified = True)
    for m in comp_metadata:
        m.modified = False
        m.save()
    comp.modified_metadata = False
    comp.save()

def synchronize_metadata(component):

    i = component.item
    c = component

    structures = [s.name for s in XMPStructure.objects.all()]
    changes = {}
    changes['item'] = {}
    my_metadata = i.metadata.filter(modified = True)
    for im in my_metadata:
        if im.schema.namespace.uri not in changes['item']:
            changes['item'][im.schema.namespace.uri] = {'prefix': im.schema.namespace.prefix, 'fields': {}}
        if im.schema.field_name not in changes['item'][im.schema.namespace.uri]['fields']:
            if im.schema.type == 'lang':
                changes['item'][im.schema.namespace.uri]['fields'][im.schema.field_name] = {'type':im.schema.type,'is_array':im.schema.is_array,'value':[im.value],'qualifier':[im.language], 'xpath':[]}
            elif im.schema.type in structures:
                changes['item'][im.schema.namespace.uri]['fields'][im.schema.field_name] = {'type':im.schema.type,'is_array':im.schema.is_array,'value':[im.value],'qualifier':[],'xpath':[im.xpath]}
            else:
                changes['item'][im.schema.namespace.uri]['fields'][im.schema.field_name] = {'type':im.schema.type,'is_array':im.schema.is_array,'value':[im.value],'qualifier':[],'xpath':[]}
        else:
            changes['item'][im.schema.namespace.uri]['fields'][im.schema.field_name]['value'].append(im.value)
            if im.schema.type == 'lang':
                changes['item'][im.schema.namespace.uri]['fields'][im.schema.field_name]['qualifier'].append(im.language)
            elif im.schema.type in structures:
                changes['item'][im.schema.namespace.uri]['fields'][im.schema.field_name]['xpath'].append(im.xpath)

    print "CHANGED IN ITEM: ", changes['item']

    changes[c.variant.name] = {}
    for k,v in changes['item'].iteritems():
        changes[c.variant.name][k] = v
    
    my_metadata = c.metadata.filter(modified = True)
    for m in my_metadata:
        print '    CHANGED IN ',c.variant.name, ': ',m.schema, m.schema.caption, m.schema.namespace, m.schema.field_name,m.schema.is_array,m.schema.is_choice, m.value	, m.schema.type, m.xpath, m.language, m.modified
    
        if m.schema.namespace.uri not in changes[c.variant.name]:
            changes[c.variant.name][m.schema.namespace.uri] = {'prefix': m.schema.namespace.prefix, 'fields': {}}
            print 'new namespace ', m.schema.namespace
        if m.schema.field_name not in changes[c.variant.name][m.schema.namespace.uri]['fields']:
            if m.schema.type == 'lang':
                changes[c.variant.name][m.schema.namespace.uri]['fields'][m.schema.field_name] = {'type':m.schema.type,'is_array':m.schema.is_array,'value':[m.value],'qualifier':[m.language], 'xpath':[]}
            elif m.schema.type in structures:
                changes[c.variant.name][m.schema.namespace.uri]['fields'][m.schema.field_name] = {'type':m.schema.type,'is_array':m.schema.is_array,'value':[m.value],'qualifier':[],'xpath':[m.xpath]}
            else:
                changes[c.variant.name][m.schema.namespace.uri]['fields'][m.schema.field_name] = {'type':m.schema.type,'is_array':m.schema.is_array,'value':[m.value],'qualifier':[], 'xpath':[]}
        else:
            changes[c.variant.name][m.schema.namespace.uri]['fields'][m.schema.field_name]['value'].append(m.value)
            if m.schema.type == 'lang':
                changes[c.variant.name][m.schema.namespace.uri]['fields'][m.schema.field_name]['qualifier'].append(m.language)
            elif m.schema.type in structures:
                changes[c.variant.name][m.schema.namespace.uri]['fields'][m.schema.field_name]['xpath'].append(m.xpath)

    print "     changes[",c.variant.name,"]:", changes[c.variant.name]
    
    return changes[c.variant.name]
