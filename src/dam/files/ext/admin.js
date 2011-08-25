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

var close_my_win = function(obj) {
    var my_win = obj.findParentByType('window');
    my_win.close();
};

var list_renderer = function status(val){
    var html = '<div>';
    for (var x = 0; x < val.length; x++) {
        html += val[x] + '</br>';
    }
    html += '</div>';
    return html;
};

var bool_renderer = function status(val){
    if (val){
        return '<div style="width:16px; height:16px; background: transparent url(/files/images/icons/fam/tick.png) no-repeat center !important;"></div>';
    }else {
        return '<div></div>';
    }
    return val;
};

var open_admin_editor = function(list_id, obj_name, func_to_call, optional_arg) {
    var selections = Ext.getCmp(list_id).getSelectionModel().getCount();
    if (selections === 0) {
        return false;
    }
    var selection = Ext.getCmp(list_id).getSelectionModel().getSelected();
    func_to_call(selection, optional_arg);
};

var open_admin_multiple_editor = function(list_id, obj_name, func_to_call, optional_arg) {
    var selections = Ext.getCmp(list_id).getSelectionModel().getCount();
    if (selections === 0) {
        return false;
    }
    var selection = Ext.getCmp(list_id).getSelectionModel().getSelections();
    func_to_call(selection, optional_arg);
};

var move_to_first_tab = function(c, i) {
    if (Ext.getCmp('admin_ui').activeGroup.getMainItem() == i) {
        Ext.getCmp('admin_ui').activeGroup.setActiveTab(1);                            
    }
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

var remove_from_list = function(list_id, url, win_title, win_desc) {
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

Ext.onReady(function() {
	Ext.QuickTips.init();

    Ext.form.Field.prototype.msgTarget = 'side';
    Ext.form.Field.prototype.invalidClass = 'invalid_field';
            
    var settings_store = new Ext.data.JsonStore({
        url:'/dam_admin/get_admin_settings/',
        root:'prefs',
        fields: ['id','name','caption','name_component', 'type', 'value', 'choices'],
        autoLoad: true,
        listeners: {
            load: function(r) {

                var tabs = generate_pref_forms(this, '/save_system_pref/');

                Ext.getCmp('configuration_panel').add({
                        xtype: 'tabpanel',
                        activeTab: 0,
                        defaults: {autoScroll:true},
                        items: tabs
                    });
                Ext.getCmp('configuration_panel').doLayout();
            }
        }
    });

    var descriptor_groups_panel = get_desc_groups_list();
    var descriptors_panel = get_desc_list();
    var rights_panel = get_rights_list();   
    var xmp_panel = get_xmp_list();
    var namespace_panel = get_namespace_list();

    var user_panel = get_user_list();
    var ws_panel = get_ws_list();
    var bk_panel = get_bk_panel();
            
    var viewport = new Ext.Viewport({
        layout:'border',
        items:[
        	header,
        	{        	
            xtype: 'grouptabpanel',
            region: 'center',
            tabWidth: 150,
            activeGroup: 0,
            id: 'admin_ui',
            items: [{
                expanded: true,
                listeners: {
                    tabchange: move_to_first_tab
                },
                items: [{
                    title: 'System',
                    iconCls: 'x-icon-configuration',
                    style: 'padding: 10px;'
                }, {
                    layout: 'fit',
                    title: 'Options',
                    iconCls: 'x-icon-configuration',
                    style: 'padding: 10px;',
                    id: 'configuration_panel'
                }, {
                    layout: 'fit',
                    title: 'Users',
                    iconCls: 'x-icon-configuration',
                    style: 'padding: 10px;',
                    items: [user_panel]
                }, {
                    layout: 'fit',
                    title: 'Workspaces',
                    iconCls: 'x-icon-configuration',
                    style: 'padding: 10px;',
                    items: [ws_panel]
                },{
                    layout: 'fit',
                    title: 'Backup',
                    iconCls: 'x-icon-configuration',
                    style: 'padding: 10px;',
                    items: [bk_panel]
                }]
            }, {
                listeners: {
                    tabchange: move_to_first_tab
                },                    
                items: [{
                    title: 'Metadata',
                    layout: 'fit',
                    iconCls: 'x-icon-configuration',
                    style: 'padding: 10px;'
                }, {
                    title: 'Descriptors',
                    iconCls: 'x-icon-descriptors',
                    style: 'padding: 10px;',
                    layout: 'fit',
                    items: [{
                        xtype: 'tabpanel',
                        activeTab: 0,
                        items: [descriptors_panel, descriptor_groups_panel]	
                    }]	
                }, {
                    title: 'Properties',
                    layout: 'fit',                          
                    iconCls: 'x-icon-xmp',
                    style: 'padding: 10px;',
                    items: [{
                        xtype: 'tabpanel',
                        activeTab: 0,
                        items: [xmp_panel, namespace_panel]	
                    }]
                },
                {
                    title: 'Licencies',
                    iconCls: 'x-icon-rights',
                    style: 'padding: 10px;',
                    layout: 'fit',
                    items: [rights_panel]
                }]
            }]
        }]
    });
        
});
