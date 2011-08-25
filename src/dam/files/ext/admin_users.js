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

var get_user_list = function() {
    var store = new Ext.data.JsonStore({
        autoDestroy: true,
        url: '/dam_admin/get_user_list/',
        fields: ["id", "name", 'is_staff', 'is_superuser', 'last_login', 'date_joined', 'is_active', 'email', 'first_name', 'last_name'],
        root: 'elements',
        autoLoad: true,
        sortInfo: {
            field: 'name',
            direction: 'ASC'
        }
    });

    var sm = get_list_selectionmodel(['remove_user_menuitem', 'edit_user_menuitem']);

    var list = new Ext.grid.GridPanel({
        title: 'Users',
        store: store,
        layout: 'fit',
        id: 'users_list',
        enableHdMenu: false,
        viewConfig: {
         forceFit: true
        }, 
        sm: sm, 
        listeners: {
            dblclick: function() {
                open_admin_editor(this.getId(), 'User', open_user_win);
            }
        },
        columns: [sm, {
            header: 'UserName',
            dataIndex: 'name'
        }, {
            header: 'Active account',
            dataIndex: 'is_active',
            renderer: bool_renderer
        },{
            header: 'Administrator',
            dataIndex: 'is_staff',
            renderer: bool_renderer
        }, {
            header: 'First name',
            dataIndex: 'first_name'
        }, {
            header: 'Last name',
            dataIndex: 'last_name'
        }, 
        {
            header: 'Email',
            dataIndex: 'email'
        },
        {
            header: 'Created on',
            dataIndex: 'date_joined'
        },
        {
            header: 'Last login',
            dataIndex: 'last_login'
        }
        
        ],
        bbar: [{
            text: 'Add',
            iconCls: 'add_icon',
            handler: function() {
                var user = undefined;
                open_user_win(user);
            }
        }, {
            text: 'Remove',
            iconCls: 'clear_icon',
            id: 'remove_user_menuitem',
            disabled: true,
            handler: function() {
                Ext.Msg.confirm('User Deletion', 'User deletion cannot be undone, do you want to proceed?', 
                function(){
                    remove_from_list('users_list', '/dam_admin/delete_user/', 'Remove User', 'User(s) removed successfully.');
                });
                
            }
        }, {
            text: 'Edit',
            iconCls: 'edit_icon',
            id: 'edit_user_menuitem',
            disabled: true,
            handler: function() {
                open_admin_editor('users_list', 'User', open_user_win);
            }
        }]
    });        

    return list;

};

var get_groups_and_open = function(current, store) {
    if (current) {
        if (!current.length) {

            var ws_id = current.get('id');

            var group_store = new Ext.data.JsonStore({
                root: "elements",
                fields: ["id", "group", "permissions", "users"],
                url: '/dam_admin/get_ws_groups/',
                baseParams: {id: ws_id},
                autoLoad: true,
                sortInfo: {
                    field: 'group',
                    direction: 'ASC'
                },
                listeners: {
                    load: function() {
                        open_user_ws_win(current, [store, this]);                    
                    }
                }
            });
        
        }
        else {
            open_user_ws_win(current, [store, undefined]);
        }
    }
    else {
        open_user_ws_win(current, [store, undefined]);
    }
    
};

var open_user_ws_win = function(current, my_stores) {

    var group_store, custom_store;
    var x;

    if (my_stores) {
        custom_store = my_stores[0];
        group_store = my_stores[1];
    }

    var myRecord = Ext.data.Record.create([
        {name: 'id'},
        {name: 'ws'},
        {name: 'permissions'},
        {name: 'groups'}
    ]);
    
    var win_title = 'Edit Membership';
    
    var default_perms = {admin: false, edit_metadata: false,  edit_taxonomy: false, add_item: false, remove_item:false };
    
    if (current) {
        if (!current.length) {
            current = [current];
        }
        if (current.length == 1) {

            var perms = current[0].get('permissions');
            for (x=0; x < perms.length; x++) {
                default_perms[perms[x]] = true;
            }
        }
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
    }];

    var form_height = 0;
    var permission_form;

    if (!current) {

        var store = new Ext.data.JsonStore({
            autoDestroy: true,
            url: '/dam_admin/get_workspaces/',
            fields: ["id", "ws"],
            root: 'elements',
            autoLoad: true,
            sortInfo: {
                field: 'ws',
                direction: 'ASC'
            },
            listeners: {
                load: function() {
                    var current_selected_store = custom_store;
                    var selected_ids = [];
                    var to_remove = [];
    
                    if (!current) {
                        for (x=0; x < current_selected_store.getCount(); x++) {
                            var r = current_selected_store.getAt(x);
                            selected_ids.push(r.get('id'));
                        }
                        this.each(function(r) {
                            var my_id = r.get('id');
                            for (x=0; x < selected_ids.length; x++) {
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
                            for (x=0; x < current.length; x++) {
                                if (current[x].get('id') == my_id) {
                                    to_remove.pop();
                                }
                            }
                        });
                    }
                    for (x=0; x < to_remove.length; x++) {
                        this.remove(to_remove[x]);
                    }
    //                 if (current) {                
    //                     var ws_grid = Ext.getCmp('user_ws_list');
    //                     ws_grid.getSelectionModel().selectAll();
    //                 }
                    if (this.getCount() === 0) {
                        Ext.MessageBox.alert('Error', 'No more workspaces available');                    
                    }
                }
            }
        });

        var sm = get_list_selectionmodel(['add_membership_button']);

        var list = new Ext.grid.GridPanel({
            title: 'Select workspaces',
            store: store,
            layout: 'fit',
            frame: true,
            id: 'user_ws_list',
            width: 300,
            height: 120,
//            enableHdMenu: false,
            hideHeaders: true,
            viewConfig: {
             forceFit: true
            }, 
            sm: sm, 
            columns: [sm, {
                header: 'Workspace',
                dataIndex: 'ws'
            }]
           
        });
        
        form_height += 250;

        permission_form = {
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

        var form_items = [{
            border: false,
            xtype:'fieldset',
            title: 'Select users and permissions',
            autoHeight:true,
            items: [list, permission_form]
        }];
    
    }

    if (current) {

        if (current.length == 1) {

            if (group_store.getCount() > 0) {

                var group_sm = new Ext.grid.CheckboxSelectionModel({
                    listeners: {
                        selectionchange: function() {
                            
                            var perm, checkbox;
                            
                            for (perm in default_perms) {
                                checkbox = Ext.getCmp('perm_' + perm);
                                checkbox.enable();
                            }
                            
                            var selections = this.getSelections();
                            for (var x=0; x < selections.length; x++) {
                                var r = selections[x];
                                var r_permissions = r.get('permissions');
                                for (var y=0; y < r_permissions.length; y++) {
                                    perm = r_permissions[y];
                                    checkbox = Ext.getCmp('perm_' + perm);
                                    checkbox.disable();
                                    checkbox.setValue(true);                        
                                }
                            }
                        }
                    }
                });
        
                form_height += 300;
        
                var user_group_list = new Ext.grid.GridPanel({
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
                                    var groups = current[0].get('group_ids');
                                    var group_to_select = [];
                                    group_store.each(function(){
                                        var r = this;
                                        var my_id = r.get('id');
                                        for (var x=0; x < groups.length; x++) {
                                            if (groups[x] == my_id) {
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
    
                permission_form = {
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
                    
                permission_form = {
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

        }            
        else {
    
            form_height += 130;
                
            permission_form = {
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

        var form_items = [permission_form];

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

                for (var perm in default_perms) {
                    var checkbox = Ext.getCmp('perm_' + perm);
                    checkbox.enable();
                }

                var permissions = Ext.getCmp('new_user_ws_form').getForm().getValues();
                var list_perms = [];
                var list_groups = [];
                var list_group_ids = [];
                
                for (var p in permissions) {
                    if (p) {
                        list_perms.push(p);
                    }
                }
                
                var current_selected_store = custom_store;

                if (!current) {

                    var ws_grid = Ext.getCmp('user_ws_list');
                    var selections = ws_grid.getSelectionModel().getSelections();

                    for (var x=0; x < selections.length; x++) {
                        var r = new myRecord({id: selections[x].get('id'), ws: selections[x].get('ws'), permissions: list_perms, groups: list_groups, group_ids: list_group_ids});
                        current_selected_store.add(r, true);
                    }

                }
                else {
                    if (current.length == 1) {
                        if (group_store.getCount() > 0) {
                            var selected_groups = user_group_list.getSelectionModel().getSelections();
                            for (x = 0; x < selected_groups.length; x++) {
                                var r = selected_groups[x];
                                list_groups.push(r.get('group'));
                                list_group_ids.push(r.get('id'));
                            }
                        }
                    }
                    for (var x=0; x < current.length; x++ ) {
                        current[x].set('permissions', list_perms);
                        current[x].set('groups', list_groups);
                        current[x].set('group_ids', list_group_ids);
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
        id: 'user_ws_win',
        items    : [panel],
        resizable: false
        
    });
    win.show();
};

var open_user_win = function(current, custom_store) {

    Ext.apply(Ext.form.VTypes, {
    
        password : function(val, field) {
            if (field.initialPassField) {
                var pwd = Ext.getCmp(field.initialPassField);
                return (val == pwd.getValue());
            }
            return true;
        },
    
        passwordText : 'Passwords do not match'
    });

    var win_title, submit_url, id, name, pwd, first_name, last_name, email, success_msg;

    if (!current) {
        win_title = 'Add User';
        submit_url = '/dam_admin/save_user/';
        id = 0;
        name = 'newUserName';
        pwd = '';
        first_name = '';
        last_name = '';
        email = 'email@domain.com';
        success_msg = 'User added successfully.';
    }
    else {
        win_title = 'User account editor';
        submit_url = '/dam_admin/save_user/';
        id = current.get('id');
        name = current.get('name');
        pwd = '';
        first_name = current.get('first_name');
        last_name = current.get('last_name');
        email = current.get('email');
        success_msg = 'User edited successfully.';
    }
    
    var form_items = [{
            fieldLabel: 'Username',
            xtype: 'textfield',
            id: 'username',
            allowBlank: false,
            value: name,
            width: 300
        }, {
            fieldLabel: 'First name',
            name: 'first_name',
            xtype: 'textfield',
            allowBlank: true,           
            value: first_name,
            width: 300
        },{
            fieldLabel: 'Last name',
            xtype: 'textfield',
            name: 'last_name',
            allowBlank: true,
            value: last_name,
            width: 300
        }, {
            fieldLabel: 'Email',
            xtype: 'textfield',
            allowBlank: false,
            name: 'email',
            vtype:'email',
            value: email,
            width: 300    
        }];

    if (!current) {
        form_items.push({
            fieldLabel: 'New Password',
            xtype: 'textfield',
            id: 'pwd',
            value: pwd,
            inputType: 'password',
            vtype: 'password',
            width: 300
        });
        form_items.push({
            fieldLabel: 'Confirm Password',
            xtype: 'textfield',
            id: 'pass-cfrm',
            vtype: 'password',
            initialPassField: 'pwd',
            inputType: 'password',
            width: 300       
        });
//         form_items.push({
//             fieldLabel: 'Create workspace',
//             xtype: 'checkbox',
//             id: 'create_ws',
//             checked: true
//         });        
    }
        
    var store = new Ext.data.JsonStore({
        autoDestroy: true,
        root: "elements",
        fields: ["id", "ws", "permissions", "groups", "group_ids"],
        url: '/dam_admin/get_user_permissions/',
        baseParams: {id: id},
        autoLoad: true,
        sortInfo: {
            field: 'ws',
            direction: 'ASC'
        }
    });

    var sm = get_list_selectionmodel(['remove_ws_menuitem', 'edit_ws_menuitem']);

    var list = new Ext.grid.GridPanel({
        title: 'Workspaces and permissions',
        store: store,
        layout: 'fit',
        frame: true,
        width: 500,
        height: 230,
        enableHdMenu: false,
        viewConfig: {
         forceFit: true
        }, 
        sm: sm, 
        listeners: {
            dblclick: function() {
                open_admin_editor(this.getId(), 'Workspace', get_groups_and_open, this.getStore());
            }
        },
        columns: [sm, {
            header: 'Workspace',
            dataIndex: 'ws'
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
                var obj = undefined;
                var my_grid = this.findParentByType('grid');
                open_user_ws_win(obj, [my_grid.getStore(), undefined]);
            }
        }, {
            text: 'Remove',
            iconCls: 'clear_icon',
            id: 'remove_ws_menuitem',
            disabled: true,
            handler: function() {
                var my_grid = this.findParentByType('grid');
                var selections = my_grid.getSelectionModel().getSelections();
                for (var x=0; x < selections.length; x++) {
                    store.remove(selections[x]);
                }
            }
        }, {
            text: 'Edit',
            iconCls: 'edit_icon',
            id: 'edit_ws_menuitem',
            disabled: true,
            handler: function() {
                var my_grid = this.findParentByType('grid');
                open_admin_editor(my_grid.getId(), 'Workspace', get_groups_and_open, my_grid.getStore());
            }
        }]
    });
        
    var form = new Ext.form.FormPanel({
        frame: true,
        width : 500,
        height: 450,
        id: 'new_user_form',
        region: 'center',
        labelWidth: 130,
        defaults: {
            width: 500,
            allowBlank: false
        },
        items: [{
            border: false,
            xtype:'fieldset',
            title: 'User Information',
            autoHeight:true,
            items: form_items
        }, list]
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
                if (Ext.getCmp('new_user_form').form.isValid()){

                    var permissions = [];

                    var perm_store = list.getStore();
                    
                    for (var x=0; x < perm_store.getCount(); x++) {
                        var r = perm_store.getAt(x);
                        permissions.push({id:r.get('id'), permissions: r.get('permissions'), groups: r.get('group_ids')});
                    }

                    var my_obj = this;

                    Ext.getCmp('new_user_form').getForm().submit({
                        params: {id: id, permissions: Ext.encode(permissions)},
                        url: submit_url,
                        success: function(data){
                            Ext.getCmp('users_list').getStore().reload();
                            Ext.MessageBox.alert(win_title, success_msg);
                            close_my_win(my_obj);
                        },
                        failure: function(data){ 
                            Ext.getCmp('users_list').getStore().reload();
                            Ext.MessageBox.alert(win_title, 'Duplicate User. Impossibible add the new user.');
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



