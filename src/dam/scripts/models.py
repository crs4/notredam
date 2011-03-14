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

thumbnail = {
    'thumbnail_image':{
        'script_name': 'adapt_image', 
        'params':{
            'actions':['resize'],
            'resize_h':100,
            'resize_w': 100,
            'source_variant': 'original',
            'output_variant': 'thumbnail',
            'output_format' : 'jpeg'        
            },
         'in': ['fe'],
         'out':['thumbnail']    
    },
}


action_audio = {
    'extract_original': {
        'script_name':  'extract_basic',
        'params' : {
            'source_variant': 'original',
        },
        'in':[],
        'out':[],
    },

    'extract_orig_xmp': {
        'script_name':  'extract_xmp',
        'params' : {
            'source_variant': 'original',
        },
        'in':[],
        'out':[],
    },

    'preview_audio': {
        'script_name':  'adapt_audio',
        'params' : {
            'source_variant': 'original',
            'output_variant': 'preview',
            'output_preset': 'MP3',
            'audio_bitrate_b': '128',
            'audio_rate': 44100,
        },
        'in':[],
        'out':[],
    },

    'extract_preview': {
        'script_name':  'extract_basic',
        'params' : {
            'source_variant': 'preview',
        },
        'in':[],
        'out':[],
    },
}

action_short = {
    'extract_original': {
        'script_name':  'extract_basic',
        'params' : {
            'source_variant': 'original',
        },
        'in':[],
        'out':['fe'],
    },

    'extract_orig_xmp': {
        'script_name':  'extract_xmp',
        'params' : {
            'source_variant': 'original',
        },
        'in':[],
        'out':['fx'],
    },

    'thumbnail': {
        'script_name':  'extract_frame',
        'params' : {
            'source_variant': 'original',
            'output_variant': 'thumbnail',
            'output_extension': '.jpg',
            'frame_w': '100',
            'frame_h': '100',
            'position': '25',
        },
        'in':['fe', 'fx'],
        'out':['thumbnail'],
    },
}


action_video = {
    'extract_original': {
        'script_name':  'extract_basic',
        'params' : {
            'source_variant': 'original',
        },
        'in':[],
        'out':['fe'],
    },

    'extract_orig_xmp': {
        'script_name':  'extract_xmp',
        'params' : {
            'source_variant': 'original',
        },
        'in':[],
        'out':['fx'],
    },

    'thumbnail': {
        'script_name':  'extract_frame',
        'params' : {
            'source_variant': 'original',
            'output_variant': 'thumbnail',
            'output_extension': '.jpg',
            'frame_w': '100',
            'frame_h': '100',
            'position': '25',
        },
        'in':['fe', 'fx'],
        'out':['thumbnail'],
    },

    'extract_thumbnail': {
        'script_name':  'extract_basic',
        'params' : {
            'source_variant': 'thumbnail',
        },
        'in':['thumbnail'],
        'out':[],
    },

    'preview': {
        'script_name':  'adapt_video',
        'params' : {
            'source_variant': 'original',
            'output_variant': 'preview',
            'output_preset': 'FLV',
            'video_width': '300',
            'video_height': '300',
            'video_bitrate_b': '640000',
            'video_framerate': '25/2',
            'audio_bitrate_kb': '128',
            'audio_rate': '44100',
        },
        'in':['fe', 'fx'],
        'out':['preview'],
    },

    'extract_preview': {
        'script_name':  'extract_basic',
        'params' : {
            'source_variant': 'preview',
        },
        'in':['preview'],
        'out':[],
    },
}


action_image = {
    'extract_original': {
        'script_name':  'extract_basic',
        'params' : {
            'source_variant': 'original',
        },
        'in':[],
        'out':['fe'],
    },

    'extract_orig_xmp': {
        'script_name':  'extract_xmp',
        'params' : {
            'source_variant': 'original',
        },
        'in':[],
        'out':['fx'],
    },

    'thumbnail_image':{
        'script_name': 'adapt_image', 
        'params':{
            'actions':['resize'],
            'resize_h':100,
            'resize_w': 100,
            'source_variant': 'original',
            'output_variant': 'thumbnail',
            'output_extension' : '.jpg'        
            },
         'in': ['fe', 'fx'],
         'out':['thumbnail']    
        
        
    },

    'extract_thumbnail': {
        'script_name':  'extract_basic',
        'params' : {
            'source_variant': 'thumbnail',
        },
        'in':['thumbnail'],
        'out':[],
    },

    'preview_image': {
        'script_name': 'adapt_image', 
        'params':{
            'actions':['resize'],
            'resize_h':300,
            'resize_w': 300,
            'source_variant': 'original',
            'output_variant': 'preview',
            'output_extension' : '.jpeg'        
            },
         'in': ['fe', 'fx'],
         'out':['preview']    
        },
        
    'extract_preview': {
        'script_name':  'extract_basic',
        'params' : {
            'source_variant': 'preview',
        },
        'in':['preview'],
        'out':[],
    },
    
    'fullscreen_image': {
        'script_name': 'adapt_image', 
        'params':{
            'actions':['resize'],
            'resize_h':800,
            'resize_w': 800,
            'source_variant': 'original',
            'output_variant': 'fullscreen',
            'output_extension' : '.jpeg'        
            },
         'in': ['fe', 'fx'],
         'out':['fullscreen']    
    },

    'extract_full': {
        'script_name':  'extract_basic',
        'params' : {
            'source_variant': 'fullscreen',
        },
        'in':['fullscreen'],
        'out':[],
    },
}

action_pdf = {
    'extract_original': {
        'script_name':  'extract_basic',
        'params' : {
            'source_variant': 'original',
        },
        'in':[],
        'out':['fe'],
    },

    'extract_orig_xmp': {
        'script_name':  'extract_xmp',
        'params' : {
            'source_variant': 'original',
        },
        'in':[],
        'out':['fx'],
    },

    'thumbnail': {
        'script_name':  'pdfcover',
        'params' : {
            'source_variant': 'original',
            'output_variant': 'thumbnail',
            'output_extension': '.jpg',
            'max_size': '100',
        },
        'in':['fe', 'fx'],
        'out':['thumbnail'],
    },

    'extract_thumbnail': {
        'script_name':  'extract_basic',
        'params' : {
            'source_variant': 'thumbnail',
        },
        'in':['thumbnail'],
        'out':[],
    },

    'preview': {
        'script_name':  'pdfcover',
        'params' : {
            'source_variant': 'original',
            'output_variant': 'preview',
            'output_extension': '.jpg',
            'max_size': '300',
        },
        'in':['fe', 'fx'],
        'out':['preview'],
    },

    'extract_preview': {
        'script_name':  'extract_basic',
        'params' : {
            'source_variant': 'preview',
        },
        'in':['preview'],
        'out':[],
    },
}

DEFAULT_PIPELINE = [{
                     'name': 'action_audio', 
                     'params': action_audio, 
                     'events': ['upload'],
                     'description': '', 
                     'media_types': ['audio']                     
                     },
                    {
                     'name': 'action_video', 
                     'params': action_video,
                     'description': '', 
                     'events': ['upload'], 
                     'media_types': ['video']                     
                     },
                     {
                     'name': 'action_image',
                     'description': '', 
                     'params': action_image, 
                     'events': ['upload'], 
                     'media_types': ['image']                     
                     },
                     {
                     'name': 'action_pdf', 
                     'description': '',
                     'params': action_pdf, 
                     'events': ['upload'], 
                     'media_types': ['application']                     
                     }
                    ]

def register_pipeline(ws,name, description, params, events, media_types): 
    from mprocessor.models import Pipeline   
    import logger
    
    p = Pipeline.objects.create(name=name,  description = description, params = params, workspace = ws)
    p.triggers.add(*events)
    p.media_type.add(*media_types)
    return p
