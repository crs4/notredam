import os
import sys
from json import loads
import shutil
from pprint import pprint

from django.core.management import setup_environ
import settings
setup_environ(settings)
from django.db.models.loading import get_models
loaded_models = get_models()

from django.utils import simplejson
from django.contrib.auth.models import User
from django.db import transaction

from dam.mprocessor.models import Pipeline, Process, ProcessTarget, TriggerEvent
from dam.mprocessor.make_plugins import pipeline, pipeline2, simple_pipe
from dam.workspace.models import DAMWorkspace
from dam.core.dam_repository.models import Type
from dam.repository.models import Item, get_storage_file_name
from dam.variants.models import Variant
from dam.upload.views import _create_items, _run_pipelines
from supported_types import mime_types_by_type, supported_types

test = {
    'features':{
        'script_name': 'extract_basic', 
        'params':{
            'source_variant': 'original',
            },
         'in': [],
         'out':[]    
    },
}


# this is just to test the speed of mprocessor. same graph as action_image
action_pinger = {
    'ping1': { 'script_name': 'test.pinger', 'params': {}, 'in': [], 'out':['a'], },
    'ping2': { 'script_name': 'test.pinger', 'params': {}, 'in': [], 'out':['b'], },
    'ping3': { 'script_name': 'test.pinger', 'params': {}, 'in': ['a', 'b'], 'out':['c'], },
    'ping4': { 'script_name': 'test.pinger', 'params': {}, 'in': ['a', 'b'], 'out':['d'], },
    'ping5': { 'script_name': 'test.pinger', 'params': {}, 'in': ['a', 'b'], 'out':['e'], },
    'ping6': { 'script_name': 'test.pinger', 'params': {}, 'in': ['c'], 'out':[], },
    'ping7': { 'script_name': 'test.pinger', 'params': {}, 'in': ['d'], 'out':[], },
    'ping8': { 'script_name': 'test.pinger', 'params': {}, 'in': ['e'], 'out':[], },
}


audio_renditions = {
    'extract_original': {
        'script_name':  'extract_basic',
        'params' : {
            'source_variant_name': 'original',
        },
        'in':[],
        'out':['fe'],
        'label': 'extract_basic',
        'x': 27,
        'y': 256,
    },

    'extract_orig_xmp': {
        'script_name':  'extract_xmp',
        'params' : {
            'source_variant_name': 'original',
        },
        'in':[],
        'out':['fx'],
        'x': 18,
        'y': 413,
        'label': 'extract_xmp',
    },

    'preview_audio': {
        'script_name':  'adapt_audio',
        'params' : {
            'source_variant_name': 'original',
            'output_variant_name': 'preview',
            'output_preset': 'MP3',
            'audio_bitrate_b': '128',
            'audio_rate': 44100,
        },
        'in':['fe', 'fx'],
        'out':['preview'],
         'label': 'preview',
         'x': 466,
         'y': 249,
    },

    'extract_preview': {
        'script_name':  'extract_basic',
        'params' : {
            'source_variant_name': 'preview',
        },
                                          'label': 'extract_preview',
        'in':['preview'],
        'out':[],
                                          'x': 917,
                                          'y': 245,
    },
}


video_renditions = {
    'extract_original': {
        'script_name':  'extract_basic',
        'params' : {
            'source_variant_name': 'original',
        },
        'in':[],
        'out':['fe'],
                                         'label': 'extract_basic',
                                         'x': 10,
                                         'y': 398,
    },

    'extract_orig_xmp': {
        'script_name':  'extract_xmp',
        'params' : {
            'source_variant_name': 'original',
        },
        'in':[],
        'out':['fx'],
                                         'label': 'extract_xmp',
                                         'x': 15,
                                         'y': 233,
    },

    'thumbnail': {
        'script_name':  'extract_frame',
        'params' : {
            'source_variant_name': 'original',
            'output_variant_name': 'thumbnail',
            'output_extension': '.jpg',
            'frame_w': '100',
            'frame_h': '100',
            'position': '25',
        },
        'in':['fe', 'fx'],
        'out':['thumbnail'],
                                         'label': 'thumbnail',
                                         'x': 493,
                                         'y': 390,
    },

    'extract_thumbnail': {
        'script_name':  'extract_basic',
        'params' : {
            'source_variant_name': 'thumbnail',
        },
        'in':['thumbnail'],
        'out':[],
                                          'label': 'extract_thumbnail',
                                          'x': 923,
                                          'y': 394,
    },

    'preview': {
        'script_name':  'adapt_video',
        'params' : {
            'source_variant_name': 'original',
            'output_variant_name': 'preview',
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
                                          'label': 'preview',
                                          'x': 484,
                                          'y': 227,
    },

    'extract_preview': {
        'script_name':  'extract_basic',
        'params' : {
            'source_variant_name': 'preview',
        },
        'in':['preview'],
        'out':[],
                                          'label': 'extract_preview',
                                          'x': 906,
                                          'y': 222,
    },
}


image_renditions = {
    'extract_original': {
        'script_name':  'extract_basic',
        'params' : {
            'source_variant_name': 'original',
        },
        'in':[],
        'out':['fe'],
                                          'label': 'extract_basic',
                                          'x': 20,
                                          'y': 388,
    },

    'extract_orig_xmp': {
        'script_name':  'extract_xmp',
        'params' : {
            'source_variant_name': 'original',
        },
        'in':[],
        'out':['fx'],
                                          'label': 'extract_xmp',
                                          'x': 22,
                                          'y': 515,
    },

    'thumbnail_image':{
        'script_name': 'adapt_image', 
        'params':{
            'actions':['resize'],
            'resize_h':100,
            'resize_w': 100,
            'source_variant_name': 'original',
            'output_variant_name': 'thumbnail',
            'output_extension' : '.jpg'        
            },
         'in': ['fe', 'fx'],
         'out':['thumbnail'],   
                                         'label': 'thumbnail',
                                         'x': 512,
                                         'y': 234,
        
        
    },

    'extract_thumbnail': {
        'script_name':  'extract_basic',
        'params' : {
            'source_variant_name': 'thumbnail',
        },
        'in':['thumbnail'],
        'out':[],
                                          'label': 'extract_basic',
                                          'x': 1041,
                                          'y': 232,
    },

    'preview_image': {
        'script_name': 'adapt_image', 
        'params':{
            'actions':['resize'],
            'resize_h':300,
            'resize_w': 300,
            'source_variant_name': 'original',
            'output_variant_name': 'preview',
            'output_extension' : '.jpeg'        
            },
         'in': ['fe', 'fx'],
         'out':['preview'],   
                                          'label': 'preview',
                                          'x': 509,
                                          'y': 409,
        },
        
    'extract_preview': {
        'script_name':  'extract_basic',
        'params' : {
            'source_variant_name': 'preview',
        },
        'in':['preview'],
        'out':[],
                                          'label': 'extract_basic',
                                          'x': 1025,
                                          'y': 404,
    },
    
    'fullscreen_image': {
        'script_name': 'adapt_image', 
        'params':{
            'actions':['resize'],
            'resize_h':800,
            'resize_w': 800,
            'source_variant_name': 'original',
            'output_variant_name': 'fullscreen',
            'output_extension' : '.jpeg'        
            },
         'in': ['fe', 'fx'],
         'out':['fullscreen'],   
                                          'label': 'fullscreen',
                                          'x': 520,
                                          'y': 626,
    },

    'extract_full': {
        'script_name':  'extract_basic',
        'params' : {
            'source_variant_name': 'fullscreen',
        },
        'in':['fullscreen'],
        'out':[],
                                          'label': 'extract_basic',
                                          'x': 1043,
                                          'y': 620,
    },
}

doc_renditions = {
    'extract_original': {
        'script_name':  'extract_basic',
        'params' : {
            'source_variant_name': 'original',
        },
        'in':[],
        'out':['fe'],
                                         'label': 'extract_basic',
                                         'x': 11,
                                         'y': 498,
    },

    'extract_orig_xmp': {
        'script_name':  'extract_xmp',
        'params' : {
            'source_variant_name': 'original',
        },
        'in':[],
        'out':['fx'],
                                         'label': 'extract_xmp',
                                         'x': 15,
                                         'y': 234,
    },

    'thumbnail': {
        'script_name':  'pdfcover',
        'params' : {
            'source_variant_name': 'original',
            'output_variant_name': 'thumbnail',
            'output_extension': '.jpg',
            'max_size': '100',
        },
        'in':['fe', 'fx'],
        'out':['thumbnail'],
                                         'label': 'thumbnail',
                                         'x': 552,
                                         'y': 451,
    },

    'extract_thumbnail': {
        'script_name':  'extract_basic',
        'params' : {
            'source_variant_name': 'thumbnail',
        },
        'in':['thumbnail'],
        'out':[],
                                          'label': 'extract_basic',
                                          'x': 1037,
                                          'y': 441,
    },

    'preview': {
        'script_name':  'pdfcover',
        'params' : {
            'source_variant_name': 'original',
            'output_variant_name': 'preview',
            'output_extension': '.jpg',
            'max_size': '300',
        },
        'in':['fe', 'fx'],
        'out':['preview'],
                                          'label': 'preview',
                                          'x': 561,
                                          'y': 240,
    },

    'extract_preview': {
        'script_name':  'extract_basic',
        'params' : {
            'source_variant_name': 'preview',
        },
        'in':['preview'],
        'out':[],
                                          'label': 'extract_basic',
                                          'x': 1018,
                                          'y': 241,
    },
}

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
            'source_variant_name': 'original',
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


action_magick = {
    'image_magick': {
        'script_name':  'adapt_magick',
        'params' : {
            'source_variant_name': 'original',
            'output_variant_name': 'thumbnail',
            'output_extension' : '.jpg',
            'cmdline': '-resize 100x100 -annotate 90x90 Notredam',
        },
        'in':[],
        'out':[],
    },
}


# all parameters are passed dynamically by the launcher metadata.views.sync_component
embed_xmp = {
    'embed_xmp': {
        'script_name': 'embed_xmp',
        'params' : {
            'source_variant_name': 'original',
            },
        'in':[],
        'out':[],
                                         'label': 'embed_xmp',
                                         'x': 603,
                                         'y': 263,
    },
}

standard_actions =  [('upload_audio', audio_renditions, 'audio', 'upload'), 
                    ('upload_video', video_renditions, 'video', 'upload'),
                    ('upload_image', image_renditions, 'image', 'upload'),
                    ('upload_pdf', doc_renditions,   'doc', 'upload'),
                    ('embed_xmp', embed_xmp, '', 'sync_xmp'),       # '' means any type
                   ]

class DoTest:
    def __init__(self):
        self.ws = DAMWorkspace.objects.get(pk = 1)
        self.user = User.objects.get(username='admin')

    def _search_types(self, media_types):
        err_msg = ""
        tbd = []
        l = media_types.split(':')
        for media_type in l:
            if not media_type:
                continue
            if media_type.find('/') < 0:
                if media_type in mime_types_by_type:
                    for subtype in mime_types_by_type[media_type]:
                        mime_type = '%s/%s' % (media_type, subtype)
                        tbd.append((mime_type, supported_types[mime_type][0]))
                else:
                    err_msg += '### Unrecognized media type %s\n' % media_type
            else:
                if media_type in supported_types:
                    tbd.append((media_type, supported_types[media_type][0]))
                else:
                    err_msg += '### unrecognized type/subtype %s: %s\n' % (media_type, str(e))
        if err_msg:
            print err_msg
        return tbd

    def register(self, name, trigger, media_types, description, pipeline_definition):
        e, created=TriggerEvent.objects.get_or_create(name=trigger)
        pipe = Pipeline.objects.create(name=name.replace('_', ' '),  description='', params = simplejson.dumps(pipeline_definition), workspace = self.ws)
        pipe.triggers.add(e)
        for (mime_type, ext) in self._search_types(media_types):
            t=Type.objects.get_or_create_by_mime(mime_type, ext)
            pipe.media_type.add(t)
        pipe.save
        print 'registered pipeline %s, pk=%s, trigger=%s' % (name, pipe.pk, '-'.join( [x.name for x in pipe.triggers.all()] ) )

    def runmany(self, times, trigger, pk):
        items = [Item.objects.get(pk=pk) for x in xrange(int(times))]
        ret = _run_pipelines(items, trigger, self.user, self.ws)
        print('Executed process %s' % ' '.join(ret))

    def execpipes(self, trigger, filepaths):
        items = _create_items(filepaths, 'original', self.user, self.ws)
        ret = _run_pipelines(items, trigger,  self.user, self.ws)
        print('Executed processes %s' % ' '.join(ret))

    def show_pipelines(self):
        print ("Pipelines:")
        pipelines=Pipeline.objects.all()
        for p in pipelines:
            d = loads(p.params)
            actions = d.keys()
            actions.sort()
            triggers = [x.name for x in p.triggers.all()]
            print('Pipe pk=%s name=%s triggers=%s\n  %s' % (p.pk, p.name, ', '.join(triggers), '\n  '.join(actions)))

    def show_process(self):
        print ("Processes:")
        processes=Process.objects.all()
        for p in processes:
            targets = ProcessTarget.objects.filter(process=p, actions_todo__gt=0)
            print('Process pk=%s start=%s end=%s pending=%s' % (p.pk, p.start_date, p.end_date, targets.count()))

    def show_items(self):
        items=Item.objects.all()
        for i in items:
            c = i.component_set.all()
            c0 = c[0]
            print ('%s (%s): %s: %s -> %s' % (i.pk, 
                                    i.type.name, 
                                    '-'.join([str(x.pk) for x in c]),
                                    c0.file_name, i.ID))

    def show_types(self):
        types=Type.objects.all()
        for t  in types:
            print t

    def show_pipe(self, pipe):
        p = Pipeline.objects.get(pk=pipe)
        params = loads(p.params)
        print 'Pipeline %s %s' % (pipe, p.name)
        pprint(params)

    def get_status(self, pid, items):
        if pid == 'auto':
            pid=[x.strip() for x in open('/tmp/uploader', 'r').readlines()]
        if items:
            targets = ProcessTarget.objects.filter(process__in=pid, target_id__in=items, actions_todo=0)
        else:
            targets = ProcessTarget.objects.filter(process=pid)
        print 'found %d targets' % len(targets)
        for t in targets:
            if not t.result:
                pprint("item %s: no result in DB" % t.target_id)
            else:
                result = loads(t.result)
                pprint("target %s" % t.target_id)
                pprint(result, indent=5, width=100)

#            if 'thumbnail_image' in result:
#                if result['thumbnail_image'][0]:
#                    print "item %s: thumbnail %s" % (t.target_id, result['thumbnail_image'][1])
#                else:
#                    print 'item %s: thumbnail generation failure: %s' % (t.target_id, result['thumbnail_image'][1])


usage="""
Usage: script_test.py <action> <arguments>
 where action is
 
  register <trigger> <mime_type> [pipeline_definition]  
  upload <trigger> <filenames>

  Examples:
  python actionctl.py standard_upload
    register all default pipelines for image, video, audio and doc.
    delete existing pipelines triggered for upload

  python actionctl.py register up1 upload image actions  
    registers the pipeline described in the global dict "actions" with the name up1,
    to react to the trigger "upload", for all types "image/*"

  python actionctl.py execpipes upload megan-fox*.jpg
    exec all tipes registered for trigger upload on the files megan-fox*.jpg 
"""


def main(argv):
    test = DoTest()
    if len(argv) < 2: 
        argv.append('register')
    task = argv[1]

    if task == 'register':
        name = argv[2]
        trigger = argv[3]
        mime_type = argv[4]
        pipeline_def = globals()[argv[5]]
        test.register(name, trigger, mime_type, '', pipeline_def)

    elif task == 'reg_standard':
        triggers = [x[3] for x in standard_actions]
        [x.delete() for x in Pipeline.objects.filter(triggers__name__in=triggers)]
        for name, action, mime, trigger in standard_actions:
            print('Registering standard pipeline %s for %s' % (name, mime))
            test.register(name, trigger, mime, '', action)
    
    elif task == 'execpipes':
        trigger = argv[2]
        files = argv[3:]
        if not files:
            raise Exception('too few arguments')
        test.execpipes(trigger, files)

    elif task == 'runmany':
        times = argv[2]
        trigger = argv[3]
        pk = argv[4]
        test.runmany(times, trigger, pk)

    elif task == 'clear':
        print('deleting all processes and processtargets')
        [x.delete() for x in Process.objects.all()]
        [x.delete() for x in ProcessTarget.objects.all()]
   
    elif task == 'status':
        process_id = argv[2]
        targets = argv[3:]
        test.get_status(process_id, targets)

    elif task == 'show':
        what = argv[2]
        if what == 'pipes':
            test.show_pipelines()
        elif what == 'process':
            test.show_process()
        elif what == 'items':
            test.show_items()
        elif what == 'types':
            test.show_types()
        elif what == 'pipe':
            pipe = argv[3]
            test.show_pipe(pipe)
        else:
            print("Error: use show pipe or show process")

    else:
        print usage
    
if __name__=='__main__':
    main(sys.argv)
