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

var current_selected_nodes = [];

MyNodeUI = function(node){
    MyNodeUI.superclass.constructor.call(this, node);
};

Ext.extend(MyNodeUI, Ext.tree.TreeNodeUI, {
    
    render : function(bulkRender) {
        MyNodeUI.superclass.render.call(this, bulkRender);   
        
        
        var cb = this.node.getUI().checkbox;
        if(cb){
            var tab = Ext.getCmp('media_tabs').getActiveTab();
            if (tab){
	            var view = tab.getComponent(0);
	            if (view.getSelectionCount() == 0) {
	                cb.disabled = true;            
	            }
        	}
        }
    }
});


Ext.override(Ext.tree.TreeNodeUI, {
   
    // private
    renderElements : function(n, a, targetNode, bulkRender){
        // add some indent caching, this helps performance when rendering a large tree
        this.indentMarkup = n.parentNode ? n.parentNode.ui.getChildIndent() : '';

        var cb = typeof a.checked == 'boolean';
        
        var span_id = Ext.id();
        var href = a.href ? a.href : Ext.isGecko ? "" : "#";
        var buf = ['<li class="x-tree-node"><div ext:tree-node-id="',n.id,'" class="x-tree-node-el x-tree-node-leaf x-unselectable ', a.cls,'" unselectable="on">',
            '<span class="x-tree-node-indent">',this.indentMarkup,"</span>",
            '<img src="', this.emptyIcon, '" class="x-tree-ec-icon x-tree-elbow" />',
            '<img src="', a.icon || this.emptyIcon, '" class="x-tree-node-icon',(a.icon ? " x-tree-node-inline-icon" : ""),(a.iconCls ? " "+a.iconCls : ""),'" unselectable="on" />',
            cb ? ('<span id="' + span_id+ '" style="margin-left: 2px; position: absolute; z-index: 10; opacity: 0.5; height: 13px; width: 12px; ; padding-bottom: 0px; margin-top: 2px;"' +(n.attributes.tristate ? 'class="tristate tri_state_cb"': 'class="tristate"') +'></span><input class="x-tree-node-cb' + (n.attributes.tristate ? ' tristate' : '') +'" type="checkbox" ' + (a.checked || n.attributes.tristate  ? 'checked="checked" />' : '/>')) : '',
            '<a hidefocus="on" class="x-tree-node-anchor" href="',href,'" tabIndex="1" ',
             a.hrefTarget ? ' target="'+a.hrefTarget+'"' : "", '><span unselectable="on" style="vertical-align:2.8">',n.text,"</span></a></div>",
            '<ul class="x-tree-node-ct" style="display:none;"></ul>',
            "</li>"].join('');
        
        this.span_id = span_id;
        var nel;
        if(bulkRender !== true && n.nextSibling && (nel = n.nextSibling.ui.getEl())){
            this.wrap = Ext.DomHelper.insertHtml("beforeBegin", nel, buf);
        }else{
            this.wrap = Ext.DomHelper.insertHtml("beforeEnd", targetNode, buf);
        }
        
        this.elNode = this.wrap.childNodes[0];
        this.ctNode = this.wrap.childNodes[1];
        var cs = this.elNode.childNodes;
       
        this.indentNode = cs[0];
        this.ecNode = cs[1];
        this.iconNode = cs[2];
        var index = 3;
        if(cb){
//            this.checkbox = cs[3].childNodes[0];
            this.checkbox = cs[4];
			// fix for IE6
			this.checkbox.defaultChecked = this.checkbox.checked;						
            index = index +2;
        }
        this.anchor = cs[index];
        this.textNode = cs[index].firstChild;
        
    
        
    n.addListener('beforeclick',  function(node, e){
        var el = e.getTarget();
        if (Ext.get(el).hasClass('tristate')){
            if (!node.getUI().checkbox.disabled) {
                node.getUI().toggleCheck();
            }
            return false;
        }
        else {return true;}
    });
   
    
        
    }
});


 var tree_loader = new Ext.tree.TreeLoader({
        dataUrl:'/get_nodes/',
        uiProviders: {
             'MyNodeUI' : MyNodeUI
         },
         listeners:{
            beforeload: function(loader, node){              
                
                loader.baseParams.items = [];
                var tab = Ext.getCmp('media_tabs').getActiveTab();
                
                if (tab){
	                
	                var items = get_selected_items();
	                if (items.length > 0){
	                    loader.baseParams.items = items;	                    
	                }
                }
                
            }
        }
        
    });

function move_node(source, dest){
    
    if (source.attributes.is_moving)
        return;
    source.attributes.is_moving = true;
    source.getOwnerTree().getSelectionModel().suspendEvents();
    var old_path = get_final_node_path(source);
    Ext.Ajax.request({
        url: '/move_node/',
        params:{
            node_id:source.id,
            dest:dest.id
            },
        success: function(){
           
          
            if(! dest.isExpanded()) {
                 source.remove();
            }                 
            else {
                dest.appendChild(source);
            }
            console.log('-------' +dest.getPath());
            if (dest.getDepth() > 0)
            	tree_loader.load(dest, function(){
                
	                dest.expand(); 
	                var media_tab = Ext.getCmp('media_tabs').getActiveTab();
	                var new_source = dest.findChild('text', source.text);                                    
	                var query = media_tab.getSearch().getValue();
	                
	                for(var i = 0; i < current_selected_nodes.length ; i++){
	                    if (source.id == current_selected_nodes[i].id){
	                        query = query.replace(old_path, get_final_node_path(new_source));
	                        dest.getOwnerTree().getSelectionModel().select(new_source,null,  true);
	                    }
	                    else {
	                        dest.getOwnerTree().getSelectionModel().select(current_selected_nodes[i], null, true);
	                    }
	                }
	                media_tab.getSearch().setValue(query);
	                set_query_on_store({query: query}, true);
	                dest.getOwnerTree().getSelectionModel().resumeEvents();
	                });
            },
        failure: function(){
            source.getOwnerTree().getSelectionModel().resumeEvents();
            source.attributes.is_moving = false;
            }
            
        });
    }

    

function clear_other_selections(tree){
    if(tree){
        var nodes;
        if (tree.getSelectedNode) {
            nodes = tree.getSelectedNode();
        }
        else {
            nodes = tree.getSelectedNodes();
        }
        if (nodes.length == 0) {
            return;
        }
    }
    var tree_list = [tree_keywords.getSelectionModel(), tree_collections.getSelectionModel(), inbox.getSelectionModel(), Ext.getCmp('smart_folders')];
    for (var i = 0; i < tree_list.length; i ++){
        
        if(tree_list[i] != tree){
                     
            tree_list[i].suspendEvents();
            tree_list[i].clearSelections();
            tree_list[i].resumeEvents();
            if (tree_list[i].id == 'smart_folders') {
                Ext.getCmp('search_box_panel').clean_up();
            }
        }
        
    }
}



function node_selected(tree){
	var media_tab = Ext.getCmp('media_tabs').getActiveTab();        
    if (!media_tab)
    	return;
	
    
    clear_other_selections(tree);
    var nodes;
    if (tree.getSelectedNode) {
        nodes = tree.getSelectedNode();
    }
    else {
        nodes = tree.getSelectedNodes();   
    }
    if(nodes == null  ) {
        return;   
    }
    var search_f = media_tab.getSearch();


    var current_search = '';
    var new_search= [];
    var node_list = [];
    var baseParams = {};
    
    
    if (nodes.length == 1 && nodes[0].attributes.is_dragged) {
        return;
    }
    if (nodes.length == 1 && nodes[0].attributes.is_moving) {
        return;
    }
    current_selected_nodes = [];
    var node;
    for (var i = 0; i < nodes.length; i++){
        node = nodes[i];
        current_selected_nodes.push(node);
        if (node.getDepth() == 0){
        	
        	search_f.setValue('');
            set_query_on_store({query: ''});
        	
            break;
        }
        
        if (node.attributes.isNoKeyword){
            new_search.push('keyword:""');
            baseParams.query = 'keyword:""';
        }
            

        else{
            var path = get_final_node_path(node);
            new_search.push(path);
            node_list.push(node.id);
         
            }
    }
    
   
    
    
    current_search = trim(current_search);
    current_search += ' ' +  new_search.join(' ');
    current_search = trim(current_search);
    if (node_list.length>0) {
        baseParams.node_id = node_list;
    }
    
    search_f.setValue(current_search);
    set_query_on_store({query: current_search });
    
}    

function create_tree(title, id){
   

    return  new Ext.tree.TreePanel({        
        id:id,
        animate:true,
        enableDD:true,
        containerScroll: true,
        ddGroup: 'organizerDD',
        
        region:'west',
        width:200,
        split:true,
        
        title:title,
        autoScroll:true,

        margins: '5 0 5 5',
        loader: tree_loader,
        rootVisible: false,
        selModel: new Ext.tree.MultiSelectionModel({
            listeners:{
                selectionchange: {fn:function(sel, nodes){node_selected(sel);}, buffer: 30}
                
            }
        }

        ),
        
        listeners:{
            startdrag: function(tree, node,e){
                node.attributes.is_dragged = true;
                tree.getSelectionModel().suspendEvents();
            
            },
            enddrag: function(tree, node, e){
                node.attributes.is_dragged = false;
                if (!node.attributes.is_moving){
                    for(var i = 0; i < current_selected_nodes.length ; i++) {
                        tree.getSelectionModel().select(current_selected_nodes[i],null,  true);
                    }
                    tree.getSelectionModel().resumeEvents();
                    
                
                }
            },
            
            //for tristate
            checkchange: function(node, checked){

                var cb = node.getUI().checkbox;
                
                var items = get_selected_items();
                if (items.length == 0){
                    cb.checked = false;
                    return false;
                }
                
                var tristate = false;                
                var cb = node.getUI().checkbox;
                
                
                if (items.length > 1 && cb && Ext.get(cb).hasClass('tristate')){
                    var tri_span = Ext.get(node.getUI().span_id);
                    
                    if (!checked && tri_span.hasClass('tri_state_cb')){
                        tri_span.removeClass('tri_state_cb');
                        tristate = false;
                        }
                    else if(!checked && !tri_span.hasClass('tri_state_cb')){
                        tristate = true;
                        cb.checked = true;
                        tri_span.addClass('tri_state_cb');
                        
                             
                         Ext.Ajax.request({
                            url:'/remove_association/',
                            params:{
                                items:items,
                                node:node.attributes.id
                                },
                            scope: node,
                                success: function(){
                                    Ext.Ajax.request({
                                        url:'/save_keyword/',
                                        params:{
                                            items:this.attributes.items,
                                            node:this.attributes.id
                                            }
                                    });
                            }
                        });
                        
                        
                    }
                    
                    
                    
                }
                
                
                if(!tristate) {
                    if (checked) {
                        Ext.Ajax.request({
                            url:'/save_keyword/',
                            params:{
                                items:items,
                                node:node.attributes.id
                                },
                            callback: function(){
                                if (this.attributes.add_metadata_parent) {
                                    store_nodes_checked.reload();
                                }
                            },
                            scope: node
                        });
                    }
                    else { 
                        Ext.Ajax.request({
                            url:'/remove_association/',
                            params:{
                                items:items,
                                node:node.attributes.id
                                }
                        });
                    }
                }    
            
            },
            
            
            render:function(){
                
                var root;
                
                if (this.title ==gettext('Keywords')) {
                    root = root_keywords;
                }
                else {
                    root = root_collections;
                }
                var dd_target = new Ext.dd.DropTarget(this.getEl(),
                    {ddGroup: 'organizerDD',
                    notifyOver: function( source, e, data ){
                        return this.dropNotAllowed;

                    }
                });
                
                this.getEl().on('contextmenu',
                	
                    function(e){     
                    	console.log('cm');
                        if (this.id == 'keywords_tree') {
                            contextMenuShow(root_keywords,e);
                        }
                        else if (this.id == 'collections_tree') {
                            contextMenuShow(root_collections,e);
                        }
                });
            }
        },
        
        
        dropConfig:{
            ddGroup:'organizerDD',
            appendOnly: true,  
            
            allowContainerDrop: true,            
            onContainerOver: function( source, e, data ){
//        		console.log(source.dragData.type);
        		if(source.dragData.type == 'items')
        			return this.dropNotAllowed;
        			
        		if (source.dragData.node.attributes.type == 'keyword'){
        			if(!source.dragData.node.attributes.isCategory)
        				return this.dropNotAllowed;
        		}        		
        		return this.dropAllowed;
        				
        		
        	},
        	onContainerDrop: function( source, e, data ){
        		
        		if(source.dragData.type == 'items')
        			return false;
//        		console.log(source.dragData)
        		if (source.dragData.node.attributes.type == 'keyword'){
        			if(!source.dragData.node.attributes.isCategory)
        				return false;
        		}        		
        		root = source.dragData.node.getOwnerTree().getRootNode();
        		 move_node(source.dragData.node, root);
                 e.stopEvent();
                 return true;
        				
        		
        	},
            
            onNodeDrop: function( nodeData, source, e,data ){
                if (!nodeData.node.attributes.allowDrop) {
                    return false;
                }
                if (data.nodes){
                    var depth = nodeData.node.getDepth();
                    if(depth == 0 || nodeData.node.attributes.isCategory ) {
                        return false; //not allowed to drop an item on the root or category
                    }
                    if (nodeData.node.attributes.type =='keyword'  && ws_permissions_store.find('name', 'edit_metadata') < 0  && ws_permissions_store.find('name', 'admin') < 0)  {
                        return false; //permission denied
                    }                    
                    if (nodeData.node.attributes.type =='collection'  && ws_permissions_store.find('name', 'edit_collection') < 0  && ws_permissions_store.find('name', 'admin') < 0)  {
                        return false; //permission denied
                    }
                    
                    var media_tab = Ext.getCmp('media_tabs').getActiveTab();
                    var view = media_tab. getComponent(0);
                    var getSelectedIndexes = view.getSelectedIndexes();
                    var items = [];
                    var node_index, item;
                    for (i = 0; i<getSelectedIndexes.length; i++){
                        node_index = getSelectedIndexes[i];
                        item = view.getStore().getAt(node_index);
                        
                        if(item){
                            items.push(item.data.pk);
                        }
                        
                    }
                        Ext.Ajax.request({
                            url:'/save_keyword/',
                            params:{
                                items:items,
                                node:nodeData.node.attributes.id
                                },
                            success: function(){
                                var cb = this.getUI().checkbox;
                                if (cb) {
                                    cb.checked = true;
                                }
                            },
                            scope: nodeData.node
                            });
                        e.stopEvent();
                        return true;
                    }
                else if (data.node){
                    if (nodeData.node.id == source.dragData.node.id) {
                        return false;
                    }
                    if(nodeData.node.getDepth() == 0 && !source.dragData.node.attributes.isCategory )
                    	return false;
                    	
                    if (source.dragData.node.contains(nodeData.node)) {
                        return false;
                    }
                    if (nodeData.node.findChild('text', source.dragData.node.text)) {
                        return false;
                    }
                    //source.dragData.node.attributes.is_moving = true;
                    move_node(source.dragData.node,nodeData.node);
                    e.stopEvent();
                    return true;
                }
            },
            
            onNodeOver: function( nodeData, source, e, data ) {

                if (data.node && source.dragData.node.contains(nodeData.node)) {
                    return false;
                }    
                
                if (data.node && nodeData.node.getDepth() == 0 && !source.dragData.node.attributes.isCategory) {
                    return false;
                }     
                
                var depth = nodeData.node.getDepth();
                if(data.nodes ){
                    if (depth == 0 || nodeData.node.attributes.isCategory) {
                        return this.dropNotAllowed; //not allowed to drop an item on the root                
                    }
                    if (nodeData.node.attributes.type =='keyword'  && ws_permissions_store.find('name', 'edit_metadata') < 0  && ws_permissions_store.find('name', 'admin') < 0) {
                        return this.dropNotAllowed; //permission denied
                    }
                    if (nodeData.node.attributes.type =='collection'  && ws_permissions_store.find('name', 'edit_collection') < 0  && ws_permissions_store.find('name', 'admin') < 0)  {
                        return false; //permission denied
                    }
                }
                
                if(nodeData.node.attributes.allowDrop) {
                    
                    return this.dropAllowed;
                }
                else {
                    return this.dropNotAllowed;
                }
            }
        
        }
                
    });
        
    }

var treeAction = function( tree_action){
    var sel_node = tree_action.scope;
    
    function submit_tree_form(cls){                        
        var params = {cls: cls};
        
        var cbs = Ext.DomQuery.select('input[class=cb_metadata]');
        var checked = [];
        var store_metadata, cb, id, row;
        if (cbs.length) {
            store_metadata = Ext.getCmp('metadata_list').getStore();
            
        }
        for (i = 0; i < cbs.length; i++){
            cb = cbs[i];
            if (cb.checked){
                if (!params.metadata)
                    params.metadata = [];
                
                id = cb.id.split('_')[1];
                checked.push(id);
                
                row = store_metadata.query('pk', id);
                params.metadata.push(Ext.encode({id: id, value: row.itemAt(0).data.value}));
                
            }                            
        }
        
        var form = Ext.getCmp('tree_form').getForm();
        
        form.submit({
            clientValidation: true,
            params: params,
            waitMsg: gettext('Saving...'),
            success: function(form, action) {
        		
                if(!sel_node.length) {
                    if(tree_action.text == gettext('Add') ||  tree_action.text == gettext('Category') || tree_action.text == gettext('Keyword') ){
                            tree_loader.clearOnLoad = false;
                            tree_loader.baseParams = {last_added: true, child: Ext.getCmp('node_label').getValue()};
                            
                            tree_loader.load(sel_node,function(){
                                tree_loader.clearOnLoad = true;
                                tree_loader.baseParams = {};
                                sel_node.expand();
                                });

                    }
                    else{
                        sel_node.setText(form.getValues().label);
                    }
                }
                var add_mdata_parent_cb = Ext.getCmp('add_metadata_parent_cb');
                
                if  (add_mdata_parent_cb ) {
                    sel_node.attributes.add_metadata_parent = add_mdata_parent_cb.checked;
                }
                win.close();
            },
            failure: function(form, action){
            }
        });

    }
    
    
    function create_add_parent_cb(node){
        
        var checked;
        
        if (node) {
            checked = node.attributes.add_metadata_parent;
        }
        else {
            checked = false;
        }  
        return new Ext.form.Checkbox({
            id: 'add_metadata_parent_cb',
            fieldLabel: 'associate ancestors',
            name: 'add_metadata_parent',    
            checked: checked
            
        });
    }
    
    
    function create_metadata_list(node_id){
        var params = {};
        if (node_id)
            params.node_id = node_id;
        return new Ext.grid.EditorGridPanel({
                id: 'metadata_list',
                viewConfig: {
                    forceFit: true
                },
                store:  new Ext.data.JsonStore({         
                    url: '/get_metadataschema_keyword_target/',
                    baseParams: params,
                    fields: ['pk','name', 'selected', 'value'],
                    root: 'metadataschema',
                    autoLoad: true

                }),
                layout: 'fit',
//                width: 250,
                height: 290,
//                autoHeight:true,
                style: {marginTop:10},
                columns:  [
                {  
                width:15,
                id: 'selected',
                dataIndex: 'delete',
                sortable: false, 
                resizable: false,
                menuDisabled: true,
                renderer: function(value, metadata, record,rowIndex, colIndex, store){
                    var onclick = String.format("record = Ext.getCmp('metadata_list').getStore().getById('{0}'); current_label = Ext.getCmp('node_label').getValue(); if (this.checked && current_label != '') {record.set('value', current_label); record.set('selected', true);} else {record.set('value', ''); record.set('selected', false)}; record.commit()", record.id);
                    if (record.data.selected) {
                        return '<input id="cb_' + record.data.pk + '" type="checkbox" class="cb_metadata" onclick="'+onclick+'" checked/>';
                    }
                    else {
                        return '<input id="cb_' + record.data.pk + '" type="checkbox" class="cb_metadata" onclick="'+onclick+'" />';
                    }
                    }
                },
                
                {id:'name', header: "metadata mapping",  dataIndex: 'name', menuDisabled: true}, 
                {id:'value', header: "value",  dataIndex: 'value', menuDisabled: true, editable: true, editor: new Ext.form.TextField({allowBlank: false})} 
                
                ],                    
            listeners:{
                afteredit: function(e){
//                        cm = e.grid.getColumnModel()
//                        editor = cm.getCellEditor( e.column, e.row );
//                        console.log(editor)
//                        v = editor.validate();
//                        
                },
                beforeedit: function(e){
                    
                    if (!e.record.data.selected) {
                        e.cancel = true;
                    }
                    
                }
            }
            });
        
        }
   console.log('----------------tree_action.text ' + tree_action.text); 
    if (tree_action.text == gettext("Delete")){
        var _delete_node = function(btn){
            if(btn == 'yes'){
                Ext.Ajax.request({
                    url: '/delete_node/',
                    params:{node_id:sel_node.id},
                    success: function(){sel_node.remove();}                        
                    }
                );
                }
                
            };
        var type = sel_node.attributes.iconCls || sel_node.attributes.type;
        Ext.MessageBox.confirm('Delete '  + type, 'Are you sure you want to delete the '+ type+' "' +sel_node.attributes.text +  '" ?', _delete_node);
        
        
    }
    
    else if (tree_action.text == gettext('Add To Search Box')){
        var box = Ext.getCmp('search_box');
        var store = box.getStore();
        if (store.find('pk', sel_node.id) <0){
            var r = new store.recordType({pk: sel_node.id, label: sel_node.text, negated: false, path: get_final_node_path(sel_node)});
            store.add(r);
        }
        
    }
    else if(tree_action.text == gettext('Show Associated Items')){
        var path = get_final_node_path(sel_node);
        var tree = Ext.getCmp('keywords_tree');
        tree.getSelectionModel().suspendEvents();
        tree.selectPath(sel_node.getPath(), null, function(success){
            
            Ext.getCmp('keywords_tree').getSelectionModel().resumeEvents();
            
        });
        
        var media_tab = Ext.getCmp('media_tabs').getActiveTab();
        var search = media_tab.getSearch();
        search.setValue(path);
        set_query_on_store({query: path, show_associated_items: true});
    }
    else{
        var fields = []; 
        
        if  (tree_action.text == gettext("Add") || tree_action.text == gettext("Category") || tree_action.text == gettext("Keyword") ||  tree_action.text == gettext("Edit")){
	        
        	var node_id, type;
	       
	        var multi_select = sel_node.length && sel_node.length>0; 
	        if (multi_select){
	            
	            type  = '';
	            node_id = [];
	            for (var i = 0; i < sel_node.length; i++) {
	                node_id.push(sel_node[i].id);
	            }
	        }
	        else {
	            node_id = sel_node.id;
	            
                if(tree_action.text == gettext("Category")) 
	                type = 'category';        
                
                else if(tree_action.text == gettext("Keyword"))
		            type = 'keyword';
	            else {
	                type = sel_node.attributes.iconCls || sel_node.attributes.type ;
	            }
	        
	            var label = new Ext.form.TextField({
	                fieldLabel: 'label',
	                name: 'label',
	                id:'node_label',                            
	                allowBlank:false,
	                listeners:{
	                    afterrender: function(field) {
	                        field.focus(false, 1000);
	                    },
	                    specialkey: function(field, e){                                    
	                        if(e.getKey() == e.ENTER && field.isValid()) {
	                            submit_tree_form(type);
	                        }
	                    }
	                }
	            });
	            fields.push(label);
	        }
	    
	        var edit_metadata = tree_action.text == gettext("Keyword")  || tree_action.text == gettext("Category") || (sel_node.attributes && (sel_node.attributes.iconCls == 'keyword' || sel_node.attributes.iconCls == 'category') && tree_action.text == gettext("Edit") );
	            
	        var action = (tree_action.text  == gettext('Add') || tree_action.text  == gettext('Keyword') || tree_action.text  == gettext('Category')) ? 'Add': 'Edit' ;
	        var title = gettext(action)  + ' ' + gettext(type);
	        var url = '/' + action.toLowerCase() + '_node/';
	            
	        var height_form, height_win, width_win;    
	            
	        if (!edit_metadata && !multi_select){
	                height_form= 100;
	                height_win = 130;
	                width_win = 300;
	            if (tree_action.text == gettext("Edit")) {       
	                label.setValue(sel_node.text);
	            }
	        }
	        else{
	            height_form= 370;
	            height_win = 400;
	            width_win = 400;
	
	        var metadata_list, add_parent_metadata;
	                    
	        if (tree_action.text == gettext("Edit")){
	            if(! multi_select){
	                label.setValue(sel_node.text);
	                if(sel_node.attributes.iconCls == 'keyword')
	                	add_parent_metadata = create_add_parent_cb(sel_node);
	            }
	            metadata_list = create_metadata_list(node_id);
	            
	            }
	        else{
	            metadata_list = create_metadata_list(null);
	            if(tree_action.text == gettext("Keyword") )
	            	add_parent_metadata = create_add_parent_cb(null);
	            
	        }
	
	        if (add_parent_metadata)
	        	fields.push(add_parent_metadata);
	        fields.push(metadata_list);
	    
	    }
    }
        var tree_form = new Ext.FormPanel({
            id:'tree_form',
            labelWidth: 70, // label settings here cascade unless overridden
            frame:true,
            height: height_form,
            bodyStyle:'padding:5px 5px 0',              
            url: url,
            baseParams:{node_id:node_id},
            items: fields,
            buttons: [{
                text: gettext('Save'),
                type: 'submit',
                handler: function(){submit_tree_form(type);}
            },{
                text: gettext('Cancel'),
                handler: function(){
                    win.close();
                }
                
            }]
        });
        
        
        win = new Ext.Window({
            title: title,
            constrain: true,
            layot: 'fit',
            width       : width_win,
            height      : height_win,
            modal: true,
            resizable: false,
            items:[ 
            tree_form 
            ],
            listeners:{
                afterrender: function() {
                    var node_l = Ext.getCmp('node_label');
                    if(node_l) {
                        node_l.focus(false, 100);
                    }
                }
            }
    });
    win.show();

    }
};
    


var add_keyword =  new Ext.menu.Item({id: 'addKeyword',text: gettext('Keyword')});
var add_category =  new Ext.menu.Item({id: 'addCategory', text: gettext('Category')});

var add_collection = new Ext.menu.Item({text: gettext('Add')});
var add_node = new Ext.menu.Item({text: gettext('Add'), menu: [add_keyword, add_category]});
var edit_node = new Ext.menu.Item({text: gettext('Edit')});
var delete_node = new Ext.menu.Item({text: gettext('Delete')});

var search_box_node = new Ext.menu.Item({text: gettext('Add To Search Box')});
var show_item_node = new Ext.menu.Item({text: gettext('Show Associated Items')});


var contextMenuKeywords = new Ext.menu.Menu({id:'mainContext'});
contextMenuKeywords.add(
    add_node,
    edit_node,
    delete_node,
    search_box_node,
    show_item_node
);

var contextMenuCollections = new Ext.menu.Menu({id:'mainContextCollections',
    items: [
    {
        text: gettext('Add')
    },
    {
        text:gettext('Edit')
    },
    {
        text: gettext('Delete')
    },
    {text: gettext('Add To Search Box')}
    
    ]
});
    
contextMenuShow = function( node_menu,e ){
		
        var admin = ws_permissions_store.find('name', 'admin') > - 1;
        var edit_taxonomy = ws_permissions_store.find('name', 'edit_taxonomy') > - 1;
        var edit_collection = ws_permissions_store.find('name', 'edit_collection') > - 1;

        var tree = node_menu.getOwnerTree();
/*        if (tree.id == 'keywords_tree') {
            if(!admin && ! edit_taxonomy){
                e.stopEvent();
                return;
            }
        }
        else if (tree.id == 'collections_tree') {
            if(!admin && ! edit_collection){
                e.stopEvent();
                return;
            }        
        } */
        if (node_menu.attributes.iconCls && node_menu.attributes.iconCls == 'no_keyword'){
            e.stopEvent();
            return;
        }
        
        var tree = node_menu.getOwnerTree();
        var sel_nodes = tree.getSelectionModel().getSelectedNodes();
        var contextMenu = tree.menu;

        contextMenu.find('text', gettext('Add To Search Box'))[0].enable(); 
        
        
        if(sel_nodes.length > 1){
            contextMenu.find('text', gettext('Add'))[0].disable();
            contextMenu.find('text', gettext('Delete'))[0].disable();
            contextMenu.find('text', gettext('Edit'))[0].setHandler(treeAction, sel_nodes);
            contextMenu.find('text', gettext('Show Associated Items'))[0].disable();        
            
            
            var all_cat = true;
            for (i = 0; i < sel_nodes.length; i ++ ){
                if (!sel_nodes[i].attributes.isCategory) {
                    all_cat = false;
                }
            }
            if (all_cat) {
                return;
            }
           
        }
        else{ 
             
//        	console.log('node_menu.getDepth()  '+ node_menu.getDepth() );
        	
        	if(node_menu.getDepth() == 0)
        		Ext.getCmp('addKeyword').disable();
        	else
        		Ext.getCmp('addKeyword').enable();
        	
            if (node_menu.attributes.type == 'keyword' || node_menu.attributes.type == 'category'  ){
            	
            	
            	
                Ext.getCmp('addKeyword').setHandler(treeAction, node_menu);
                Ext.getCmp('addCategory').setHandler(treeAction, node_menu);
                contextMenu.find('text', gettext('Show Associated Items'))[0].enable();
                contextMenu.find('text', gettext('Show Associated Items'))[0].setHandler(treeAction, node_menu);

            }
            else{
                contextMenu.find('text', gettext('Add'))[0].setHandler(treeAction, node_menu);

            }
            contextMenu.find('text', gettext('Delete'))[0].setHandler(treeAction, node_menu);
            contextMenu.find('text', gettext('Edit'))[0].setHandler(treeAction, node_menu);
            contextMenu.find('text', gettext('Add To Search Box'))[0].setHandler(treeAction, node_menu);

            if (!node_menu.attributes.editable){
                contextMenu.find('text', gettext('Delete'))[0].disable();
                contextMenu.find('text', gettext('Edit'))[0].disable();
                contextMenu.find('text', gettext('Add To Search Box'))[0].disable();
                
                if(!node_menu.attributes.allowDrop) //this is for new keywords node
                    {
                    e.stopEvent();
                    return;
                    }
            }
            
            else{
        
                contextMenu.find('text', gettext('Delete'))[0].enable();
                contextMenu.find('text', gettext('Edit'))[0].enable();
                contextMenu.find('text', gettext('Add'))[0].enable();
            }        
        }
            
        if (node_menu.attributes.isCategory) {
            contextMenu.find('text', gettext('Add To Search Box'))[0].disable();
            contextMenu.find('text', gettext('Show Associated Items'))[0].disable();
        }
        if (tree.id == 'keywords_tree') {
            if(!admin && ! edit_taxonomy){
                contextMenu.find('text', gettext('Add'))[0].disable();
                contextMenu.find('text', gettext('Delete'))[0].disable();
                contextMenu.find('text', gettext('Edit'))[0].disable();
            }
        }
        else if (tree.id == 'collections_tree') {
            if(!admin && ! edit_collection){
                contextMenu.find('text', gettext('Add'))[0].disable();
                contextMenu.find('text', gettext('Delete'))[0].disable();
                contextMenu.find('text', gettext('Edit'))[0].disable();
            }        
        }
                            
        e.stopEvent();
        contextMenu.show(node_menu.ui.getEl());
    };

    
    // set up the Album tree
    var tree_collections = create_tree(gettext('Collections'), 'collections_tree');

    var root_collections = new Ext.tree.AsyncTreeNode({
        text: gettext('All items'),
        id:'fake',
        expanded:true,
        allowDrag:false,
        allowDrop:true,
        editable: false,
        type:'collection',
        listeners:{
                beforeload: function(node){
                    if (node.id == 'fake') {
                        return false;
                    }
                }
            }
    });

    tree_collections.setRootNode(root_collections);

    tree_collections.on('contextmenu', contextMenuShow);
  
    var tree_keywords =create_tree(gettext('Keywords'), 'keywords_tree');

    
        var root_keywords = new Ext.tree.AsyncTreeNode({
            text: gettext('All items'),
            id:'fake',
            expanded: true,
            allowDrag:false,
            allowDrop:true,
            editable: false,
            
            type:'keyword',
            iconCls:'category',
            listeners:{
                beforeload: function(node){
                    if (node.id == 'fake') {
                        return false;
                    }
                }
            }
        });
        

    
    tree_keywords.setRootNode(root_keywords);

    tree_keywords.on('contextmenu', contextMenuShow);    

    tree_keywords.menu = contextMenuKeywords;
    tree_collections.menu = contextMenuCollections;

    // add an inline editor for the nodes
    
        
    function create_editor(tree){
        return new Ext.tree.TreeEditor(tree, 
            new Ext.form.TextField({
                allowBlank:false,
                 blankText:gettext('A name is required')
                })
        ,{
        selectOnFocus:true,
        listeners:{
                        
            beforecomplete: function( editor, value, startValue ){
                var sel_node = tree.getSelectionModel().getSelectedNodes()[0];
                Ext.Ajax.request({
                    url: '/edit_node/',
                    params:{node_id:sel_node.id, label:value}
                    });
                
                }
                
            }
        });
        
    } 


    Ext.app.SearchField = Ext.extend(Ext.form.TriggerField, {
//        id: 'search_field',
        triggerClass: 'x-form-search-trigger',
        
        initComponent : function(){
            Ext.app.SearchField.superclass.initComponent.call(this);
            this.on('specialkey', function(f, e){
                if(e.getKey() == e.ENTER){
                    this.onTriggerClick();
                }
            }, this);
        },
        
                
        setValue: function(value){        	
        	Ext.app.SearchField.superclass.setValue.call(this, value);
        	
        	if (value == '')
        		setTabTitle(gettext('All Items'));
        	else
        		setTabTitle(value);

        	
        },

        onTriggerClick: function() {
            var v = this.getRawValue();
            if(v.length < 1){
                
                clear_other_selections();
                
                set_query_on_store({});
                setTabTitle(gettext('All Items'));
            }
            else {
                set_query_on_store({query:v});
                setTabTitle(v);
            }

        }

    });
    
    
    var inbox = new Ext.tree.TreePanel({        
        id: 'inbox_tree',
        animate:true,
        containerScroll: true,
        region:'west',
        width:200,
        split:true,
        title:'Inbox',
        autoScroll:true,
        margins: '5 0 5 5',
        loader: tree_loader,
        rootVisible: false,
        selModel: new Ext.tree.MultiSelectionModel({
            listeners:{
                selectionchange: function(sel, nodes){node_selected(sel);}           
                }
            }

        )
        
    });

    
    var root_inbox= new Ext.tree.AsyncTreeNode({
            text: gettext('All items'),
            id:'fake',
            expanded: true,
            editable: false,
            type:'inbox',
            listeners:{
                beforeload: function(node){                    
                    if (node.id == 'fake') {
                        return false;
                    }
                }
            }
        });
        

    
    inbox.setRootNode(root_inbox);
   


var smart_folders = new Ext.Panel({
    id:'smart_folders_panel',
	title: gettext('Smart Folders'),
    autoScroll: true,
    items: [
        new Ext.ListView({
            id: 'smart_folders',
            hideHeaders: true,
            singleSelect: true,
            trackOver: true,
            store: new Ext.data.JsonStore({
                root: 'smart_folders',                     
                idProperty: 'pk',
                fields: [ 'pk','label', 'condition'],
                url :'/get_smart_folders/'
                
            }),
             columns: [
                {
                    dataIndex: 'label',
                    tpl: '<p style="padding-left:10px">{label}</p>'
                }
            ],
            listeners: {
                selectionchange: function(view){
                    
                    clear_other_selections(view);
                    var selected = view.getSelectedRecords()[0];
                    var store = Ext.getCmp('search_box').getStore();
                    var bbar= Ext.getCmp('search_box_bbar');
                    var sb_current_smart_folder = Ext.getCmp('search_box_current_smart_folder');
                    
                    var media_tab = Ext.getCmp('media_tabs').getActiveTab();
                    var search = media_tab.getSearch();
                    
                    if (selected){
                        var query = selected.data.label ;
                        search.setValue( gettext('SmartFolders:') + ' "' + query+ '"');
                        view.old_selected = selected;
                        store.load({
                            params: {
                                pk: selected.data.pk
                            },
                            scope: query,
                            callback: function(){
                                sb_current_smart_folder.setText(gettext('smart folder: ') + this);
                                bbar.show();
                                
                            }
                        });
                    }
                    else{
                        store.removeAll();
                        Ext.getCmp('save_as_smart_folder').setDisabled(true);
                        
                        sb_current_smart_folder.setText('');
                        bbar.hide();

                    }
                    set_query_on_store({query: search.getValue()});
                },
                contextmenu: function(view, index,node, e){
                    var record = view.getStore().getAt(index);
                   
                    var menu = new Ext.menu.Menu({
                        items: [
                        {
                            text: gettext('Edit'),
                            handler: function(){save_smart_folder(record.data.label, record.data.pk);}
                        },
                        {
                            text:gettext('Delete'),
                            handler: function(){
                                Ext.Msg.confirm(gettext('Delete Smart Folder'), gettext('Are you sure you want to delete the smart folder') + ' "' + record.data.label+'" ?',
                                function(btn){
                                    
                                    if (btn == 'yes'){
                                        Ext.Ajax.request({
                                            url: '/delete_smart_folder/',
                                            params: {smart_folder_id: record.data.pk},
                                            scope: view,
                                            success: function(){
                                                this.getStore().reload();
                                            }
                                            
                                            
                                        });
                                    }
                                    
                                });
                                
                            }
                        }
                        ]
                        
                    });
                    
                    menu.show(node);
                    e.preventDefault(); 
                    
                }
                
            }
        })
    ]


    });
