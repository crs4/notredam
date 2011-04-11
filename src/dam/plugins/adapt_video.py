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

import math
from dam.repository.models import get_storage_file_name
from dam.core.dam_repository.models import Type
from dam.plugins.common.adapter import Adapter
from dam.plugins.common.utils import resize_image
from dam.plugins.adapt_video_idl import inspect
from twisted.internet import defer, reactor
from mediadart import log

def run(workspace,            # workspace object
        item_id,              # item pk
        source_variant_name,  # name of the source variant (a string)
        output_variant_name,  # name of the destination variat (a string)
        output_preset,        # CMD_<output_preset> must be one of the gstreamer pipelines below
        **preset_params       # additional parameters (see pipeline for explanation)
        ):
    deferred = defer.Deferred()
    adapter = AdaptVideo(deferred, workspace, item_id, source_variant_name)
    reactor.callLater(0, adapter.execute, output_variant_name, output_preset,  **preset_params)
    return deferred


class AdaptVideo(Adapter):
    remote_exe = 'gst-launch-0.10'
    md_server = 'HighLoad'
    #fake=True

    def get_cmdline(self, output_variant, output_preset, **preset_params):
        try:
            cmd = globals()['CMD_%s' % output_preset]
        except KeyError:
            raise  Exception('%s: unsupported output_preset' % (output_preset))

        av = self.source.get_features()
        self.cmdline = cmd['cmdline']
        self.out_type = Type.objects.get_or_create_by_mime(cmd['mime'])
        self.out_file = get_storage_file_name(self.item.ID, self.workspace.pk, output_variant, self.out_type.ext)

        if not av.has_audio():
            self.cmdline = synthetic_audio(self.cmdline)

        params = {}
        params.update(cmd['defaults'])
        params.update(preset_params)

        w, h = resize_image(av.get_video_width(), av.get_video_height(),
                            int(params.get('video_width', 0)), int(params.get('video_height', 0)))

        params.update({'in_filename': self.source.uri, 
                       'out_filename': self.out_file,
                       'video_width': w,
                       'video_height': h, 
                       'num_buffers': str(int(math.ceil(float(av.get_video_duration())*(44100./2100.)))),})

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

#
# Common part of the pipelines
#
# video decoding
__video_decoder = """
  filesrc location="file://%(in_filename)s" ! decodebin name=decode ! queue 
  ! ffmpegcolorspace ! video/x-raw-rgb, bpp=24 
  ! watermark filename="file://%(watermark_filename)s" top=%(watermark_top)s left=%(watermark_left)s 
  ! ffmpegcolorspace ! videoscale 
  ! video/x-raw-rgb, width=%(video_width)s, height=%(video_height)s 
  ! videorate ! video/x-raw-rgb, bpp=24, framerate=%(video_framerate)s ! ffmpegcolorspace 
"""

# filesink
__encoder = ' ! progressreport name=report ! filesink location="outfile://%(out_filename)s"'

# audio decoding, when present
__audio_decoder = ' decode. ! queue ! audioconvert ! audioresample ! audio/x-raw-int, rate=%(audio_rate)s '

# syntethize silent audio when audio is absent in source
__silent_audio = """
  audiotestsrc num-buffers=%(num_buffers)s samplesperbuffer=2100 wave=4 
  ! audio/x-raw-int, rate=44100 ! audioresample ! audioconvert 
  ! audio/x-raw-int, rate=%(audio_rate)s
"""

#
# Return the version of the pipeline that synthetizes a silent audio track
#
def synthetic_audio(cmdline):
    return cmdline.replace(__audio_decoder, __silent_audio)

def get_presets():
    return [x[4:] for x in globals() if x.startswith('CMD_')]

CMD_MATROSKA_MPEG4_AAC = {
    'cmdline': 
        __video_decoder + 
        ' ! queue ! ffenc_mpeg4 bitrate=%(video_bitrate_b)s ! matroskamux name=mux ' + 
        __encoder + __audio_decoder +
        ' ! queue ! faac bitrate=%(audio_bitrate_b)s ! mux.',

    'defaults': {
        'in_filename': TBD,
        'out_filename': TBD,
        'watermark_filename':'' ,
        'watermark_top':'0' ,
        'watermark_left':'0' ,
        'video_width':'320' ,
        'video_height':'240' ,
        'video_framerate':'30/1' ,
        'audio_rate':'44100',
        'video_duration': TBD,   # only required for video with no audio
        'audio_rate': '44100', 
        'video_bitrate_b':'264000' ,
        'audio_bitrate_b':'128000' ,
    },
    'mime': 'video/x-m4v',
}

CMD_MP4_H264_AACLOW = {
    'cmdline':
        __video_decoder + 
        ' ! x264enc bitrate=%(video_bitrate_kb)s ! mp4mux name=mux ' +
        __encoder + __audio_decoder +
        ' ! faac bitrate=%(audio_bitrate_b)s profile=2 ! mux.',

    'defaults': {
        'in_filename': TBD,
        'out_filename': TBD,
        'watermark_filename':'' ,
        'watermark_top':'0' ,
        'watermark_left':'0' ,
        'video_width':'320' ,
        'video_height':'240' ,
        'video_framerate':'30/1' ,
        'audio_rate':'44100',
        'video_duration': TBD,   # only required for video with no audio
        'audio_rate': '44100', 
        'video_bitrate_kb':'192' ,
        'audio_bitrate_b':'128000' ,
    },
    'mime': 'video/mp4',
}

CMD_FLV = {
    'cmdline':
        __video_decoder + 
        ' ! ffenc_flv bitrate=%(video_bitrate_b)s ! queue ! flvmux name=mux ' +
        __encoder + __audio_decoder +
        ' ! lame bitrate=%(audio_bitrate_kb)s ! mp3parse ! mux.',

    'defaults': {
        'in_filename': TBD,
        'out_filename': TBD,
        'watermark_filename':'' ,
        'watermark_top':'0' ,
        'watermark_left':'0' ,
        'video_width':'320' ,
        'video_height':'240' ,
        'video_framerate':'30/1' ,
        'audio_rate':'44100',
        'video_duration': TBD,   # only required for video with no audio
        'audio_rate': '44100', 
        'audio_bitrate_kb': '128',
        'video_bitrate_b': '640000',
    },
    'mime': 'video/flv',
}

CMD_AVI = {
    'cmdline':
        __video_decoder + 
        ' ! xvidenc bitrate=%(video_bitrate_b)s ! queue ! avimux name=mux ' +
        __encoder + __audio_decoder +
        ' ! lame bitrate=%(audio_bitrate_kb)s ! mp3parse ! mux. ',

    'defaults' : {
        'in_filename': TBD,
        'out_filename': TBD,
        'watermark_filename':'' ,
        'watermark_top':'0' ,
        'watermark_left':'0' ,
        'video_width':'320' ,
        'video_height':'240' ,
        'video_framerate':'30/1' ,
        'audio_rate':'44100',
        'video_duration': TBD,   # only required for video with no audio
        'audio_rate': '44100', 
        'audio_bitrate_kb': '128',
        'video_bitrate_b': '180000',
    },
    'mime': 'video/x-msvideo',
}

CMD_MPEGTS = {
    'cmdline':
        __video_decoder + 
       ' ! ffenc_mpeg2video bitrate=%(video_bitrate_b)s ! mpegvideoparse ! flutsmux name=mux ' +
        __encoder + __audio_decoder +
       ' ! lame bitrate=%(audio_bitrate_kb)s ! mp3parse ! mux.' ,

    'defaults' : {
        'in_filename': TBD,
        'out_filename': TBD,
        'watermark_filename':'' ,
        'watermark_top':'0' ,
        'watermark_left':'0' ,
        'video_width':'320' ,
        'video_height':'240' ,
        'video_framerate':'30/1' ,
        'audio_rate':'44100',
        'video_duration': TBD,   # only required for video with no audio
        'audio_rate': '44100', 
        'audio_bitrate_kb': '256',
        'video_bitrate_b': '12000000',
    },
    'mime': 'video/ts',
}

CMD_FLV_H264_AAC = {
    'cmdline':
        __video_decoder + 
       ' ! x264enc bitrate=%(video_bitrate_kb)s ! queue ! flvmux name=mux ' +
        __encoder + __audio_decoder +
       ' ! faac bitrate=%(audio_bitrate_b)s ! mux.',  

    'defaults' : {
        'in_filename': TBD,
        'out_filename': TBD,
        'watermark_filename':'' ,
        'watermark_top':'0' ,
        'watermark_left':'0' ,
        'video_width':'320' ,
        'video_height':'240' ,
        'video_framerate':'30/1' ,
        'audio_rate':'44100',
        'video_duration': TBD,   # only required for video with no audio
        'audio_rate': '44100', 
        'audio_bitrate_b': '128000',
        'video_bitrate_kb': '2048',
    },
    'mime': 'video/flv',
}


CMD_THEORA = {
    'cmdline':
        __video_decoder + 
       ' ! theoraenc bitrate=%(video_bitrate_kb)s ! queue ! oggmux name=mux  ' +
        __encoder + __audio_decoder +
       ' ! audioconvert ! audio/x-raw-float ! vorbisenc quality=%(audio_quality)s ! mux. ',

    'defaults' : {
        'in_filename': TBD,
        'out_filename': TBD,
        'watermark_filename':'' ,
        'watermark_top':'0' ,
        'watermark_left':'0' ,
        'video_width':'320' ,
        'video_height':'240' ,
        'video_framerate':'30/1' ,
        'audio_rate':'44100',
        'video_duration': TBD,   # only required for video with no audio
        'audio_rate': '44100', 
        'audio_quality': '0.9',
        'video_bitrate_kb': '192',
    },
    'mime': 'video/ogg',
}




#
# Stand alone test: need to provide a compatible database (item must be an item with a audio comp.)
#
from twisted.internet import defer, reactor
from dam.repository.models import Item
from dam.workspace.models import DAMWorkspace

def test():
    print 'test xx'
    item = Item.objects.get(pk=1)
    workspace = DAMWorkspace.objects.get(pk = 1)
    d = run(workspace,
            item.pk,
            source_variant_name = 'original',
            output_variant_name =  'preview',
            output_preset =  'FLV',
            preset_params =  {
            'video_width': '320',
            'video_height': '240',
            'video_bitrate_b': '640000',
            'video_framerate': '25/2',
            'audio_bitrate_kb': '128',
            'audio_rate': '44100',
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

