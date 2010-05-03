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

var ws_grid_view, store_tabs, pref_store, pref_ws_store;
var pageSize = 25;
var firstlayout = true;
var metadata_structures = {};

var old_selected_nodes = [];
var CLOSABLE_TAB_CLASS = 'x-tab-strip-closable'; 
var cls_audio = 'loadPlayer';


if (window['loadFirebugConsole']) {
    window.loadFirebugConsole();
} else {
    if (!window['console']) {
        window.console = {};
        var f = function func(arg){};
        window.console.info = f;
        window.console.log = f;
        window.console.warn = f;
        window.console.error = f;
    }
}

Ext.BLANK_IMAGE_URL = '/files/images/s.gif';

function play_audio(player_id){
    var player = flowplayer(player_id);
    
    if(!player.isLoaded()) {
        player.load(function(){
            player.play();
        });
    }
    
};


function shortName(name, obj, len){
	if (!len)
		var len = 15;
	
    if(name.length > len){
        return name.substr(0, len - 3) + '...';
    }
    return name;
}

function calculatePageSize() {
    var view = Ext.getCmp('viewport');
    var view_height = view.getSize().height - 150;
    var view_width = view.getSize().width - 200;
//    console.log(view_height);
//    console.log(view_width);
    var per_row = Math.floor(view_width / 128); 
    var num_row = Math.floor(view_height / 135); 
    pageSize = per_row * num_row;

    
//    console.log(pageSize);
//    Ext.getCmp('paginator_images').pageSize = pageSize;
//    Ext.getCmp('paginator_videos').pageSize = pageSize;
//    Ext.getCmp('paginator_audio').pageSize = pageSize;
//    Ext.getCmp('paginator_docs').pageSize = pageSize;
//    Ext.getCmp('paginator_all').pageSize = pageSize;

}
        
function set_query_on_store(params, skip_load){
	
    var media_tab = Ext.getCmp('media_tabs').getActiveTab();    
    if (!media_tab)
    	return;
    
    var view = media_tab.getComponent(0);
    var store = view.getStore();
    store.baseParams = params;
    
    var per_page = store.paginator.pageSize;
    if (!skip_load){
        store.removeAll();
        store.load({
            params:{
        	
                start:0,
                limit:per_page
                },
            });
            
            }
    if (media_tab.getId().indexOf('map_') != -1) {
        media_tab.getComponent(1).onMapMove();
    }
}


var FieldSetCheckBox = function(config){  
    var id;
    var on_click_cb;
    if (config.id) {
        id = config.id;
    }
    else {
        id =  Ext.id();
    }
    this.cb_id = Ext.id();        
    this.cb_checked = config.cb_checked;

    on_click_cb = 'fs = Ext.getCmp("'+id+'");';

    on_click_cb += ' fs.cb_checked = this.checked; ';
    on_click_cb += 'for(i=0; i< fs.items.items.length; i++) if(!this.checked) fs.items.items[i].disable(); else fs.items.items[i].enable();';
    
    var onrender =  function(){
        var cb = Ext.get(this.cb_id).dom;
        if (this.cb_checked) {
            cb.checked = true;
        }
        else{
            cb.checked = false;
            for(var i=0; i< this.items.items.length; i++) {
                this.items.items[i].disable(); 
            }
        }
    };
    
    Ext.apply(this,{
        id: id,
        name: config.name,
        autoHeight: true,
        cb_status: true,
        checkboxToggle: {tag: 'input', 
            type:'checkbox', 
            name: config.name, 
            id:this.cb_id, 
            onclick: on_click_cb
        },        
        listeners:{
            beforecollapse: function(fs){
                return false;
            },
            render: onrender
        }
        
    });
    FieldSetCheckBox.superclass.constructor.apply(this, arguments);
        
};

Ext.extend(FieldSetCheckBox, Ext.form.FieldSet, {});
Ext.reg("fieldsetcheckbox", FieldSetCheckBox);


Ext.override(Ext.tree.AsyncTreeNode, {
		setIconCls: function(iconClassName) {
			var iel = this.getUI().getIconEl();
			if (iel) {
				var el = Ext.get(iel);
				if (el) {
					el.addClass(iconClassName);
				}
			}
		}
	});
    
    
var cp_ws_menu = new Ext.menu.Menu({
            id: 'cp_ws_menu',
            items:[]
        });
    
var mv_ws_menu = new Ext.menu.Menu({
        id: 'mv_ws_menu',
        items:[]
    }) ;

    
function get_selected_items(){
    var view = Ext.getCmp('media_tabs').getActiveTab().items.items[0];
    var selNodes= view.getSelectedNodes();
    if(selNodes && selNodes.length > 0){ 
        var selected_ids = [];
        for (var i=0; i < selNodes.length; i++) {
            console.log(selNodes[i].id);
            var data = view.store.getAt(view.store.findExact('pk', selNodes[i].id)).data;
            selected_ids.push(data.pk);
            console.log(data.pk);
        }
    
    }
    return selected_ids;
}

function populate_menu(){
    
        cp_ws_menu.removeAll();
        mv_ws_menu.removeAll();
    
        ws_store.each(function(r){
            if (ws.id != r.data.pk){
                cp_ws_menu.add(
                     new Ext.menu.Item({
                        text: r.data.name,
                        record: r,
                        handler:function(ci){
                            var selected_ids = get_selected_items();
                            Ext.Ajax.request({
                                url: '/add_items_to_ws/',
                                params:{
                                    ws_id: ci.record.data.pk,
                                    remove:false,
                                    item_id: selected_ids
                                    
                                    },
                                    success: function() {
                                        Ext.MessageBox.alert('Success', 'Item(s) copied successfully.');
                                    }
                                
                                });
                        }
                    })
                );
            
            mv_ws_menu.add(
                 new Ext.menu.Item({
                    text: r.data.name,
                    record: r,
                    handler:function(ci){
                        var selected_ids = get_selected_items();
                        Ext.Ajax.request({
                            url: '/add_items_to_ws/',
                            params:{
                                ws_id: ci.record.data.pk,
                                remove:true,
                                item_id: selected_ids
                            },
                            success: function(){
                                var view = Ext.getCmp('media_tabs').getActiveTab().items.items[0];                                        
                                view.getStore().reload();
                                Ext.MessageBox.alert('Success', 'Item(s) moved successfully.');
                            }
                        });
                    }
                })
            );
        }
    });
}

function trim(str){
        return str.replace(/^\s+|\s+$/g,"");
} 

function toggle_negated_search_box (pk, value){    
    var store = Ext.getCmp('search_box').getStore();
    var record = store.getAt(store.find('pk', pk));        
    record.data.negated = value;
    record.commit();  
    if(value) {
        Ext.get('sb_' + pk).dom.src = '/files/images/icons/fam/delete.gif';
    }
    else {
        Ext.get('sb_' + pk).dom.src = '/files/images/icons/fam/delete_grey.gif';
    }
}

function get_final_node_path(node){
	var root = node.getOwnerTree().getRootNode();
    var path = node.getPath('text') + '/';
    var title = node.getOwnerTree().title;
//    path = path.replace('/' + root.text, node.attributes.type + ':');
    path = path.replace('/' + root.text, title + ':');
    return path;
}

function search_box_do_search(condition){
    var baseParams = {complex_query:{nodes:[], condition:condition}};
    
    var store = Ext.getCmp('search_box').getStore();
    if (store.getCount() > 0){
        var new_search = [];
        store.each(function(r){
            baseParams.complex_query.nodes.push({id:r.data.pk, negated: r.data.negated});
            new_search.push(r.data.path);
        });
        
//    current_search = ' ' +  new_search.join(' ');
//    current_search = trim(current_search)
        if(Ext.getCmp('smart_folders').getSelectionCount() == 0) {
            var media_tab = Ext.getCmp('media_tabs').getActiveTab();
            media_tab.getSearch().setValue('');
        }

        baseParams.complex_query = Ext.encode(baseParams.complex_query);
        set_query_on_store(baseParams);
    }
}


var save_smart_folder = function(label_value, smart_folder_id){
                    
    var url =  '/save_smart_folder/';
    
    var baseParams ={node_id: []};
    var condition;
    var only_label_edit;

    if (Ext.getCmp('sb_and').pressed) {
        condition = 'and';
    }
    else {
         condition = 'or';
    }

    baseParams.condition = condition;    
    
    if (label_value){
        only_label_edit = true;
        baseParams.only_label_edit = only_label_edit;
    }
    else {
        only_label_edit  = false;
    }

    if (smart_folder_id) {
        baseParams.smart_folder_id = smart_folder_id;
    }
        
    var submit = function(smart_folder_id, only_label_edit){
                    
        if(!only_label_edit){
            var store = Ext.getCmp('search_box').getStore();
            store.each(function(r){
                
                baseParams.node_id.push({'pk':r.data.pk, 'negated': r.data.negated});
            });
            baseParams.node_id = Ext.encode(baseParams.node_id);
        }
        else {
            baseParams.only_label_edit = true;
        }
        
        if (smart_folder_id && !only_label_edit){
            Ext.get('search_box_panel').mask('Saving...');
            
            Ext.Ajax.request({
                url: url,
                params: baseParams,              
                scope: condition,
                success: function(){
                    Ext.get('search_box_panel').unmask();
                    var view = Ext.getCmp('smart_folders');
                    var record = view.getSelectedRecords()[0];
                    record.data.condition = this;
                    record.commit();
                }
            });
        }
            
        else{
            var b_form = form.getForm();
            b_form.baseParams = baseParams;
            b_form.submit({success: function(){
                Ext.getCmp('smart_folders').getStore().reload({callback: function(){win.close();}});
            }
            });
        }      
        
    };
                    
    
    if(!smart_folder_id){
    
        var selected_smart_folder = Ext.getCmp('smart_folders').getSelectedRecords();

        if (selected_smart_folder.length > 0) {
            smart_folder_id = selected_smart_folder[0].data.pk;
        }
    }

    if(smart_folder_id && !only_label_edit) {       
        baseParams.smart_folder_id = smart_folder_id;
        submit(smart_folder_id);
    }
    else{
        
        var form = new Ext.form.FormPanel({
            labelWidth: 70, // label settings here cascade unless overridden
            frame:true,
            items: [
                        new Ext.form.TextField({
                        allowBlank: false,
                        fieldLabel: 'label',
                        name: 'label',
                        value: only_label_edit? label_value: ''
                        })
            
            ],
            url: url
            
        });
        
        var win = new Ext.Window({
            title: 'New Smart Folder',
            layout      : 'fit',
            constrain: true,
            width       : 300,
            height      : 140,
            modal: true,
            items:[form],
            buttons:[
                {
                    text: 'Save',
                    type: 'submit',
                    handler: function(){submit();}
                },
                {
                    text:'Cancel',
                    handler: function(){
                        win.close();
                    }
                    
                }
            
            ]
            
        });
        
        win.show();         
    }
};


function open_variant(name, url, media_type, width, height){
    if (media_type == 'image'){
        var img = new Image();
        var img_width, img_height;
        img.onload = function(){
            var tmp = getFullscreenSize(img);
            
            img_width = tmp[0];
            img_height = tmp[1];
            img.width = img_width; 
            img.height= img_height;
            
            var win = new Ext.Window({
        //                        id:'fullscreen_win',
                    modal: true,
                    width:img_width + 15 ,
                    height:img_height + 30,
                    resizable: false,
                    constrain: true,
                    
                   
                    title: name,
                    html: '<div id="fullscreen"><img width="'+img_width +'" height="'+img_height+'" src="' + url+'"></img></div>',
    
                listeners:{
                    show: function(){
                        this.center();
                        
                    }
                        
                }
            
                    
            });
                
                
            win.show();
                        
        };
        img.src = url;
    
    }
    
    else if(media_type == 'movie' || media_type == 'audio'){
        
        var html = '<div class="details"><a href="' + url + ((media_type == 'audio')? '.mp3': '')   + '" style="display:block;';
        if (width && height && width != '0' && height != '0'){
            width = parseInt(width);
            height = parseInt(height);
        }
        else{
            width = 300;
            height = 300;
        }
        
        
        var vp = Ext.getCmp('viewport');
        var win_width = vp.getSize().width -15;
        var win_height = vp.getSize().height -30;
        
        if (width > win_width) {
            width = win_width;
        }

        if (height> win_height) {
            height = win_height;
        }
        html += String.format('width:{0}px;height:{1}px;" id="player_variant"> </a></div>', width, height);
        
        var win = new Ext.Window({
    //                        id:'fullscreen_win',
            modal: true,
            constrain: true,
            width:width+ 15 ,
            height:height+ 30,
            resizable: false,
            title: name,
            html: html,
            listeners:{
                show: function(){
                    if(media_type == 'movie') {
                        flowplayer("player_variant", "/files/flowplayer/flowplayer-3.1.4.swf", { 
                            clip: { initialScale: 'orig', autoPlay: false, scaling: 'orig' },             
                            plugins: { 
                                controls: { 
                                    fullscreen: false, 
                                    height: 30 
                                } 
                            }
                        });
                    }
                    else {
                        flowplayer("player_variant", "/files/flowplayer/flowplayer-3.1.4.swf", { 
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
                }
            }            
        });

        win.show();

    }
    else {
        window.open(url);
    }
}




function show_variants_menu (el){
    var menu = new Ext.menu.Menu({
        items: [{
            text: 'Generate'
        },
        {
            text: 'Import'
            
        }
        ]
    });
    
    menu.show(el);
    
    
    
}

function setTabTitle(value,panel_id){
	var short_value = shortName(value, null, 20);
	var media_tab = Ext.getCmp(panel_id);
	
	if(media_tab){
		if (value.length > 0)
            media_tab.setTitle(short_value);
        
        else
            media_tab.setTitle('All Items');
//		media_tab.tabTip = value;
	}
	
};

store_tabs = new Ext.data.JsonStore({
	root: 'tabs',        
    fields: ['name','workspace', 'active', 'query', 'loaded', 'new_tab', 'media_type'],
});


function do_search(v){
	if(v.length < 1){
        
        clear_other_selections();
        
        set_query_on_store({});
        setTabTitle('All Items');
    }
    else {
        set_query_on_store({query:v});
        setTabTitle(v);
    }
	
	
};

function create_tabs(ws_id, media_type){
	
	if (!media_type)
		var media_type = ['image', 'audio', 'video', 'doc'];
	
	return {name: 'All Items', 
   		workspace: ws_id, 
   		active: true, 
   		loaded: false, 
   		new_tab: false, 
   		media_type: media_type
   	}		
	
}


function createTemplate(panel_id, media_type){
	function get_audio_tpl(media_type){
		
		var audio_tpl_base = '<div class="thumb-wrap thumb-audio" id="{pk}"  >';
		audio_tpl_base += '<tpl if="preview_available == 0">';
			audio_tpl_base += '<div class="thumb  thumb-play" >';
		audio_tpl_base += '</tpl>';
		
		audio_tpl_base += '<tpl if="preview_available == 1">';
			audio_tpl_base += '<div class="thumb  " >';
		audio_tpl_base += '</tpl>';	
		
		
//			if (media_type.length > 1)
//				audio_tpl_base += '<span class="{type}_icon media_icon"></span>';
			audio_tpl_base += '<tpl if="inprogress === 1"><span class="inprogress"></span></tpl>';
			audio_tpl_base += '<tpl if="inbasket === 1"><span class="basket_icon" ></span></tpl>';
			audio_tpl_base += '<tpl if="inbasket === 0"><span class="nobasket_icon" ></span></tpl>';
			audio_tpl_base += '<tpl if="preview_available == 0">';
				audio_tpl_base += '<span>';	
					audio_tpl_base += '<tpl if="inprogress == 0">';
//						audio_tpl_base += '<a id="' +Ext.id() + '_{pk}"  class="myPlayer myPlayer_' + panel_id + '" href="/redirect_to_component/{pk}/preview/?t=134.4.mp3">';
						audio_tpl_base += '<a id="' +Ext.id() + '_{pk}"  class="myPlayer ' + cls_audio  +'" href="/redirect_to_component/{pk}/preview/?t=134.4.mp3">';
					audio_tpl_base += '</tpl>'; 
					audio_tpl_base += '<tpl if="inprogress == 1">';
						audio_tpl_base += '<a id="' +Ext.id() + '_{pk}">';
					audio_tpl_base += '</tpl>'; 
					
					
						audio_tpl_base += '<img class="play" style="display:none;" src="/files/images/play.png" />';
					audio_tpl_base += '</a>';
				audio_tpl_base += '</span>';
			audio_tpl_base += '</tpl>';
			audio_tpl_base += '</div>';           
		audio_tpl_base += '<span>{shortName}</span></div>';
		
		return audio_tpl_base;
	};
	
	var tpl_str = '<tpl for=".">';
	tpl_str += '<tpl if="type == \'audio\'">';
	tpl_str += get_audio_tpl(media_type);
	tpl_str += '</tpl>';
	tpl_str += '<tpl if="type != \'audio\'">';    
	tpl_str += '<div class="thumb-wrap" id="{pk}">';
	tpl_str += '<div class="thumb">';
	if (media_type.length > 1)
		tpl_str += '<span class="{type}_icon media_icon"></span>'; 
	
	tpl_str += '<tpl if="inprogress === 1"><span class="inprogress"></span></tpl>';
	tpl_str += '<tpl if="inbasket === 1"><span class="basket_icon" ></span></tpl>';
	tpl_str += '<tpl if="inbasket === 0"><span class="nobasket_icon" ></span></tpl>'; 
	tpl_str += '<!--img src="{url}" class="thumb-img"--><div style="width: 100; height: 100; background: url({url}) no-repeat bottom center; border:1px solid white;"></div></div>';                
	tpl_str += '<span>{shortName}</span></div>';
	tpl_str += '</tpl>';
	tpl_str += '</tpl>';

	return new Ext.XTemplate(
			tpl_str 
        );
	
};

var more_button = function(id){
    Ext.get('basic_metadata_' + id).setStyle('display', 'none');
    Ext.get('full_metadata_' + id).setStyle('display', 'block');
    
};

var less_button = function(id){
    Ext.get('full_metadata_' + id).setStyle('display', 'none');
    Ext.get('basic_metadata_' + id).setStyle('display', 'block');
    
};
