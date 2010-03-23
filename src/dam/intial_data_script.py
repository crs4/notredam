
#import os
#os.putenv('DJANGO_SETTINGS_MODULE', 'dam.settings')
#os.putenv('PYTHONPATH', '/home/mauro/work/dam/dam/')

from variants.models import *
from workspace.models import *

ws = Workspace.objects.get(pk = 1)
user = User.objects.get(pk = 1)
wspa = WorkSpacePermissionAssociation.objects.get_or_create(workspace = ws, permission = WorkSpacePermission.objects.get(name='admin'))[0]
wspa.users.add(user)
ws.members.add(user)


image = Type.objects.get(name = 'image')

orig = Variant.objects.create(name = 'original', caption = 'Original',  is_global = True, auto_generated = False,  shared = True,  media_type = image, default_rank = 2,)

edited = Variant.objects.create(name = 'edited', caption = 'edited',  is_global = True, auto_generated = False, media_type = image, default_rank = 1)
#orig = Variant.objects.create(name = 'original', caption = 'Original',  is_global = True)

thumb  = Variant.objects.create(name = 'thumbnail', caption = 'Thumbnail',   media_type = image,  is_global = True,  resizable = False,  editable = False)
thumb_pref = ImagePreferences.objects.create(max_dim = 100)
thumb_pref_def = ImagePreferences.objects.create(max_dim = 100)

SourceVariant.objects.create(workspace = ws,  source = edited,  rank = 1,  destination = thumb)
SourceVariant.objects.create(workspace = ws,  source = orig,  rank = 2,  destination = thumb)

preview = Variant.objects.create(name = "preview", media_type = image,  is_global = True,  resizable = False)
preview_pref = ImagePreferences.objects.create(max_dim = 300)
preview_pref_def = ImagePreferences.objects.create(max_dim = 300)

SourceVariant.objects.create(workspace = ws,  source = edited,  rank = 1,  destination = preview)
SourceVariant.objects.create(workspace = ws,  source = orig,  rank = 2,  destination = preview)



fullscreen = Variant.objects.create(name = "fullscreen", media_type = image,  is_global = True)
fullscreen_pref = ImagePreferences.objects.create(max_dim = 800)
fullscreen_pref_def = ImagePreferences.objects.create(max_dim = 800)

SourceVariant.objects.create(workspace = ws,  source = edited,  rank = 1,  destination = fullscreen)
SourceVariant.objects.create(workspace = ws,  source = orig,  rank = 2,  destination = fullscreen)

VariantAssociation.objects.create(variant = orig, workspace = ws, )
VariantAssociation.objects.create(variant = edited, workspace = ws, )
VariantAssociation.objects.create(variant = thumb, workspace = ws, preferences = thumb_pref)
VariantAssociation.objects.create(variant = preview, workspace = ws,preferences = preview_pref)
VariantAssociation.objects.create(variant = fullscreen, workspace = ws,preferences = fullscreen_pref)

VariantDefault.objects.create(variant = thumb,  preferences = thumb_pref_def)
VariantDefault.objects.create(variant = preview,preferences = preview_pref_def)
VariantDefault.objects.create(variant = fullscreen,preferences = fullscreen_pref_def)




audio = Type.objects.get(name = 'audio')
orig = Variant.objects.create(name = 'original', caption = 'Original',  is_global = True,  auto_generated = False, media_type = audio, shared = True,default_rank = 2)

edited = Variant.objects.create(name = 'edited', caption = 'edited',  is_global = True, auto_generated = False,   media_type = audio, default_rank = 1)


thumb  = Variant.objects.create(name = 'thumbnail', caption = 'Thumbnail',  media_type = audio, auto_generated = False,  is_global = True,  default_url = '/files/images/audio_thumbnail.jpg',  editable = False)



audio_quality = PresetParameter.objects.create(name = 'audio_quality', caption = 'audio_quality',  default = '0.9', _class = 'Sampling',  type = 'combo',  values="[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]")
audio_rate = PresetParameter.objects.create(name = 'audio_rate', caption = 'audio sample rate (Hz)',  default = '44100', _class = 'Sampling',  type = 'combo',  values="[32000, 44100, 48000]" )
audio_bitrate_kb = PresetParameter.objects.create(name = 'audio_bitrate_kb', caption = 'audio bitrate (Kbps)',  default = '128', _class = 'Sampling',  type = 'combo',  values="[64, 80, 96, 112,128, 160, 192, 224, 256,320]" )
audio_bitrate_b = PresetParameter.objects.create(name = 'audio_bitrate_b', caption = 'audio bitrate (Kbps)',  default = '128000', _class = 'Sampling',  type = 'combo',  values='[["64000", 64], ["80000", 80], ["96000", 96], ["112000", 112],["128000", 128], ["160000", 160], ["192000", 192], ["224000", 224], ["256000", 256],["320000", 320]]' )



preset_mp3 = Preset.objects.create(name = 'mp3', caption = 'mp3',  media_type = audio,  extension = 'mp3')
preset_mp3.parameters.add(*[audio_rate,  audio_bitrate_kb ])


preset_aac = Preset.objects.create(name = 'aac', caption = 'aac',  media_type = audio,  extension = 'm4a')
preset_aac.parameters.add(*[audio_rate,  audio_bitrate_b ])


preset_vorbis = Preset.objects.create(name = 'ogg', caption = 'ogg',  media_type = audio,  extension = 'ogg')
preset_vorbis.parameters.add(*[audio_rate,  audio_quality ])




preview = Variant.objects.create(name = "preview", media_type = audio,  is_global = True)
preview_pref = AudioPreferences.objects.create(preset = preset_mp3)
preview_pref_def = AudioPreferences.objects.create(preset = preset_mp3)

for param in preset_mp3.parameters.all():
    PresetParameterValue.objects.create(parameter = param,  preferences = preview_pref,  value = param.default)
    PresetParameterValue.objects.create(parameter = param,  preferences = preview_pref_def,  value = param.default)




SourceVariant.objects.create(workspace = ws,  source = edited,  rank = 1,  destination = preview)
SourceVariant.objects.create(workspace = ws,  source = orig,  rank = 2,  destination = preview)


VariantAssociation.objects.create(variant = orig, workspace = ws, )
VariantAssociation.objects.create(variant = edited, workspace = ws, )
VariantAssociation.objects.create(variant = thumb, workspace = ws, preferences = thumb_pref)
VariantAssociation.objects.create(variant = preview, workspace = ws,preferences = preview_pref)

VariantDefault.objects.create(variant = thumb,  preferences = thumb_pref_def)
VariantDefault.objects.create(variant = preview,preferences = preview_pref_def)




movie = Type.objects.get(name = 'movie')





########### PRESETS


#watermark_filename = PresetParameter.objects.create(name = 'watermark_filename', caption = 'watermarking file' ,  _class = 'watermarking',  type = 'string', default = '' )
#watermark_position =  PresetParameter.objects.create(name = 'watermarking_position', caption = 'watermarking position',  default = '1',  _class = 'watermarking',  type = 'combo')

max_size =  PresetParameter.objects.create(name = 'max_size', caption = 'max size (pixel)' , default = '320',  _class = 'size',  type = 'int',  values = "[256, 320, 512, 640, 800, 1024, 1280, 1600, 2048]")
#video_height =  PresetParameter.objects.create(name = 'video_height', caption = 'height',  default = '240',  _class = 'size',  type = 'int')
video_framerate = PresetParameter.objects.create(name = 'video_framerate', caption = 'video frame rate (fps)',  default = '25/1',  _class = 'Sampling',  type = 'combo',  values= '[["25/2", 12.5], ["24/1", 24], ["25/1", 25], ["30000/1001", 29.97],["30/1", 30]]')



video_bitrate_b = PresetParameter.objects.create(name = 'video_bitrate_b', caption = 'video bitrate (Kbps)',  default = '640000', _class = 'Sampling',  type = 'combo',  values=
'[["64000", 64], ["128000", 128], ["192000", 192], ["256000", 256], ["320000", 320],["640000", 640], ["1024000",1024], ["1536000", 1536],["2048000", 2048], ["4096000", 4096],  ["8192000", 8192], ["12288000", 12288], ["20040000", 20040]]')



preset_flv = Preset.objects.create(name = 'flv', caption = 'flv',  media_type = movie,  extension = 'flv')
preset_flv.parameters.add(*[max_size, video_framerate,  audio_rate,  video_bitrate_b,  audio_bitrate_kb ])


preset_flv_h264 = Preset.objects.create(name = 'flv_h264_aac',  caption = 'flv h264', media_type = movie,  extension = 'flv')

video_bitrate_kb = PresetParameter.objects.create(name = 'video_bitrate_kb', caption = 'video bitrate (Kbps)',  default = '2048', _class = 'Sampling',  type = 'combo',  values='[64, 128, 192, 256, 320, 640, 1024, 1536,2048, 4096,  8192, 12288, 20040]' )
preset_flv_h264.parameters.add(*[max_size, video_framerate,  audio_rate,  video_bitrate_kb,  audio_bitrate_b ])


preset_avi = Preset.objects.create(name = 'avi',  caption = 'avi xvid ', media_type = movie,  extension = 'avi')
preset_avi.parameters.add(*[max_size, video_framerate,  audio_rate,  video_bitrate_b,  audio_bitrate_kb ])


preset_theora = Preset.objects.create(name = 'theora',  caption = 'theora ogg',  media_type = movie, extension = 'ogg')


preset_theora.parameters.add(*[max_size, video_framerate,  audio_rate,  video_bitrate_kb,  audio_quality])

preset_matroska = Preset.objects.create(name = 'matroska_mpeg4_aac',  caption = 'matroska mpeg4', media_type = movie,  extension = 'mkv')
preset_matroska.parameters.add(*[max_size, video_framerate,  audio_rate,  video_bitrate_b,  audio_bitrate_b])

preset_mp4 = Preset.objects.create(name = 'mp4_h264_aaclow',  caption = 'mp4 h264', media_type = movie,  extension = 'mp4')
preset_mp4.parameters.add(*[max_size, video_framerate,  audio_rate,  video_bitrate_kb,  audio_bitrate_b])


preset_mpegts = Preset.objects.create(name = 'mpegts',  caption = 'mpeg transport stream', media_type = movie,  extension = 'mpeg')


#video_bitrate_b_mpegts = PresetParameter.objects.create(name = 'video_bitrate_b', caption = 'video bitrate (Kbps)',  default = '12000000', _class = 'Sampling',  type = 'combo',  values=
#'[["12000000", 12000]]')

preset_mpegts.parameters.add(*[max_size, video_framerate,  audio_rate,  video_bitrate_b ,  audio_bitrate_kb])




orig = Variant.objects.create(name = 'original', caption = 'Original',  is_global = True,  media_type = movie,  auto_generated = False, shared = True,default_rank = 2)


edited = Variant.objects.create(name = 'edited', caption = 'edited',  is_global = True, auto_generated = False,   media_type = movie, default_rank = 1)


thumb  = Variant.objects.create(name = 'thumbnail', caption = 'Thumbnail', media_type = movie,  is_global = True,  resizable = False,  editable = False)
thumb_pref = ImagePreferences.objects.create(max_dim = 100,  video_position = 25)
thumb_pref_def = ImagePreferences.objects.create(max_dim = 100,  video_position = 25)

SourceVariant.objects.create(workspace = ws,  source = edited,  rank = 1,  destination = thumb)
SourceVariant.objects.create(workspace = ws,  source = orig,  rank = 2,  destination = thumb)




preview = Variant.objects.create(name = "preview", media_type = movie,  is_global = True,  resizable = False)
#preview_pref = VideoPreferences.objects.create()
preview_pref_def = VideoPreferences.objects.create(preset = preset_flv)
preview_pref = VideoPreferences.objects.create(preset = preset_flv)


for param in preset_flv.parameters.all():
    PresetParameterValue.objects.create(parameter = param,  preferences = preview_pref,  value = param.default)
    PresetParameterValue.objects.create(parameter = param,  preferences = preview_pref_def,  value = param.default)



#max_dim_value = Pre


SourceVariant.objects.create(workspace = ws,  source = edited,  rank = 1,  destination = preview)
SourceVariant.objects.create(workspace = ws,  source = orig,  rank = 2,  destination = preview)

VariantAssociation.objects.create(variant = orig, workspace = ws, )
VariantAssociation.objects.create(variant = edited, workspace = ws, )
VariantAssociation.objects.create(variant = thumb, workspace = ws, preferences = thumb_pref)
VariantAssociation.objects.create(variant = preview, workspace = ws,preferences = preview_pref)


VariantDefault.objects.create(variant = thumb,  preferences = thumb_pref_def)
VariantDefault.objects.create(variant = preview,preferences = preview_pref_def)








doc = Type.objects.get(name = 'doc')

orig = Variant.objects.create(name = 'original', caption = 'Original',  is_global = True,  media_type = doc,  auto_generated = False, shared = True, default_rank = 1)


thumb  = Variant.objects.create(name = 'thumbnail', caption = 'Thumbnail',  media_type = doc,  is_global = True,  resizable = False,  editable = False)
thumb_pref = ImagePreferences.objects.create(max_dim = 100)
thumb_pref_def = ImagePreferences.objects.create(max_dim = 100)


SourceVariant.objects.create(workspace = ws,  source = orig,  rank = 1,  destination = thumb)

preview = Variant.objects.create(name = "preview", media_type = doc,  is_global = True,  resizable = False)
preview_pref = ImagePreferences.objects.create(max_dim = 300)
preview_pref_def = ImagePreferences.objects.create(max_dim = 300)


SourceVariant.objects.create(workspace = ws,  source = orig,  rank = 1,  destination = preview)

#fullscreen = Variant.objects.create(name = "fullscreen", source = orig, media_type = movie,  is_global = True)
#fullscreen_pref = VideoPreferences.objects.create()
#fullscreen_pref_def = VideoPreferences.objects.create()



VariantAssociation.objects.create(variant = orig, workspace = ws, )
VariantAssociation.objects.create(variant = thumb, workspace = ws, preferences = thumb_pref)
VariantAssociation.objects.create(variant = preview, workspace = ws,preferences = preview_pref)
#VariantAssociation.objects.create(variant = fullscreen, workspace = ws,preferences = fullscreen_pref)

VariantDefault.objects.create(variant = thumb,  preferences = thumb_pref_def)
VariantDefault.objects.create(variant = preview,preferences = preview_pref_def)
#VariantDefault.objects.create(variant = fullscreen,preferences = fullscreen_pref_def)







