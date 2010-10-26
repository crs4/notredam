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

var ws_store = new Ext.data.JsonStore({
            url: '/get_workspaces/',
            id:'store_workspaces',
//            autoLoad: true,
//            totalProperty: 'totalCount',
            root: 'workspaces',
            idProperty: 'pk',
            fields:[{name:'pk', type:'int'}, 'name', 'description', 'root_id', 'collections_root_id', 'inbox_root_id', 'media_type']
        
        });

        
var ws_state_store = new Ext.data.JsonStore({
        url: '/get_states/',
        id:'ws_state_store',
        root: 'states',
        idProperty: 'pk',
        fields:['pk', 'name']
    });
        

var ws_permissions_store = new Ext.data.JsonStore({
        url: '/get_permissions/',
        id:'ws_permissions_store',
        root: 'permissions',
        idProperty: 'name',
        fields:['name'],
        method: 'POST',
        listeners: {
            load: function(records){
                var admin = ws_permissions_store.find('name', 'admin') > - 1;
                var new_ws = ws_permissions_store.find('name', 'add_ws') > -1;        

                Ext.getCmp('new_ws_menu').disable();

                if (new_ws) {
                    Ext.getCmp('new_ws_menu').enable();                
                }

                if (admin ){
                    Ext.getCmp('new_item_menu').enable();
                    Ext.getCmp('preferences_menu').enable();
                    Ext.getCmp('delete_ws_menu').enable();
                    Ext.getCmp('preferences_scripts').enable();
    //            Ext.getCmp('mvto').enable()
    //            Ext.getCmp('removefrom').enable()
    //            Ext.getCmp('remove_from_ws').enable()
    //            Ext.getCmp('remove_from_collection').enable()
                    if(ws_state_store.getCount()) {
                        Ext.getCmp('set_state_to').show();
                    }
                    else {
                        Ext.getCmp('set_state_to').hide();
                    }
                    Ext.getCmp('metadata_panel').buttons[0].show();            
                    Ext.getCmp('metadata_panel').buttons[1].show();            
                    Ext.getCmp('xmp_panel').buttons[0].show();            
                    Ext.getCmp('xmp_panel').buttons[1].show();                           

                    return;
                }
                Ext.getCmp('preferences_menu').disable();
                Ext.getCmp('delete_ws_menu').disable();             
                
                var add_item = ws_permissions_store.find('name', 'add_item') > -1;
                var edit_metadata = ws_permissions_store.find('name', 'edit_metadata') > -1;
                
                var edit_scripts = ws_permissions_store.find('name', 'edit_scripts') > -1;
                var run_scripts = ws_permissions_store.find('name', 'run_scripts') > -1;
                
                if (add_item){
                    Ext.getCmp('new_item_menu').enable();        
                }
                else{
                    Ext.getCmp('new_item_menu').disable();                
                }

                if (edit_metadata){
                    Ext.getCmp('metadata_panel').buttons[0].show();            
                    Ext.getCmp('metadata_panel').buttons[1].show();            
                    Ext.getCmp('xmp_panel').buttons[0].show();            
                    Ext.getCmp('xmp_panel').buttons[1].show();                           
                }
                else {
                    Ext.getCmp('metadata_panel').buttons[0].hide();            
                    Ext.getCmp('metadata_panel').buttons[1].hide();            
                    Ext.getCmp('xmp_panel').buttons[0].hide();            
                    Ext.getCmp('xmp_panel').buttons[1].hide();           
                }
                
                if(edit_scripts)
                    Ext.getCmp('preferences_scripts').enable();
                else
                    Ext.getCmp('preferences_scripts').disable();
                
//                 if(run_scripts)
//                    Ext.getCmp('runscript').enable();
//                else
//                    Ext.getCmp('runscript').disable();
                
                if(ws_state_store.getCount()) {
                    Ext.getCmp('set_state_to').show();               
                }
                else {
                    Ext.getCmp('set_state_to').hide();
                }
            }            
        }
    });
    
function find_current_ws_record(record, id){
    if (record.get('pk') == ws.id) {
        return true;
    }
}

var ws_win;

    
function cell_click(grid, rowIndex, columnIndex, e){
    
    var media_tab = Ext.getCmp('media_tabs').getActiveTab();
    var view = media_tab. getComponent(0);
    var ws_record = ws_grid.getSelectionModel().getSelected();
    
    if (ws.id == ws_record.data.pk){
        return;
    }
    
    current_ws = Ext.select('.current_ws');
    current_ws.addClass('ws_over');
    current_ws.removeClass('current_ws');
    
    if (!rowIndex) {
       rowIndex = 0;
    }

    var row_selected = Ext.get(ws_grid.getView().getRow(rowIndex));
         
    row_selected.removeClass('ws_over');
    row_selected.addClass('current_ws');
    
    ws.id = ws_record.data.pk;
    ws.name = ws_record.data.name;
    ws.description= ws_record.data.description;
    var current_ws_div = Ext.get('current_ws');
    current_ws_div.update(ws.name);
    set_query_on_store({workspace_id:ws_record.data.pk });
    
    
    var media_tab = Ext.getCmp('media_tabs').getActiveTab();
    var search = media_tab.getSearch();
    
    
    
    search.setValue('');

    root_keywords = tree_keywords.getRootNode();
    root_keywords.id = ws_record.data.root_id;
    root_keywords.reload();
    
    root_collections = tree_collections.getRootNode();
    root_collections.id = ws_record.data.collections_root_id;
    root_collections.reload();

    root_inbox = inbox.getRootNode();
    root_inbox.id = ws_record.data.inbox_root_id;
    root_inbox.reload();

}
    
function switch_ws(current_record, ws_id){
	clear_other_selections(); //to avoid selectionchange event later, that can change tab name
	Ext.getCmp('detail_tabs').getActiveTab().hide();
	media_tabs = Ext.getCmp('media_tabs');
	if (!current_record || current_record == null){
    	//initial load
        current_record = ws_store.query('pk', ws_id).items[0];    
    }
    else{
        Ext.Ajax.request({
            url:'/switch_ws/',
            params: {
                workspace_id: current_record.data.pk
            }
        });
        
    	if (store_tabs.isFiltered)
        	store_tabs.clearFilter();        
        //reseting store_tabs for the current ws
    	
    	store_tabs.filter('workspace', ws.id);    
    	
        //deleting all previous tabs for the old ws
    	store_tabs.each(function(){
        	store_tabs.remove(this);
        	
        });
        store_tabs.clearFilter();
        
        var tabs = []
        var active_tab = media_tabs.getActiveTab();
        var store;
        var view;
        if (!ws.deleted){
	        for(var i = 0; i < media_tabs.items.items.length; i++){
	        	
	        	view = media_tabs.items.items[i].getComponent(0);
	        	store = view.getStore();
	        	
	        	var query = null;        	
	        	if (store.baseParams.query || store.baseParams.query == '')
	        		query = store.baseParams.query;    
	        	
	        	var new_tab = false;
	        	if (query == null)
	        		new_tab = true;
	        	var media_type = media_tabs.items.items[i].getMediaTypes();
	        	
	            var tab = {name: media_tabs.items.items[i].title, 
	            		workspace: ws.id, 
	            		active: media_tabs.items.items[i] == active_tab, 
	            		loaded: false, 
	            		query: query, 
	            		new_tab: new_tab, 
	            		media_type: media_type
	            };            
	            	
	        	tabs.push(tab);    	        	
	        } 
	        //adding new tabs for the ws 
	        store_tabs.loadData({tabs: tabs}, true);
        }        
        media_tabs.removeAll();
        
        
    }
    
    ws.id = current_record.data.pk;
    ws.name = current_record.data.name;
    ws.description= current_record.data.description;
    
//    var current_ws_div = Ext.get('current_ws');
//    current_ws_div.update(ws.name);
    
    store_tabs.filter('workspace', ws.id);
   
    var query = {workspace_id:current_record.data.pk}; 
    
//    var load_items; 
    
    var tab_to_activate;
    var media_type;
    var count = 0;
    store_tabs.each(function(){
    	
    		
    		var tab = createMediaPanel({
    			title: this.data.name,    			
    			query: this.data.query,
    			media_type: this.data.media_type,
    			closable: true
//                closable: count > 0
//                search_value: this.data.query || ''
    		});
    		count += 1;
    		media_type = this.data.media_type;

                        
            if (this.data.query)
                tab.getSearch().setValue(this.data.query);
                
	    	if (this.data.active){
	    		tab_to_activate = tab;	    			    		
	    		query.query = this.data.query;                
	    		load_items = !this.data.new_tab;
	
	    	}
	    	
            media_tabs.add(tab);
    });
       
    // suspend events to avoid tabchange on first load
    media_tabs.suspendEvents();
    media_tabs.setActiveTab(tab_to_activate);
    media_tabs.resumeEvents();
    media_tabs.doLayout();
   
    if (load_items)
    	set_query_on_store(query);
    
    
    
    root_keywords = tree_keywords.getRootNode();
    root_keywords.id = current_record.data.root_id;
    root_keywords.reload();
    
    
    
    root_collections = tree_collections.getRootNode();
    root_collections.id = current_record.data.collections_root_id;
    root_collections.reload();
    
    root_inbox = inbox.getRootNode();
    root_inbox.id = current_record.data.inbox_root_id;
    root_inbox.reload();
    
    Ext.getCmp('smart_folders').getStore().reload();
    Ext.getCmp('search_box').getStore().removeAll();
    
    ws_state_store.load(); //permissions loaded in callback
    
    populate_menu();
    
    var sb = Ext.getCmp('dam_statusbar');
    sb.showBusy({
        iconCls: 'x-status-busy status_busy'
    });
    
//     if (sb.tip) {
//         if (sb.tip.body) {
//             sb.tip.body.update('Loading...');
//         }
//     }
        
    if (Ext.getCmp('variantMenu').store) {
        Ext.getCmp('variantMenu').store.reload();
    }

}
    
var ws_view = new Ext.DataView({
            store: ws_store,
            itemSelector: 'div.thumb-wrap',
            style:'overflow:auto',
            multiSelect: false,
            height: 300,
            tpl: new Ext.XTemplate(
                '<tpl for=".">',
                '<div class="thumb-wrap" id="{name}">',
                '{name}',
                '</div>',
//                '<div class="thumb"><img src="{url}" class="thumb-img"></div>',
//                '<span>{shortName}</span></div>',
                '</tpl>'
            ),
            listeners: {        
//                'selectionchange': {fn:showDetails, buffer:100}
            }
        });
    
ws_grid = new Ext.grid.GridPanel({
    id: 'ws_grid',
    store: ws_store,
    hideHeaders:true,
    columns: [
        {id:'pk',header: "id", dataIndex: 'pk', hidden: true},
        {id:'name',header: "name", width:190,  dataIndex: 'name', sortable: true}
    ],
    listeners:{
        render: initializeWsDropZone
        },
    
    sm: new Ext.grid.RowSelectionModel({
        singleSelect:true,
        listeners:{
            selectionchange: {buffer:50, fn: function(){
                cell_click();
                }
            }
        }
        
        
        }),
    viewConfig: {
        forceFit: true,
        tpl: new Ext.XTemplate('<div id="{pk}" class="ws-info"></div>'),
        enableRowBody: true,
//      Return CSS class to apply to rows depending upon data values
        getRowClass: function(record, index,  p, store) {
            p.body = this.tpl.apply(record.data);
            var ws_id = record.get('pk');
            if (ws_id == ws.id) {
                return 'x-grid3-row-selected ws-target current_ws ';
            } 
            return 'ws-target ws_over';
            
        }
    }
    
});

function select_current_ws(){    
    var ws_record = ws_store.getAt(ws_store.findBy(find_current_ws_record));
    ws_grid.getSelectionModel().selectRecords([ws_record]);
}

ws_grid.on('render', function(grid){
    grid.focus();
    select_current_ws();

    }
);

ws_grid.on('cellclick', cell_click);
    
    
var workspaces_panel = new Ext.Panel({
    id:'workspaces_panel',
    title: 'Workspaces',
    items:ws_grid,
    layout:'fit'
});

function _get_general_fields(close_win_on_submit){
    var field_name = new Ext.form.TextField({
        id: 'field_name',
        fieldLabel: 'Name',
        name: 'name',                       
        allowBlank:false,
        enableKeyEvents: true,
        listeners: {render: function() {this.focus(true, 100);},
            keydown: function(field, e){
                var my_win = this.findParentByType('window');
                
                if (e.getKey() == e.ENTER) {
                    _general_submit(close_win_on_submit, my_win);
                }
            }
        }
    });
    
    var field_description = new Ext.form.TextArea({
        id: 'field_description',
        fieldLabel: 'Description',        
        name: 'description',
        allowBlank:true,
        height: 100
    });

    return [field_name, field_description];
}
    
    

function _general_submit(close_win_on_submit, win_obj){                        

    Ext.getCmp('general_form').getForm().submit({
        clientValidation: true,
        waitMsg: 'Saving...',
        success: function(form, action) {
            ws_store.reload();
            var new_name = form.getValues().name;
            if(close_win_on_submit) {
            	//new ws            	
            	var ws_id = Ext.decode(action.response.responseText).ws_id;
            	store_tabs.loadData({'tabs':[create_tabs(ws_id)]}, true);
                win_obj.close();
            }
            else{

                ws.name = new_name
                win_obj.close();
            }
        },
        
        failure: function(form, action) {
            console.log('failure :(');
            console.log('form.isValid() ' + form.isValid());
            
        }
        
        
    });
                        
}



function general_form(title, url,  close_win_on_submit, values){
    
    var fields = _get_general_fields(close_win_on_submit);   
    
    if (values){
        for(var i=0; i<values.length; i++) {
            fields[i]['value'] = values[i];
        }
    }
    return new Ext.FormPanel({
        id:'general_form',
//        labelWidth: 75, // label settings here cascade unless overridden
        frame:true,
        title: title,
//        bodyStyle:'padding:5px 5px 0',
//        width: 450,
        defaults: {width:300},
        url: url ,
        defaultType: 'textfield',

        items:fields,
        buttons: [{
            id: 'save_button',
            text: 'Save',
            type: 'submit',
            handler: function(){
                var my_win = this.findParentByType('window');                
                _general_submit(close_win_on_submit, my_win );
                }
        },{
            text: 'Cancel',
            handler: function(){
                var my_win = this.findParentByType('window');
                my_win.close();
            }
            
        }]
    });
}
function edit_ws(create){
    
   var title, url, g_form; 
    
   if(create){
        title = 'New Workspace';
        url = '/admin_workspace/add/';
        g_form = general_form(title, url, true);
   }
   else{
        current_ws = ws_store.getAt(ws_store.findBy(find_current_ws_record)).data;
        title = 'General';
        url = '/admin_workspace/' + current_ws.pk + '/';
        g_form = general_form('General',url,false, [current_ws.name, current_ws.description]);
       
    }
   
    var ws_win = new Ext.Window({
        constrain: true,
        layout      : 'fit',
        width       : 450,
        height      : 270,
        modal: true,
        items:[g_form]
    });

    ws_win.show();     

}

    
//    create a fieldset with checkbox and toggle button


function initializeWsDropZone(g){
    g.dropZone = new Ext.dd.DropZone(g.getView().scroller,{ddGroup: 'organizerDD'});
        
    g.dropZone.getTargetFromEvent=function(e) {
        var target = e.getTarget('.ws-target',10, true);
        if (target){
            var ws_id_col = target.child('div');
            return ws_id_col;
        }
    };

    g.dropZone.onNodeOver = function(target, dd, e, data){       
        var ws_id = target.dom.innerHTML;
        if (ws_id == ws.id) {
            return Ext.dd.DropZone.prototype.dropNotAllowed;
        }
        else {
            return Ext.dd.DropZone.prototype.dropAllowed;
        }
    };
        
    g.dropZoneonNodeOut = function( nodeData, source, e, data ) {
        
    };
    
    g.dropZone.onNodeDrop = function( nodeData, source, e, data ){
        var ws_id = nodeData.dom.innerHTML;
        if (ws_id == ws.id) {
            return;
        }
        
        var media_tab = Ext.getCmp('media_tabs').getActiveTab();
        var view = media_tab.getComponent(0);
        var getSelectedIndexes = view.getSelectedIndexes();
        var params = 'ws_id='+ws_id+'&';
        var node_index, item;
        for (var i = 0; i<getSelectedIndexes.length; i++){
            node_index = getSelectedIndexes[i];
            item = view.getStore().getAt(node_index);
            if(item){
                params+='item_id=' + item.data.pk + '&';
            }            
        }
        function move_item(btn){
            if (btn == 'cancel') {
                return;
            }
            var on_success;
            if(btn == 'no'){
                params+='remove=true&';
                on_success = function(){
                    view.getStore().reload();
                };
            }
            else {
                on_success = null;
                Ext.Ajax.request({
                    url: '/add_items_to_ws/',
                    params:params,
                    success: on_success
                    });
            }
        }
                
            Ext.MessageBox.show({
                fn:move_item,
                title:'Copying items',
                msg:'Move the item(s) to the selected workspace or just copy?',
                 buttons:{
                        yes:'copy',
                        no:'move',
                        cancel:'cancel'
                        }
                });
        
        return true;
    };
    
}



function workflow(){
    var workflow_win;    
    var grid_id = 'wf_grid';
    var wf_grid = new Ext.grid.EditorGridPanel({
        id: grid_id,
        viewConfig: {
            forceFit: true
            },
        store: ws_state_store,
        
//        hideHeaders: true,
        layout: 'fit',
        
        columns:  [{id:'state_name', header: "name",  dataIndex: 'name', editor: new Ext.form.TextField({selectOnFocus:true, allowBlank: false})}, 
            {  
            width:8,
            header:'delete',
            dataIndex: 'delete',
            sortable: false, 
            resizable: false,
            renderer: function(value, metadata, record,rowIndex, colIndex, store){
                if (!record.data.is_global) {
                    return '<input id="cb_' + record.data.pk + '" type="checkbox" class="cb_delete"/>';
                }
                else {
                    return '';
                }
            }
        }],
        
        tbar:[{
                text:'Add a state',
                store: ws_state_store,
                grid_id: grid_id ,
                handler:function(){                    
                    var record_constructor = this.store.recordType;
                    var new_state = new record_constructor({pk: null, name: 'new state'});
                    this.store.add(new_state);
                    var grid = Ext.getCmp(this.grid_id);                    
                    grid.getSelectionModel().selectLastRow();
                    grid.startEditing( this.store.getCount() - 1, 0);                                        
                    }            
            }
//            {text: 'Delete',
//            store: ws_state_store,
//            handler: function(){
//                cbs = Ext.DomQuery.select('input[class=cb_delete]')
//                for (i = 0; i<cbs.length; i ++){
//                    cb = cbs[i]
//
//                    console.log('cb.id ' + cb.id)
//                    id = cb.id.split('_')[1] 
//                    record = this.store.query('pk', id).items[0]
//                    if (cb.checked)
//                        this.store.remove(record)
//                    }
//
//                
//                }
//            
//                
//            }
            
            ],
        sm: new Ext.grid.RowSelectionModel({
            }),
        buttonAlign: 'center',
        buttons:[
            {text:'Save',
                handler: function(){
                    var grid = this.ownerCt;
                    var store = grid.getStore();
                    var cbs = Ext.DomQuery.select('input[class=cb_delete]');
                    var cb, id, record;
                    for (i = 0; i<cbs.length; i ++){
                        cb = cbs[i];

                        id = cb.id.split('_')[1] ;
                        record = store.query('pk', id).items[0];
                        if (cb.checked) {
                            store.remove(record);
                        }
                    }
                    var states = [];
                    var records = {};
                    store.each(function(r){states.push({pk: r.data.pk, name: r.data.name});});
                    records.states = Ext.encode(states);
                    Ext.Ajax.request({
                        scope: store,
                        url: '/save_states/',
                        params:records,
                        success: function(){
                            this.reload();                            
                            }
                        });
            
                    }
            },
            {text: 'Close',
            handler: function(){
                workflow_win.close();
                }
                }
            ],
            listeners:{
                afteredit:function(e){
                    e.record.commit();
                    },
                beforeedit:function(e){
                    if (e.record.data.is_global) {
                        return false;
                    }
                }
            }
    });
        
    
   workflow_win = new Ext.Window({
        constrain: true,
        title: 'Workflow',
        layout      : 'fit',
        width       : 550,
        height      : 270,
        modal: true,
        items:[wf_grid]
    });
    
    workflow_win.show();     
}

