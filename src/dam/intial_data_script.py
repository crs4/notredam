from django.core.management import setup_environ
import settings
setup_environ(settings)


from variants.models import *
from workspace.models import *

ws = Workspace.objects.get(pk = 1)
user = User.objects.get(pk = 1)
#wspa = WorkSpacePermissionAssociation.objects.get_or_create(workspace = ws, permission = WorkSpacePermission.objects.get(name='admin'))[0]
#wspa.users.add(user)
#ws.members.add(user)


image = Type.objects.get(name = 'image')

orig = Variant.objects.create(name = 'original', caption = 'Original',  is_global = True, auto_generated = False,  shared = True,  media_type = image, default_rank = 2)

edited = Variant.objects.create(name = 'edited', caption = 'edited',  is_global = True, auto_generated = False, media_type = image, default_rank = 1, dest_media_type = image)
#orig = Variant.objects.create(name = 'original', caption = 'Original',  is_global = True)

thumb  = Variant.objects.create(name = 'thumbnail', caption = 'Thumbnail',   media_type = image,  is_global = True,  resizable = False,  editable = False, dest_media_type = image)


fullscreen = Variant.objects.create(name = "fullscreen", media_type = image,  is_global = True)

audio = Type.objects.get(name = 'audio')
orig = Variant.objects.create(name = 'original', caption = 'Original',  is_global = True,  auto_generated = False, media_type = audio, shared = True,default_rank = 2)

edited = Variant.objects.create(name = 'edited', caption = 'edited',  is_global = True, auto_generated = False,   media_type = audio, default_rank = 1)


thumb  = Variant.objects.create(name = 'thumbnail', caption = 'Thumbnail',  media_type = audio, auto_generated = False,  is_global = True,  default_url = '/files/images/audio_thumbnail.jpg',  editable = False, dest_media_type = image)


preview = Variant.objects.create(name = "preview", media_type = audio,  is_global = True)

movie = Type.objects.get(name = 'movie')


orig = Variant.objects.create(name = 'original', caption = 'Original',  is_global = True,  media_type = movie,  auto_generated = False, shared = True,default_rank = 2)


edited = Variant.objects.create(name = 'edited', caption = 'edited',  is_global = True, auto_generated = False,   media_type = movie, default_rank = 1)


thumb  = Variant.objects.create(name = 'thumbnail', caption = 'Thumbnail', media_type = movie,  is_global = True,  resizable = False,  editable = False, dest_media_type = image)

preview = Variant.objects.create(name = "preview", media_type = movie,  is_global = True,  resizable = False)
#preview_pref = VideoPreferences.objects.create()


doc = Type.objects.get(name = 'doc')

orig = Variant.objects.create(name = 'original', caption = 'Original',  is_global = True,  media_type = doc,  auto_generated = False, shared = True, default_rank = 1)


thumb  = Variant.objects.create(name = 'thumbnail', caption = 'Thumbnail',  media_type = doc,  is_global = True,  resizable = False,  editable = False, dest_media_type = image)

preview = Variant.objects.create(name = "preview", media_type = doc,  is_global = True,  resizable = False, dest_media_type = image)


