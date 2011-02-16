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

#from django.db import models

from django.utils import simplejson

DEFAULT_PIPELINE = [{
    'name': 'uploader',
    'type': 'upload',
    'description': '',
    'params': simplejson.dumps({'thumbnail_image':{
        'script_name': 'adapt_image', 
        'params':{
            'actions':['resize'],
            'resize_h':100,
            'resize_w': 100,
            'source_variant': 'original',
            'output_variant': 'thumbnail',
            'output_format' : 'jpeg'        
            },
         'in': [],
         'out':[]    
        
        
    },
    'preview_image': {
        'script_name': 'adapt_image', 
        'params':{
            'actions':['resize'],
            'resize_h':300,
            'resize_w': 300,
            'source_variant': 'original',
            'output_variant': 'preview',
            'output_format' : 'jpeg'        
            },
         'in': [],
         'out':[]    
        },
        
    
    'fullscreen_image': {
        'script_name': 'adapt_image', 
        'params':{
            'actions':['resize'],
            'resize_h':800,
            'resize_w': 600,
            'source_variant': 'original',
            'output_variant': 'fullscreen',
            'output_format' : 'jpeg'        
            },
         'in': [],
         'out':[]    
    },
    
})
    
                     
                     
                     
}]

