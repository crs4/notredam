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



//for load checkboxgroup by ajax, from http://www.extjs.com/forum/showthread.php?47243-Load-data-in-checkboxgroup/page2, used in variant.js

Ext.form.CheckboxGroup.prototype.initComponent = function(){
    Ext.form.CheckboxGroup.superclass.initComponent.call(this);
    var panelCfg = {
        cls: this.groupCls,
        layout: 'column',
        border: false
    };
    var colCfg = {
        defaultType: this.defaultType,
        layout: 'form',
        border: false,
        defaults: {
            hideLabel: true,
            anchor: '100%'
        }
    }
    if(this.items[0].items){
        Ext.apply(panelCfg, {
            layoutConfig: {columns: this.items.length},
            defaults: this.defaults,
            items: this.items
        })
        for(var i=0, len=this.items.length; i<len; i++){
            Ext.applyIf(this.items[i], colCfg);
        };
    }else{
        var numCols, cols = [];
        if(typeof this.columns == 'string'){
            this.columns = this.items.length;
        }
        if(!Ext.isArray(this.columns)){
            var cs = [];
            for(var i=0; i<this.columns; i++){
                cs.push((100/this.columns)*.01);
            };
            this.columns = cs;
        }
        numCols = this.columns.length;
        for(var i=0; i<numCols; i++){
            var cc = Ext.apply({items:[]}, colCfg);
            cc[this.columns[i] <= 1 ? 'columnWidth' : 'width'] = this.columns[i];
            if(this.defaults){
                cc.defaults = Ext.apply(cc.defaults || {}, this.defaults)
            }
            cols.push(cc);
        };
        if(this.vertical){
        var rows = Math.ceil(this.items.length / numCols), ri = 0;
            for(var i=0, len=this.items.length; i<len; i++){
                if(i>0 && i%rows==0){
                    ri++;
                }
                if(this.items[i].fieldLabel){
                    this.items[i].hideLabel = false;
                }
                cols[ri].items.push(this.items[i]);
            };
        }else{
            for(var i=0, len=this.items.length; i<len; i++){
                var ci = i % numCols;
                if(this.items[i].fieldLabel){
                    this.items[i].hideLabel = false;
                }
                cols[ci].items.push(this.items[i]);
            };
        }
        Ext.apply(panelCfg, {
            layoutConfig: {columns: numCols},
            items: cols
        });
    }
    this.panel = new Ext.Panel(panelCfg);
    if(this.forId && this.itemCls){
        var l = this.el.up(this.itemCls).child('label', true);
        if(l){
            l.setAttribute('htmlFor', this.forId);
        }
    }
    var fields = this.panel.findBy(function(c){
        return c.isFormField;
    }, this);
    this.items = new Ext.util.MixedCollection();
    this.items.addAll(fields);
};
Ext.form.CheckboxGroup.prototype.onRender = function(ct, position){
    if(!this.el){
        this.panel.render(ct, position);
        this.el = this.panel.getEl();
    }
    Ext.form.CheckboxGroup.superclass.onRender.call(this, ct, position);
};
Ext.FormPanel.prototype.initFields = function(){
    var f = this.form;
    var formPanel = this;
    var fn = function(c){
        if(c.isFormField){
            if (!c.items){
                f.add(c);
            }else{
                c.items.each(fn);
            }
        }else if(c.doLayout && c != formPanel){
            Ext.applyIf(c, {
                labelAlign: c.ownerCt.labelAlign,
                labelWidth: c.ownerCt.labelWidth,
                itemCls: c.ownerCt.itemCls
            });
            if(c.items){
                c.items.each(fn);
            }
        }
    }
    this.items.each(fn);
};






var ws_grid_view, store_tabs, pref_store, pref_ws_store;
var pageSize = 25;
var firstlayout = true;
var metadata_structures = {};

var old_selected_nodes = [];
var CLOSABLE_TAB_CLASS = 'x-tab-strip-closable'; 
var cls_audio = 'loadPlayer';

var cue_point_list = [];

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

function openCuePointEditor() {

	var items = get_selected_items();

	if (items.length > 0) {
	
		var win = new Ext.Window({
			height: 600,
			width: 800,
			resizable: false,
			modal: true,
			constrain:true,
			items: [
				{
					title: 'CuePoint Editor',
					html: '<object classid="clsid:d27cdb6e-ae6d-11cf-96b8-444553540000" codebase="http://download.macromedia.com/pub/shockwave/cabs/flash/swflash.cab#version=10,0,0,0" width="750" height="500" id="taggatore" align="middle"> <param name="allowScriptAccess" value="sameDomain" /> <param name="allowFullScreen" value="false" /> <param name="movie" value="/files/cuepoint_editor/taggatore.swf" /><param name="quality" value="high" /><param name="bgcolor" value="#ffffff" /><embed src="/files/cuepoint_editor/taggatore.swf" quality="high" bgcolor="#ffffff" width="750" height="500" name="taggatore" align="middle" allowScriptAccess="sameDomain" allowFullScreen="false" type="application/x-shockwave-flash" pluginspage="http://www.adobe.com/go/getflashplayer_it" /> </object>'
				}
			]
		});
	
		var cue_point_keywords = new Ext.data.JsonStore({
            baseParams: {item_id: items[0]},
			url: '/get_cuepoint_keywords/',
			root: 'keywords',
			fields: ['keyword', 'item_values'],
			autoLoad: true,
			listeners: {
				load: function() {
					cue_point_list = [];
					this.each(function(r) {
						cue_point_list.push([r.get('keyword'), r.get('item_values')]);
					});
					win.show();
				}
			}
		});			
	
	}

};

function getCuePoint() {

	var items = get_selected_items();
	
	if (items) {

        var keywords = [];
        var metadata = [];

        var tmp_key;

        for (var x=0; x < cue_point_list.length; x++) {
            tmp_key = cue_point_list[x][0];
            tmp_value = cue_point_list[x][1];
            keywords.push(tmp_key);
            metadata.push(tmp_value)
        }

        console.log(keywords, metadata);

		var metadata_list = {
		    item: items[0], 
            
		    video_url: '/redirect_to_component/' + items[0] + '/1/', 
		    keywords: keywords,
		    metadata: metadata
		}
	
        console.log(metadata_list);
		
		return metadata_list;
	
	}
	
};

function setCuePoint(cuepoints, item) {

	console.log(cuepoints);
	console.log(item);

	Ext.Ajax.request({
		url: '/set_cuepoint/',
		params:{
			cuepoints: Ext.encode(cuepoints),
			item: item			
		},
		success: function() {
			Ext.MessageBox.alert('Success', 'CuePoints saved successfully.');
		}
	});


};


function play_audio(player_id){
    var player = flowplayer(player_id);
    
    if(!player.isLoaded()) {
        player.load(function(){
            player.play();
        });
    }
    
};


function shortName(name, obj, len, left_truncate){
	if (!len)
		var len = 15;
	
    if(name.length > len){
        if (left_truncate)
             return '...' + name.substr(name.length -15) ;
        else
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
                }
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
    var selected_ids = [];
    if(selNodes && selNodes.length > 0){ 
        for (var i=0; i < selNodes.length; i++) {
            var data = view.store.getAt(view.store.findExact('pk', selNodes[i].id)).data;
            selected_ids.push(data.pk);
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
                                        Ext.MessageBox.alert('Success', 'Item(s) shared successfully.');
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
    
    else if(media_type == 'video' || media_type == 'audio'){
        
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
                    if(media_type == 'video') {
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
	var short_value = shortName(value, null, 20, true);
    
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
    fields: ['name','workspace', 'active', 'query', 'loaded', 'new_tab', 'media_type']
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
		
		
//			audio_tpl_base += '<tpl if="preview_available == 1">';
				audio_tpl_base += '<div class="thumb  ">';
//			audio_tpl_base += '</tpl>';	
			audio_tpl_base += '<tpl if="status == \'in_progress\'"><span class="inprogress"></span></tpl>';
			audio_tpl_base += '<tpl if="inbasket === 1"><span class="basket_icon" ></span></tpl>';
			audio_tpl_base += '<tpl if="inbasket === 0"><span class="nobasket_icon" ></span></tpl>';
			audio_tpl_base += '</div>';
			
			audio_tpl_base += '<span>{shortName}</span>'
		audio_tpl_base += '</div>';

		
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
			
					tpl_str += '<tpl if="status == \'in_progress\'"><span class="inprogress"></span></tpl>';
					tpl_str += '<tpl if="inbasket === 1"><span class="basket_icon" ></span></tpl>';
					tpl_str += '<tpl if="inbasket === 0"><span class="nobasket_icon" ></span></tpl>'; 
					tpl_str += '<div style="width: 100; height: 100; background: url({url}) no-repeat bottom center; border:1px solid white;"></div>';
//					tpl_str += '<img src="{url}"></img>';
				tpl_str +='</div>';                
				
				tpl_str += '<span>{shortName}</span>' 
			tpl_str += '</div>';
		tpl_str += '</tpl>';
	tpl_str += '</tpl>';

	return new Ext.XTemplate(
			tpl_str 
        );
	
};

var scripts_jsonstore = new Ext.data.JsonStore({
	url: '/get_scripts/',
	root: 'scripts',
	storeId: 'scripts_store',
	fields: ['id', 'name'],
	listeners:{
		load: function(store, records){			
			var run_scripts_menu = Ext.getCmp('run_scripts_menu');
			var edit_scripts_menu = Ext.getCmp('edit_scripts_menu');
			
			run_scripts_menu.removeAll();
			edit_scripts_menu.removeAll();
			Ext.each(records, function(record){
				run_scripts_menu.add({
					
					text: record.data.name,
					handler: function(){
						var items = []
						var tab = Ext.getCmp('media_tabs').getActiveTab();                    
                        var view = tab.getComponent(0);
                        var items_selected = view.getSelectedRecords();
                        
                        if (items_selected.length){
                        	Ext.each(items_selected, function(i){
                        		items.push(i.data.pk);
                        	});
                        Ext.Ajax.request({
                        	url: '/run_script/',
                        	params:{
                        		items: items,
                        		script_id: record.data.id
                        	},
                        	success: function(){
                        		Ext.Msg.alert('','Script started successfully.');
                        		var media_tabs = Ext.getCmp('media_tabs').getActiveTab();
                        		var view = media_tabs.getComponent(0);
                        		view.getStore().reload();
                        		
                        	},
                        	failure: function(){
                        		Ext.Msg.alert('', 'Script failed, a server side error occurred.');
                        	}
                        
                        });	
                        
                        }
                       
                       
						
					}
				});
				
				edit_scripts_menu.add({
					
					text: record.data.name,
					handler: function(){
						window.open('/script_editor/' + record.data.id + '/')
                       
                       
						
					}
				});
				
			});
			
		
		}
	}
});
