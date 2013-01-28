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
from dam.plugins.common.utils import resize_image
from dam.plugins.extract_frame_idl import inspect
from twisted.internet import defer, reactor
from mediadart import log

def run(workspace, 
        item_id, 
        source_variant_name,
        output_variant_name,
        output_extension,      # with leading '.'
        frame_w = 0,           # desired width (0 = use original width)
        frame_h = 0,           # desired height
        position = 20,         # position (as percentage of total duration)
        ):
    """
    Extract a single thumbnail from a video.

    @param thumb_size: desired (width, height) of the thumbnail (aspect ratio is preserved)
    @param thumb_pos: approximate position (percent of total length)
    """
    deferred = defer.Deferred()
    adapter = ExtractFrame(deferred, workspace, item_id, source_variant_name)
    reactor.callLater(0, adapter.execute, output_variant_name, output_extension,
                      frame_w=frame_w, frame_h=frame_h, position=position)
    return deferred

#
# The command line to be executed remotely
#
CMDLINE = '-i "file://%(infile)s" -ss %(real_pos)f -r 1 -vframes 1 -s %(thumb_w)sx%(thumb_h)s ' \
          '-f image2 "outfile://%(outfile)s"'

class ExtractFrame(Adapter):
    remote_exe = 'ffmpeg'
    md_server = "LowLoad"

    def get_cmdline(self, output_variant_name, output_extension, frame_w, frame_h, position):
        features = self.source.get_features()
        self.out_type = Type.objects.get_or_create_by_filename('foo%s' % output_extension)
        self.out_file = get_storage_file_name(self.item.ID, self.workspace.pk, 
                                              output_variant_name, output_extension)
        thumb_w, thumb_h = resize_image(features.get_video_width(), features.get_video_height(),
                                        frame_w, frame_h )
        real_pos = float(features.get_video_duration()) * (float(position)/100.)
        self.cmdline =  CMDLINE % {'infile': self.source.uri, 'outfile':self.out_file,
                                'thumb_w':thumb_w, 'thumb_h':thumb_h, 'real_pos':real_pos}





#
# Stand alone test: need to provide a compatible database (item 2 must be an item with a audio comp.)
#
from twisted.internet import defer, reactor
from dam.repository.models import Item
from dam.workspace.models import DAMWorkspace

def test():
    print 'test'
    item = Item.objects.get(pk=2)
    workspace = DAMWorkspace.objects.get(pk = 1)
    d = run(workspace,
            item.pk,
            source_variant_name = 'original',
            output_variant_name =  'fullscreen',
            output_extension = '.jpg',
            frame_w = '250',
            frame_h = '250',
            position = '62.8',
            )
    d.addBoth(print_result)
    
def print_result(result):
    print 'print_result', result
    reactor.stop()

if __name__ == "__main__":
    from twisted.internet import reactor
    
    reactor.callWhenRunning(test)
    reactor.run()

    
    
    

    
    
    
