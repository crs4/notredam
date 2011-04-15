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

var robject_loader =  new Ext.tree.TreeLoader({
            dataUrl:'/get_real_objects/'
        });

var add_robject = new Ext.menu.Item({text: 'Add'})
var edit_robject = new Ext.menu.Item({text: 'Edit'})
var delete_robject = new Ext.menu.Item({text: 'Delete'})
var realObjectMenu = new Ext.menu.Menu({id:'realObjectMenu'});
realObjectMenu.add(
    add_robject,
    edit_robject,
    delete_robject      
);


var rObjectMenuHandler = function(menu_action){
    sel_node = menu_action.scope;

    function submit_robject_form(){                        

        Ext.getCmp('robject_form').getForm().submit({
            clientValidation: true,
            waitMsg: gettext('Saving...'),
            success: function(form, action) {

                if(menu_action.text == 'Add'){
                                        
                        robject_loader.clearOnLoad = true;
                        robject_loader.baseParams = {last_added: true}
                        robject_loader.load(real_objects.getRootNode(),function(){
                            robject_loader.clearOnLoad = true;
                            robject_loader.baseParams = {}
                            real_objects.getRootNode().expand()
                            })

                }
                else{
                    sel_node.setText(form.getValues().label);
                }
                win.close();                            
            },
            failure: function(form, action){
                console.log('failure')
                }
            })

    }
    
    
    if (menu_action.text == "Delete"){
        delete_node = function(btn){
            if(btn == 'yes'){
                Ext.Ajax.request({
                    url: '/delete_real_object/',
                    params:{node_id:sel_node.id},
                    success: function(){sel_node.remove();}                        
                    }
                )
                }
                
            }
        Ext.MessageBox.confirm('Delete Real Object', 'Are you sure you want to delete the selected real object ?', delete_node)
        
        
        }
    else if  (menu_action.text == "Add" ||  menu_action.text == "Edit"){
        
        var field = new Ext.form.TextField({
                        fieldLabel: gettext('label'),
                        name: 'label',
                        id:'node_label',                            
                        allowBlank:false,
                        listeners:{
                            render: function() {
                                this.focus(false, 100);
                            },
                            specialkey: function(field, e){                                    
                                if(e.getKey() == e.ENTER && field.isValid())
                                    submit_robject_form()
                                }
                            }
                    })
        if (menu_action.text == "Edit"){
            field.setValue(sel_node.text)
            console.log("edit of a real object... to be done")            
            
            }
        else{
            
            url = '/add_real_object/'                
            title = 'New Real Object'
            
        }
        var robject_form = new Ext.FormPanel({
            id:'robject_form',
            labelWidth: 70, // label settings here cascade unless overridden
            frame:true,
            height: 100,
            bodyStyle:'padding:5px 5px 0',              
            url: url,
            baseParams:{node_id:sel_node.id},
            items: [field],
            buttons: [{
                text: gettext('Save'),
                type: 'submit',
                handler: submit_robject_form
            },{
                text: gettext('Cancel'),
                handler: function(){
                    win.close()
                    }
                
            }]
        });
        
        
        var win = new Ext.Window({
            title: title,
            layot: 'fit',
            width       : 280,
            height      : 130,
            modal: true,
            items:[ 
            robject_form 
            ]
    })
    win.show()

    }
}

var realObjectMenuShow = function( node_menu, e ){
                
        add_robject.setHandler(rObjectMenuHandler, node_menu);
        edit_robject.setHandler(rObjectMenuHandler, node_menu);
        delete_robject.setHandler(rObjectMenuHandler, node_menu);

        if (!node_menu.attributes.editable){
            edit_robject.disable();
            delete_robject.disable();
            
        }
        
        else{
    
            edit_robject.enable();
            delete_robject.enable();
            }        
            
        e.stopEvent()
        realObjectMenu.show(node_menu.ui.getEl());
    }   


    
        var root_robjects = new Ext.tree.AsyncTreeNode({
            text: gettext('Root'),
            id:'root_robj',
            expanded: true,
            allowDrag:false,
            allowDrop:true,
            editable: false,
            type:'keyword',
            iconCls:'icon_keyword'
//            listeners:{
//                load: function(node){
//                    add_no_keyword_node(node)
//                    }
//                }
        });

var selmodel = new Ext.tree.DefaultSelectionModel({
    listeners:{
        selectionchange: function(sel, node){
            if(node == null )
                return
            if (node.getDepth() == 0){
                Ext.getCmp('search_field').reset()
                baseParams = {query: ''}
            }
        
            else{
                search_field = Ext.getCmp('search_field')
            path = node.getPath('text')+ '"'
            path = path.replace('/Root/', 'real_object:"')
            search_field.setValue(path)
            baseParams = {query:path}
        }

        set_query_on_store(baseParams)
        }
    }
});

var real_objects = new Ext.tree.TreePanel({
        // tree
        id:'real_objects',
        selModel: selmodel,
        animate:true,
        enableDD:true,
        containerScroll: true,
        ddGroup: 'organizerDD',
        // layout
        region:'west',
        width:200,
        split:true,
        // panel
        title:'Real Objects',
        autoScroll:true,
//        ddAppendOnly:true,
        margins: '5 0 5 5',
        loader: robject_loader,
        rootVisible: false,
        listeners:{
            render:function(){
                
                dd_target = new Ext.dd.DropTarget(this.getEl(),
                {ddGroup: 'organizerDD',
                    notifyOver: function( source, e, data ){
                        return this.dropNotAllowed
                        },
                    })
                
                this.getEl().on('contextmenu',
                function(e){                    
                    realObjectMenuShow(root_robjects,e)
                    })
                },
        },
        dropConfig:{
            ddGroup:'organizerDD',
            appendOnly: true,
            onNodeDrop: function( nodeData, source, e,data ){
                if (!nodeData.node.attributes.allowDrop)
                    return false
                if (data.nodes){
                    depth = nodeData.node.getDepth()
                    if(depth == 0 )
                        return false //not allowed to drop an item on the root or category
                    
                    media_tab = Ext.getCmp('media_tabs').getActiveTab()
                    view = media_tab. getComponent(0)
                    getSelectedIndexes = view.getSelectedIndexes()
                    items = []
                    for (i = 0; i<getSelectedIndexes.length; i++){
                        node_index = getSelectedIndexes[i]
                        item = view.getStore().getAt(node_index)
                        
                        if(item){                            
                            items.push(item.data.pk)
                        }
                        
                    }
                        Ext.Ajax.request({
                            url:'/add_items_to_real_object/',
                            params:{
                                items:items,
                                node:nodeData.node.attributes.id
                                }
                            })
                        return true
                    }
                    else if (data.node){

                        if (nodeData.node.id == source.dragData.node.id)
                            return false
                        if (source.dragData.node.contains(nodeData.node))
                            return false
                    }
            },
            
            onNodeOver: function( nodeData, source, e, data ) {
//                console.log('onNodeOver')
                
                if (data.node && source.dragData.node.contains(nodeData.node))
                        return false

                depth = nodeData.node.getDepth()
                if(data.nodes )
                    if (depth == 0 )
                        return this.dropNotAllowed//not allowed to drop an item on the root                
                
//                console.log(this.dropAllowed)
                if(nodeData.node.attributes.allowDrop)                    
                    return this.dropAllowed
                else
                    return this.dropNotAllowed
            }
     
    }
});
    
    real_objects.setRootNode(root_robjects);

    real_objects.on('contextmenu', realObjectMenuShow);
