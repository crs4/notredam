import flickrapi

from dam.repository.models import Item, Component
from dam.metadata.models import *
from django.utils.encoding import smart_str
from dam.workspace.models import Workspace
from dam.geo_features.views import save_geo_coords

api_key = 'd993f922f8677449aad279a029abedac'

def get_geo_metadata():

    flickr = flickrapi.FlickrAPI(api_key)

    photo_id = '10813776'

    info = flickr.photos_geo_getLocation(photo_id=photo_id)

    items = Item.objects.all()

    for p in info:
        location = p.getiterator('location')[0]
        if location:
            latitude = location.attrib.get('latitude')
            longitude = location.attrib.get('longitude')
            if latitude and longitude:
                print latitude, longitude
                for i in items:
                    save_geo_coords(i, latitude, longitude)

def get_metadata_from_flickr():

    flickr = flickrapi.FlickrAPI(api_key)

    comps = Component.objects.filter(variant__name = 'original').exclude(comp_rights__in=RightsValue.objects.all())
    
    schema_creator = MetadataProperty.objects.get(namespace__prefix='dc', field_name='creator')
    schema_description = MetadataProperty.objects.get(namespace__prefix='dc', field_name='description')
    schema_title = MetadataProperty.objects.get(namespace__prefix='dc', field_name='title')
    schema_subject = MetadataProperty.objects.get(namespace__prefix='dc', field_name='subject')

    schema_cc_creator = MetadataProperty.objects.get(namespace__prefix='cc', field_name='attributionName')
    schema_cc_url = MetadataProperty.objects.get(namespace__prefix='cc', field_name='attributionUrl')

    ws = Workspace.objects.all()[0]

    license_dict = {'1': 'Creative Commons BY-NC-SA', '0': 'All rights reserved', '3': 'Creative Commons BY-NC-ND', '2': 'Creative Commons BY-NC', '5': 'Creative Commons BY-SA', '4': 'Creative Commons BY', '7': 'No known copyright restrictions', '6': 'Creative Commons BY-ND', '8': 'United States Government Work'}

    for l, v in license_dict.iteritems():
        try:
            license_dict[l] = RightsValue.objects.get(value=v)
        except:
            print l
            continue
            
    for comp in comps:
    
        photo_id = comp.file_name.split('.')[0]
        info = flickr.photos_getInfo(photo_id=photo_id)
    
        item = comp.item

        item.metadata.filter(schema=schema_cc_url).delete()
        item.metadata.filter(schema=schema_cc_creator).delete()        
        comp.metadata.filter(schema=schema_cc_url).delete()
        comp.metadata.filter(schema=schema_cc_creator).delete()
        item.metadata.filter(schema=schema_creator).delete()
        item.metadata.filter(schema=schema_description).delete()
        item.metadata.filter(schema=schema_title).delete()
        item.metadata.filter(schema=schema_subject).delete()
    
        for p in info:
            title = p.getiterator('title')[0].text
            description = p.getiterator('description')[0].text
            author = p.getiterator('owner')[0].attrib.get('realname')
            print photo_id, title, description, author
            if description:
                description = smart_str(description)        
                item.metadata.create(schema=schema_description, value=description, language='en-US')
            if title:
                title = smart_str(title)
                item.metadata.create(schema=schema_title, value=title, language='en-US')
            if author:
                author = smart_str(author)
                item.metadata.create(schema=schema_creator, value=author)
                comp.metadata.create(schema=schema_cc_creator, value=author)

            urls = p.getiterator('urls')[0]
            url = urls[0].getiterator('url')[0].text

            print url

            license = p.attrib.get('license')

            if license:
                schema = license_dict.get(license)
                if isinstance(schema, RightsValue):
                    schema.components.add(comp)

            if url:
                url = smart_str(url)
                comp.metadata.create(schema=schema_cc_url, value=url)                
    
            for t in p.find('tags'):
                tag = smart_str(t.text)
                item.metadata.create(schema=schema_subject, value=tag)

#get_metadata_from_flickr()
get_geo_metadata()