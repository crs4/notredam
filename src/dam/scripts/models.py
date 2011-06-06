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
            'source_variant_name': ['edited', 'original'],
            'output_variant_name': 'thumbnail',
            'output_format' : 'jpeg'        
            },
         'in': ['fe'],
         'out':['thumbnail']    
    },
}


action_audio = {"adapt_audio56":{"params":{"source_variant_name":['edited', 'original'],"output_variant_name":"preview","output_preset":"MP3","audio_rate":"44100","audio_bitrate_kb":"128"},"in":["extract_basic153","extract_xmp154"],"out":["preview152"],"script_name":"adapt_audio","x":466,"y":249,"label":"preview"},"extract_basic104":{"params":{"source_variant_name":["edited", "original"]},"in":[],"out":["extract_basic153"],"script_name":"extract_basic","x":27,"y":256,"label":"extract_basic"},"extract_basic120":{"params":{"source_variant_name":"preview"},"in":["preview152"],"out":[],"script_name":"extract_basic","x":917,"y":245,"label":"extract_preview"},"extract_xmp136":{"params":{"source_variant_name":["edited", "original"]},"in":[],"out":["extract_xmp154"],"script_name":"extract_xmp","x":18,"y":413,"label":"extract_xmp"}}
action_short = {
    'extract_original': {
        'script_name':  'extract_basic',
        'params' : {
            'source_variant_name': 'original',
        },
        'in':[],
        'out':['fe'],
    },

    'extract_orig_xmp': {
        'script_name':  'extract_xmp',
        'params' : {
            'source_variant_name': 'original',
        },
        'in':[],
        'out':['fx'],
    },

    'thumbnail': {
        'script_name':  'extract_frame',
        'params' : {
            'source_variant_name': ['edited', 'original'],
            'output_variant_name': 'thumbnail',
            'output_extension': '.jpg',
            'frame_w': '100',
            'frame_h': '100',
            'position': '25',
        },
        'in':['fe', 'fx'],
        'out':['thumbnail'],
    },
}


action_video = {"extract_xmp56":{"params":{"source_variant_name":["edited", "original"]},"in":[],"out":["extract_xmp281"],"script_name":"extract_xmp","x":15,"y":233,"label":"extract_xmp"},"extract_basic72":{"params":{"source_variant_name":["edited", "original"]},"in":[],"out":["extract_basic282"],"script_name":"extract_basic","x":10,"y":398,"label":"extract_basic"},"extract_frame88":{"params":{"source_variant_name":['edited', 'original'],"output_variant_name":"thumbnail","frame_w":"100","frame_h":"100","position":"25","output_extension":".jpg"},"in":["extract_xmp281","extract_basic282"],"out":["thumbnail283"],"script_name":"extract_frame","x":493,"y":390,"label":"thumbnail"},"extract_basic118":{"params":{"source_variant_name":"thumbnail"},"in":["thumbnail283"],"out":[],"script_name":"extract_basic","x":923,"y":394,"label":"extract_thumbnail"},"adapt_video134":{"params":{"source_variant_name":['edited', 'original'],"output_variant_name":"preview","output_preset":"FLV","video_bitrate_b":"640000","audio_bitrate_kb":"128","video_framerate":"25/2","audio_rate":"44100","video_height":"300","video_width":"300"},"in":["extract_xmp281","extract_basic282"],"out":["preview284"],"script_name":"adapt_video","x":484,"y":227,"label":"preview"},"extract_basic265":{"params":{"source_variant_name":"preview"},"in":["preview284"],"out":[],"script_name":"extract_basic","x":906,"y":222,"label":"extract_preview"}}
action_image = {"adapt_image56":{"params":{"source_variant_name":['edited', 'original'],"output_variant_name":"thumbnail","resize_h":"100","resize_w":"100","actions":"resize","output_extension":".jpg"},"in":["extract_xmp371","extract_basic373"],"out":["thumbnail370"],"script_name":"adapt_image","x":512,"y":195,"label":"thumbnail"},"extract_basic134":{"params":{"source_variant_name":"thumbnail"},"in":["thumbnail370"],"out":[],"script_name":"extract_basic","x":1041,"y":193,"label":"extract_basic"},"extract_xmp150":{"params":{"source_variant_name":["edited", "original"]},"in":[],"out":["extract_xmp371"],"script_name":"extract_xmp","x":22,"y":476,"label":"extract_xmp"},"adapt_image166":{"params":{"source_variant_name":['edited', 'original'],"output_variant_name":"fullscreen","resize_h":"800","resize_w":"800","actions":"resize","output_extension":".jpeg"},"in":["extract_xmp371","extract_basic373"],"out":["fullscreen372"],"script_name":"adapt_image","x":520,"y":587,"label":"fullscreen"},"extract_basic244":{"params":{"source_variant_name":["edited", "original"]},"in":[],"out":["extract_basic373"],"script_name":"extract_basic","x":20,"y":349,"label":"extract_basic"},"extract_basic260":{"params":{"source_variant_name":"fullscreen"},"in":["fullscreen372"],"out":[],"script_name":"extract_basic","x":1043,"y":581,"label":"extract_basic"},"extract_basic276":{"params":{"source_variant_name":"preview"},"in":["preview374"],"out":[],"script_name":"extract_basic","x":1025,"y":365,"label":"extract_basic"},"adapt_image292":{"params":{"source_variant_name":['edited', 'original'],"output_variant_name":"preview","resize_h":"300","resize_w":"300","actions":"resize","output_extension":".jpeg"},"in":["extract_xmp371","extract_basic373"],"out":["preview374"],"script_name":"adapt_image","x":509,"y":370,"label":"preview"}}
action_pdf = {"extract_xmp56":{"params":{"source_variant_name":["edited", "original"]},"in":[],"out":["extract_xmp172"],"script_name":"extract_xmp","x":15,"y":234,"label":"extract_xmp"},"extract_basic72":{"params":{"source_variant_name":["edited", "original"]},"in":[],"out":["extract_basic173"],"script_name":"extract_basic","x":11,"y":498,"label":"extract_basic"},"pdfcover88":{"params":{"source_variant_name":['edited', 'original'],"output_variant_name":"thumbnail","max_size":"300","output_extension":".jpg"},"in":["extract_xmp172","extract_basic173"],"out":["thumbnail174"],"script_name":"pdfcover","x":552,"y":451,"label":"thumbnail"},"extract_basic114":{"params":{"source_variant_name":"thumbnail"},"in":["thumbnail174"],"out":[],"script_name":"extract_basic","x":1037,"y":441,"label":"extract_basic"},"pdfcover130":{"params":{"source_variant_name":['edited', 'original'],"output_variant_name":"preview","max_size":"300","output_extension":".jpg"},"in":["extract_xmp172","extract_basic173"],"out":["preview175"],"script_name":"pdfcover","x":561,"y":240,"label":"preview"},"extract_basic156":{"params":{"source_variant_name":"preview"},"in":["preview175"],"out":[],"script_name":"extract_basic","x":1018,"y":241,"label":"extract_basic"}}
embed_xmp = {"embed_xmp57":{"params":{"source_variant_name":""},"dynamic":["source_variant_name"],"in":[],"out":[],"script_name":"embed_xmp","x":603,"y":263,"label":"embed_xmp"}}
extract_all = {"extract_basic57":{"params":{"source_variant_name":""}, "dynamic":["source_variant_name"],"in":[],"out":[],"script_name":"extract_basic","x":435,"y":227,"label":"extract_basic"},"extract_xmp73":{"params":{"source_variant_name":""}, "dynamic":["source_variant_name"], "in":[],"out":[],"script_name":"extract_xmp","x":433,"y":376,"label":"extract_xmp"}}

DEFAULT_PIPELINE = [{
                     'name': 'audio renditions', 
                     'params': action_audio, 
                     'events': ['upload'],
                     'description': '', 
                     'media_types': ['audio']                     
                     },
                    {
                     'name': 'video renditions', 
                     'params': action_video,
                     'description': '', 
                     'events': ['upload'], 
                     'media_types': ['video']                     
                     },
                     {
                     'name': 'image renditions',
                     'description': '', 
                     'params': action_image, 
                     'events': ['upload'], 
                     'media_types': ['image']                     
                     },
                     {
                     'name': 'doc renditions', 
                     'description': '',
                     'params': action_pdf, 
                     'events': ['upload'], 
                     'media_types': ['doc']                     
                     },
                     {
                     'name': 'embed xmp', 
                     'description': '',
                     'params': embed_xmp, 
                     'events': [], 
                     'media_types': ['doc', 'video', 'audio', 'image']                     
                     },
                     {
                     'name': 'extract features and xmp', 
                     'description': '',
                     'params': extract_all, 
                     'events': ['replace_rendition'], 
                     'media_types': ['doc', 'video', 'audio', 'image']                     
                     }
                    ]

def register_pipeline(ws,name, description, params, events, media_types): 
    from mprocessor.models import Pipeline   
    from dam.logger import logger
    
    p = Pipeline.objects.create(name=name,  description = description, params = params, workspace = ws)
    p.triggers.add(*events)
    p.media_type.add(*media_types)
    return p
