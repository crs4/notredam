from django.core.management import setup_environ
from dam import settings
setup_environ(settings)


from dam.variants.models import *
from dam.workspace.models import *

ws = Workspace.objects.get(pk = 1)
user = User.objects.get(pk = 1)
#wspa = WorkSpacePermissionAssociation.objects.get_or_create(workspace = ws, permission = WorkSpacePermission.objects.get(name='admin'))[0]
#wspa.users.add(user)
#ws.members.add(user)


image = Type.objects.get(name = 'image')
audio = Type.objects.get(name = 'audio')
video = Type.objects.get(name = 'movie')
doc = Type.objects.get(name = 'doc')
orig = Variant.objects.create(name = 'original', caption = 'Original',  auto_generated = False,  shared = True)
orig.media_type.add(*[image, audio, video, doc])

edited = Variant.objects.create(name = 'edited', caption = 'edited', auto_generated = False, )
edited.media_type.add(*[image, audio, video, doc])
#orig = Variant.objects.create(name = 'original', caption = 'Original',  is_global = True)

thumb  = Variant.objects.create(name = 'thumbnail', caption = 'Thumbnail',      editable = False)
thumb.media_type.add(*[image, audio, video, doc])

preview  = Variant.objects.create(name = 'preview', caption = 'Preview',    editable = False)
preview.media_type.add(*[image, audio, video, doc])

fullscreen = Variant.objects.create(name = "fullscreen", caption = 'Fullscreen')
fullscreen.media_type.add(image)
#audio = Type.objects.get(name = 'audio')
#orig = Variant.objects.create(name = 'original', caption = 'Original',  is_global = True,  auto_generated = False, media_type = audio, shared = True,default_rank = 2)
#
#edited = Variant.objects.create(name = 'edited', caption = 'edited',  is_global = True, auto_generated = False,   media_type = audio, default_rank = 1)
#
#
#
#preview = Variant.objects.create(name = "preview", media_type = audio,  is_global = True)
#
#movie = Type.objects.get(name = 'movie')
#
#
#orig = Variant.objects.create(name = 'original', caption = 'Original',  is_global = True,  media_type = movie,  auto_generated = False, shared = True,default_rank = 2)
#
#
#edited = Variant.objects.create(name = 'edited', caption = 'edited',  is_global = True, auto_generated = False,   media_type = movie, default_rank = 1)
#
#
#thumb  = Variant.objects.create(name = 'thumbnail', caption = 'Thumbnail', media_type = movie,  is_global = True,  resizable = False,  editable = False, dest_media_type = image)
#
#preview = Variant.objects.create(name = "preview", media_type = movie,  is_global = True,  resizable = False)
##preview_pref = VideoPreferences.objects.create()
#
#
#doc = Type.objects.get(name = 'doc')
#
#orig = Variant.objects.create(name = 'original', caption = 'Original',  is_global = True,  media_type = doc,  auto_generated = False, shared = True, default_rank = 1)
#
#
#thumb  = Variant.objects.create(name = 'thumbnail', caption = 'Thumbnail',  media_type = doc,  is_global = True,  resizable = False,  editable = False, dest_media_type = image)
#
#preview = Variant.objects.create(name = "preview", media_type = doc,  is_global = True,  resizable = False, dest_media_type = image)
#
#
