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

var bool_renderer = function status(val){
    if (val){
        return '<div style="width:16px; height:16px; background: transparent url(/files/images/icons/fam/tick.png) no-repeat center !important;"></div>';
    }else {
        return '<div></div>';
    }
    return val;
};

var perform_demo_action = function(list_id, url, win_title, win_desc) {
    var selections = Ext.getCmp(list_id).getSelectionModel().getSelections();
    var selected_ids = [];
    for (var x=0; x < selections.length; x++) {
        selected_ids.push(selections[x].get('id'));
    }
    Ext.Ajax.request({
        url: url,
        params: {obj_list: Ext.encode(selected_ids)},
        success: function(data){
            Ext.getCmp(list_id).getStore().reload();
            Ext.MessageBox.alert(win_title, win_desc);
        }
    });                        
};

var get_list_selectionmodel = function(menu_items) {
    var sm = new Ext.grid.CheckboxSelectionModel({
        listeners: {
            selectionchange: function() {
                if (this.getCount() === 0) {
                    for (var x=0; x < menu_items.length; x++) {
                        Ext.getCmp(menu_items[x]).disable();
                    }

                }
                else {
                    for (var x=0; x < menu_items.length; x++) {
                        Ext.getCmp(menu_items[x]).enable();
                    }
                }
            }
        }
    });

    return sm;
};

var get_user_list = function() {
    var store = new Ext.data.JsonStore({
        autoDestroy: true,
        url: '/demo_admin/get_user_list/',
        fields: ["id", "name", 'is_staff', 'is_active', 'email', 'first_name', 'last_name'],
        root: 'elements',
        autoLoad: true,
        sortInfo: {
            field: 'name',
            direction: 'ASC'
        }
    });

    var sm = get_list_selectionmodel(['disable_user_menu', 'enable_user_menu']);

    var list = new Ext.grid.GridPanel({
        title: 'Users',
        store: store,
        layout: 'fit',
        id: 'users_list',
        height: 500,
        viewConfig: {
         forceFit: true
        }, 
        sm: sm, 
        columns: [sm, {
            header: 'UserName',
            dataIndex: 'name',
            sortable: true
        }, {
            header: 'Active member',
            dataIndex: 'is_active',
            renderer: bool_renderer,
            sortable: true
        },{
            header: 'Staff member',
            dataIndex: 'is_staff',
            renderer: bool_renderer
        }, {
            header: 'First name',
            dataIndex: 'first_name',
            sortable: true
        }, {
            header: 'Last name',
            dataIndex: 'last_name',
            sortable: true
        }, {
            header: 'Email',
            dataIndex: 'email',
            sortable: true
        }],
        bbar: [{
            text: 'Activate',
            iconCls: 'add_icon',
            id: 'enable_user_menu',
            handler: function() {                
                perform_demo_action('users_list', '/demo_admin/confirm_user/', 'Demo admin', 'User(s) activated successfully.');
            }
        }, {
            text: 'Disable',
            iconCls: 'clear_icon',
            id: 'disable_user_menu',
            disabled: true,
            handler: function() {
                perform_demo_action('users_list', '/demo_admin/disable_user/', 'Demo admin', 'User(s) disabled successfully.');
            }
        }]
    });

    var viewport = new Ext.Viewport({
        layout:'fit',
        items:[list]
    });
};

Ext.onReady(function() {

    get_user_list();

});