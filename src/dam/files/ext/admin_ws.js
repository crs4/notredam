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

var open_fb_win = function()
{
	
	var currentTime = new Date()
	var month = currentTime.getMonth() + 1
	var day = currentTime.getDate()
	var year = currentTime.getFullYear()

    var form_items = [{
        fieldLabel: 'Name\'s file',
        xtype: 'textfield',
        id: 'name',
        value: day + "_" + month + "_" + year,
        width: 300
    }];
    
	var form = new Ext.form.FormPanel({
        frame: true,
        width : 500,
        height: 140,
        id: 'new_fb_form',
        region: 'center',
        labelWidth: 130,
        defaults: {
            width: 500,
            allowBlank: false
        },
        items: [{
            border: false,
            xtype:'fieldset',
            title: 'Insert file name',
            autoHeight:true,
            items: form_items
        }]
    });
    
    
    var panel = new Ext.Panel({
        layout      : 'border',
        items    : [form],
        width       : 520,
        height      : 140,
        buttons: [{
            text: 'Save',
            type: 'submit',
            handler: function(){
                if (Ext.getCmp('new_fb_form').form.isValid()){
                    Ext.getCmp('new_fb_form').getForm().submit({
                        params: {name: Ext.getCmp('new_fb_form').getForm().getFieldValues().name},
                        url: '/dam_admin/create_file_backup/',
                        success: function(data){
                        	close_my_win(Ext.getCmp('new_fb_form'));
                        	Ext.getCmp('backup_file_grid').store.reload();
                        	Ext.getCmp('del_sel').disable();
                        }
                    });

                }
            }
        },{
            text: 'Cancel',
            handler: function(){
                close_my_win(Ext.getCmp('new_fb_form'));
            }
            
        }]
    });
    var win = new Ext.Window({
        layout: 'fit',
        constrain: true,
        plain       : true,
        modal: true,
        title: 'Create file name',
        items    : [panel],
        resizable: false
        
    });
    win.show();
}    

var get_bk_panel = function(){

    var store_fb = new Ext.data.JsonStore({
        url: '/dam_admin/get_list_file_backup/',
        fields: ["file_name", 'data'],
        root: 'file_backup',
        autoLoad: true,
        sortInfo: {
            field: 'data',
            direction: 'ASC'
        }
    });
    
    var sme = new Ext.grid.CheckboxSelectionModel({
    	singleSelect : true,
    	listeners: {
    		rowselect : function() {
    			Ext.getCmp('del_sel').enable();
    		} 
    	}
    });
    
	var list = new Ext.Panel({
        title: 'Backup Notre DAM',
        layout: 'fit',
        id: 'bk_panel',
        viewConfig: {
         forceFit: true
        },
        items : [new Ext.grid.GridPanel({
            title: 'File backup',
            id: 'backup_file_grid',
            store: store_fb,
            enableHdMenu: false,
            sm : sme,
            listeners: {
                dblclick: function() {
                    rec_sel = this.getSelectionModel().getSelected();
    				window.open('/dam_admin/download_file_backup/'+rec_sel.data['file_name']);
                }
            },
            layout:'fit',
            frame: true,
            width: 400,
            height: 500,
            enableHdMenu: false,
            viewConfig: {
             forceFit: true
            }, 
            columns: [{
                header: 'file name',
                dataIndex: 'file_name'
            }, {
                header: 'data',
                dataIndex: 'data'
            }],
        })],
        bbar: [new Ext.PagingToolbar({
            id: 'paginator_backup_file',
            displayInfo: true,
            displayMsg: 'Displaying items {0} - {1} of {2}',
            emptyMsg: "No items to display",
            store: store_fb            
        }),{
            xtype: 'tbseparator' 
        },{
            text: 'Start new backup',
            iconCls: 'add_icon',
            id: 'str_bak',
            handler: function() {
	            open_fb_win();
            }},{
                xtype: 'tbseparator' 
            },{
                text: 'Delete selected backup',
                iconCls: 'clear_icon',
                id: 'del_sel',
                disabled: true,
                handler: function() {
            		rec_sel = Ext.getCmp('backup_file_grid').getSelectionModel().getSelected();
            		Ext.Ajax.request({
            			   url: '/dam_admin/delete_file_backup/',
            			   params: { 'filename': rec_sel.data['file_name'] },
            			   metod: 'POST',
            			   success: function(response) {
            				   if (Ext.decode(response.responseText)['success']){
            					   //reload store
            					   Ext.getCmp('backup_file_grid').store.reload();
            					   Ext.getCmp('del_sel').disable();
            				   }else{
            					   Ext.Msg.show({title:'Warning', msg: Ext.decode(response.responseText), width: 300,
  			        				   buttons: Ext.Msg.OK, icon: Ext.MessageBox.WARNING });
            				   }
            			   },
            			});
            	}},{
                    xtype: 'tbseparator' 
                }
        ]
    });        

    return list;
	
}
var get_ws_list = function() {
    var store = new Ext.data.JsonStore({
        url: '/dam_admin/get_workspaces/',
        fields: ["id", "ws", 'description', 'creator', 'creator_id'],
        root: 'elements',
        autoLoad: true,
        sortInfo: {
            field: 'ws',
            direction: 'ASC'
        }
    });

    var sm = get_list_selectionmodel(['remove_workspace_menuitem', 'edit_workspace_menuitem']);

    var list = new Ext.grid.GridPanel({
        title: 'Workspaces',
        store: store,
        layout: 'fit',
        id: 'workspaces_list',
        enableHdMenu: false,
        viewConfig: {
         forceFit: true
        }, 
        sm: sm, 
        listeners: {
            dblclick: function() {
                open_admin_editor(this.getId(), 'Workspace', open_ws_win);
            }
        },
        columns: [sm, {
            header: 'Name',
            dataIndex: 'ws'
        }, {
            header: 'Description',
            dataIndex: 'description'
        },{
            header: 'Creator',
            dataIndex: 'creator'
        }],
        bbar: [{
            text: 'Add',
            iconCls: 'add_icon',
            handler: function() {
                var ws = undefined;
                open_ws_win(ws);
            }
        }, {
            text: 'Remove',
            iconCls: 'clear_icon',
            id: 'remove_workspace_menuitem',
            disabled: true,
            handler: function() {
                var my_grid = this.findParentByType('grid');

                remove_from_list(my_grid.getId(), '/dam_admin/delete_ws/', 'Remove Workspace', 'Workspace(s) removed successfully.');
            }
        }, {
            text: 'Edit',
            iconCls: 'edit_icon',
            id: 'edit_workspace_menuitem',
            disabled: true,
            handler: function() {
                var my_grid = this.findParentByType('grid');            
                open_admin_editor(my_grid.getId(), 'Workspace', open_ws_win);
            }
        }]
    });        

    return list;

};

var open_ws_win = function(current) {

    var win_title, submit_url, id, name, description, creator, success_msg;

    if (!current) {
        win_title = 'Add Workspace';
        submit_url = '/dam_admin/save_ws/';
        id = 0;
        name = 'newWorkspace';
        description = '';
        creator = '';
        success_msg = 'Workspace added successfully.';
    }
    else {
        win_title = 'Edit Workspace';
        submit_url = '/dam_admin/save_ws/';
        id = current.get('id');
        name = current.get('ws');
        description = current.get('description');
        creator = current.get('creator_id');
        success_msg = 'Workspace edited successfully.';
    }
    
    var users_store = new Ext.data.JsonStore({
        url: '/dam_admin/get_user_list/',
        fields: ["id", "name"],
        root: 'elements',
        autoLoad: true,
        sortInfo: {
            field: 'name',
            direction: 'ASC'
        }, 
        listeners: {
            load: function() {
                Ext.getCmp('creator_field').setValue(creator);                
            }
        }
    });    
    
    var form_items = [{
            fieldLabel: 'Name',
            xtype: 'textfield',
            id: 'name',
            value: name,
            width: 300
        }, {
            fieldLabel: 'Description',
            name: 'description',
            xtype: 'textarea',
            allowBlank: true,
            value: description,
            width: 300
        },{
            fieldLabel: 'Creator',
            xtype: 'combo',
            id: 'creator_field',
            hiddenName: 'creator',
            emptyText: 'Choose User...',
            store: users_store,
            valueField: 'id',
            displayField: 'name',
            triggerAction: 'all',
            lazyRender:true,
            mode: 'local',
            width: 300
        }];
        
    var user_store = new Ext.data.JsonStore({
        root: "elements",
        fields: ["id", "username", "permissions", "groups"],
        url: '/dam_admin/get_ws_users/',
        baseParams: {id: id},
        autoLoad: true,
        sortInfo: {
            field: 'username',
            direction: 'ASC'
        }
    });

    var group_store = new Ext.data.JsonStore({
        root: "elements",
        fields: ["id", "group", "permissions", "users"],
        url: '/dam_admin/get_ws_groups/',
        baseParams: {id: id},
        autoLoad: true,
        sortInfo: {
            field: 'group',
            direction: 'ASC'
        }
    });

    var user_sm = get_list_selectionmodel(['remove_wsuser_menuitem', 'edit_wsuser_menuitem']);

    var user_list = new Ext.grid.GridPanel({
        title: 'Users',
        store: user_store,
        layout: 'fit',
        frame: true,
        width: 500,
        height: 230,
        enableHdMenu: false,
        viewConfig: {
         forceFit: true
        }, 
        sm: user_sm, 
        listeners: {
            dblclick: function() {
                open_admin_multiple_editor(this.getId(), 'Workspace', open_ws_user_win, [this.getStore(), group_store]);
            }
        },
        columns: [user_sm, {
            header: 'User',
            dataIndex: 'username'
        }, {
            header: 'Permissions',
            dataIndex: 'permissions',
            renderer: list_renderer
        }, {
            header: 'Groups',
            dataIndex: 'groups',
            renderer: list_renderer
        }],
        bbar: [{
            text: 'Add',
            iconCls: 'add_icon',
            handler: function() {
                var my_grid = this.findParentByType('grid');
                var obj = undefined;
                open_ws_user_win(obj, [my_grid.getStore(), group_store]);
            }
        }, {
            text: 'Remove',
            iconCls: 'clear_icon',
            id: 'remove_wsuser_menuitem',
            disabled: true,
            handler: function() {
                var my_grid = this.findParentByType('grid');
                var selections = my_grid.getSelectionModel().getSelections();
                for (var x=0; x < selections.length; x++) {
                    my_grid.getStore().remove(selections[x]);
                }
            }
        }, {
            text: 'Edit',
            iconCls: 'edit_icon',
            id: 'edit_wsuser_menuitem',
            disabled: true,
            handler: function() {
                var my_grid = this.findParentByType('grid');
                open_admin_multiple_editor(my_grid.getId(), 'Workspace', open_ws_user_win, [my_grid.getStore(), group_store]);

            }
        }]
    });

    var group_sm = get_list_selectionmodel(['remove_wsgroup_menuitem', 'edit_wsgroup_menuitem']);

    var group_list = new Ext.grid.GridPanel({
        title: 'Groups',
        store: group_store,
        layout: 'fit',
        frame: true,
        enableHdMenu: false,
        viewConfig: {
         forceFit: true
        }, 
        sm: group_sm, 
        listeners: {
            dblclick: function() {
                open_admin_multiple_editor(this.getId(), 'Workspace Group', open_ws_group_win);
            }
        },
        columns: [group_sm, {
            header: 'Group',
            dataIndex: 'group'
        }, {
            header: 'Permissions',
            dataIndex: 'permissions',
            renderer: list_renderer
        }],
        bbar: [{
            text: 'Add',
            iconCls: 'add_icon',
            handler: function() {
                var my_grid = this.findParentByType('grid');
                var obj = undefined;
                open_ws_group_win(obj, my_grid.getStore());
            }
        }, {
            text: 'Remove',
            iconCls: 'clear_icon',
            id: 'remove_wsgroup_menuitem',
            disabled: true,
            handler: function() {
                var my_grid = this.findParentByType('grid');
                var selections = my_grid.getSelectionModel().getSelections();
                for (var x=0; x < selections.length; x++) {
                    my_grid.getStore().remove(selections[x]);
                }
            }
        }, {
            text: 'Edit',
            iconCls: 'edit_icon',
            id: 'edit_wsgroup_menuitem',
            disabled: true,
            handler: function() {
                var my_grid = this.findParentByType('grid');
                open_admin_multiple_editor(my_grid.getId(), 'Workspace', open_ws_group_win, my_grid.getStore());

            }
        }]
    });
    
    var permissions = new Ext.TabPanel({
        activeTab: 0,
        width: 500,
        height: 230,
        items: [user_list, group_list]
    });
    
    var form = new Ext.form.FormPanel({
        frame: true,
        width : 500,
        height: 450,
        id: 'new_ws_form',
        region: 'center',
        labelWidth: 130,
        defaults: {
            width: 500,
            allowBlank: false
        },
        items: [{
            border: false,
            xtype:'fieldset',
            title: 'Workspace Information',
            autoHeight:true,
            items: form_items
        }, permissions]
    });
    
    
    var panel = new Ext.Panel({
        layout      : 'border',
        items    : [form],
        width       : 520,
        height      : 450,
        buttons: [{
            text: 'Save',
            type: 'submit',
            handler: function(){
                if (Ext.getCmp('new_ws_form').form.isValid()){

                    var permissions = [];
                    var groups = [];
                    
                    for (var x=0; x < user_store.getCount(); x++) {
                        var r = user_store.getAt(x);
                        permissions.push({id:r.get('id'), permissions: r.get('permissions')});
                    }

                    for (var x=0; x < group_store.getCount(); x++) {
                        var r = group_store.getAt(x);
                        groups.push({name:r.get('group'), permissions: r.get('permissions'), users: r.get('users')});
                    }
                    
                    var my_obj = this;
                    
                    Ext.getCmp('new_ws_form').getForm().submit({
                        params: {id: id, permissions: Ext.encode(permissions), groups: Ext.encode(groups)},
                        url: submit_url,
                        success: function(data){
                            Ext.getCmp('workspaces_list').getStore().reload();
                            Ext.MessageBox.alert(win_title, success_msg);
                            close_my_win(my_obj);
                        }
                    });

                }
            }
        },{
            text: 'Cancel',
            handler: function(){
                close_my_win(this);
            }
            
        }]
    });
    var win = new Ext.Window({
        layout: 'fit',
        constrain: true,
        plain       : true,
        modal: true,
        title: win_title,
        items    : [panel],
        resizable: false
        
    });
    win.show();
    
};

var open_ws_user_win = function(current, my_stores) {

    var custom_store, group_store;
    var user_group_list;

    if (my_stores) {
        custom_store = my_stores[0];
        group_store = my_stores[1];
    }
    
    var myRecord = Ext.data.Record.create([
        {name: 'id'},
        {name: 'username'},
        {name: 'permissions'},
        {name: 'groups'}
    ]);

    var win_title = 'Edit Membership';
    
    var default_perms = {admin: false, edit_metadata: false, edit_collection: false, edit_taxonomy: false, add_item: false, remove_item:false };
    
    if (current) {
        if (!current.length) {
            current = [current];
        }
        if (current.length == 1) {
            var perms = current[0].get('permissions');
            for (var x=0; x < perms.length; x++) {
                default_perms[perms[x]] = true;
            }
        }
    }

    var store = new Ext.data.JsonStore({
        url: '/dam_admin/get_user_list/',
        fields: ["id", "name"],
        root: 'elements',
        autoLoad: true,
        sortInfo: {
            field: 'name',
            direction: 'ASC'
        },
        listeners: {
            load: function() {
                var current_selected_store = custom_store;
                var selected_ids = [];
                var to_remove = [];

                if (!current) {
                    for (var x=0; x < current_selected_store.getCount(); x++) {
                        var r = current_selected_store.getAt(x);
                        selected_ids.push(r.get('id'));
                    }
                    this.each(function(r) {
                        var my_id = r.get('id');
                        for (var x=0; x < selected_ids.length; x++) {
                            if (selected_ids[x] == my_id) {
                                to_remove.push(r);
                            }
                        }
                    });
                }
                else {
                    this.each(function(r) {
                        var my_id = r.get('id');
                        to_remove.push(r);
                        for (var x=0; x < current.length; x++) {
                            if (current[x].get('id') == my_id) {
                                to_remove.pop();
                            }
                        }
                    });
                }
                for (var x=0; x < to_remove.length; x++) {
                    this.remove(to_remove[x]);
                }
//                 if (current) {                
//                     var ws_grid = Ext.getCmp('user_ws_list');
//                     ws_grid.getSelectionModel().selectAll();
//                 }
            }
        }
    });

    if (!current) {
    
        var sm = get_list_selectionmodel(['add_membership_button']);

        var list = new Ext.grid.GridPanel({
            store: store,
            layout: 'fit',
            frame: true,
            id: 'user_ws_list',
            width: 300,
            height: 70,
            hideHeaders: true,
            viewConfig: {
             forceFit: true
            }, 
            sm: sm, 
            columns: [sm, {
                header: 'User',
                dataIndex: 'name'
            }]
           
        });
    }
    else {
    
        var list = new Ext.grid.GridPanel({
            store: store,
            layout: 'fit',
            frame: true,
            hidden: true,
            id: 'user_ws_list',
            width: 300,
            height: 70,
            hideHeaders: true,
            viewConfig: {
             forceFit: true
            }, 
            columns: [{
                header: 'User',
                dataIndex: 'name'
            }]
           
        });            
    }

    var perm_items = [{
        boxLabel: 'Is Admin?',
        name: 'admin',
        id: 'perm_admin',
        checked: default_perms['admin']
    }, {
        boxLabel: 'Can add items?',
        name: 'add_item',
        id: 'perm_add_item',
        checked: default_perms['add_item']        
    },{
        boxLabel: 'Can remove items?',
        name: 'remove_item',
        id: 'perm_remove_item',
        checked: default_perms['remove_item']
    }, {
        boxLabel: 'Can edit metadata?',
        name: 'edit_metadata',
        id: 'perm_edit_metadata',
        checked: default_perms['edit_metadata']
    }, {
        boxLabel: 'Can edit keywords?',
        name: 'edit_taxonomy',
        id: 'perm_edit_taxonomy',
        checked: default_perms['edit_taxonomy']
    }, {
        boxLabel: 'Can add collections?',
        name: 'edit_collection',
        id: 'perm_edit_collection',
        checked: default_perms['edit_collection']                
    }];

    var form_height = 0;
            
    if (group_store.getCount() > 0) {

        var group_sm = new Ext.grid.CheckboxSelectionModel({
            listeners: {
                selectionchange: function() {
                    
                    for (var perm in default_perms) {
                        var checkbox = Ext.getCmp('perm_' + perm);
                        checkbox.enable();
                    }
                    
                    var selections = this.getSelections();
                    for (var x=0; x < selections.length; x++) {
                        var r = selections[x];
                        var r_permissions = r.get('permissions');
                        for (var y=0; y < r_permissions.length; y++) {
                            var perm = r_permissions[y];
                            var checkbox = Ext.getCmp('perm_' + perm);
                            checkbox.disable();
                            checkbox.setValue(true);                        
                        }
                    }
                }
            }
        });

        form_height += 300;

        user_group_list = new Ext.grid.GridPanel({
            title: 'Groups',
            store: group_store,
            layout: 'fit',
            frame: true,
            height: 150,
            plain: false,
            hideHeaders: true,
            viewConfig: {
                forceFit: true,
                afterRender: function(){
                    this.constructor.prototype.afterRender.call(this);

                    if (current) {
                        if (current.length == 1) {
                            var user = current[0].get('id');
                            var group_to_select = [];
                            var my_grid = this.grid;
                            group_store.each(function(){
                                var r = this;
                                var r_users = r.get('users');
                                for (var x=0; x < r_users.length; x++) {
                                    if (r_users[x] == user) {
                                        group_to_select.push(r);
                                        break;
                                    }
                                }
                            });
                            user_group_list.getSelectionModel().selectRecords(group_to_select);
                        }
                    }        
                }
            }, 
            sm: group_sm, 
            columns: [group_sm, {
                header: 'Group',
                dataIndex: 'group'
            }, {
                header: 'Permissions',
                dataIndex: 'permissions',
                renderer: list_renderer
            }]
        });
    
//         var permission_form = {
//             xtype:'tabpanel',
//             plain: true,
//             activeTab: 0,
//             height: 150,
//             width : 300,
//             deferredRender: false,
//             defaults:{bodyStyle:'padding:10px'},
//             items: [user_group_list, {
//                 layout:'form',
//                 title: 'Permissions',
//                 autoHeight:true,
//                 items: [{
//                     xtype:'checkboxgroup',
//                     columns: 2,
//                     items: form_items,
//                 }]
//             }]
//         };

        var permission_form = {
            border: false,
            xtype:'fieldset',
            title: 'Choose groups/permissions',
            autoHeight:true,
            items: [user_group_list, {
                border: false,
                xtype:'fieldset',
                title: 'Permissions',
                autoHeight:true,
                items: [{
                    xtype:'checkboxgroup',
                    columns: 2,
                    items: perm_items
                }]
            }]
        };
            
    }
    else {

        form_height += 130;
            
        var permission_form = {
            border: false,
            xtype:'fieldset',
            title: 'Permissions',
            autoHeight:true,
            items: [{
                xtype:'checkboxgroup',
                columns: 2,
                items: perm_items
            }]
        };

    }

    if (current) { 

        var form_items = [permission_form];
    
    }
    else {

        form_height += 70;

        var form_items = {
            border: false,
            xtype:'fieldset',
            title: 'Select users and permissions',
            autoHeight:true,
            items: [list, permission_form]
        };
    
    }
        
    var form = new Ext.form.FormPanel({
        frame: true,
        width : 300,
        autoHeight: true,
        id: 'new_user_ws_form',
        region: 'center',
        defaultType: 'checkbox',
        defaults: {
            allowBlank: true
        },
        labelWidth: 10,
        items: form_items
    });
    
    
    var panel = new Ext.Panel({
        layout      : 'border',
        items    : [form],
        width       : 350,
        height      : form_height + 50,
        buttons: [{
            text: 'OK',
            type: 'submit',
            disabled: current === undefined,            
            id: 'add_membership_button',
            handler: function(){

                var ws_grid = Ext.getCmp('user_ws_list');
                var selections = ws_grid.getSelectionModel().getSelections();

                for (var perm in default_perms) {
                    var checkbox = Ext.getCmp('perm_' + perm);
                    checkbox.enable();
                }

                var permissions = Ext.getCmp('new_user_ws_form').getForm().getValues();
                var list_perms = [];
                var list_groups = [];
                
                for (var p in permissions) {
                    list_perms.push(p);
                }
                
                var current_selected_store = custom_store;

                if (group_store.getCount() > 0) {
                    var selected_groups = user_group_list.getSelectionModel().getSelections();
                    for (var x = 0; x < selected_groups.length; x++) {
                        var r = selected_groups[x];
                        list_groups.push(r);
                    }
                }

                if (!current) {

                    for (var x=0; x < selections.length; x++) {
                        var my_groups = [];
                        for (var y=0; y < list_groups.length; y++) {
                            var r_g = list_groups[y];
                            var g_users = r_g.get('users');
                            g_users.push(selections[x].get('id'));
                            r_g.set('users', g_users);
                            my_groups.push(r_g.get('group'));
                        }
                        var r = new myRecord({id: selections[x].get('id'), username: selections[x].get('name'), permissions: list_perms, groups: my_groups});
                        current_selected_store.add(r, true);
                    }

                }
                else {
                    
                    group_store.each(function() {
                        var r = this;
                        var users = r.get('users');
                        var index_to_remove = [];
                        for (var x=0; x < current.length; x++ ) {
                            for (var y=0; y < users.length; y++ ) {
                                if (users[y] == current[x].get('id')) {
                                    users.splice(y, 1);
                                    break;
                                }
                            }
                        }
                        r.set('users', users);
                    });
                    
                    for (var x=0; x < current.length; x++ ) {
                        current[x].set('permissions', list_perms);
                        var my_groups = [];
                        for (var y=0; y < list_groups.length; y++) {
                            var r_g = list_groups[y];
                            var g_users = r_g.get('users');
                            g_users.push(current[x].get('id'));
                            r_g.set('users', g_users);
                            my_groups.push(r_g.get('group'));
                        }
                        current[x].set('groups', my_groups);
                        current[x].commit();
                    }
                }

                close_my_win(this);

            }
        },{
            text: 'Cancel',
            handler: function(){
                close_my_win(this);
            }
            
        }]
    });
    var win = new Ext.Window({
        layout: 'fit',
        constrain: true,
        plain       : true,
        modal: true,
        title: win_title,
        items    : [panel],
        resizable: false
        
    });
    win.show();
    
};

var open_ws_group_win = function(current, custom_store) {

    var myRecord = Ext.data.Record.create([
        {name: 'id'},
        {name: 'group'},
        {name: 'permissions'},
        {name: 'users'} 
    ]);

    var win_title = 'Edit Group';
    
    var default_perms = {admin: false, edit_metadata: false, edit_collection: false, edit_taxonomy: false, add_item: false, remove_item:false };
    
    var group_name, group_users, group_perms;
    
    if (current) {
        if (!current.length) {
            current = [current];
        }
        group_name = current[0].get('group');
        group_users = current[0].get('users');
        group_perms = current[0].get('permissions');
        for (var x=0; x < group_perms.length; x++) {
            default_perms[group_perms[x]] = true;
        }
    }
    else {
        group_name = '';
        group_users = [];
    }

    var form_items = [{
        xtype:'checkboxgroup',
        columns: 2,
        fieldLabel: 'Permissions',
        items: [{
            fieldLabel: 'Is Admin?',
            name: 'admin',
            checked: default_perms['admin']
        }, {
            fieldLabel: 'Can add items?',
            name: 'add_item',
            checked: default_perms['add_item']        
        },{
            fieldLabel: 'Can remove items?',
            name: 'remove_item',
            checked: default_perms['remove_item']
        }, {
            fieldLabel: 'Can edit metadata?',
            name: 'edit_metadata',
            checked: default_perms['edit_metadata']
        }, {
            fieldLabel: 'Can edit keywords?',
            name: 'edit_taxonomy',
            checked: default_perms['edit_taxonomy']
        }, {
            fieldLabel: 'Can add collections?',
            name: 'edit_collection',
            checked: default_perms['edit_collection']                
        }]
    }];
        
    var group_name_field = {
        fieldLabel: 'Group name',
        id: 'new_group_name',
        xtype: 'textfield',
        allowBlank: false,
        value: group_name
    };    
        
    if (current) {
        if (current.length == 1) {                        
            form_items.splice(0, 0, group_name_field);
        }
    }
    else {
        form_items.splice(0, 0, group_name_field);
    }
                
    var form = new Ext.form.FormPanel({
        frame: true,
        width : 400,
        height: 200,
        id: 'new_group_form',
        region: 'center',
        defaultType: 'checkbox',
        defaults: {
            allowBlank: true
        },
        items: [
            form_items
        ]
    });
    
    
    var panel = new Ext.Panel({
        layout      : 'border',
        items    : [form],
        width       : 450,
        height      : 200,
        buttons: [{
            text: 'OK',
            type: 'submit',
            handler: function(){

                var permissions = Ext.getCmp('new_group_form').getForm().getValues();
                var list_perms = [];
                
                for (var p in permissions) {
                    if (p != 'new_group_name') {
                        list_perms.push(p);
                    }
                }
                
                var current_selected_store = custom_store;

                if (!current) {

                    var group_name = Ext.getCmp('new_group_name').getValue();

                    var r = new myRecord({group: group_name, permissions: list_perms, users: group_users});
                    custom_store.add(r, true);

                }
                else {
                    for (var x=0; x < current.length; x++ ) {
                        if (current.length == 1) {
                            var group_name = Ext.getCmp('new_group_name').getValue();                    
                            current[x].set('group', group_name);
                        }
                        current[x].set('permissions', list_perms);
                        current[x].commit();
                    }
                }

                close_my_win(this);

            }
        },{
            text: 'Cancel',
            handler: function(){
                close_my_win(this);
            }
            
        }]
    });
    var win = new Ext.Window({
        layout: 'fit',
        constrain: true,
        plain       : true,
        modal: true,
        title: win_title,
        items    : [panel],
        resizable: false
        
    });
    win.show();
    
};
