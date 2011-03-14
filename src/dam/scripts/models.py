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


action_audio = {"preview":{"params":{"source_variant":"original","output_variant":"preview","output_preset":"MP3","audio_rate":"44100","audio_bitrate_kb":"128"},"in":["ext-gen155","ext-gen157"],"out":["ext-gen153"],"script_name":"adapt_audio","x":465,"y":193,"label":"preview"},
"extract_orig":{"params":{"source_variant":"original"},"in":[],"out":["ext-gen155"],"script_name":"extract_basic","x":26,"y":200,"label":"extract_basic"},
"extarct_preview":{"params":{"source_variant":"preview"},"in":["ext-gen153"],"out":[],"script_name":"extract_basic","x":916,"y":189,"label":"extract_preview"},
"extract_xmp":{"params":{"source_variant":"original"},"in":[],"out":["ext-gen157"],"script_name":"extract_xmp","x":17,"y":357,"label":"extract_xmp"}}

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


action_video = {"extract_xmp":{"params":{"source_variant":"original"},"in":[],"out":["ext-gen282","ext-gen284"],"script_name":"extract_xmp","x":14,"y":177,"label":"extract_xmp"},
"extract_orig":{"params":{"source_variant":"original"},"in":[],"out":["ext-gen286","ext-gen288"],"script_name":"extract_basic","x":9,"y":342,"label":"extract_basic"},
"thumbnail":{"params":{"source_variant":"original","output_variant":"thumbnail","frame_w":"100","frame_h":"100","position":"25","output_extension":".jpg"},"in":["ext-gen282","ext-gen286"],"out":["ext-gen290"],"script_name":"extract_frame","x":492,"y":334,"label":"thumbnail"},
"extract_thumbnail":{"params":{"source_variant":"thumbnail"},"in":["ext-gen290"],"out":[],"script_name":"extract_basic","x":922,"y":338,"label":"extract_thumbnail"},
"preview":{"params":{"source_variant":"original","output_variant":"preview","preset":"FLV","video_bitrate_b":"640000","audio_bitrate_kb":"128","video_framerate":"25/2","audio_rate":"44100","video_height":"300","video_width":"300"},"in":["ext-gen284","ext-gen288"],"out":["ext-gen292"],"script_name":"adapt_video","x":483,"y":171,"label":"preview"},
"extract_preview":{"params":{"source_variant":"preview"},"in":["ext-gen292"],"out":[],"script_name":"extract_basic","x":905,"y":166,"label":"extract_preview"}}


action_image = {"thumbnail":{"params":{"source_variant":"original", "output_variant":"thumbnail", "resize_h":"100","resize_w":"100","actions":"resize","output_extension":".jpg"},"in":["ext-gen375","ext-gen390"],"out":["ext-gen371"],"script_name":"adapt_image","x":511,"y":178,"label":"thumbnail" },

"extract_thumbnail":{"params":{"source_variant":"thumbnail"},"in":["ext-gen371"],"out":[],"script_name":"extract_basic","x":1040,"y":176,"label":"extract_basic"},

"extract_xmp_orig":{"params": {"source_variant":"original"},"in":[],"out":["ext-gen384","ext-gen387","ext-gen390"],"script_name":"extract_xmp","x":21,"y":459,"label":"extract_xmp"},

"fullscreen":{"params":{"source_variant":"original","output_variant":"fullscreen","resize_h":"800","resize_w":"800","actions":"resize","output_extension":".jpeg"},"in":["ext-gen377","ext-gen384"],"out":["ext-gen373"],"script_name":"adapt_image","x":519,"y":570,"label":"fullscreen"},

"extract_orig":{"params":{"source_variant":"original"},"in":[],"out":["ext-gen375","ext-gen377","ext-gen379"],"script_name":"extract_basic","x":19,"y":332,"label":"extract_basic"},

"extract_fullscreen":{"params":{"source_variant":"fullscreen"},"in":["ext-gen373"],"out":[],"script_name":"extract_basic","x":1042,"y":564,"label":"extract_basic"},

"extract_preview":{"params":{"source_variant":"preview"},"in":["ext-gen381"],"out":[],"script_name":"extract_basic","x":1024,"y":348,"label":"extract_basic"},

"preview":{"params":{"source_variant":"original","output_variant":"preview","resize_h":"300","resize_w":"300","actions":"resize","output_extension":".jpeg"},"in":["ext-gen379","ext-gen387"],"out":["ext-gen381"],"script_name":"adapt_image","x":508,"y":353,"label":"preview"}}


action_pdf = {"extract_xmp":{"params":{"source_variant":"original"},"in":[],"out":["ext-gen173","ext-gen175"],"script_name":"extract_xmp","x":14,"y":178,"label":"extract_xmp"},
"extract_orig":{"params":{"source_variant":"original"},"in":[],"out":["ext-gen177","ext-gen179"],"script_name":"extract_basic","x":10,"y":442,"label":"extract_basic"},
"thumbnail":{"params":{"source_variant":"original","output_variant":"thumbnail","maxsize":"300","output_extension":".jpg"},"in":["ext-gen173","ext-gen177"],"out":["ext-gen181"],"script_name":"pdfcover","x":551,"y":395,"label":"thumbnail"},
"extract_thumb":{"params":{"source_variant":"thumbnail"},"in":["ext-gen181"],"out":[],"script_name":"extract_basic","x":1036,"y":385,"label":"extract_basic"},
"preview":{"params":{"source_variant":"original","output_variant":"preview","maxsize":"300","output_extension":".jpg"},"in":["ext-gen175","ext-gen179"],"out":["ext-gen183"],"script_name":"pdfcover","x":560,"y":184,"label":"preview"},
"extract_preview":{"params":{"source_variant":"preview"},"in":["ext-gen183"],"out":[],"script_name":"extract_basic","x":1017,"y":185,"label":"extract_basic"}}

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
