import os
import sys
from json import loads
import shutil
from pprint import pprint

from django.core.management import setup_environ
#from django.db import transaction
import settings
setup_environ(settings)

from django.utils import simplejson
from django.contrib.auth.models import User
from django.db import transaction

from dam.mprocessor.models import new_processor, Pipeline, Process, ProcessTarget, TriggerEvent
from dam.mprocessor.make_plugins import pipeline, pipeline2, simple_pipe
from dam.workspace.models import DAMWorkspace
from dam.core.dam_repository.models import Type
from dam.repository.models import Item, get_storage_file_name
from dam.variants.models import Variant
from mediadart.storage import new_id
from dam.upload.views import _create_item, _create_variant
from supported_types import mime_types_by_type, supported_types

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
        'out':['fe'],
    },

    'extract_xmp': {
        'script_name':  'extract_xmp',
        'params' : {
            'source_variant': 'original',
        },
        'in':[],
        'out':['fe'],
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

    'extract_frame': {
        'script_name':  'extract_frame',
        'params' : {
            'source_variant': 'original',
            'output_variant': 'thumbnail',
            'output_format': 'image/jpeg',
            'frame_w': '100',
            'frame_h': '100',
            'position': '20',
        },
        'in':['fe', 'fx'],
        'out':[],
    },
}


actions = {
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
            'output_format' : 'image/jpeg'        
            },
         'in': ['fe'],
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
            'output_format' : 'image/jpeg'        
            },
         'in': ['fe'],
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
            'resize_w': 600,
            'source_variant': 'original',
            'output_variant': 'fullscreen',
            'output_format' : 'image/jpeg'        
            },
         'in': ['fe'],
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
            raise(Exception(err_msg))
        return tbd

    def register(self, name, trigger, media_types, description, pipeline_definition):
        e, created=TriggerEvent.objects.get_or_create(name=trigger)
        pipe = Pipeline.objects.create(name=name,  description='', params = simplejson.dumps(pipeline_definition), workspace = self.ws)
        pipe.triggers.add(e)
        for (mime_type, ext) in self._search_types(media_types):
            t=Type.objects.get_or_create_by_mime(mime_type, ext)
            pipe.media_type.add(t)
        pipe.save
        print 'registered pipeline %s, pk=%s, trigger=%s' % (name, pipe.pk, '-'.join( [x.name for x in pipe.triggers.all()] ) )

    def _new_item(self, filepath, media_type):
        variant = Variant.objects.get(name = 'original')
        fpath, ext = os.path.splitext(filepath)
        res_id = new_id()
        final_file_name = get_storage_file_name(res_id, self.ws.pk, variant.name, ext)
        item = _create_item(self.user, self.ws, res_id, media_type)
        component = _create_variant(filepath, final_file_name, media_type, item, self.ws, variant)
        return item, component

    #@transaction.commit_manually
    def upload(self, trigger, filepaths):
        print "executing upload, trigger=%s, filepaths=%s" % (trigger, ' '.join(filepaths))
        uploaders = []
        f = open('/tmp/uploader', 'w')
        for p in Pipeline.objects.filter(triggers__name=trigger):
            print '## adding pipeline %s to uploaders' % p.name
            uploader=Process.objects.create(pipeline=p, workspace=self.ws, launched_by=self.user)
            uploaders.append(uploader)
            f.write('%s\n' % uploader.pk)
        f.close()
        for fn in filepaths:
            print 'uploading', fn
            variant = Variant.objects.get(name = 'original')
            fpath, ext = os.path.splitext(fn)
            res_id = new_id()
            media_type = Type.objects.get_or_create_by_filename(fn)
            item = _create_item(self.user, self.ws, res_id, media_type)
            found = 0
            for uploader in uploaders:
                # here decide which uploader to use based on the content type of the item
                if uploader.is_compatible(media_type):
                    found = 1
                    uploader.add_params(item.pk)
            if not found:
                print ">>>>>>>>>> No action for %s" % fn
            final_file_name = get_storage_file_name(res_id, self.ws.pk, variant.name, ext)
            final_path = os.path.join(settings.MEDIADART_STORAGE, final_file_name)
            component = _create_variant(fn, final_file_name, media_type, item, self.ws, variant)
            shutil.copyfile(fn, final_path)
        #transaction.commit()
        print '#### uploaders', uploaders
        for uploader in uploaders:
            print 'Launching %s-%s' % (str(uploader.pk), uploader.pipeline.name)
            uploader.run()
        print 'Launched uploaders ',
        print ' '.join(open('/tmp/uploader', 'r').readlines())

    def show_pipelines(self):
        print ("Pipelines:")
        pipelines=Pipeline.objects.all()
        for p in pipelines:
            d = loads(p.params)
            actions = d.keys()
            actions.sort()
            print('Pipe pk=%s name=%s length=%s actions=%s' % (p.pk, p.name, len(d), ' '.join(actions)))

    def show_process(self):
        print ("Processes:")
        processes=Process.objects.all()
        for p in processes:
            targets = ProcessTarget.objects.filter(process=p, actions_todo__gt=0)
            print('Process pk=%s start=%s end=%s pending=%s' % (p.pk, p.start_date, p.end_date, targets.count()))

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
                pprint("item %s" % t.target_id)
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
  python scripts_test.py register up1 upload image actions  
    registers the pipeline described in the global dict "actions" with the name up1,
    to react to the trigger "upload", for all types "image/*"

  python scripts_test.py execpipes upload megan-fox*.jpg
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
    
    elif task == 'execpipes':
        trigger = argv[2]
        files = argv[3:]
        if not files:
            raise Exception('too few arguments')
        test.upload(trigger, files)
   
    elif task == 'status':
        process_id = argv[2]
        targets = argv[3:]
        test.get_status(process_id, targets)

    elif task == 'show':
        what = argv[2]
        if what == 'pipe':
            test.show_pipelines()
        elif what == 'process':
            test.show_process()
        else:
            print("Error: use show pipe or show process")

    else:
        print usage
    
if __name__=='__main__':
    main(sys.argv)
