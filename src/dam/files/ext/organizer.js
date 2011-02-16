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

function set_status_bar_busy(){
	var sb = Ext.getCmp('dam_statusbar');
	if(sb)
		sb.showBusy({
		    iconCls: 'x-status-busy status_busy'
		});
};

function update_task_status(data){
	
	
	var sb = Ext.getCmp('dam_statusbar');
	if(sb){
		
		
		data = data.status_bar;
		if (data){
		    var pending = data.pending + data.failed;
		    var text, iconCls;
		    
		    
		    function _set_ok(){
				text = 'No script running';
			
		        iconCls = 'status-ok';	        
		        if (Ext.query('.'+ cls_audio).length > 0)
		        	start_audio_player();
			};
		    
		    
		    if (data.process_in_progress == 0) {
		        _set_ok();
		    }
		    else {
		
		        text = String.format('<a href=javascript:show_monitor();>running {0} script(s), {1} item(s) left</a>', data.process_in_progress, data.pending_items);
				iconCls = 'status-warning';
		    }
	    
	    }
	    else {
	    	_set_ok();
	    	
	    	
	    }
	    (function(){
	        sb.setStatus({
	            text: text,
	            iconCls: iconCls
	        });
	    }).defer(1500);

	}
};

var basket_size_var =0;
function basket_size(){
        Ext.Ajax.request({
            url:'/basket_size/',
	    params: {},
            success: function(response){
	        // return response.responseText;
	        Ext.getCmp('basket_items').setText(response.responseText);	
            }
        });  
        //return '0'; 
}

function  reload_selected_nodes(){

    var ac = Ext.getCmp('media_tabs').getActiveTab();
    var view = ac.getComponent(0);

    var selNodes= view.getSelectedNodes();
    var items_param = [];
    for (var i = 0; i < selNodes.length; i++) {
        items_param.push(selNodes[i].id);
    }
    Ext.Ajax.request({
        url:'/reload_item/',
        params: {items: items_param},
        success: function(response){
            view.getStore().reload();
            Ext.getCmp('basket_items').setText(response.responseText);	
        }
    });

}

function  remove_from_basket(){

    var ac = Ext.getCmp('media_tabs').getActiveTab();
    var view = ac.getComponent(0);

    var selNodes= view.getSelectedNodes();
    var items_param = [];
    for (var i = 0; i < selNodes.length; i++) {
        items_param.push(selNodes[i].id);
    }
    Ext.Ajax.request({
        url:'/remove_from_basket/',
	    params: {items: items_param},
            success: function(response){
                view.getStore().reload();
                Ext.getCmp('basket_items').setText(response.responseText);	
            }
    });  

}


function  clear_basket(){

    var ac = Ext.getCmp('media_tabs').getActiveTab();
    var view = ac.getComponent(0);

        Ext.Ajax.request({
            url:'/clear_basket/',
            params: {},
            success: function(response){
                view.getStore().reload();	
                Ext.getCmp('basket_items').setText(response.responseText);	
            }
        });  

}


function reload_node(items){
    var ac = Ext.getCmp('media_tabs').getActiveTab();
    var view = ac.getComponent(0);

   //var selNodes= view.getSelectedNodes();
    var items_param = items;

    Ext.Ajax.request({
        url:'/reload_item/',
        params: {items: items_param},
        success: function(response){
            view.getStore().reload();	
        // view.refresh();	
        }
    });       
       
   // view.refreshNode(0);
}

var previewTemplate, previewAudioTemplate, previewMovieTemplate = null;

var basicTemplate = new Ext.XTemplate(
'<div class="details">',
'<div class="details-info"><br/>',
'<tpl for="descriptors">',
    '<b>{caption}:</b><br/>',
	'<tpl if="value.properties === undefined">',
        '<tpl if="this.isString(value)">',
            '<span>{value}</span><br/>',
        '</tpl>',
        '<tpl if="this.isString(value) == false">',
            '<span>',
            '<tpl for="value">',
                '{.}, ',
            '</tpl>',
            '</span><br/>',
        '</tpl>',
    '</tpl>',
    '<tpl if="value.properties">',
        '<tpl for="value.properties">',
            '<b class="metadata-structure">{caption}:</b><br/>',
            '<span class="metadata-structure">{value}</span><br/>',      
        '</tpl>',
    '</tpl>',
'</tpl>',
'</div>',
'</div>',
{
        compiled: true,
        isString: function(value){
            return typeof(value) == 'string';
        }
    }
 );

basicTemplate.compile();

var store_nodes_checked = new Ext.data.JsonStore({
    fields:['id', 'type', 'tristate', 'items'],
    url:'/get_item_nodes/',
    root: 'nodes',
    listeners:{
        load:  function(store, nodes){
            for (var i = 0; i < nodes.length; i++){
                var node, cb;
                if (nodes[i].data.type == 'keyword') {
                    node= Ext.getCmp('keywords_tree').getNodeById(nodes[i].data.id);
                }
                else {
                    node= Ext.getCmp('collections_tree').getNodeById(nodes[i].data.id);
                }
                if (node){                        
                    cb = node.getUI().checkbox;
                    
                    if (cb){
                        cb.checked = true;                           
                        set_tristate(node, nodes[i].data.tristate, nodes[i].data.items);
                        
                    }
                }
            }
        }
    }
});

var current_item_selected;

function showFullscreen(view, index, node, e){
	
    var data = view.store.getAt(view.store.findExact('pk', node.id)).data;
        
    Ext.Ajax.request({
        url:'/get_component_url/'+data.pk+'/fullscreen/',
        success: function(response){
            var resp = response.responseText;
//                img =Ext.get('fullscreen_img').dom

            try {
                var decoded_resp = Ext.decode(resp);
                var url = '/redirect_to_component/' + data.pk + '/original/?download=1';
                window.open(url);

            }
            catch(err) {

                var fullscreen_url = resp;            

                var img = new Image();
                var img_width, img_height;
                img.onload = function(){
                    var tmp = getFullscreenSize(img);
                    
                    img_width = tmp[0];
                    img_height = tmp[1];
                    img.width = img_width; 
                    img.height= img_height;
                    
                    var win = new Ext.Window({
                        modal: true,
                        width:img_width + 15 ,
                        height:img_height + 30,
                        resizable: false,
                        constrain: true,
                        title: 'fullscreen',
                        html: '<div id="fullscreen"><img width="'+img_width +'" height="'+img_height+'" src="' + fullscreen_url+'"></img></div>',
    
                        listeners:{
                            show: function(){
                                this.center();                     
                            }                            
                        }                
                    });

                    win.show();
                   
                };
    
                img.src = fullscreen_url;
                            
            }


        }
        
    });
    
}

function _show_details(data, active_tab, view, selNode){
    active_tab.show();
    var store = null;
//        if(active_tab.id == 'variant_panel'){
//            store = store_variant;
//            var items_param = data.pk;
//
//        }
    var selNodes= view.getSelectedNodes();
    
    if(active_tab.id == 'metadata_panel' || active_tab.id == 'xmp_panel') {
        store = active_tab.getStore();
        
        var items_param = get_selected_items();
    }
    
    else if(active_tab.id == 'preview_panel'){
        
        var store = Ext.getCmp('variant_summary').getStore();
        var preview = Ext.getCmp('summary_panel').body;
        if( selNodes.length > 1){
            store.removeAll();
            var detail_tabs_panel = Ext.getCmp('detail_tabs');
            var active_tab =  detail_tabs_panel.getActiveTab();
            active_tab.hide();
            current_item_selected = null;
            return;
        }
        
        if (selNode == current_item_selected ) {
            return;
        }
        
        var items_param = data.pk;
        current_item_selected = selNode;        
        
        preview.hide();

        Ext.Ajax.request({
            url: '/get_basic_descriptors/',
            params: {items: items_param},
            success: function(data){
                data = Ext.decode(data.responseText);
                var basic_p = Ext.getCmp('basic_panel').body;
                basicTemplate.overwrite(basic_p, data);
            }
        });
        
        var state_id = data.state;
        if (state_id){
            var record = ws_state_store.query('pk', state_id);
            var state_name = record.items[0].data.name;
            data.state_name = state_name;
            
            
            }
        
        if (data.type == 'image' || data.type == 'doc') {
            previewTemplate.overwrite(preview, data);
        }
        else if (data.type == 'video') {
            previewMovieTemplate.overwrite(preview, data);
            flowplayer("player", "/files/flowplayer/flowplayer-3.1.4.swf", { 
                clip: { initialScale: 'orig', autoPlay: false, scaling: 'orig' },             
                plugins: { 
                    controls: { 
                        fullscreen: false, 
                        height: 30 
                    } 
                }
            }); 
        } else if (data.type == 'audio') {
            previewAudioTemplate.overwrite(preview, data);
            flowplayer("player", "/files/flowplayer/flowplayer-3.1.4.swf", { 
                clip: { autoPlay: false},
                plugins: { 
                    audio: { 
                        url: '/files/flowplayer/flowplayer.audio.swf' 
                    }, 
                    controls: { 
                        fullscreen: false, 
                        height: 30 
                    } 
                }
            }); 
        }

//            preview.slideIn('l', {stopFx:true,duration:.2});
        preview.fadeIn({stopFx:true,duration:0.4});

        
        
        
        
        
        }

    if(store) {
            var old_items_selected = store.lastOptions ? store.lastOptions.params.items : items_param ;
            store.load({params: {items: items_param, old_items: old_items_selected}});
/*            if (!store.lastOptions)
            store.load({params: {items: items_param}});
        else
            if (store.lastOptions.params.items != items_param)
                store.load({params: {items: items_param}}); */

    }
}

var getFullscreenSize = function (size) {

//        var win_width = Ext.lib.Dom.getViewWidth(true)-15;
//        var win_height = Ext.lib.Dom.getViewHeight(true)-30;
    var vp = Ext.getCmp('viewport');
    var win_width = vp.getSize().width -15;
    var win_height = vp.getSize().height -30;
                
    if (win_width  > size.width) {
        var win_width = size.width;
    }
    if ( win_height > size.height) {
        var win_height = size.height;
    }

    var scalewidth = 1;
    var scaleheight = 1;
    if (size.width > win_width) { scalewidth = win_width/size.width; }
    if (size.height > win_height) { scaleheight = win_height/size.height; }
    var scale = (scalewidth < scaleheight)? scalewidth : scaleheight;
    var image_width = Math.round(scale * size.width);
    var image_height = Math.round(scale * size.height);
      
    return  [image_width, image_height];
 
};

function set_tristate(node, tristate, items){
    
    node.attributes.items = null;
    var tri_span = Ext.get(node.getUI().span_id);
    var cb = node.getUI().checkbox;
    if(cb) {
        if (tristate){
            Ext.get(cb).addClass('tristate');                                    
            tri_span.addClass('tri_state_cb');
            node.attributes.items = items;
        }
        else{
            Ext.get(cb).removeClass('tristate');
            tri_span.removeClass('tri_state_cb');
        }
    }
}

var showDetails = function(view){
    var selNodes= view.getSelectedNodes();
    
    var detail_tabs_panel = Ext.getCmp('detail_tabs');
    var active_tab =  detail_tabs_panel.getActiveTab();
    var cbs_tristate = Ext.DomQuery.select('input[class=x-tree-node-cb tristate]');
    
    var i;
 
    for(i = 0; i < cbs_tristate.length;i ++){
        Ext.get(cbs_tristate[i]).dom.className = 'x-tree-node-cb';
        
    }
    
    var cbs = Ext.DomQuery.select('input[class=x-tree-node-cb]');
    
    for(i = 0; i < cbs.length;i ++){
//            cbs[i].disabled = false;
        cbs[i].checked = false;
    }
        
    var spans;
    spans = cbs = Ext.DomQuery.select('span[class=tristate tri_state_cb]');
    for(i = 0; i < spans.length;i ++) {
        Ext.get(spans[i]).dom.className = 'tristate';
    }
    
    if(selNodes && selNodes.length > 0){
        cbs = Ext.DomQuery.select('input[class=x-tree-node-cb]');
        for(i = 0; i < cbs.length;i ++){
            cbs[i].disabled = false;
        }
                
        var items = [];
        for(i = 0; i < selNodes.length; i++) {
            items.push(selNodes[i].id);
        }
        store_nodes_checked.load({
            params:{
                items: items
            }
        });
        
        
        Ext.getCmp('download').enable();
        
        var admin = ws_permissions_store.find('name', 'admin') > -1;        
        var add_item = ws_permissions_store.find('name', 'add_item') > -1;
        var edit_collection = ws_permissions_store.find('name', 'edit_collection') > -1;            
        var remove_item = ws_permissions_store.find('name', 'remove_item') > -1;
        var set_state = ws_permissions_store.find('name', 'set_state') > -1;        
        var run_scripts = ws_permissions_store.find('name', 'run_scripts') > -1;
        
        if(admin | run_scripts){
            Ext.getCmp('object_menu').menu.items.get('addto').enable();
            Ext.getCmp('runscript').enable();
        }
        
        if (admin | remove_item){
            Ext.getCmp('mvto').enable();
            Ext.getCmp('remove_from_ws').enable();
        
        }
        else{
            Ext.getCmp('mvto').disable();
            Ext.getCmp('remove_from_ws').disable();
        }
        
        
        if (admin | add_item){
            Ext.getCmp('sync_xmp').enable();


        }
        else{
            Ext.getCmp('sync_xmp').disable();

        }

        
        if (admin | set_state){
            if(ws_state_store.getCount()) {
                Ext.getCmp('set_state_to').show();
            }
        }
        else{
            Ext.getCmp('set_state_to').hide();
            
        }
        
//            Ext.getCmp('object_menu').menu.items.get('addto').enable();
//            Ext.getCmp('object_menu').menu.items.get('mvto').enable();
//            Ext.getCmp('object_menu').menu.items.get('removefrom').enable();
             var set_state_to = Ext.getCmp('object_menu').menu.items.get('set_state_to')            
            set_state_to.enable();
        
        var selNode = selNodes[0];            
        var data = view.store.getAt(view.store.findExact('pk', selNode.id)).data;
        if (selNodes.length == 1 && data.state){
            var state_id = 'state_' + data.state;
            var state= Ext.getCmp(state_id);
            if(state) {
                state.setChecked(true);
            }
        }
        else{
            for(var j = 0; j < set_state_to.menu.items.items.length; j ++) {
                set_state_to.menu.items.items[j].setChecked(false);
            }            
        }           
        
        _show_details(data, active_tab, view, selNode);
        
        //Ext.getCmp('sync_xmp').enable();
        
    } 
    else{
        cbs = Ext.DomQuery.select('input[class=x-tree-node-cb]');
        for(i = 0; i < cbs.length;i ++){
            cbs[i].disabled = true;
        }
        
        Ext.getCmp('download').disable();
        
        Ext.getCmp('object_menu').menu.items.get('addto').disable();
        Ext.getCmp('object_menu').menu.items.get('mvto').disable();
        Ext.getCmp('object_menu').menu.items.get('remove_from_ws').disable();
        Ext.getCmp('object_menu').menu.items.get('set_state_to').disable();
        Ext.getCmp('sync_xmp').disable();
        
        
        Ext.getCmp('runscript').disable();
//            preview = Ext.getCmp('preview_panel').body;
//            preview.update('');
        if(active_tab) {
            active_tab.hide();
        }
        current_item_selected = null;
        var m_store = Ext.getCmp('metadata_panel').getStore();
        var x_store = Ext.getCmp('xmp_panel').getStore();
        m_store.saveChangedRecords(Ext.getCmp('metadata_panel'));
        x_store.saveChangedRecords(Ext.getCmp('xmp_panel'));

        Ext.getCmp('sync_xmp').disable();


    }



};

var createStore = function(config) {

    return new Ext.data.JsonStore(Ext.apply({
        
    	totalProperty: 'totalCount',
        root: 'items',
        idProperty: 'pk',
//            autoLoad: true, 
		fields:[
		        'pk', 
                'name', 
                'url', 
                'url_preview', 
                'size', 

                'geotagged', 
                'status', 
                'thumb', 
                'type',
                'inbasket', 
                'preview_available',
                {name: 'shortName', mapping: 'name', convert: shortName}, 
                {name: 'inprogress', mapping: 'status', convert: function(status){
                	return status == 'in_progress'
                }},
                'state'
            ],
        listeners:{
    		load: function(){start_audio_player(this.panel_id);}
    	
    }
    }, config));

};

var createView = function(config) {
	
	var tpl = createTemplate(config.panel_id, config.media_type);
           
    return new Ext.DataView(Ext.apply({
        region:'center',        
        itemSelector: 'div.thumb-wrap',
        style:'overflow:auto; background-color:white;',
        multiSelect: true,
        plugins: new Ext.DataView.DragSelector({dragSafe:true}),
        height: 300,
        tpl: tpl,
        listeners: {
            selectionchange: {fn:showDetails, buffer:100},
//            dblclick: {fn:showFullscreen, buffer:100},
//            dblclick: function(){
//            	console.log('sdsfd');
//            	
//            },
            render: function(){
    	    	var drag_zone = new ImageDragZone(this, {containerScroll:true,
    	            ddGroup: 'organizerDD'});
    	    	
    	    	}
        }
    }, config));
};

var createPaginator = function(config) {

//    var paginator_id = config.id;

    var combo = new Ext.form.ComboBox({
      width: 70,
      store: new Ext.data.ArrayStore({
        fields: ['caption', 'value'],
        data  : [
          ['Auto', '-1'],
          ['25', '25'],
          ['50', '50'],
          ['70', '70'],
          ['100', '100'],
          ['All', '0']
        ]
      }),
      mode : 'local',
      value: 'Auto',

      listWidth     : 40,
      triggerAction : 'all',
      displayField  : 'caption',
      valueField    : 'value',
      editable      : false,
      forceSelection: true,
      listeners: {
        select: function(combo, record) {
//            var bbar = Ext.getCmp(paginator_id);
            var bbar = combo.ownerCt;
            var per_page = parseInt(record.get('value'), 10);
            if (per_page === 0) {
                per_page = 5000;
            }
            else if (per_page == -1) {
                calculatePageSize();
                per_page = pageSize;
            }
            bbar.pageSize = per_page;
            bbar.doLoad(bbar.cursor);
            }	
        }
    });			

    var paginator =  new Ext.PagingToolbar(Ext.apply({
        pageSize: pageSize,
        displayInfo: true,
        displayMsg: 'Displaying items {0} - {1} of {2}',
        emptyMsg: "No items to display",
        items: ['-', 'Items per page: ', combo]
        
    }, config));

    config.store.paginator = paginator;

    return paginator;
};


function start_audio_player(panel_id){	
//	var cls = 'myPlayer_' + panel_id;
	
	flowplayer('a.' +cls_audio, "/files/flowplayer/flowplayer-3.1.4.swf", { 
        clip: { autoPlay: true},
        plugins: { 
            audio: { 
                url: '/files/flowplayer/flowplayer.audio.swf' 
            }, 
            controls: { 
            	scrubber: true,
                fullscreen: false, 
                time:false,
//                width: 10,
                volumeSliderHeightRatio: 0.3,
                volume: false,
                mute:false
            } 
        },
        
        onBeforeLoad: function(){
        	
//        	Ext.get(this.getParent().id).setStyle('margin-top', 80);
        	flowplayer('*').each(function(){
              if(this.isPlaying())
        		this.pause();
        	});
        	
        	
        	
        },
        onBeforeUnload: function(){
            
            if (this.forceUnload){
//            	var play_img = Ext.get(this.getParent().id);
//            	if (play_img)
//            		play_img.setStyle('margin-top', 80);
            	this.forceUnload = false;
            	return true;
            	}
            else
            	return false;
        }
    });
	
	Ext.each(Ext.query('.' + cls_audio), function(){
		//removinf cls_audio, to avoid autoplay next call
		
		Ext.get(this.id).removeClass(cls_audio);
		
	});
	
};


function createMediaPanel(config, autoLoad) {
	var panel_id = Ext.id();
	
	var gmap_container = new Ext.Panel({
		hidden: true,
		region: 'north',
		layout: 'fit'
	});
	
	
	var store = createStore({	        
        url: '/load_items/',
        autoLoad: autoLoad,
        panel_id: panel_id,
        listeners:{
        	load: function(){
        		var inprogress = this.query('inprogress', 1);
        		var data = {
        			pending: inprogress.length,
        			failed: 0
        		};
        		console.log(data);
        		update_task_status(data);
        		
        	}
        }
        
	});
	
	store.on('beforeload', function(store, options){
				var media_type = Ext.getCmp(this.panel_id).getMediaTypes();						
				options.params.media_type = media_type;				
			}
			
		)
	var view = createView({
	    store: store,	   
	    panel_id: panel_id,
	    media_type: config.media_type
	});
	
	
	var paginator = createPaginator({       
        store: store
    });
//	var search = new Ext.app.SearchField(); 
	var search = new Ext.form.TextField({
//		value: config.search_value,
		width:250,
		setValue: function(value){        	
    	Ext.form.TextField.superclass.setValue.call(this, value);
    	
    	if (value == '')
    		setTabTitle('All Items', panel_id);
    	else
    		setTabTitle(value, panel_id);    	
    }
		
	
	});
	search.on('specialkey', function(f, e){
        if(e.getKey() == e.ENTER){
        	
        	setTabTitle(this.getValue(), panel_id);
        	do_search(this.getValue());
        }
    });
	
	
	var trigger = new Ext.BoxComponent({
	    autoEl: {
			tag:'a',
			href: 'javascript:void(0)',
			children: [{
					tag: 'img',
			        src: "/files/images/s.gif",
			        cls: "trigger"
			}]
		},
		
	    listeners:{
	    	afterrender:function(){
	    		this.getEl().on('click', function(){
	    			var v = Ext.getCmp('media_tabs').getActiveTab().getSearch().getValue();
	    			setTabTitle(v, panel_id);
	                do_search(v);
	    			
	    		});
	    	
	    	}
	    }
	});
	
	function capitalize(str){
		try{
			return (str[0].toUpperCase() + str.substring(1));
		}
		catch(e){
			return str;
			
		}
		
		
	};
	
	function create_filter(name){
		
		var checked = false;
       if  (config.media_type)
           checked= config.media_type.indexOf(name) >= 0;
		
		return {
			xtype: 'checkbox',
			boxLabel: capitalize(name),
			listeners: {
				check: function(cb, checked){
					
			
					var current_tab = Ext.getCmp('media_tabs').getActiveTab();
					if (current_tab.getMediaTypes().length == 0){
						this.suspendEvents();
						this.setValue(true);
						this.resumeEvents();
						return;						
					}
					if (current_tab.getComponent(0).getStore().lastOptions)
						current_tab.getComponent(0).getStore().reload();
					
					current_tab.getComponent(0).tpl = createTemplate(current_tab.id, current_tab.getMediaTypes());
					
					
					
				}		
			},
			name:name,
			cls: panel_id +'_filter',
			width: 60,	
			checked: checked
		};
		
		
	};
	
	var filters = [
	    create_filter('image'),
	    create_filter('video'),
	    create_filter('audio'),
	    create_filter('doc')
	    
	];
    
    function create_order_by_button(text, query){
      
        return {         
                
                text: text,
                query: query, 
                handler:function(){
        			var order_by_button = Ext.getCmp('order_by_button_' + panel_id); 
        			order_by_button.setText(this.text);
        			order_by_button.query = this.query;
        			order_by_button.sort();
                }
        };
        
    };
    
    
    
    var order_by_menu = [
        create_order_by_button('Creation Date', 'creation_time'),
        create_order_by_button('Title', 'dc_title')
//        create_order_by_button('File Size', 'size'),
//        create_order_by_button('Duration', 'notredam_duration')
    ];
	

    var order_by = new Ext.SplitButton({
        id: 'order_by_button_' + panel_id,
        text: order_by_menu[0].text,
        iconCls: order_by_menu[0].iconCls,
        query: order_by_menu[0].query,
        menu: order_by_menu,
        order_mode: 'decrescent',
        iconCls:'sort_desc',
        sort: function(){
            var store = Ext.getCmp('media_tabs').getActiveTab().getComponent(0).getStore();
            store.baseParams.order_by = this.query;
            store.baseParams.order_mode = this.order_mode;
            console.log('store.baseParams.order_mode ' + store.baseParams.order_mode);
            store.load();
                        
            
        },
        handler: function(){
           
             if(this.iconCls == 'sort_asc'){
                    this.setIconClass('sort_desc');
                    this.order_mode = 'decrescent';
                }
            else{
                this.setIconClass('sort_asc');
                this.order_mode = 'crescent';
            }
            this.sort();
        }
        
    });
    
	var show_all = new Ext.Button({
	   text: 'Show All',
		//			   icon: '/files/images/broom.png',
		   handler: function(){
   			Ext.getCmp('media_tabs').getActiveTab().getSearch().setValue('');
   			var catalogue = Ext.getCmp('west-panel').items.items;
   			var selection_model;
   			
   			for (var i = 0; i < catalogue.length; i++){
   				
   				if (catalogue[i].getSelectionModel)
   					selection_model = catalogue[i].getSelectionModel();
   				else
   					selection_model = catalogue[i].items.items[0];
   				
   					var selected = selection_model.getSelectedNodes() 
   	   			if (selected.length > 0){
   	   				selection_model.clearSelections();
   	   				return;
   	   			}
   					
   			}
   			
   			set_query_on_store({query: ''});		
   			},
   			tooltip:'Show All Objects'
		   			
				   	   			
  	});
	
	
	var p = new Ext.Panel(Ext.apply({
		id: panel_id,
		ctCls: 'empty',		
		media_type_query:'input.' + panel_id + '_filter',  
	    margins: '5 5 5 0',
	    layout:'border',
	    items:[view, gmap_container],
	    bbar: paginator,
//	    closable: config.closable,
//	    search: search,
	     
	    getMediaTypes: function(){
			var media_type = [];			
			var query = Ext.query(this.media_type_query + ':checked');
//		if (query.length == 0) //impossibble
//			media_type = ['image', 'video', 'audio', 'doc'];
//		else
			Ext.each(query,function(){
				media_type.push(this.name);					
			});					
		return media_type;
		},
		setMediaTypes:function(media_types){
			var query = this.media_type_query;
			Ext.each(media_types, function(){
				
				var final_query = query + '[name=' + this + ']';				
				var media_type = Ext.query(final_query)[0];
				
				if (media_type)
					media_type.checked = true;
				
				
			});
			
			
		},
		getFilter: function(name){
			var map = {image:0, video: 1,audio:2, doc: 3};
			return filters[map[name]];			
		
		},
	    getSearch: function(){
	    	return search;
	    	
	    },
	    
	    listeners: {
	    	close: function(){
	    		
	    		var media_tabs = Ext.getCmp('media_tabs');
	    		console.log('media_tabs.getActiveTab().title ' + media_tabs.getActiveTab().title);
	    		console.log('closeee ' + media_tabs.items.items.length);
	    		
	    		if (media_tabs.items.items.length == 2){
	    			
	    			
	    			var tab_closed = this;
	    			
	    			Ext.each(media_tabs.items.items, function(){
		    			if (this != tab_closed){
		    				Ext.get(media_tabs.getTabEl(this).id).removeClass(CLOSABLE_TAB_CLASS);
		    				return false;
		    			}
		    		});
	    			
	    			
	    			
	    			
	    		}
	    	
	    	},
	    	afterrender: function(){
	    		var media_tabs = Ext.getCmp('media_tabs');
	    		if (media_tabs .items.items.length == 1){	    			
	    			Ext.get(media_tabs.getTabEl(this).id).removeClass(CLOSABLE_TAB_CLASS);
	    		}
	    		else if (media_tabs.items.items.length == 2){
	    			Ext.get(media_tabs.getTabEl(media_tabs.items.items[0]).id).addClass(CLOSABLE_TAB_CLASS);
	    		}
	    			
	    	}
	    	
	    },
	    
	   
	    tbar: new Ext.Toolbar({	
	    	listeners:{
	    		render: function(){
//	    			this.doLayout();	    	
	    		}
	    	
	    	},
	    	items:[
		      'Quick Search: ', 
		      ' ',		     
		      search, 
		      trigger,
//		      ' ',		      
		      show_all,
            
		      '-',
		      {xtype: 'tbspacer', width: 5},              
              'Order By: ',
              order_by,
              '-',
              {xtype: 'tbspacer', width: 5},
              filters,              
		      '->',               
		//{
		//    icon: '/files/images/icons/fam/application_view_list.png', // icons can also be specified inline
		//    cls: 'x-btn-icon',
		//    tooltip: 'Change to List view'
		//}, 
			{
			   icon: '/files/images/icons/fam/grid.png', // icons can also be specified inline
			   cls: 'x-btn-icon',
			   tooltip: 'Change to Grid view',
			   handler: function() {
			       var tab = Ext.getCmp('media_tabs').getActiveTab();			       
			       close_map();
			       
			   }
			}, {
			   icon: '/files/images/map.png', // icons can also be specified inline
			   cls: 'x-btn-icon',
			   tooltip: 'Change to Map view',
			   handler: function() {
			       var tab = Ext.getCmp('media_tabs').getActiveTab();			       
			       open_map();
			       
			   }
			}]
	    })
	    
	}, config));
	
	return p;

};

Ext.onReady(function(){
    
    // Album toolbar

    Ext.form.Field.prototype.msgTarget = 'side';
    Ext.form.Field.prototype.invalidClass = 'invalid_field';

    Ext.Ajax.request({
        url: '/metadata_structures/',
        success: function(data){
            data = Ext.decode(data.responseText);
            metadata_structures = {};
            for (var x in data) {
                metadata_structures[x] = data[x];
            }
        }
    });


    previewTemplate = new Ext.XTemplate(
	'<div class="details">',
	'<div style="text-align:center">',
    '<img  src="{url_preview}" width="200">',    
    '</div>',    
    '</div>'
     );

    previewTemplate.compile();

    previewMovieTemplate = new Ext.XTemplate(
	'<div class="details">',
		'<tpl for=".">',
			'<a href="{url_preview}" style="display:block;width:300px;height:300px;" id="player"> </a>', 
//			'<object width="300" height="200" data="/files/flowplayer/flowplayer-3.1.4.swf" type="application/x-shockwave-flash">',
//			'<param name="movie" value="/files/flowplayer/flowplayer-3.1.4.swf" />', 
//			'<param name="allowfullscreen" value="false" />',
//			'<param name="flashvars" value=\'config={"clip":{"{"url": url_preview}", "scaling":"orig"}, onStart: function(clip) { var wrap = jQuery(this.getParent()); wrap.css({width: clip.width, height: clip.height}); } }\' />',
//			'</object>',
		'</tpl>',
	'</div>'
     );

    previewMovieTemplate.compile();

    previewAudioTemplate = new Ext.XTemplate(
	'<div class="details">',
		'<tpl for=".">',
			'<a href="{url_preview}.mp3" style="display:block;width:300px;height:30px;" id="player"> </a>', 
//			'<object width="300" height="200" data="/files/flowplayer/flowplayer-3.1.4.swf" type="application/x-shockwave-flash">',
//			'<param name="movie" value="/files/flowplayer/flowplayer-3.1.4.swf" />', 
//			'<param name="allowfullscreen" value="false" />',
//			'<param name="flashvars" value=\'config={"clip":{"{"url": url_preview}", "scaling":"orig"}, onStart: function(clip) { var wrap = jQuery(this.getParent()); wrap.css({width: clip.width, height: clip.height}); } }\' />',
//			'</object>',
		'</tpl>',
	'</div>'
     );

    previewAudioTemplate.compile();
    


    var changeLanguage = function(menu) {
        var tbar = Ext.getCmp('metadata_language');
        tbar.setText(menu.text);
        tbar.getEl().dom.getElementsByTagName('button')[0].style.backgroundImage= 'url('+menu.icon+')';
        var metadata_grid = Ext.getCmp('metadata_panel');
        metadata_grid.language = menu.text;
        metadata_grid.render();
        var xmp_grid = Ext.getCmp('xmp_panel');
        xmp_grid.language = menu.text;
        xmp_grid.render();
    };

    var changeVariant = function(menu) {
        var tbar = Ext.getCmp('metadata_variant');
        tbar.setText('Rendition: ' + menu.text);

        var metadata_grid = Ext.getCmp('metadata_panel');
        metadata_grid.variant = menu.text;
        var params = metadata_grid.getStore().lastOptions;
        if (params) {
            metadata_grid.getStore().load(params);
        }
        var xmp_grid = Ext.getCmp('xmp_panel');
        xmp_grid.variant = menu.text;
        var params = xmp_grid.getStore().lastOptions;
        if (params) {
            xmp_grid.getStore().load(params);
        }
    };
 
    var language_menu = new Ext.menu.Menu({
        id: 'languageMenu'
    });
    
    var variant_menu = new Ext.menu.Menu({
        id: 'variantMenu',
        items: [
            {
                text: 'original',
                handler: changeVariant
            }
        ]
    });    

    var variants_menu_store = new Ext.data.JsonStore({
            url: '/get_variants_menu_list/',
            root: 'variants',
            autoLoad: true,
            fields:[
                'variant_name'
            ],
            params: {ws: ws.id},
            listeners: {load: function(){
                variant_menu.removeAll();
                variant_menu.add({
                        text: 'original',
                        handler: changeVariant
                    });
                variant_menu.store = this;
                this.each(function(r){
                    variant_menu.add({
                        text: r.data.variant_name,
                        handler: changeVariant
                    });
                 });
            }}
        });

    var languages_store = new Ext.data.JsonStore({
            url: '/get_lang_pref/',
            root: 'languages',
            autoLoad: true,
            fields:[
                'language', 'code', 'country', 'default_value'
            ],
            listeners: {load: function(){
                language_menu.removeAll();
                language_menu.store = this;
                var language_handler = function(r) {
                            var tbar = Ext.getCmp('metadata_language');
                            var menu_icon = '/files/images/flag_icons/'+r.data.code.substr(3,2).toLowerCase()+'.png';
                            tbar.setText(r.data.language);
                            tbar.getEl().dom.getElementsByTagName('button')[0].style.backgroundImage= 'url('+menu_icon+')';

                            var metadata_grid = Ext.getCmp('metadata_panel');
                            metadata_grid.language = r.data.code;

                            var xmp_grid = Ext.getCmp('xmp_panel');
                            xmp_grid.language = r.data.code;

                            var detail_tabs_panel = Ext.getCmp('detail_tabs');
                            var active_tab =  detail_tabs_panel.getActiveTab().getId();

                            if (active_tab == 'metadata_panel' || active_tab == 'xmp_panel') { 
                                var current_grid = Ext.getCmp(active_tab);
                                var metadata_lang = current_grid.getStore().query('type', 'lang');
                                for (var i=0; i < metadata_lang.items.length; i++) {
                                    var record = metadata_lang.items[i];
                                    current_grid.getStore().fireEvent('update', current_grid.getStore(), record, Ext.data.Record.EDIT);
                                    if (record.data.choices[current_grid.language]) {
                                        record.set('value', record.data.choices[current_grid.language]);
                                    }
                                }
                            }
                        };
                this.each(function(r){
                    language_menu.add({
                        text: r.data.language + " ("+r.data.country+")",
                        iconCls: 'language',
                        icon: '/files/images/flag_icons/'+r.data.code.substr(3,2).toLowerCase()+'.png',
                        handler: function(menu) {
                            language_handler(r);
                        }
                    });
                    if (r.data.default_value) {
                        language_handler(r);
                    }
                 });
            }}
        });

    var metadata_tbar = new Ext.Toolbar({items: [{
            id: 'metadata_language',
            text:'English',
            menu: language_menu,
            iconCls: 'language',
            icon: '/files/images/flag_icons/us.png'
            }, {
            id: 'metadata_variant',
            text:'Rendition: original',
            menu: variant_menu
            }
        ]}
    );

    var task = {
        run: function(){
        	
        	
        	var win_monitor = Ext.WindowMgr.get('script_monitor'); 
        	if (win_monitor){
        		win_monitor.update_progress();	
        	
        	}
        	
//        	
            var tab = Ext.getCmp('media_tabs').getActiveTab();
            var items = [];
            var reload_details = false;
            
            if (tab) {
                var view = tab.getComponent(0);
                if (view) {
                    var store = view.getStore();
                    items_in_progress = store.query('status','in_progress').items;
                    Ext.each(items_in_progress, function(i){
                    	items.push(i.data.pk);
                    });
                  
//                    store_variant = Ext.getCmp('variant_summary').getStore();
//                  
//                    for (var i = 0; i < store.getCount(); i++) {
//                        var current_item = store.getAt(i);
//                        var item_data = current_item.data;
//                        
////                        if(item_data.inprogress == 0 && view.getSelectedIndexes().length == 1 && view.getSelectedIndexes()[0] == i)
////                        	items.push(item_data.pk); //check if selected item changed,since some script has been run 
//                        
//                        if (item_data.inprogress) {
//                            items.push(item_data.pk);                          
//                            
//                            if(i == 0 &&  view.getSelectionCount()  ==  1 && Ext.getCmp('detail_tabs').isVisible() && Ext.getCmp('detail_tabs').getActiveTab().id == 'preview_panel' && store_variant.lastOptions && store_variant.lastOptions.params.items == item_data.pk) {
//                                reload_details = true;
//                            }
//                        }
//                    }
//                    
//                    if(reload_details){
//                        current_item_selected = null;
//                        showDetails(view);
//                        
//                    }
                }
            }
            
            var update_script_monitor;
            var script_monitor_win = Ext.WindowMgr.get('script_monitor');
			if (script_monitor_win)
				update_script_monitor = script_monitor_win.update_progress();
				
            
            if (items.length > 0 || update_script_monitor){
            	var params = {};
            	
            	if (items.length > 0)
            		params.items = items;
            		
            	if (update_script_monitor)
            		params.update_script_monitor = true;
				
            	Ext.Ajax.request({
                url: '/get_status/',
                params: params,
                
                success: function(data){    
                	console.log(data);
//                    set_status_bar_busy();
                    data = Ext.decode(data.responseText);
                    if (data.scripts){
                    	var monitor = Ext.getCmp('script_monitor_list')
                    	if (monitor){
                    		store = monitor.getStore();
                    		store.loadData(data);
                    	}
                    	
                    }
                    var update_items = data.items;
                   
                    var tab = Ext.getCmp('media_tabs').getActiveTab();
                    if (tab) {
                        var view = tab.getComponent(0);
                        if (view) {
                            var store = view.getStore();
                            Ext.each(update_items, function(){
                            	info = this;
                            	
                            	var i = info.pk;
                                if (store.findExact('pk', i) != -1) {
                                    var item_data = store.getAt(store.findExact('pk', i));
                                    var previous_thumb_ready = item_data.data.thumb;
                                    var thumb_ready = info['thumb'];
                                    for (var key in info) {
                                    	if (key == 'url') 
                                    		info[key] = info[key] + '?t=' + Math.floor(Math.random()*100001);
                                    	item_data.set(key, info[key]);
//                                        if (key == 'url') {
//                                        	info[key] = info[key] + '?t=' + (new Date()).getTime();
//                                        	
//                                            if (previous_thumb_ready == 0 && thumb_ready == 1) {
//                                                item_data.set(key, info[key]);
//                                            }
//                                        }
//                                        else {
//                                            item_data.set(key, info[key]);
//                                            
//                                        }
                                    }
                                    
                                    var detail_tabs_panel = Ext.getCmp('detail_tabs');
                                    var active_tab =  detail_tabs_panel.getActiveTab();
                                    if(active_tab == null) {
                                        return;
                                    }
                                    if (active_tab.id == 'variant_panel'){
                                        var sel_records = view.getSelectedRecords();                               
                                        for(var j=0; j<sel_records.length; j ++){
                                            if(sel_records[j].data.pk == item_data.data.pk){                                               
                                                store_variant.reload();
                                                break;
                                            }
                                        }
                                        
                                    }                                    
                                } 
                            
                            
                            
                            })
                            
                        }
                    }

					update_task_status(data);

                }
            });
        }
        },
        interval: 3000 //3 second
    };
    var runner = new Ext.util.TaskRunner();
    runner.start(task);
 

    var media_tabs = new Ext.TabPanel({
        region:'center',
        deferredRender:false,
        activeTab:0,
        id: 'media_tabs',
        enableTabScroll: true,
        plugins: [ Ext.ux.AddTabButton ],
        createTab: function() { // Optional function which the plugin uses to create new tabs    		
    		
            return  createMediaPanel({
                title:'New Tab',
//                media_type: ws_store.query('pk', ws.id).items[0].data.media_type,
                media_type: Ext.getCmp('media_tabs').getActiveTab().getMediaTypes(),
                closable: true
            });
        },
        addTabText: '+',
        
//        items:[tab_images, tab_videos, tab_audio, tab_docs, tab_all],
//        items:[initial_tab],
        items:[],
        listeners:{        	
        	beforetabchange: function(){
		    	flowplayer('*').each(function(){		    		
		    		this.forceUnload =  true;
		    		this.unload();
		    		
		    	});    	
    		},
//    		tabchange:function(tab_panel,tab){
//    			var store = tab.getComponent(0).getStore();    			
//    			if (!store.lastOptions && (tab.query == '' || tab.query)) //if tab not loaded yet, for example when you switch ws
//    				set_query_on_store({query:tab.query, workspace_id: ws.id});
//    				
//    			
//    			
//    		},
    		
 		
            tabchange: function(tab_panel, tab){
				if(!tab)
					return;
    			var store = tab.getComponent(0).getStore();    			
    			if (!store.lastOptions && (tab.query == '' || tab.query)) //if tab not loaded yet, for example when you switch ws
    				set_query_on_store({query:tab.query, workspace_id: ws.id});
    				
    	
                var detail_tabs_panel = Ext.getCmp('detail_tabs');
                var active_tab =  detail_tabs_panel.getActiveTab();
                if(active_tab) {
                    active_tab.hide();
                }
                
                if (!Ext.get(tab_panel.id).isMasked() && !firstlayout) {     
                    var media_tab = tab_panel.getActiveTab();
                    var view = media_tab.getComponent(0);
                    view.clearSelections();
                    showDetails(view);
//                    set_query_on_store(view.getStore().baseParams);
                }
            }
        }
    });
   
    
var search_box = {
               
        title: 'Search Box',
        id: 'search_box_panel',
        width: 200,
        height: 100,
        region:'south',
        split: true,
        autoScroll: true,
        hideCollapseTool: true,
        collapsible: true,
        clean_up: function(){
            Ext.getCmp('search_box').getStore().removeAll();
            Ext.getCmp('search_box_current_smart_folder').setText('');
            
        },
        tbar:{
            items:[
            {
                id: 'sb_and',
                text: 'AND',
                pressed: true,
                enableToggle: true,
                toggleHandler: function(button, state){
                    var or = Ext.getCmp('sb_or'); 
                    if (!state) {
                        or.toggle(true);
                    }
//                    else
//                        search_box_do_search('and')
                    
                },
                toggleGroup: 'search_box'
    
                },
                {
                    id: 'sb_or',
                    text: 'OR',
                    enableToggle: true,
                    toggleGroup: 'search_box',
                    toggleHandler: function(button, state){
                        var and = Ext.getCmp('sb_and');
                        if (!state) {
                            and.toggle(true);
                        }
    //                    else
    //                        search_box_do_search('or')
                        }
    
                },
                {
                    xtype: 'tbseparator' 
                },
                {
                    iconCls:'refresh_button',
                    icon:'/files/images/Play-Pressed-16x16.png',                        
                    handler: function(){
                        var and = Ext.getCmp('sb_and');
                        var or = Ext.getCmp('sb_or');
                        if (and.pressed) {
                            search_box_do_search('and');
                        }
                        else if(or.pressed) {
                            search_box_do_search('or');
                        }
                    }
                },
                {xtype: 'tbfill'},
                {
                    id: 'save_as_smart_folder',
                    text: 'Save',
                    disabled: true,
                    tooltip: 'Save query as a Smart Folder',
                    handler: function(){save_smart_folder();}
                }            
            ]
        },
        
        bbar:{
            id:'search_box_bbar',
            hidden: true,
            items :[
                new Ext.Toolbar.TextItem({
                    id: 'search_box_current_smart_folder',
                    text: ''
                    
                })
            ],
            listeners:{
                show: function(comp){
                    comp.doLayout();
                },
                
                hide: function(comp){
                    comp.doLayout();
                }
                
            }
        },
        items: new Ext.ListView({
            id: 'search_box',
            autoScroll: true,
//            height: 50,
            hideHeaders: true,
            trackOver: true,
            store: new Ext.data.JsonStore({
                root: 'queries',                     
                idProperty: 'pk',
                fields: [ 'pk','negated','label', 'path'],
                url :'/get_query_smart_folder/',
                listeners: {
                    add: function(store){
                        Ext.getCmp('save_as_smart_folder').setDisabled(false);
                    },
                    remove: function (store){
                        if(store.getCount() == 0 && Ext.getCmp('smart_folders').getSelectionCount() == 0) {
                            Ext.getCmp('save_as_smart_folder').setDisabled(true);
                        }
                    },
                    load: function(store, records){
                        Ext.getCmp('save_as_smart_folder').setDisabled(false);
                        var record;
                        for (var i=0; i  < records.length; i++){
                            record = records[i];    
                            if(record.data.negated) {
                                Ext.get('sb_' + record.data.pk).dom.src = '/files/images/icons/fam/delete.gif';
                            }
                        }
                        var sm_view = Ext.getCmp('smart_folders');
                        var sm = sm_view.getSelectedRecords();

                        Ext.getCmp('sb_' + sm[0].data.condition).toggle(true);
                            
                    }
                }
                
            }),
             columns: [
                {name: 'negated', dataIndex: 'negated',
                width:0.10,
                tpl: new Ext.Template('<img id="sb_{pk}" src="/files/images/icons/fam/delete_grey.gif" onclick=" if(this.src.indexOf(\'grey.gif\')>=0) {toggle_negated_search_box(\'{pk}\', true);  } else  {toggle_negated_search_box(\'{pk}\', false); }"/>')
                
                },                        
                {
                    dataIndex: 'label',
                    tpl: '<tpl for="."><div ext:qtip="{path}" >{label}</div></tpl>'

                },
                {name: 'delete',
                width:0.10,
                tpl: new Ext.Template('<img src="/files/images/icons/fam/cross_blue.gif" onclick="store = Ext.getCmp(\'search_box\').getStore(); store.removeAt(store.find(\'pk\', {pk}))"/>')
                
                }      
                
                
                ]

            
        })
        };
        
        
    var basketMenu = new Ext.menu.Menu({id:'basketMenu',
    items: [
    {
        text: 'Add',
        handler: function (data){ 
                    reload_selected_nodes();
                 }
    },
    {
        text:'Remove', 
        handler: function (data){ 
                    remove_from_basket();
                 }        
    },
    {
        text:'Clear', 
          handler: function (data){ 
                    clear_basket();
                 }              
    }
   
    
    ]
    }); 
        
    var viewport = new Ext.Viewport({
           id:'viewport',
            layout:'border',
            listeners: {afterlayout: function() {
                            if (firstlayout) {
                                calculatePageSize(); 
                                firstlayout = false;
//                                store_image.load({params:{start:0, limit:pageSize}});
                            }
                        }
            },
            items:[
            new Ext.ux.StatusBar({
                region: 'south',
                defaultText: 'Default status',
                id: 'dam_statusbar',
                height: 25,
                statusAlign: 'right', // the magic config
                bodyStyle: 'padding:5px;'
//                items: [new Ext.Toolbar.TextItem('Failed jobs : 0'), '-', new Ext.Toolbar.TextItem('Pending adaptation jobs : 0'), '-', new Ext.Toolbar.TextItem('Pending Feature extractions jobs: 0'), '-']
            }),
            
//                new Ext.BoxComponent({ // raw
//                    region:'north',
//                    el: 'north',
//                    height:32
//                }),
                header,
                new Ext.Panel({
                    layout:'border',
                    region:'west',
//                    layout: 'fit',
                    width: 200,
                    minSize: 175,
                    maxSize: 400,
                    collapsible: true,
                    split:true,
                    border: false,
//                    margins:'0 0 0 5',
                    items:[{
                        id:'west-panel',
                        region:'center',
                        title:'Catalogue',
                        width: 200,
                        layoutConfig:{
                            animate:true
                            
                        },
                        layout: 'accordion',
    //                    items: [workspaces_panel, tree_keywords, tree_collections, ]
                        items: [tree_keywords, tree_collections, inbox, smart_folders],
                        bbar: { 
                            id :"basket_container",
                            listeners:{
                                render: function (basket){ 
                                    var ddBasket = new Ext.dd.DropTarget(basket.getEl(),{
                                        ddGroup:'organizerDD', 
                                        //menu: basketMenu,
                                        notifyDrop : function(ddSource, e, data) {
                                            reload_selected_nodes();
                                             return true;										
                                        }
                                    } );
                                    basket.getEl().on("contextmenu",function(e){ 
                                        e.preventDefault();
                                        Ext.getCmp("basketMenu").show(basket.getEl());
                                    });
                                }
        
                            },
                              
                            items: [ 
                                {
                                    text:"Basket",
                                    id : "panel_basket",
                                    //menu: basketMenu,
                                    enableToggle: true,
                                    
                                    listeners:{
                                         
                                        toggle:function(button, pressed){
                                            
                                                /*
                                                if (pressed){
                                                    console.log('toooooooooogggggggggle')
                                                    button.addClass('basket_pressed');
                                                }
                                                else
                                                button.removeClass('basket_pressed');
                                                */
                                                //console.log('toooooooooogggggggggle')
                                            //Ext.getCmp("basket_container").addClass('basket_pressed');	
                                            set_query_on_store({only_basket:pressed});
                                        }
                                    }
                                }, {xtype: 'tbfill'},
                                new Ext.Toolbar.TextItem ({id:"basket_items", text:basket_size()  })
                            ]
                        }
                    },
                        search_box
                    ]
                }),
                new Ext.TabPanel({
//                            border:false,
                            activeTab:0,
                            id: 'detail_tabs',
                            region:'east',
                            collapsible: true,
                            collapsed: true,
                            split:true,
                            width: 350,
                            minSize: 200,
                            maxSize: 400,
//                            layout:'fit',
                            margins:'0 5 0 0',
//                            collapseFirst: false,
//                            hideCollapseTool: true, //[<<] icon
//                            titleCollapse: true,
                            tbar: metadata_tbar,
                            listeners: {
                                tabchange: function(tab_panel, tab){
                                    if (tab.getId() == 'preview_panel') {
                                        metadata_tbar.hide();                                    
                                    }
                                    else {
                                        metadata_tbar.show();                                    
                                    }
                                    var media_tab = Ext.getCmp('media_tabs').getActiveTab();
                                    if (media_tab) {
                                        var view = media_tab.getComponent(0);
                                        showDetails(view);
                                    }
                                },
                                expand: function(panel) {
                                    panel.header.on('dblclick', panel.toggleCollapse, panel);
                                    
                                }
                            },
                            
                            items:[{
                                title: 'Summary',
                                autoScroll:true,
                                id: 'preview_panel',
                                hideBorders: true,
                                items:[
                                    {
                                        id: 'summary_panel',
                                        html:'',
                                        hideBorders: true,
                                        
                                        region: 'north'

                                    },
                                    {
                                        id: 'basic_panel',
                                        html:'',
                                        hideBorders: true,
                                        region: 'center',
                                        autoScroll:false
                                    },
                                    new Ext.ListView({
                                        title:'Variants',
                                        id:'variant_summary',
                                        autoScroll: false,
                                        selectedClass: 'x-list-selected list-variant',
										singleSelect: true,
                                        store: new Ext.data.JsonStore({
                                                root: 'variants',              
                                                fields: ['pk','variant_name', 'data_basic','data_full', 'resource_url', 'abs_resource_url', 'imported', 'item_id', 'auto_generated', 'media_type', 'extension', 'work_in_progress', 'width', 'height'] ,
                                            url: '/get_variants/'

                                            
                                        }),
                                     
                                        columns:[
                                            
                                            {id:'variant_name',
                                            header: 'variant_name',
                                            dataIndex: 'variant_name',
                                            cls: 'list-variant',
                                            
                                                tpl: new Ext.XTemplate(  
                                                	'<div class="list-variant">',
                                                    '<b style="color:#3764A0;">{variant_name:capitalize()}</b>', 
                                                    '<tpl if="work_in_progress">',                                                
                                                        '<img src="/files/images/warning.gif" style="width: 13px; padding-left: 5px; height: 13px;"/>',                                                                                                    
                                                    '</tpl>',
                                               
                                                
                                                '<span style="position:absolute; right:10px;">' ,
                                                '<tpl if="resource_url">',                                                
                                                    '<tpl if="work_in_progress == 0">',
                                                        '<img ext:qtip="View" src="/files/images/search_blue.png" class="variant_button"  onclick="open_variant(\'{variant_name}\',\'{resource_url}\', \'{media_type}\', \'{width}\', \'{height}\')"/>',
                                                    '</tpl>',
                                                '   <img ext:qtip="Download" src="/files/images/icons/save.gif" onclick=" window.open(\'{resource_url}?download=true\')" class="variant_button"/>',
                                                '</tpl>',
                                                '<img ext:qtip="Replace" id="import_{pk}" src="/files/images/box_upload.png" onclick="variant_id=this.id.split(\'_\')[1];import_variant(variant_id)" class="variant_button"/>',
                                                
                                                //'<tpl if="auto_generated == 1"><img id="generate_{pk}" ext:qtip="Generate" src="/files/images/icons/fam/cog.png" class="variant_button" onclick="variant_id=this.id.split(\'_\')[1];generate_variant(variant_id, \'{item_id}\')"/></tpl>',
                                                '</span>',
                                                
                                                '<tpl if="work_in_progress == 0" >',                                                
                                                    	
                                                                
                                                        '<div id="full_metadata_{pk}"  style="padding-left:20px;"  >',
                                                        	    
                                                            '<tpl for="data_basic">',
                                                                '<p><b>{caption}:</b>',
                                                                '<tpl if="value.properties === undefined">',
                                                                    '<span ext:qtip="{value}"> {value:ellipsis(20)}</span></p>',
                                                                '</tpl>',
                                                                '<tpl if="value.properties"><br/>',
                                                                    '<tpl for="value.properties">',
                                                                        '<b style="padding-left:20px;">{caption}:</b>',
                                                                        '<span style="padding-left:20px;" ext:qtip="{value}"> {value:ellipsis(20)}</span><br/>',      
                                                                    '</tpl></p>',
                                                                '</tpl>',
                                                            '</tpl>',
                                                        
                                                            '<tpl for="data_full">',
                                                                '<p><b>{caption}:</b>',
                                                                '<tpl if="value.properties === undefined">',
                                                                    '<span ext:qtip="{value}"> {value:ellipsis(20)}</span></p>',
                                                                '</tpl>',
                                                                '<tpl if="value.properties"><br/>',
                                                                    '<tpl for="value.properties">',
                                                                        '<b style="padding-left:20px;">{caption}:</b>',
                                                                        '<span style="padding-left:20px;" ext:qtip="{value}"> {value:ellipsis(20)}</span><br/>',      
                                                                    '</tpl></p>',
                                                                '</tpl>',
                                                            '</tpl>',
                                                        '<p class="permalink"><b>Link: </b><input value="{abs_resource_url}" readonly/></p>',
                                                        '</div>',
                                                        
                                                    '</tpl>',
                                                    '</div>'
                                                )}
                                            
                                            
                                            ],
                                        hideHeaders: true,
                                        autoShow: true,
                                        trackOver: true,                                        
                                        listeners:{
                                            mouseenter: function(view, index, node, e){
                                                var imgs =Ext.query('img',node);
//                                                console.log(imgs)
                                                for (i = 0; i< imgs.length; i++){
                                                    if (imgs[i].className == 'variant_button') {
                                                        Ext.get(imgs[i]).setStyle('visibility', 'visible');
                                                    }
                                                }
                                            },
                                        mouseleave: function(view, index, node, e){
                                                imgs =Ext.query('img',node);
//                                                console.log(imgs)
                                                for (i = 0; i< imgs.length; i++){
                                                    if (imgs[i].className== 'variant_button') {
                                                        Ext.get(imgs[i]).setStyle('visibility', 'hidden');
                                                    }
                                                }
                                            }
                                        }

//                                        height: 250,
                                    })
                                
                                ]
                            }, new Ext.grid.MetadataGrid({
                    title: 'Metadata',
                    id: 'metadata_panel',
                    view: new Ext.grid.GroupingView({
                        forceFit:true,
                        startCollapsed: true,
                        hideGroupedColumn:true,
                        showGroupName: false,
                        groupTextTpl: '{text}'
                    }),
 
                    buttons: [{
                        text: 'Save',
                        handler: function() {
                            var my_grid = this.findParentByType('metadatagrid');
                            my_grid.saveMetadata('/save_descriptors/');
                         }
                         },{
                             text: 'Cancel',
                             handler: function() {
                                var my_grid = this.findParentByType('metadatagrid');
                                my_grid.getStore().rejectChanges();
                             }
                         }]
                      }), new Ext.grid.MetadataGrid({
                    title: 'XMP',
                    id: 'xmp_panel',
                    advanced: true,
                    view: new Ext.grid.GroupingView({
                        forceFit:true,
                        startCollapsed: true,
                        hideGroupedColumn:true,
                        showGroupName: false,
                        groupTextTpl: '{text}'
                    }),
 
                    buttons: [{
                        text: 'Save',
                        handler: function() {
                            var my_grid = this.findParentByType('metadatagrid');
                            my_grid.saveMetadata('/save_metadata/');
                        }
                         },{
                             text: 'Cancel',
                             handler: function() {
                                var my_grid = this.findParentByType('metadatagrid');
                                my_grid.getStore().rejectChanges();
                             }
                         }]
                      })
//                                variant_panel
                            ]
                        }),
                media_tabs
             ]
        });

//    variant_info.setVisible(false)
        
    
//    var drag_zone_image = new ImageDragZone(view_image, {containerScroll:true,
//        ddGroup: 'organizerDD'});
//        
//    var drag_zone_movie = new ImageDragZone(view_movie, {containerScroll:true,
//        ddGroup: 'organizerDD'});
//        
//    var drag_zone_audio = new ImageDragZone(view_audio, {containerScroll:true,
//        ddGroup: 'organizerDD'});
//        
//    var drag_zone_doc = new ImageDragZone(view_doc, {containerScroll:true,
//        ddGroup: 'organizerDD'});
//
//    var drag_zone_all = new ImageDragZone(view_all, {containerScroll:true,
//        ddGroup: 'organizerDD'});

});

// this.panel_basket.on('render', this.notifyDrop, this);


/**
 * Create a DragZone instance for our JsonView
 */
ImageDragZone = function(view, config){
    this.view = view;
    ImageDragZone.superclass.constructor.call(this, view.getEl(), config);
};
Ext.extend(ImageDragZone, Ext.dd.DragZone, {
    // We don't want to register our image elements, so let's 
    // override the default registry lookup to fetch the image 
    // from the event instead
    getDragData : function(e){
        var target = e.getTarget('.thumb-wrap');
        if(target){
            var view = this.view;
            if(e.ctrlKey == false) {
                if(!view.isSelected(target)){
                    view.onClick(e);
                }
            } 
            var selNodes = view.getSelectedNodes();
            var dragData = {
                nodes: selNodes,
                type:'items'
            };
            if(selNodes.length == 1){
                dragData.single = true;
            }else{                
                dragData.multi = true;
            }
            
            var div = document.createElement('div'); // create the multi element drag "ghost"
            div.className = 'multi-proxy';

            i = selNodes.length;

            var count = document.createElement('div'); // selected image count
            count.innerHTML = i + ' items selected';
            div.appendChild(count);

            dragData.ddel = div;

            return dragData;
        }
        return false;
    },

    // this method is called by the TreeDropZone after a node drop
    // to get the new tree node (there are also other way, but this is easiest)
    getTreeNode : function(){
        var treeNodes = [];
        var nodeData = this.view.getRecords(this.dragData.nodes);
        for(var i = 0, len = nodeData.length; i < len; i++){
            var data = nodeData[i].data;
            treeNodes.push(new Ext.tree.TreeNode({
                text: data.name,
                icon: '../view/'+data.url,
                data: data,
                leaf:true,
                cls: 'image-node'
            }));
        }
        return treeNodes;
    },
    
    // the default action is to "highlight" after a bad drop
    // but since an image can't be highlighted, let's frame it 
    afterRepair:function(){
        for(var i = 0, len = this.dragData.nodes.length; i < len; i++){
            Ext.fly(this.dragData.nodes[i]).frame('#8db2e3', 1);
        }
        this.dragging = false;    
    },
    
    // override the default repairXY with one offset for the margins and padding
    getRepairXY : function(e){
        if(!this.dragData.multi){
            var xy = Ext.Element.fly(this.dragData.ddel).getXY();
            xy[0]+=3;xy[1]+=3;
            return xy;
        }
        return false;
    }
    
});
