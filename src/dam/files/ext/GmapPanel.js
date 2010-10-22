/*
 * Ext JS Library 2.2.1
 * Copyright(c) 2006-2009, Ext JS, LLC.
 * licensing@extjs.com
 * 
 * http://extjs.com/license
 */

/**
 * @author Shea Frederick
 */

Ext.namespace('Ext.ux');
 
/**
 *
 * @class GMapPanel
 * @extends Ext.Panel
 */
Ext.ux.GMapPanel = Ext.extend(Ext.Panel, {
    initComponent : function(){
        
        var defConfig = {
            plain: true,
            zoomLevel: 3,
            yaw: 180,
            pitch: 0,
            zoom: 0,
            gmapType: 'map',
            border: false
        };
        
        Ext.applyIf(this,defConfig);
        
        Ext.ux.GMapPanel.superclass.initComponent.call(this);        

    },
    afterRender : function(){
        
        var wh = this.ownerCt.getSize();
        Ext.applyIf(this, wh);
        
        Ext.ux.GMapPanel.superclass.afterRender.call(this);    
        
        var mapTypes = G_DEFAULT_MAP_TYPES;
        for(var i = 0; i < mapTypes.length; i++){
            mapTypes[i].getMaximumResolution = function(latlng){ return 13;};
            mapTypes[i].getMinimumResolution = function(latlng){ return 3;};
        }

        if (this.gmapType === 'map'){
            this.gmap = new GMap2(this.body.dom, {mapTypes: mapTypes});
        }
        
        if (this.gmapType === 'panorama'){
            this.gmap = new GStreetviewPanorama(this.body.dom);
        }
        
        if (typeof this.addControl == 'object' && this.gmapType === 'map') {
            this.gmap.addControl(this.addControl);
        }

        GEvent.bind(this.gmap, 'load', this, function(){
            this.onMapReady();
        });
        
        if (typeof this.setCenter === 'object') {
            if (typeof this.setCenter.geoCodeAddr === 'string'){
                this.geoCodeLookup(this.setCenter.geoCodeAddr);
            }else{
                if (this.gmapType === 'map'){
                    var point = new GLatLng(this.setCenter.lat,this.setCenter.lng);
                    this.gmap.setCenter(point, this.zoomLevel);    
                }
            }
            if (this.gmapType === 'panorama'){
                this.gmap.setLocationAndPOV(new GLatLng(this.setCenter.lat,this.setCenter.lng), {yaw: this.yaw, pitch: this.pitch, zoom: this.zoom});
            }
        }

//        this.markerManager = new MarkerManager(this.gmap);

        GEvent.bind(this.gmap,'moveend', this, function(){this.onMapMove();}); 

        GEvent.bind(this.gmap,'zoomend', this, function(){this.onMapMove();}); 

        GEvent.bind(this.gmap,'mousemove', this, function(point){this.current_point=point;}); 

        GEvent.bind(this.gmap,'click', this, function(overlay, point){
            if (overlay && overlay.gmap) {
                item = overlay.gmap.lastMarkers[overlay.map_index].item;
                var html = "<img src='/redirect_to_component/"+item+"/3/'/>";
                overlay.openInfoWindowHtml(html);
            }
        }); 

    },

    onMapMove: function() {        
        var bounds = this.gmap.getBounds();
        var map_bounds = {sw_lat: bounds.getSouthWest().lat(), sw_lng: bounds.getSouthWest().lng(), ne_lat: bounds.getNorthEast().lat(), ne_lng: bounds.getNorthEast().lng()}
        var clusterIcon = MapIconMaker.createFlatIcon({width: 24, height: 24, primaryColor: "#00ff00", label: '+', labelColor: "#ffffff"});
        var mgr = this.markerManager || new ClusterMarker(this.gmap, {clusterMarkerIcon: clusterIcon, clusterMarkerClick: function(args) { var i = args.clusterMarker.cluster_index; args.clusterMarker.openInfoWindowHtml('<b>' + args.clusteredMarkers.length + ' items found in this area</b><br /><a href="#" onClick="javascript: var tab = Ext.getCmp(\'media_tabs\').getActiveTab(); var map_id = \'gmappanel\' + tab.id.replace(\'map_\', \'\'); Ext.getCmp(map_id).markerManager.clusterMarkerClickByIndex(' + i + '); var bounds = Ext.getCmp(map_id).gmap.getBounds(); var map_bounds = {sw_lat: bounds.getSouthWest().lat(), sw_lng: bounds.getSouthWest().lng(), ne_lat: bounds.getNorthEast().lat(), ne_lng: bounds.getNorthEast().lng()}; var geo_query = \'geo:(\'+bounds.getNorthEast().lat()+\',\'+bounds.getNorthEast().lng()+\'),(\'+bounds.getSouthWest().lat()+\',\'+bounds.getSouthWest().lng()+\')\'; var search_field = Ext.getCmp(\'search_field\'); search_field.setValue(geo_query); set_query_on_store({query:geo_query});">Search items here</a>-<a href="#" onClick="javascript: var tab = Ext.getCmp(\'media_tabs\').getActiveTab(); var map_id = \'gmappanel\' + tab.id.replace(\'map_\', \'\'); Ext.getCmp(map_id).markerManager.clusterMarkerClickByIndex(' + i + ');">Zoom here</a>');}});
        this.markerManager = mgr;
        var conn = new Ext.data.Connection();
        var gmap = this;
        var store_params = Ext.getCmp('media_tabs').getActiveTab().getComponent(0).getStore().lastOptions ? Ext.getCmp('media_tabs').getActiveTab().getComponent(0).getStore().lastOptions.params : {};
        store_params['map_bounds'] = Ext.encode(map_bounds);
        store_params['zoom'] = this.gmap.getZoom();        
        
        store_params['media_type'] = Ext.getCmp('media_tabs').getActiveTab().getMediaTypes();
        gmap.items_map = {};
        gmap.last_selected = {};
        conn.request({
            method:'POST', 
            url: '/get_markers/',
            params: store_params,
            success: function(data, textStatus){
                var points = Ext.decode(data.responseText);
                var batch = [];
                for (var i=0; i < points.length; i++) {
                    p = new GLatLng(points[i].lat, points[i].lng);
                    var newIcon = MapIconMaker.createMarkerIcon({width: 24, height: 24, primaryColor: "#ff0000", labelColor: "#ffffff"});
                    var marker = new GMarker(p, {icon: newIcon, draggable: true});
                    marker.map_index = i;
                    marker.gmap = gmap;
                    gmap.items_map[points[i].item] = marker;
                    GEvent.addListener(marker, "dragend", function(m) { 
                        var marker = this;
                        var coords = {lat: m.lat(), lng: m.lng()};
                        var conn = new Ext.data.Connection();
                        conn.request({
                            method:'POST', 
                            url: '/save_geoinfo/',
                            params: {coords: Ext.encode(coords), items: Ext.encode([marker.gmap.lastMarkers[marker.map_index].item])},
                            success: function(data, textStatus){
                                marker.gmap.onMapMove();
                            },
                            failure: function (XMLHttpRequest, textStatus, errorThrown) {
                                Ext.MessageBox.alert('Status', 'Saving failed!');
                            }
                        });
                    });
                    batch.push(marker);
                }
                gmap.lastMarkers = points;
//                mgr.clearMarkers();
//                mgr.addMarkers(batch, 3);
//                mgr.refresh();
                mgr.removeMarkers();
                if (batch.length > 0)
                    mgr.addMarkers(batch);
                mgr.refresh();
                
//                mgr.fitMapToMarkers();
            },
            failure: function (XMLHttpRequest, textStatus, errorThrown) {
                Ext.MessageBox.alert('Status', 'Saving failed!');
            }            
       });
    },
    onMapReady : function(){
        this.addMarkers(this.markers);
        this.addMapControls();
        this.addOptions();  
        this.onMapMove();
    },
    onResize : function(w, h){

        if (typeof this.getMap() == 'object') {
            this.gmap.checkResize();
        }
        
        Ext.ux.GMapPanel.superclass.onResize.call(this, w, h);

    },
    setSize : function(width, height, animate){
        
        if (typeof this.getMap() == 'object') {
            this.gmap.checkResize();
        }
        
        Ext.ux.GMapPanel.superclass.setSize.call(this, width, height, animate);
        
    },
    getMap : function(){
        
        return this.gmap;
        
    },
    getCenter : function(){
        
        return this.getMap().getCenter();
        
    },
    getCenterLatLng : function(){
        
        var ll = this.getCenter();
        return {lat: ll.lat(), lng: ll.lng()};
        
    },
    addMarkers : function(markers) {
        
        if (Ext.isArray(markers)){
            for (var i = 0; i < markers.length; i++) {
                var mkr_point = new GLatLng(markers[i].lat,markers[i].lng);
                this.addMarker(mkr_point,markers[i].marker,false,markers[i].setCenter, markers[i].listeners);
            }
        }
        
    },
    addMarker : function(point, marker, clear, center, listeners, props){
        
        Ext.applyIf(marker,G_DEFAULT_ICON);

        if (clear === true){
            this.getMap().clearOverlays();
        }
        if (center === true) {
            this.getMap().setCenter(point, this.zoomLevel);
        }

        var mark = new GMarker(point,marker);
        if (typeof listeners === 'object'){
            for (evt in listeners) {
                GEvent.bind(mark, evt, this, listeners[evt]);
            }
        }

        if (typeof props === 'object'){

            for (p in props) {
                mark.p = props[p];
            }
        }

        this.getMap().addOverlay(mark);


    },
    addMapControls : function(){
        
        if (this.gmapType === 'map') {
            if (Ext.isArray(this.mapControls)) {
                for(i=0;i<this.mapControls.length;i++){
                    this.addMapControl(this.mapControls[i]);
                }
            }else if(typeof this.mapControls === 'string'){
                this.addMapControl(this.mapControls);
            }else if(typeof this.mapControls === 'object'){
                this.getMap().addControl(this.mapControls);
            }
        }
        
    },
    addMapControl : function(mc){
        
        var mcf = window[mc];
        if (typeof mcf === 'function') {
            this.getMap().addControl(new mcf());
        }    
        
    },
    addOptions : function(){
        
        if (Ext.isArray(this.mapConfOpts)) {
            var mc;
            for(i=0;i<this.mapConfOpts.length;i++){
                this.addOption(this.mapConfOpts[i]);
            }
        }else if(typeof this.mapConfOpts === 'string'){
            this.addOption(this.mapConfOpts);
        }        
        
    },
    addOption : function(mc){
        
        var mcf = this.getMap()[mc];
        if (typeof mcf === 'function') {
            this.getMap()[mc]();
        }    
        
    },
    geoCodeLookup : function(addr) {
        
        this.geocoder = new GClientGeocoder();
        this.geocoder.getLocations(addr, this.addAddressToMap.createDelegate(this));
        
    },
    addAddressToMap : function(response) {
        
        if (!response || response.Status.code != 200) {
            Ext.MessageBox.alert('Error', 'Code '+response.Status.code+' Error Returned');
        }else{
            place = response.Placemark[0];
            addressinfo = place.AddressDetails;
            accuracy = addressinfo.Accuracy;
            if (accuracy === 0) {
                Ext.MessageBox.alert('Unable to Locate Address', 'Unable to Locate the Address you provided');
            }else{
                if (accuracy < 7) {
                    Ext.MessageBox.alert('Address Accuracy', 'The address provided has a low accuracy.<br><br>Level '+accuracy+' Accuracy (8 = Exact Match, 1 = Vague Match)');
                }else{
                    point = new GLatLng(place.Point.coordinates[1], place.Point.coordinates[0]);
                    if (typeof this.setCenter.marker === 'object' && typeof point === 'object'){
                        this.addMarker(point,this.setCenter.marker,this.setCenter.marker.clear,true, this.setCenter.listeners);
                    }
                }
            }
        }
        
    }
 
});

Ext.reg('gmappanel',Ext.ux.GMapPanel); 
