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

var wsadmin_prop_renderer = function status(val){
    var html = '<div>';
    for (var x = 0; x < val.length; x++) {
        html += val[x] + '</br>';
    }
    html += '</div>';
    return html;
};

var wsadmin_get_list_selectionmodel = function(menu_items) {
    var sm = new Ext.grid.CheckboxSelectionModel({
        listeners: {
            selectionchange: function() {
                if (this.getCount() == 0) {
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

var wsadmin_remove_from_grid = function() {

    var my_grid = this.findParentByType('grid');

    var selections = my_grid.getSelectionModel().getSelections();
    for (var x=0; x < selections.length; x++) {
        my_grid.getStore().remove(selections[x]);
    }

};    

var wsadmin_generate_config_list = function(menus, store, title, columns, add_handler, edit_handler) {

    var sm = wsadmin_get_list_selectionmodel(menus);

    var my_columns = columns.slice(0, columns.length);

    my_columns.splice(0, 0, sm);

    var list = new Ext.grid.GridPanel({
        region: 'center',
        frame: true,
        store: store,
        width: 210,
        title: title,
        enableHdMenu: false,
        sm: sm,
        columns: my_columns,
        viewConfig: {
            forceFit:true
        },
        listeners: {
            dblclick: edit_handler
        },
        bbar: [{	
            text: 'Add',
            iconCls: 'add_icon',
            handler: add_handler
        }, {
            text: 'Remove',
            iconCls: 'clear_icon',
            id: menus[0],
            disabled: true,
            handler: wsadmin_remove_from_grid
        }, {
            text: 'Edit',
            iconCls: 'edit_icon',
            id: menus[1],
            disabled: true,
            handler: edit_handler
        }]        
    });    
    
    return list;

};

var wsadmin_open_desc_editor = function(list, store, variant) {
    var selections = list.getSelectionModel().getCount();
    if (selections == 0) {
        Ext.MessageBox.alert('Edit Descriptor', 'You have to select a Descriptor from the list');
        return false;
    }
    var selection = list.getSelectionModel().getSelected();
    open_descriptor_win(store, variant, selection);    
};

var wsadmin_open_group_editor = function(list, store, variant) {
    var selections = list.getSelectionModel().getCount();
    if (selections == 0) {
        Ext.MessageBox.alert('Edit Descriptor group', 'You have to select a Group from the list');
        return false;
    }
    var selection = list.getSelectionModel().getSelected();
    open_descriptor_group_win(store, variant, selection);    
};

var open_config_descriptors = function() {
    
    var basic_store = new Ext.data.JsonStore({
        url: '/ws_admin/config_descriptors/basic_summary/',
        fields: ["id", "name", "properties", "properties_ids"],
        root: 'elements',
        autoLoad: true
    });

    var variant_basic_store = new Ext.data.JsonStore({
        url: '/ws_admin/config_descriptors/specific_basic/',
        fields: ["id", "name", "properties", "properties_ids"],
        root: 'elements',
        autoLoad: true
    });

    var variant_full_store = new Ext.data.JsonStore({
        url: '/ws_admin/config_descriptors/specific_full/',
        fields: ["id", "name", "properties", "properties_ids"],
        root: 'elements',
        autoLoad: true
    });

    var groups_store = new Ext.data.JsonStore({
        url: '/ws_admin/config_descriptor_groups/',
        fields: ["id", "name", "descriptors"],
        root: 'elements',
        autoLoad: true
    });

    var summary_columns = [{
        header: 'Name',
        dataIndex: 'name'
    }, {
        header: 'XMP Mapping',
        dataIndex: 'properties',
        renderer: wsadmin_prop_renderer
    }];

    var groups_columns = [{
        header: 'Name',
        dataIndex: 'name'
    }];

    var basic_add_handler = function() {
        open_descriptor_win(basic_store, 'item');
    };

    var basic_edit_handler = function() {
        var my_list = this.findParentByType('grid');
        if (!my_list) {
            my_list = this;
        }
        wsadmin_open_desc_editor(my_list, basic_store, 'item');
    };

    var basic_list = wsadmin_generate_config_list(['remove_basic_desc_menuitem', 'edit_basic_desc_menuitem'], basic_store, 'Basic Descriptors', summary_columns, basic_add_handler, basic_edit_handler );

    var vbasic_add_handler = function() {
        open_descriptor_win(variant_basic_store, 'variant');
    };

    var vbasic_edit_handler = function() {
        var my_list = this.findParentByType('grid');
        if (!my_list) {
            my_list = this;
        }
        wsadmin_open_desc_editor(my_list, variant_basic_store, 'variant');
    };

    var variant_basic_list = wsadmin_generate_config_list(['remove_variant_basic_menuitem', 'edit_variant_basic_menuitem'], variant_basic_store, 'Variant Basic Descriptors', summary_columns, vbasic_add_handler, vbasic_edit_handler );

    var vfull_add_handler = function() {
        open_descriptor_win(variant_full_store, 'variant');
    };

    var vfull_edit_handler = function() {
        var my_list = this.findParentByType('grid');
        if (!my_list) {
            my_list = this;
        }
        wsadmin_open_desc_editor(my_list, variant_full_store, 'variant');
    };

    var variant_full_list = wsadmin_generate_config_list(['remove_variant_full_menuitem', 'edit_variant_full_menuitem'], variant_full_store, 'Variant Full Descriptors', summary_columns, vfull_add_handler, vfull_edit_handler );

    var group_add_handler = function() {
        open_descriptor_group_win(groups_store, 'all');
    };

    var group_edit_handler = function() {
        var my_list = this.findParentByType('grid');
        if (!my_list) {
            my_list = this;
        }
        wsadmin_open_group_editor(my_list, groups_store, 'all');
    };

    var groups_list = wsadmin_generate_config_list(['remove_groups_menuitem', 'edit_groups_menuitem'], groups_store, 'Descriptor Groups', groups_columns, group_add_handler, group_edit_handler );

    var information_panel = new Ext.Panel({
        frame: true,
        height: 30,
        region: 'north',
        layout: 'fit',
        html: 'You can configure the descriptors shown in the Summary View'
    });

    var group_information_panel = new Ext.Panel({
        frame: true,
        height: 30,
        region: 'north',
        layout: 'fit',
        html: 'You can configure the descriptor groups shown in the Metadata View'
    });
        
    var panel = new Ext.TabPanel({
        autoTabs: true,
        activeTab: 0,
        items    : [{
            title: 'Summary view', 
            layout      : 'border',
            items: [information_panel, 
                new Ext.TabPanel({
                    autoTabs: true,
                    activeTab: 0,
                    region: 'center',
                    items    : [
                        basic_list, variant_basic_list, variant_full_list
                    ]
                })
            ]
        }, {
            title: 'Metadata view', 
            layout      : 'border',
            items: [group_information_panel, groups_list]
        }],
        width       : 650,
        height      : 400 
    });
    
    var win = new Ext.Window({
        layout: 'fit',
        constrain: true,
        plain       : true,
        modal: true,
        title: 'Descriptors Configuration',
        resizable: false,
        items    : [panel],
        buttons: [{
            text: 'Save',
            type: 'submit',
            handler: function(){
                
                var basic_props = [];
                var vbasic_props = [];
                var vfull_props = [];
                var groups = [];
                
                for (var x=0; x < basic_store.getCount(); x++) {
                    var r = basic_store.getAt(x);
                    var my_data = r.data;
                    delete(my_data['properties']);
                    basic_props.push(my_data);
                }

                for (var x=0; x < variant_basic_store.getCount(); x++) {
                    var r = variant_basic_store.getAt(x);
                    var my_data = r.data;
                    delete(my_data['properties']);
                    vbasic_props.push(my_data);
                }

                for (var x=0; x < variant_full_store.getCount(); x++) {
                    var r = variant_full_store.getAt(x);
                    var my_data = r.data;
                    delete(my_data['properties']);
                    vfull_props.push(my_data);
                }

                for (var x=0; x < groups_store.getCount(); x++) {
                    var r = groups_store.getAt(x);
                    var my_data = r.data;
                    delete(my_data['properties']);
                    groups.push(my_data);
                }

                var my_win = this.findParentByType('window');
                
                Ext.Ajax.request({
                    url: '/ws_admin/save_ws_descriptors/',
                    params: {basic: Ext.encode(basic_props), vbasic: Ext.encode(vbasic_props), vfull: Ext.encode(vfull_props), custom_groups: Ext.encode(groups)},
                    success: function(data){
                        Ext.MessageBox.alert('Save configuration', 'Configuration saved successfully.');
                        my_win.close();
                    }
                });
                
            }
        },{
            text: 'Restore Default',
            handler: function(){
                var my_win = this.findParentByType('window');
            
                Ext.Ajax.request({
                    url: '/ws_admin/set_default_descriptors/',
                    success: function(data){
                        Ext.MessageBox.alert('Save configuration', 'Configuration saved successfully.');
                        my_win.close();
                    }
                });
            }
            
        },{
            text: 'Cancel',
            handler: function(){
                var my_win = this.findParentByType('window');
                my_win.close();
            }
            
        }]
    });
    win.show();
    
};


var open_descriptor_win = function(custom_store, variant, current_descriptor) {

    var descRecord = Ext.data.Record.create([
        {name: 'id'},
        {name: 'name'},
        {name: 'properties'},
        {name: 'properties_ids'}
    ]);

    var win_title, submit_url, desc_id, desc_name, success_msg, prop_list;

    if (!current_descriptor) {
        win_title = 'Add Descriptor';
        submit_url = '/ws_admin/save_descriptor/';
        desc_id = 0;
        desc_name = 'newDescName';
        success_msg = 'Descriptor added successfully.';
        prop_list = [];
    }
    else {
        win_title = 'Edit Descriptor';        
        submit_url = '/ws_admin/save_descriptor/';
        desc_id = current_descriptor.get('id');
        desc_name = current_descriptor.get('name');
        success_msg = 'Descriptor edited successfully.';
        prop_list = current_descriptor.get('properties_ids');
    }
    
    var desc_properties_store = new Ext.data.JsonStore({
        url: '/ws_admin/get_descriptor_properties/',
        baseParams: {desc_id: desc_id, prop_list: Ext.encode(prop_list), variant: variant},
        fields: ["id", "name", "selected"],
        root: 'elements',
        autoLoad: true,
        listeners: {
            load: function() {
                var grid = Ext.getCmp('new_desc_prop_list');
                var selected = this.query('selected', true);
                for (var x=0; x < selected.length; x++) {
                    grid.getSelectionModel().selectRecords([selected.itemAt(x)], true);
                }
            }    
        }
    });

    var properties_list = new Ext.grid.GridPanel({
        store: desc_properties_store,
        region: 'center',
        height: 150,
        width: 200,
        id: 'new_desc_prop_list',
        columns: [new Ext.grid.CheckboxSelectionModel(), {
            header: 'Property name',
            dataIndex: 'name'
        }],
        viewConfig: {
            forceFit:true
        }
        
    });

    var selections_panel = new Ext.Panel({
        height: 200,
        region: 'center',
        layout: 'border',
        items: [properties_list]
    });
    
    var form = new Ext.form.FormPanel({
        frame: true,
        height: 50,
        id: 'new_desc_form',
        region: 'north',
        items: [{
            fieldLabel: 'Descriptor name',
            xtype: 'textfield',
            id: 'new_desc_name',
            allowBlank: false,
            value: desc_name
        }]
    });
    
    var panel = new Ext.Panel({
        layout      : 'border',
        items    : [form, selections_panel],
        width       : 400,
        height      : 300,
        buttons: [{
            text: 'Save',
            type: 'submit',
            handler: function(){
                if (Ext.getCmp('new_desc_form').form.isValid()){
                    var prop_list = Ext.getCmp('new_desc_prop_list').getSelectionModel().getSelections();
                    var selected_prop_ids = [];
                    var selected_prop = [];

                    for (var x=0; x < prop_list.length; x++) {
                        var r = prop_list[x];
                        selected_prop_ids.push(r.get('id'));
                        selected_prop.push(r.get('name'));
                    }
                    var desc_name = Ext.getCmp('new_desc_name').getValue();

                    if (current_descriptor) {
                        var b_r = current_descriptor;
                        b_r.set('properties', selected_prop); 
                        b_r.set('properties_ids', selected_prop_ids); 
                        b_r.set('name', desc_name); 
                        b_r.commit();
                    }
                    else {
                        var new_record = new descRecord({id: desc_id, name: desc_name, properties: selected_prop, properties_ids: selected_prop_ids});
                        custom_store.add(new_record, true);
                    }

                    var my_win = this.findParentByType('window');
                    my_win.close();

                }
            }
        },{
            text: 'Cancel',
            handler: function(){
                var my_win = this.findParentByType('window');
                my_win.close();
            }
            
        }] 
    });
    var win = new Ext.Window({
        layout: 'fit',
        constrain: true,
        plain       : true,
        modal: true,
        title: win_title,
        resizable: false,
        items    : [panel]
    });
    win.show();
    
};

var open_descriptor_group_win = function(custom_store, variant, current_group) {

    var descRecord = Ext.data.Record.create([
        {name: 'id'},
        {name: 'name'},
        {name: 'properties'},
        {name: 'properties_ids'}
    ]);

    var groupRecord = Ext.data.Record.create([
        {name: 'id'},
        {name: 'name'},
        {name: 'descriptors'}
    ]);

    var win_title, group_id, group_name, success_msg, descriptors;

    if (!current_group) {
        win_title = 'Add Descriptor Group';
        group_id = 0;
        group_name = 'newGroupName';
        success_msg = 'Descriptor Group added successfully.';
        descriptors = [];
    }
    else {
        win_title = 'Edit Descriptor Group';        
        group_id = current_group.get('id');
        group_name = current_group.get('name');
        success_msg = 'Descriptor Group edited successfully.';
        descriptors = current_group.get('descriptors');
    }
        
    var desc_properties_store = new Ext.data.JsonStore({
        fields: ["id", "name", "properties", "properties_ids"]
    });

    for (var x=0; x < descriptors.length; x++) {
        var r = new descRecord(descriptors[x]);
        desc_properties_store.add(r);        
    }

    var groups_columns = [{
        header: 'Property name',
        dataIndex: 'name'
    }, {
        header: 'XMP Mapping',
        dataIndex: 'properties',
        renderer: wsadmin_prop_renderer
    }];

    var add_handler = function() {
        open_descriptor_win(desc_properties_store, variant);
    };

    var edit_handler = function() {
        var my_list = this.findParentByType('grid');
        if (!my_list) {
            my_list = this;
        }
        wsadmin_open_desc_editor(my_list, desc_properties_store, variant);
    };

    var properties_list = wsadmin_generate_config_list(['remove_group_desc_menuitem', 'edit_group_desc_menuitem'], desc_properties_store, 'Descriptors', groups_columns, add_handler, edit_handler );

    var selections_panel = new Ext.Panel({
        height: 300,
        region: 'center',
        layout: 'border',
        items: [properties_list]
    });
    
    var form = new Ext.form.FormPanel({
        frame: true,
        height: 50,
        id: 'new_group_form',
        region: 'north',
        items: [{
            fieldLabel: 'Descriptor Group name',
            xtype: 'textfield',
            id: 'new_group_name',
            allowBlank: false,
            value: group_name
        }]
    });
    
    var panel = new Ext.Panel({
        layout      : 'border',
        items    : [form, selections_panel],
        width       : 400,
        height      : 300,
        buttons: [{
            text: 'Save',
            type: 'submit',
            handler: function(){
                if (Ext.getCmp('new_group_form').form.isValid()){

                    var new_descriptors = [];

                    for (var x=0; x < desc_properties_store.getCount(); x++) {
                        var r = desc_properties_store.getAt(x);
                        new_descriptors.push(r.data);
                    }
                    var group_name = Ext.getCmp('new_group_name').getValue();

                    if (current_group) {
                        var b_r = current_group;
                        b_r.set('descriptors', new_descriptors); 
                        b_r.set('name', group_name); 
                        b_r.commit();
                    }
                    else {
                        var new_record = new groupRecord({id: group_id, name: group_name, descriptors: new_descriptors});
                        custom_store.add(new_record, true);
                    }
                    
                    var my_win = this.findParentByType('window');
                    my_win.close();

                }
            }
        },{
            text: 'Cancel',
            handler: function(){
                var my_win = this.findParentByType('window');
                my_win.close();
            }
            
        }] 
    });
    var win = new Ext.Window({
        layout: 'fit',
        constrain: true,
        plain       : true,
        modal: true,
        title: win_title,
        resizable: false,
        items    : [panel]
    });
    win.show();
    
};
