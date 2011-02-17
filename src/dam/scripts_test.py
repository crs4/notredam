import os
import sys
from json import loads
import mimetypes
import shutil

from django.core.management import setup_environ
from django.db import transaction
import settings
setup_environ(settings)

from django.utils import simplejson
from django.contrib.auth.models import User
from dam.mprocessor.models import new_processor, Pipeline, Process, ProcessTarget, PipelineType
from dam.workspace.models import DAMWorkspace
from dam.core.dam_repository.models import Type
from dam.repository.models import Item
from dam.variants.models import Variant
from mediadart.storage import new_id
from dam.upload.views import guess_media_type


actions = {'thumbnail_image':{
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
    
}

class DoTest:
    def __init__(self):
        self.ws = DAMWorkspace.objects.get(pk = 1)
        self.user = User.objects.get(username='admin')

    def create_item(self, filepath):
        guess = guess_media_type(filepath)
        media_type = Type.objects.get(name=guess)
        item = Item.objects.create(owner = self.user, uploader = self.user, type=media_type)
        item.add_to_uploaded_inbox(self.ws)
        item.workspaces.add(self.ws)
        return item

    def create_variant(self, item, variant, filepath):
        fname, ext = os.path.splitext(filepath)
        res_id = new_id() + ext
        comp = item.create_variant(variant, self.ws)
        if variant.auto_generated:
            comp.imported = True
        comp.file_name = filepath
        comp._id = res_id
        mime_type = mimetypes.guess_type(filepath)[0]
        comp.format = mime_type.split('/')[1]
        comp.save()
        return comp

    def register(self, name, type, description, pipeline_definition):
        preview = Pipeline.objects.create(name=name,  description='', params = simplejson.dumps(pipeline_definition), workspace = self.ws)
        print 'registered pipeline %s, pk = %s' % (name, preview.pk)
        PipelineType.objects.create(type = 'upload', workspace = self.ws, pipeline = preview)

    def _new_item(self, filepath):
        item = self.create_item(filepath)
        print ('created item %s' % item.pk)
        variant = Variant.objects.get(name = 'original')
        comp = self.create_variant(item, variant, filepath)
        imported_filepath = os.path.join(settings.MEDIADART_STORAGE, comp._id)
        shutil.copyfile(filepath, imported_filepath)
        print('file moved to %s' % imported_filepath)
        return item.pk

    def upload(self, filepaths):
        uploader = new_processor('uploader', self.user, self.ws)
        open('/tmp/uploader', 'w').write('%s\n' % uploader.pk)
        for fn in filepaths:
            print 'uploading', fn
            target_id = self._new_item(fn)
            uploader.add_params(target_id)
        uploader.run()
        print 'done'

    def get_status(self, pid, items):
        if items:
            targets = ProcessTarget.objects.filter(process=pid, target_id__in=items, actions_todo=0)
        else:
            targets = ProcessTarget.objects.filter(process=pid)
        print 'found %d targets' % len(targets)
        for t in targets:
            result = loads(t.result)
            if 'thumbnail_image' in result:
                if result['thumbnail_image'][0]:
                    print "item %s: thumbnail %s" % (t.target_id, result['thumbnail_image'][1])
                else:
                    print 'item %s: thumbnail generation failure: %s' % (t.target_id, result['thumbnail_image'][1])



usage="""
Usage: script_test.py <action> <arguments>
 where action is
 
  register [pipeline_definition]  (default register actions)

  upload <filename>
"""


def main(argv):
    test = DoTest()
    if len(argv) < 2: 
        argv.append('register')
    task = argv[1]

    if task == 'register':
        if len(argv) < 3:
            argv.append('actions')
        pipeline_def = globals()[argv[2]]
        test.register('uploader', 'upload', '', pipeline_def)
    elif task == 'upload':
        test.upload(argv[2:])
    elif task == 'status':
        test.get_status(argv[2], argv[3:])
    else:
        print usage
    
if __name__=='__main__':
    main(sys.argv)
