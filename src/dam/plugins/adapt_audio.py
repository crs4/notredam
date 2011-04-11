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

import os
from dam.repository.models import get_storage_file_name
from dam.core.dam_repository.models import Type
from dam.plugins.common.adapter import Adapter
from dam.plugins.adapt_audio_idl import inspect
from twisted.internet import defer, reactor
from mediadart import log


def run(workspace,            # workspace object
        item_id,              # item pk
        source_variant_name,  # name of the source variant (a string)
        output_variant_name,  # name of the destination variat (a string)
        output_preset,        # CMD_<output_preset> must be one of the gstreamer pipelines below
        **preset_params):     # additional parameters (see pipeline for explanation)

    deferred = defer.Deferred()
    adapter = AdaptAudio(deferred, workspace, item_id, source_variant_name)
    reactor.callLater(0, adapter.execute, output_variant_name, output_preset,  **preset_params)
    return deferred

class AdaptAudio(Adapter):
    remote_exe = 'gst-launch-0.10'
    md_server = 'HighLoad'
    env = {'SDL_VIDEODRIVER': 'dummy'}
    #fake = True

    # Implementation in Adapter
    def get_cmdline(self, output_variant_name, output_preset, **preset_params):
        try:
            cmd = globals()['CMD_%s' % output_preset]
        except KeyError:
            raise  Exception('%s: unsupported output_preset' % (output_preset))

        av = self.source.get_features()
        self.cmdline = cmd['cmdline']

        self.out_type = Type.objects.get_or_create_by_mime(cmd['mime'])
        self.out_file = get_storage_file_name(self.item.ID, self.workspace.pk, output_variant_name,
                                              self.out_type.ext)

        params = {}
        params.update(cmd['defaults'])
        params.update(preset_params)
        params.update({'in_filename': self.source.uri, 
                       'out_filename': self.out_file,})
        self.cmdline = self.cmdline % params

        if TBD in self.cmdline:
            raise Exception('missing required parameter from preset')


########################################################################################
# COMMAND LINE DEFINITIONS
#
#  Definition of command lines for remote execution
#
#  All variables with the prefix CMD_ are considered executable pipelines
#
#  Command line for remote executions are codified in a dictionary as below:
#
#  The only special syntax is required for specifying input files and output files
#  as arguments.
#
#  The syntax is required because absolute paths cannot be exchanged, because it is
#  possible that the local filename in a remote computer is different.
#  
#  To specify that an argument is a filename, prefix the relative path to the 
#  (local) repository root (mediadart option cache_dir) with file://
#
#  To specify that an argument is a output filename, prefix the relative path to the 
#  (local) repository root (mediadart option cache_dir) with outfile://
#
#  Parameters are specified in the cmdline with python syntax
#
#  Defaults can be specified. It a default has the special value TBD, the value MUST
#  be provided at execution time, or an error will be raised.
#
###################################################################################

TBD='___undefined___'   # this is the value of parameters for which there is no default

__encoder = ' ! progressreport ! filesink location="outfile://%(out_filename)s"'
__decoder = """ filesrc location="file://%(in_filename)s" ! decodebin name=decode ! queue 
                ! audioconvert ! audioresample ! audio/x-raw-int, rate=%(audio_rate)s """
__sink_video = ' decode. ! ffmpegcolorspace ! fakesink silent=true '


CMD_WAV = {
    'cmdline': __decoder + ' ! wavenc ' + __encoder,
    'defaults': { 
        'in_filename': TBD,
        'out_filename': TBD,
        'audio_rate': '44100',
        },
    'mime': 'audio/x-wav',
}

CMD_MP3 = {
    'cmdline': __decoder + 
       ' ! lame bitrate=%(audio_bitrate_kb)s ! mp3parse ! id3mux write-v1=true write-v2=true' 
       + __encoder,
    'defaults': { 
        'in_filename': TBD,
        'out_filename': TBD,
        'audio_rate': '44100',
        'audio_bitrate_kb': '128',
        },
    'mime': 'audio/mpeg',
}

CMD_OGG = {
    'cmdline': __decoder + 
        ' ! audioconvert ! audio/x-raw-float ! vorbisenc quality=%(audio_quality)s ! vorbisparse ! vorbistag ! oggmux' +
         __encoder,
    'defaults': { 
        'in_filename': TBD,
        'out_filename': TBD,
        'audio_rate': '44100',
        'audio_quality': '0.9',
        },
    'mime': 'audio/ogg',
}

CMD_AAC = {
    'cmdline': __decoder + ' ! faac bitrate=%(audio_bitrate_b)s profile=2 ! ffmux_mp4' + __encoder,
    'defaults': { 
        'in_filename': TBD,
        'out_filename': TBD,
        'audio_rate': '44100',
        'audio_bitrate_b': '320000',
        },
    'mime': 'audio/x-m4a',
}

def sink_video(cmdline):
    return cmdline.replace(__encoder, __encoder + __sink_video)

####################################################################
#
# Stand alone test: need to provide a compatible database (item 2 must be an item with a audio comp.)
#
from dam.repository.models import Item
from twisted.internet import defer, reactor
from dam.workspace.models import DAMWorkspace

def test():
    print 'test'
    item = Item.objects.get(pk=5)
    workspace = DAMWorkspace.objects.get(pk = 1)
    d = run(workspace,
            item.pk,
            source_variant_name = 'original',
            output_variant_name=  'fullscreen',
            output_preset =  'MP3',
            preset_params =  {
#           'audio_bitrate_b': '128',
#            'audio_rate': 44100,
                },   # per esempio
            )
    d.addBoth(print_result)
    

def print_result(result):
    print 'print_result', result
    reactor.stop()

if __name__ == "__main__":
    from twisted.internet import reactor
    reactor.callWhenRunning(test)
    reactor.run()

    
    
    

    
    
    
