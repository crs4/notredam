import mimetypes
from mediadart import log
from dam.metadata.models import MetadataProperty, MetadataValue

def save_type(ctype, component):
    "Extract and save the format of the component as the value of dc:format"
    log.debug( '1' )
    mime_type = mimetypes.guess_type(component.uri)[0]
    log.debug( '2' )
    component.format = mime_type.split('/')[1]
    log.debug( '3' )
    metadataschema_mimetype = MetadataProperty.objects.get(namespace__prefix='dc',field_name='format')
    log.debug( '4' )
    MetadataValue.objects.create(schema=metadataschema_mimetype, content_object=component, value=mime_type)
    log.debug( '5' )

