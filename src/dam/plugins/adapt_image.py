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

from dam.plugins.common.adapter import Adapter
from dam.repository.models import get_storage_file_name
from dam.core.dam_repository.models import Type
from dam.plugins.adapt_image_idl import inspect
from twisted.internet import defer, reactor
from mediadart import log


def run(workspace,              # workspace object
        item_id,                # item primary key
        source_variant_name,    # name of the source variant (a string)
        output_variant_name,    # name of the destination variat (a string)
        output_extension,       # desired extension (with the dot)
        actions = [],           # ordered list of actions from resize, crop, watermark
        resize_h = None,        # desired height (aspect ratio is preserved)
        resize_w = None,        # desired width
        crop_w = None,          # crop width
        crop_h = None,          # crop height
        crop_x = None,          # x-position of top-left corner crop area
        crop_y = None,          # y-position of top-left corner crop area
        crop_ratio = None,      # size centered crop area as percentage (ex. 50:80)
                                # (used instead of crop_x etc.)
        pos_x_percent = None,   # x-position of top-left corner of watermark placement
        pos_y_percent = None,   # y-position of top-left corner of watermark placement
        wm_id = None,           # repository-relative file name of watermark resource
        ):

    deferred = defer.Deferred()
    adapter = AdaptImage(deferred, workspace, item_id, source_variant_name)
    reactor.callLater(0, adapter.execute, output_variant_name, output_extension,
        actions=actions, resize_h=resize_h, resize_w=resize_w, crop_w=crop_w,
        crop_h=crop_h, crop_x=crop_x, crop_y=crop_y, crop_ratio=crop_ratio, 
        pos_x_percent=pos_x_percent, pos_y_percent=pos_y_percent, wm_id=wm_id)
    return deferred


class AdaptImage(Adapter):
    remote_exe = 'convert'
    md_server = 'MediumLoad'
    #fake = True

    def get_cmdline(self, output_variant_name, output_extension, actions, resize_h,
                   resize_w, crop_w, crop_h, crop_x, crop_y, crop_ratio, pos_x_percent,
                   pos_y_percent, wm_id):
        if not isinstance(actions, list):
            actions = [actions]

        if output_extension == 'same_as_source':
            self.out_type = self.source.media_type
            output_extension = self.source.media_type.ext
        else:
            self.out_type = Type.objects.get_or_create_by_filename('foo%s' % output_extension)
                
        features = self.source.get_features()
        argv = ""
        for action in actions:
            if action == 'resize':
                argv +=  '-resize %sx%s' % (resize_w, resize_h)
                
            elif action == 'crop':
                if crop_ratio:
                    x, y = crop_ratio.split(':')
                    argv += ' -gravity center -crop %sx%s%%+0+0' % (x, y)
                else:
                    crop_x = crop_x or 0   # here None means 0
                    crop_y = crop_y or 0
                    argv += ' -gravity center -crop %sx%s+%s+%s' % (
                              int(crop_w), int(crop_h), int(crop_x), int(crop_y))

            elif action == 'watermark':
                pos_x = int(float(pos_x_percent) * float(features.get_width())/100.)
                pos_y = int(float(pos_y_percent) * float(features.get_height())/100.)
                argv +=  ' -gravity NorthWest "file://%s" -geometry +%s+%s -composite' % (wm_id, pos_x, pos_y)
        
        log.debug("calling adapter")
        self.out_file = get_storage_file_name(self.item.ID, self.workspace.pk, output_variant_name, output_extension)
        self.cmdline = '"file://%s[0]" %s "outfile://%s"' % (self.source.uri, argv, self.out_file)



#
# Stand alone test: need to provide a compatible database (item 2 must be an item with a audio comp.)
#
from twisted.internet import defer, reactor
from dam.repository.models import Item
from dam.workspace.models import DAMWorkspace

def test():
    print 'test'
    item = Item.objects.get(pk=5)
    workspace = DAMWorkspace.objects.get(pk = 1)
    d = run(workspace,
            item.pk,
            source_variant_name = 'original',
            output_variant_name =  'fullscreen',
            output_extension = '.jpg',
            actions = ['resize', 'crop', 'watermark'],
            resize_h = 150,
            resize_w = 150,
            crop_w = 900,
            crop_h = 900,
            crop_x = 0,
            crop_y = 0,
            crop_ratio = None, #'50:50',
            pos_x_percent = '0',
            pos_y_percent = '0',
            wm_id = 'aba2c175b12f43f39bb87948285df6ef_1_thumbnail.jpg')
    d.addBoth(print_result)
    
def print_result(result):
    print 'print_result', result
    reactor.stop()

if __name__ == "__main__":
    from twisted.internet import reactor
    
    reactor.callWhenRunning(test)
    reactor.run()

    
    
    

    
    
    
