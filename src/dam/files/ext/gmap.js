/*
*
* NotreDAM, Copyright (C) 2009, Sardegna Ricerche.
* Email: labcontdigit@sardegnaricerche.it
* Web: www.notre-dam.org
*
* This program is free software: you can redistribute it and/or modify
*    it under the terms of the GNU General Public License as published by
*    the Free Software Foundation, either version 3 of the License, or
*    (at your option) any later version.
*
*    This program is distributed in the hope that it will be useful,
*    but WITHOUT ANY WARRANTY; without even the implied warranty of
*    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
*    GNU General Public License for more details.
*
*/

var close_map = function(button) {

    var tab = Ext.getCmp('media_tabs').getActiveTab();
    if(tab.getComponent(1).items.items.length > 0){
	    tab.getComponent(1).hide();
	    tab.getComponent(1).removeAll();
	    
	    tab.doLayout();
	}
//    
//    var view_store = Ext.getCmp('media_tabs').getActiveTab().getComponent(0).getStore();
//
//    var media_view = createView({
//        store: view_store
//    });
//
//    var view_id = tab.id.replace('map_', '');
//
//    var pagingBar_media = createPaginator({
//        store: view_store,
//        id: 'paginator_'+view_id
//    });
//
//    var media_tab = createMediaPanel({
//        id:view_id,
//        title:tab.title,
//        items: [media_view],
//
//        bbar: pagingBar_media
//    });
//
//    Ext.get('media_tabs').mask('Loading, please wait...');
//
//    var dest_index;
//
//    if (view_id == 'images') {
//        dest_index = 0;
//    }
//    else if (view_id == 'videos') {
//        dest_index = 1;
//    }
//    else if (view_id == 'audio') {
//        dest_index = 2;
//    }        
//    else { 
//        dest_index = 3;
//    }
//    
//    Ext.getCmp('media_tabs').remove(Ext.getCmp(tab.id));
//    Ext.getCmp('media_tabs').insert(dest_index, Ext.getCmp(view_id));
//    Ext.getCmp('media_tabs').setActiveTab(Ext.getCmp(view_id));
//    Ext.get('media_tabs').unmask();
//
//    var drag_zone = new ImageDragZone(Ext.getCmp(view_id).getComponent(0), {containerScroll:true,
//        ddGroup: 'organizerDD'});

};

var initializeMapDropZone = function(g){
        
    var dz = new Ext.dd.DropZone(g.getEl(), {ddGroup: 'organizerDD'});
//    dz.onContainerOver = function(source, e, data) { 
//        return this.dropAllowed;
//    }

    dz.getTargetFromEvent=function(e) {
        var target = e.getTarget('', 10, true);
        if (target){
            return target;
        }
    };

    dz.onNodeOver = function(target, dd, e, data){
        return this.dropAllowed;
    };

    dz.onNodeDrop = function(nodeData, source, e, data ){
    	
        var media_tab = Ext.getCmp('media_tabs').getActiveTab();
        var view = media_tab.getComponent(0);
        var getSelectedIndexes = view.getSelectedIndexes();
        var items = [];
        for (i = 0; i<getSelectedIndexes.length; i++){
            var node_index = getSelectedIndexes[i];
            var item = view.getStore().getAt(node_index).data.pk;
            items.push(item);            
        }
        var events = {dragend: function(marker){
               var coords = {lat: marker.lat(), lng: marker.lng()};
               var conn = new Ext.data.Connection();
               conn.request({
                   method:'POST', 
                   url: '/save_geoinfo/',
                   params: {coords: Ext.encode(coords), items: Ext.encode(items)},
                   success: function(data, textStatus){
                       g.onMapMove();
                   },
                   failure: function (XMLHttpRequest, textStatus, errorThrown) {
                       Ext.MessageBox.alert(gettext('Status'), gettext('Saving failed!'));
                   }
              });
        }};
//        g.addMarker(g.current_point, {draggable:true}, false, false, events, {items: items});
        var coords = {lat: g.current_point.lat(), lng: g.current_point.lng()};
        var conn = new Ext.data.Connection();
        conn.request({
            method:'POST', 
            url: '/save_geoinfo/',
            params: {coords: Ext.encode(coords), items: Ext.encode(items)},
            success: function(data, textStatus){
                g.onMapMove();
            },
            failure: function (XMLHttpRequest, textStatus, errorThrown) {
                Ext.MessageBox.alert(gettext('Status'), gettext('Saving failed!'));
            }            
        });
        
        return true;  
    };
            
};

var open_map = function(button) {
	var tab = Ext.getCmp('media_tabs').getActiveTab();
	if(tab.getComponent(1).items.items.length > 0)
		return;

    var selectMarker = function(view) {
        var selNodes= view.getSelectedNodes();
        var map_id = 'gmappanel' + Ext.getCmp('media_tabs').getActiveTab().getId().replace('map_', '');
        var map = Ext.getCmp(map_id);
        var defaultIcon = MapIconMaker.createMarkerIcon({width: 24, height: 24, primaryColor: "#ff0000", labelColor: "#ffffff"});
        for (var key in map.last_selected) {
            map.last_selected[key].setImage(defaultIcon.image);
        }
        map.last_selected = {};
        if (selNodes && selNodes.length > 0) {

            for (var i = 0; i < selNodes.length; i++) {
                var item_data = view.store.getAt(view.store.find('pk', selNodes[i].id)).data;
                if (map.items_map[item_data.pk]) {
                    var newIcon = MapIconMaker.createMarkerIcon({width: 24, height: 24, primaryColor: "#ffff00", labelColor: "#ffffff"});
                    map.items_map[item_data.pk].setImage(newIcon.image);
                    map.last_selected[item_data.pk] = map.items_map[item_data.pk];
                }
            }

        }

    };

    var createMapView = function(config) {
 
        var tpl;
 
        if (config['store'].id == 'store_all') {

            tpl = new Ext.XTemplate(
                '<tpl for=".">',
                '<div class="thumb-wrap" id="{pk}">',
                '<div class="thumb"><tpl if="geotagged === 1"><span class="geotagged"></span></tpl><span class="{type}_icon"></span><img src="{url}" class="thumb-img"></div>',
                '<span>{shortName}</span></div>',
                '</tpl>'
            );

        }
        else {
            tpl = new Ext.XTemplate(
                '<tpl for=".">',
                '<div class="thumb-wrap" id="{pk}">',
                '<div class="thumb"><tpl if="geotagged === 1"><span class="geotagged"></span></tpl><img src="{url}" class="thumb-img"></div>',
                '<span>{shortName}</span></div>',
                '</tpl>'
            );
        }

        return new Ext.DataView(Ext.apply({
            region:'center',
            itemSelector: 'div.thumb-wrap',
            style:'overflow:auto',
            multiSelect: true,
            plugins: new Ext.DataView.DragSelector({dragSafe:true}),
            height: 300,
            tpl: tpl,
            listeners: {
                'selectionchange': {fn:function(view) {showDetails(view); selectMarker(view);}, buffer:100},
                'dblclick': {fn:showFullscreen, buffer:100}
            }
        }, config));
    };

    
//    var view_store = Ext.getCmp('media_tabs').getActiveTab().getComponent(0).getStore();

//    var map_view = createMapView({
//        frame: true,
//        store: view_store,
//        height:150
//    });
//
//    var pagingBar_map = createPaginator({
//        store: view_store,
//        id: 'paginator_'+tab.id
//    });

    var zoomOpts = { 
          buttonStartingStyle: {display:'block',color:'black',background:'white',width:'7em',textAlign:'center',
            fontFamily:'Verdana',fontSize:'12px',fontWeight:'bold',border:'1px solid gray',paddingBottom:'1px',cursor:'pointer'},
          buttonHTML: 'Search items',
          buttonZoomingHTML: 'Drag a region on the map (click here to reset)',
          buttonZoomingStyle: {background:'yellow'},
          backButtonHTML: 'Zoom Back',  
          backButtonStyle: {display:'none',marginTop:'3px',background:'#FFFFC8'},
          backButtonEnabled: true,
          restrictedRectangleMap: false
    };

    var gmap = new Ext.ux.GMapPanel({
        height: 300,
        zoomLevel: 3,
        gmapType: 'map',
        id: 'gmappanel'+tab.id,
        region: 'north',
        frame: true,
        split: true,
        mapConfOpts: ['enableScrollWheelZoom','enableDoubleClickZoom','enableDragging'],
        mapControls: ['GLargeMapControl3D','GMapTypeControl'],
        setCenter: {
            lat: 41.64, 
            lng: 13.00
        },
        addControl: new DragZoomControl({}, zoomOpts, {dragend:function(nw,ne,se,sw,nwpx,nepx,sepx,swpx){
        	var geo_query = 'geo:('+ne.lat()+','+ne.lng()+'),('+sw.lat()+','+sw.lng()+')'; 
        	var search_f = Ext.getCmp('media_tabs').getActiveTab().getSearch(); 
        	search_f.setValue(geo_query); set_query_on_store({query:geo_query});
        	}
        })
    });

    Ext.get('media_tabs').mask('Loading, please wait...');
    tab.getComponent(1).add(gmap);
    tab.getComponent(1).show();
    tab.getComponent(1).doLayout();
    tab.doLayout();

    Ext.get('media_tabs').unmask();


    initializeMapDropZone(gmap);

};
