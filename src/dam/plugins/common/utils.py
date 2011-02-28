import mimetypes
from mediadart import log
from dam.metadata.models import MetadataProperty, MetadataValue

def save_type(ctype, component):
    "Extract and save the format of the component as the value of dc:format"
    mime_type = mimetypes.guess_type(component.uri)[0]
    component.format = mime_type.split('/')[1]
    metadataschema_mimetype = MetadataProperty.objects.get(namespace__prefix='dc',field_name='format')
    MetadataValue.objects.create(schema=metadataschema_mimetype, content_object=component, value=mime_type)

def get_variants(workspace, media_type = None):
    from django.db.models import Q
    from dam.variants.models import Variant
    tmp_variants = Variant.objects.filter(Q(workspace = workspace) | Q(workspace__isnull = True),  hidden = False)
    if media_type:
        tmp_variants = tmp_variants.filter(media_type__name = media_type)
     
    return [[variant.name] for variant in tmp_variants]