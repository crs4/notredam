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
import re
from django.db import models
from dam.repository.models import Item
from dam.metadata.models import MetadataProperty
from django.db.models import Q

class GeoManager(models.Manager):

    def save_geo_coords(self, item, lat, lng):
        """
        Save geo coordinates of the given item
        """
        coord = re.compile(r"(\d*),(\d*.\d*)(\w)")
        lat_coord = coord.match(lat)
        lng_coord = coord.match(lng)
        decimal_lat = float(lat_coord.group(2)) / 60
        decimal_lng = float(lng_coord.group(2)) / 60
        if lat_coord.group(3) == 'N':
            latitude = str(float(lat_coord.group(1)) + decimal_lat)
        else:
            latitude = '-' + str(float(lat_coord.group(1)) + decimal_lat)
        if lng_coord.group(3) == 'E':
            longitude  = str(float(lng_coord.group(1)) + decimal_lng)
        else:
            longitude  = '-' + str(float(lng_coord.group(1)) + decimal_lng)
        metadata_lat = MetadataProperty.objects.filter(latitude_target=True)
        metadata_lng = MetadataProperty.objects.filter(longitude_target=True)
    
        self.filter(item=item).delete()
        geo = self.create(latitude=latitude, longitude=longitude, item=item)
        item.metadata.filter(schema__in=metadata_lat).delete()
        item.metadata.filter(schema__in=metadata_lng).delete()
        for m in metadata_lat:
            item.metadata.create(schema=m, value=latitude)
        for m in metadata_lng:
            item.metadata.create(schema=m, value=longitude)
        

    def search_geotagged(self, ne_lat, ne_lng, sw_lat, sw_lng, items=None):
        """
        Find items in the given area
        """    
        if(float(ne_lng)>float(sw_lng)):
            geotagged = self.filter(latitude__lte=ne_lat, latitude__gte=sw_lat, longitude__lt=ne_lng, longitude__gt=sw_lng)
        else:
            geotagged = self.filter(Q(longitude__gte=sw_lng) | Q(longitude__lte=ne_lng), latitude__lte=ne_lat, latitude__gte=sw_lat)

        if items:
            geotagged = geotagged.filter(item__in=items)

        return geotagged        

class GeoInfo(models.Model):
    """
    It contains geo coords of an item.
    """
    latitude = models.FloatField()
    longitude = models.FloatField()
    item = models.ForeignKey(Item)
    objects = GeoManager()
