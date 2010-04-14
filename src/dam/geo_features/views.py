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

"""
Views used for geoannotation and geo search functionalities
"""

from django.shortcuts import render_to_response
from django.template import RequestContext, Context, loader
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.utils import simplejson

from dam.repository.models import Item, Component, Container
from dam.workspace.models import Workspace
from dam.metadata.models import MetadataProperty
from dam.workspace.decorators import permission_required
from dam.geo_features.models import GeoInfo
from dam.workspace.views import _search_items

import logger

def _convert_deg_to_dms(latitude,longitude):
    
    """
    Converts coordinates from decimal degrees format to degree/minutes/seconds/ (DMS) format
    example: 39.5388888889 ---> 39,32,20N
    @param latitude: is coordinate in decimal degrees format.
    @param longitude: is coordinate in decimal degrees format.
    """
    
    latitude=float(latitude)
    longitude=float(longitude)
    if latitude < 0:
        lat_dir = "S"
    else:
        lat_dir = "N"
    if longitude < 0:
        lng_dir = "W"
    else:
        lng_dir = "E"
    
    latitude = abs(latitude)
    longitude= abs(longitude)
    
    lat_deg = int(latitude)
    lng_deg = int(longitude)
    
    lat_min_float = 60*(latitude - lat_deg)
    lng_min_float = 60*(longitude - lng_deg)
    
    lat_min = int(lat_min_float)
    lng_min = int(lng_min_float)
    
    lat_ss_float = 60*(lat_min_float - lat_min)
    lng_ss_float = 60*(lng_min_float - lng_min)
    
    lat_ss =  int(round(lat_ss_float))      
    lng_ss =  int(round(lng_ss_float))
    
    if lat_ss == 60:
        lat_ss = 0
        lat_min = lat_min + 1
    if lng_ss == 60:
        lng_ss = 0
        lng_min = lng_min + 1
            
    dms_latitude = "%d,%02d,%02d%s" % (lat_deg,lat_min,lat_ss,lat_dir)
    dms_longitude = "%d,%02d,%02d%s" % (lng_deg,lng_min,lng_ss,lng_dir)
    
    return dms_latitude,dms_longitude
    
def _convert_dms_to_deg(gpscoordinate):
    
    """
    Converts coordinates from DMS format to decimal degrees format
    example: 39,32,20N ---> 39.5388888889
    @param gpscoordinate: is coordinate in DMS format.
    """
    gpscoordinate = gpscoordinate.strip()

    gpscoordinate=gpscoordinate.split(",")
    
    deg_float=float(gpscoordinate[0])
    min_float=float(gpscoordinate[1])
    sc=gpscoordinate[2]
    if len(sc)==2:
        sc = "0"+sc
    sec_float=float(sc[0:2])
    card=sc[2]
    coord_float=min_float*60+sec_float
    coord_float=coord_float/3600
    coord_abs=deg_float+coord_float
    what_is_it = 'unknown'
    if card=='N' or card=="E":
        what_is_it = 'latitude' 
        coordinate=coord_abs
    elif card=='S' or card=="W":
        what_is_it = 'longitude' 
        coordinate=-coord_abs
    else:
        logger.debug('error: could not convert %s value %s'% (what_is_it,gpscoordinate) )
        return ''
    return str(coordinate)

def get_markers(request):
    
    """
    Get markers info for the given area
    """
    
    workspace = request.session.get('workspace') 

    bounds = simplejson.loads(request.POST.get('map_bounds'))
    zoom = int(request.POST.get('zoom'))
    media_type = request.POST.getlist('media_type')

    sw_lat= float(bounds['sw_lat'])
    sw_lng= float(bounds['sw_lng'])
    ne_lat= float(bounds['ne_lat'])
    ne_lng= float(bounds['ne_lng'])

    filter_items, count = _search_items(request, workspace, media_type, unlimited=True)

    point = []

    if(float(ne_lng)>float(sw_lng)):
        geotagged = GeoInfo.objects.filter(latitude__lte=ne_lat, latitude__gte=sw_lat, longitude__lt=ne_lng, longitude__gt=sw_lng, item__in=filter_items)
    else:
        geotagged = GeoInfo.objects.filter(Q(longitude__gte=sw_lng) | Q(longitude__lte=ne_lng), latitude__lte=ne_lat, latitude__gte=sw_lat, item__in=filter_items)

    for i in geotagged:
        point.append({'lat': i.latitude, 'lng': i.longitude, 'item': i.item.pk})

    resp = simplejson.dumps(list(point))
    return HttpResponse(resp)

def save_geo_coords(item, lat, lng):
    metadata_lat = MetadataProperty.objects.filter(latitude_target=True)
    metadata_lng = MetadataProperty.objects.filter(longitude_target=True)

    GeoInfo.objects.filter(item=item).delete()
    geo = GeoInfo.objects.create(latitude=lat, longitude=lng, item=item)
    item.metadata.filter(schema__in=metadata_lat).delete()
    item.metadata.filter(schema__in=metadata_lng).delete()
    for m in metadata_lat:
        item.metadata.create(schema=m, value=lat)
    for m in metadata_lng:
        item.metadata.create(schema=m, value=lng)
    

def save_geoinfo(request):

    """
    Save geotag info for the given items
    """
    
    coords = simplejson.loads(request.POST.get('coords'))
    items = simplejson.loads(request.POST.get('items'))

    for i in items:
        item_object = Item.objects.get(pk=i)
        latitude = coords['lat']
        longitude = coords['lng']
        save_geo_coords(item_object, latitude, longitude)

    resp = simplejson.dumps({'success': True})

    return HttpResponse(resp)
    
