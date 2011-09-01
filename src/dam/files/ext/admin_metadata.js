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

var get_namespace_list = function() {

    var namespace_store = new Ext.data.JsonStore({
        url: '/dam_admin/get_xmp_namespaces/',
        fields: ["id", "name", "url", "prefix"],
        root: 'elements',
        autoLoad: true,
        sortInfo: {
            field: 'name',
            direction: 'ASC'
        }
    });

    var ns_sm = get_list_selectionmodel(['remove_ns_menuitem', 'edit_ns_menuitem']);

    var xmp_namespace_list = new Ext.grid.GridPanel({
        title: 'XMP Namespaces',
        store: namespace_store,
        layout: 'fit',
        id: 'namespace_list',
        enableHdMenu: false,
        viewConfig: {
         forceFit: true
        }, 
        sm: ns_sm, 
        listeners: {
            dblclick: function() {
                open_admin_editor(this.getId(), 'XMP Namespace', open_ns_win);
            }
        },
        columns: [ns_sm, {
            header: 'XMP Namespace',
            dataIndex: 'name'
        }, {
            header: 'URL',
            dataIndex: 'url'
        }, {
            header: 'Prefix',
            dataIndex: 'prefix'
        }],
        bbar: [{
            text: 'Add',
            iconCls: 'add_icon',
            handler: function() {
                var ns = undefined;
                open_ns_win(ns);
            }
        }, {
            text: 'Remove',
            iconCls: 'clear_icon',
            id: 'remove_ns_menuitem',
            disabled: true,
            handler: function() {
                remove_from_list('namespace_list', '/dam_admin/delete_namespace/', 'Remove XMP Namespace', 'XMP Namespace(s) removed successfully.');
            }
        }, {
            text: 'Edit',
            iconCls: 'edit_icon',
            id: 'edit_ns_menuitem',
            disabled: true,
            handler: function() {
                open_admin_editor('namespace_list', 'XMP Namespace', open_ns_win);
            }
        }]
    });        

    return xmp_namespace_list;
};

var get_xmp_list = function() {
    var xmp_store = new Ext.data.GroupingStore({
        reader: new Ext.data.JsonReader({
            root: "xmp",
            fields: ['namespace_name', 'id', 'caption', 'keyword_target', 'xmp_type', 'description', 'editable', 'searchable', 'array', 'target', 'choice', 'variant', 'type', 'namespace', 'name', 'image', 'video', 'audio', 'doc']
        }),
        autoLoad: true,
        sortInfo: {
            field: 'name',
            direction: 'ASC'
        },
        groupField: 'namespace_name',
        url: '/dam_admin/get_xmp_list/'
    });

    var xmp_sm = get_list_selectionmodel(['remove_xmp_menuitem', 'edit_xmp_menuitem']);

    var xmp_panel = new Ext.grid.GridPanel({
        title: 'XMP Schemas',
        layout: 'fit',
        store: xmp_store,
        id: 'xmp_list',
        enableHdMenu: false,
        view: new Ext.grid.GroupingView({
            forceFit:true,
            groupTextTpl: '{text}',
            hideGroupedColumn: true,
            startCollapsed: true          
        }),
        sm: xmp_sm, 
        listeners: {
            dblclick: function() {
                open_admin_editor(this.getId(), 'XMP Schema', open_xmp_win);
            }
        },
        columns: [xmp_sm, {
            header: 'Namespace',
            dataIndex: 'namespace_name'
        }, {
            header: 'XMP Schema',
            dataIndex: 'name'
        }, {
            header: 'Type',
            dataIndex: 'type'
        }, {
            header: 'Image',
            dataIndex: 'image',
            renderer: bool_renderer,                    
            width: 50
        }, {
            header: 'Movie',
            dataIndex: 'video',
            renderer: bool_renderer,
            width: 50
        }, {
            header: 'Audio',
            dataIndex: 'audio',
            renderer: bool_renderer,                    
            width: 50
        }, {
            header: 'Docs',
            dataIndex: 'doc',
            renderer: bool_renderer,                    
            width: 50
        }],
        bbar: [{
            text: 'Add',
            iconCls: 'add_icon',
            handler: function() {
                var schema = undefined;
                open_xmp_win(schema);
            }
        }, {
            text: 'Remove',
            iconCls: 'clear_icon',
            id: 'remove_xmp_menuitem',
            disabled: true,
            handler: function() {
                remove_from_list('xmp_list', '/dam_admin/delete_xmp/', 'Remove XMP Schema', 'XMP Schema(s) removed successfully.');
            }
        }, {
            text: 'Edit',
            iconCls: 'edit_icon',
            id: 'edit_xmp_menuitem',
            disabled: true,
            handler: function() {
                open_admin_editor('xmp_list', 'XMP Schema', open_xmp_win);
            }
        }]
    });        

    return xmp_panel;

};

var get_rights_list = function() {

    var rights_store = new Ext.data.JsonStore({
        url: '/dam_admin/get_rights_list/',
        root: 'rights',
        fields: ['id', 'name'],
        autoLoad: true,
        sortInfo: {
            field: 'name',
            direction: 'ASC'
        }
    });

    var rights_sm = get_list_selectionmodel(['remove_rights_menuitem', 'edit_rights_menuitem']);

    var rights_panel = new Ext.grid.GridPanel({
        layout: 'fit',
        store: rights_store,
        id: 'list_rights',
        enableHdMenu: false,
        viewConfig: {
         forceFit: true
        }, 
        sm: rights_sm, 
        listeners: {
            dblclick: function() {
                open_admin_editor(this.getId(), 'Rights', open_rights_win);
            }
        },
        columns: [rights_sm, {
            header: 'Licencies',
            dataIndex: 'name'
        }],
        bbar: [{
            text: 'Add',
            iconCls: 'add_icon',
            handler: function() {
                var right = undefined;
                open_rights_win(right);
            }
        }, {
            text: 'Remove',
            iconCls: 'clear_icon',
            id: 'remove_rights_menuitem',
            disabled: true,
            handler: function() {
                remove_from_list('list_rights', '/dam_admin/delete_rights/', 'Remove Right', 'Right(s) removed successfully.');
            }
        }, {
            text: 'Edit',
            iconCls: 'edit_icon',
            id: 'edit_rights_menuitem',
            disabled: true,
            handler: function() {
                open_admin_editor('list_rights', 'Rights', open_rights_win);
            }
        }]
    });    
    
    return rights_panel;

};

var get_desc_list = function() {

    var d_list_store = new Ext.data.JsonStore({
        url: '/dam_admin/get_desc_list/',
        root: 'descs',
        fields: ['id', 'name', 'mapping', 'groups'],
        autoLoad: true
    });

    var list_desc_sm = get_list_selectionmodel(['remove_desc_menuitem', 'edit_desc_menuitem']);

    var list_desc = new Ext.grid.GridPanel({
        store: d_list_store,
        id: 'list_desc',
        layout: 'fit',
        title: 'Descriptors',
        enableHdMenu: false,
//                multiSelect: true,
//                reserveScrollOffset: true,
        viewConfig: {
         forceFit: true
        }, 
        sm: list_desc_sm, 
        listeners: {
            dblclick: function() {
                open_admin_editor(this.getId(), 'Descriptor', open_descriptor_win);
            }
        },
        columns: [list_desc_sm, {
            header: 'Descriptor Name',
            dataIndex: 'name'
        }, {
            header: 'XMP Mapping',
            dataIndex: 'mapping'
        }, {
            header: 'Descriptor Group(s)',
            dataIndex: 'groups'
        }],
        bbar: [{				
            text: 'Add',
            iconCls: 'add_icon',
            handler: function() {
                var descriptor = undefined;
                open_descriptor_win(descriptor);
            }
        }, {
            text: 'Remove',
            iconCls: 'clear_icon',
            id: 'remove_desc_menuitem',
            disabled: true,
            handler: function() {
                remove_from_list('list_desc', '/dam_admin/delete_descriptor/', 'Remove Descriptor', 'Descriptor(s) removed successfully.');
            }
        }, {
            text: 'Edit',
            iconCls: 'edit_icon',
            id: 'edit_desc_menuitem',
            disabled: true,
            handler: function() {
                open_admin_editor('list_desc', 'Descriptor', open_descriptor_win);
            }
        }]                
    });
            
    return list_desc;

};

var get_desc_groups_list = function() {

    var d_group_store = new Ext.data.JsonStore({
        url: '/dam_admin/get_desc_groups/',
        root: 'groups',
        fields: ['id', 'name', 'removable', 'target'],
        autoLoad: true
    });

    var list_group_sm = get_list_selectionmodel(['remove_group_menuitem', 'edit_group_menuitem']);

    var list_groups = new Ext.grid.GridPanel({
        id: 'list_group',
        layout: 'fit',
        title: 'Groups',        
        store: d_group_store,
        viewConfig: {
         forceFit: true
        }, 
        enableHdMenu: false,
        sm: list_group_sm,         
        listeners: {
            dblclick: function() {
                open_admin_editor(this.getId(), 'Descriptor Group', open_descriptor_group_win);
            }
        },
        columns: [list_group_sm, {
            header: 'Group Name',
            dataIndex: 'name'
        }],
        bbar: [{				
            text: 'Add',
            iconCls: 'add_icon',
            handler: function() {
                var group = undefined;
                open_descriptor_group_win(group);                        
            }
        }, {
            text: 'Remove',
            iconCls: 'clear_icon',
            id: 'remove_group_menuitem',
            handler: function() {
                remove_from_list('list_group', '/dam_admin/delete_descriptor_group/', 'Remove Descriptor Group', 'Descriptor Group(s) removed successfully.');
            }
        }, {
            text: 'Edit',
            iconCls: 'edit_icon',
            id: 'edit_group_menuitem',
            handler: function() {
                open_admin_editor('list_group', 'Descriptor Group', open_descriptor_group_win);
            }
        }]
    });    
    
    return list_groups;

};

var open_ns_win = function(current_ns) {

    var win_title, submit_url, ns_id, ns_name, ns_url, ns_prefix, success_msg;

    if (!current_ns) {
        win_title = 'Add XMP Namespace';
        submit_url = '/dam_admin/save_ns/';
        ns_id = 0;
        ns_name = 'newXMPNamespace';
        ns_url = 'http://www.namespace_url.com/';
        ns_prefix = 'newPrefix';
        success_msg = 'XMP Namespace added successfully.';
    }
    else {
        win_title = 'Edit XMP Namespace';        
        submit_url = '/dam_admin/save_ns/';
        ns_id = current_ns.get('id');
        ns_name = current_ns.get('name');
        ns_url = current_ns.get('url');
        ns_prefix = current_ns.get('prefix');
        success_msg = 'XMP Namespace edited successfully.';
    }
    
    var form = new Ext.form.FormPanel({
        frame: true,
        width : 500,
        height: 150,
        id: 'new_ns_form',
        region: 'center',
        defaults: {
            width: 300,
            allowBlank: false
        },
        items: [{
            fieldLabel: 'Name',
            xtype: 'textfield',
            id: 'new_ns_name',
            value: ns_name
        }, {
            fieldLabel: 'URL',
            xtype: 'textfield',
            id: 'new_ns_url',
            value: ns_url
        }, {
            fieldLabel: 'Prefix',
            xtype: 'textfield',
            id: 'new_ns_prefix',
            value: ns_prefix
        }]
    });
    
    var panel = new Ext.Panel({
        layout      : 'border',
        items    : [form],
        width       : 450,
        height      : 150,
        buttons: [{
            text: 'Save',
            type: 'submit',
            handler: function(){
                if (Ext.getCmp('new_ns_form').form.isValid()){

                    var ns_name = Ext.getCmp('new_ns_name').getValue();
                    var ns_url = Ext.getCmp('new_ns_url').getValue();
                    var ns_prefix = Ext.getCmp('new_ns_prefix').getValue();

                    var my_obj = this;

                    Ext.Ajax.request({
                        url: submit_url,
                        params: {ns_name: ns_name, ns_id: ns_id, ns_url: ns_url, ns_prefix: ns_prefix},
                        success: function(data){
                            Ext.getCmp('namespace_list').getStore().reload();
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

var open_xmp_win = function(current_xmp) {

    var win_title, submit_url, success_msg;
    var xmp_id, xmp_name, xmp_media_types, xmp_namespace;
    var xmp_editable, xmp_searchable, xmp_variant, xmp_array, xmp_choice;
    var xmp_target, xmp_caption, xmp_description, xmp_type, xmp_keyword;
    
    if (!current_xmp) {
        win_title = 'Add XMP Schema';
        submit_url = '/dam_admin/save_xmp/';
        xmp_id = 0;
        xmp_name = 'newXMPSchema';
        xmp_media_types = [true, false ,false, false];     
        xmp_namespace = '';
        xmp_editable = true;
        xmp_searchable = false;
        xmp_variant = false;
        xmp_array = 'not_array';
        xmp_choice = 'not_choice';
        xmp_target = '';
        xmp_caption = 'XMPSchema';
        xmp_description = 'Description';
        xmp_type = '';
        xmp_keyword = false;
        success_msg = 'XMP Schema added successfully.';
    }
    else {
        win_title = 'Edit XMP Schema';        
        submit_url = '/dam_admin/save_xmp/';
        xmp_id = current_xmp.get('id');
        xmp_name = current_xmp.get('name');
        xmp_media_types = [current_xmp.get('image'), current_xmp.get('video'), current_xmp.get('audio'), current_xmp.get('doc')];
        xmp_namespace = current_xmp.get('namespace');
        xmp_editable = current_xmp.get('editable');
        xmp_searchable = current_xmp.get('searchable');
        xmp_variant = current_xmp.get('variant');
        xmp_array = current_xmp.get('array');
        xmp_choice = current_xmp.get('choice');
        xmp_target = current_xmp.get('target');
        xmp_caption = current_xmp.get('caption');
        xmp_description = current_xmp.get('description');
        xmp_type = current_xmp.get('xmp_type');
        xmp_keyword = current_xmp.get('keyword_target');
        success_msg = 'XMP Schema edited successfully.';
    }

    var namespace_store = new Ext.data.JsonStore({
        url: '/dam_admin/get_xmp_namespaces/',
        fields: ["id", "name"],
        root: 'elements',
        autoLoad: true,
        listeners: {
            load: function() {
                Ext.getCmp('field_xmp_namespace').setValue(xmp_namespace);                
            }            
        }
    });
    
    var form = new Ext.form.FormPanel({
        frame: true,
        width       : 500,
        height: 550,
        id: 'new_xmp_form',
        region: 'center',
        defaults: {
            width: 300,
            allowBlank: false
        },
        items: [{
            fieldLabel: 'XMP Namespace',
            xtype: 'combo',
            id: 'field_xmp_namespace',
            hiddenName: 'xmp_namespace',
            emptyText: 'Choose Namespace...',
            store: namespace_store,
            valueField: 'id',
            displayField: 'name',
            triggerAction: 'all',
            lazyRender:true,
            mode: 'local'
        }, {
            fieldLabel: 'Field name',
            xtype: 'textfield',
            id: 'xmp_name',
            value: xmp_name
        }, {
            fieldLabel: 'Caption',
            xtype: 'textfield',
            id: 'xmp_caption',
            value: xmp_caption
        }, {
            fieldLabel: 'Description',
            xtype: 'textarea',
            id: 'xmp_desc',
            height: 100,
            value: xmp_description
        }, {
            fieldLabel: 'Is Array?',
            xtype: 'combo',
            hiddenName: 'xmp_array',
            emptyText: 'Choose...',
            store: new Ext.data.ArrayStore({
                fields: ['id', 'name'],
                data: [['not_array', 'No'], ['alt', 'Alt'], ['bag', 'Bag'], ['seq', 'Sequence']]
            }),
            valueField: 'id',
            displayField: 'name',
            triggerAction: 'all',
            lazyRender:true,
            mode: 'local',
            value: xmp_array
        }, {
            fieldLabel: 'Is Choice?',
            xtype: 'combo',
            hiddenName: 'xmp_choice',
            emptyText: 'Choose...',
            store: new Ext.data.ArrayStore({
                fields: ['id', 'name'],
                data: [['not_choice', 'No'], ['open_choice', 'Open choice'], ['close_choice', 'Close choice']]
            }),
            valueField: 'id',
            displayField: 'name',
            triggerAction: 'all',
            lazyRender:true,
            mode: 'local',
            value: xmp_choice
        }, {
            fieldLabel: 'Field type',
            xtype: 'combo',
            hiddenName: 'xmp_type',
            emptyText: 'Choose...',
            store: new Ext.data.ArrayStore({
                fields: ['id', 'name'],
                data: [
                    ['agent_name','AgentName'],
                    ['bool','Bool'],
                    ['beat_splice_stretch', 'BeatSliceStretch'], 
                    ['cfapattern', 'CFAPattern'], 
                    ['colorant', 'Colorant'], 
                    ['date','Date'],
                    ['date_only_year','Date [only year]'],
                    ['date_and_time','Date and time'],
                    ['device_settings', 'DeviceSettings'], 
                    ['Dimensions', 'Dimensions'], 
                    ['Flash', 'Flash'], 
                    ['font', 'Font'], 
                    ['gpscoordinate','GPSCoordinate'],
                    ['int','Integer'],
                    ['job', 'Job'], 
                    ['lang','Lang'],
                    ['locale', 'Locale'], 
                    ['marker', 'Marker'], 
                    ['media', 'Media'], 
                    ['mimetype','MIMEType'],
                    ['oecf_sfr', 'OECF/SFR'], 
                    ['ProjectLink', 'ProjectLink'], 
                    ['proper_name','ProperName'],
                    ['rational', 'Rational'], 
                    ['real', 'Real'], 
                    ['rendition_class', 'RenditionClass'], 
                    ['resample_params', 'ResampleParams'], 
                    ['resource_event','ResourceEvent'],
                    ['resource_ref','ResourceRef'],
                    ['txt','Text'],
                    ['time', 'Time'],
                    ['time_scale_stretch', 'timeScaleStretch'], 
                    ['timecode', 'Timecode'], 
                    ['thumbnail','Thumbnail'],
                    ['uri','URI'],
                    ['url','URL'],
                    ['version','Version'],
                    ['xpath','XPath'],
                    ['ContactInfo','ContactInfo'],
                    ['LocationDetails','LocationDetails'],
                    ['LicensorDetail','LicensorDetail'],
                    ['CopyrightOwnerDetail','CopyrightOwnerDetail'],
                    ['ImageCreatorDetail','ImageCreatorDetail'],
                    ['ArtworkOrObjectDetails','ArtworkOrObjectDetails'],
                    ['filesize','Filesize']
                ]
            }),
            valueField: 'id',
            displayField: 'name',
            triggerAction: 'all',
            lazyRender:true,
            mode: 'local',
            value: xmp_type
        }, {
            id: 'xmp_editable',
            xtype: 'radiogroup',
            fieldLabel: 'Is Editable?',
            items: [
                {boxLabel: 'Yes', name:'xmp_editable', inputValue: 'true', checked: xmp_editable},
                {boxLabel: 'No', name:'xmp_editable', inputValue: 'false', checked: !xmp_editable}
            ]
        }, {
            id:'xmp_searchable',
            xtype: 'radiogroup',
            fieldLabel: 'Is Searchable?',
            items: [
                {boxLabel: 'Yes', name:'xmp_searchable', inputValue: 'true', checked: xmp_searchable},
                {boxLabel: 'No', name:'xmp_searchable', inputValue: 'false', checked: !xmp_searchable}
            ]
        }, {
            id:'xmp_variant',
            xtype: 'radiogroup',
            fieldLabel: 'Is Variant?',
            items: [
                {boxLabel: 'Yes', name:'xmp_variant', inputValue: 'true', checked: xmp_variant},
                {boxLabel: 'No', name:'xmp_variant', inputValue: 'false', checked: !xmp_variant}
            ]
        }, {
            id:'xmp_keyword',
            xtype: 'radiogroup',
            fieldLabel: 'Is a keyword target?',
            items: [
                {boxLabel: 'Yes', name:'xmp_keyword', inputValue: 'true', checked: xmp_keyword},
                {boxLabel: 'No', name:'xmp_keyword', inputValue: 'false', checked: !xmp_keyword}
            ]
        }, {
            fieldLabel: 'Special target',
            xtype: 'combo',
            hiddenName: 'xmp_target',
            emptyText: '(optional)',
            store: new Ext.data.ArrayStore({
                fields: ['id', 'name'],
                data: [
                    ['uploaded_by','Uploaded by'],
                    ['creation_date', 'Uploaded on'], 
                    ['latitude_target', 'Latitude'], 
                    ['longitude_target', 'Longitude'], 
                    ['rights_target','Rights'],
                    ['item_owner_target','Owner'],
                    ['file_size_target','File size'],
                    ['file_name_target', 'File name']
                ]
            }),
            valueField: 'id',
            displayField: 'name',
            triggerAction: 'all',
            lazyRender:true,
            mode: 'local',
            allowBlank: true,
            value: xmp_target                                
        }, {
            xtype: 'checkboxgroup',
            fieldLabel: 'Media Types',
            columns: 2,
            items: [
                {boxLabel: 'Image', name: 'xmp_media_type_image', checked: xmp_media_types[0]},
                {boxLabel: 'Movie', name: 'xmp_media_type_movie', checked: xmp_media_types[1]},
                {boxLabel: 'Audio', name: 'xmp_media_type_audio', checked: xmp_media_types[2]},
                {boxLabel: 'Doc', name: 'xmp_media_type_doc', checked: xmp_media_types[3]}
            ]
        }]
    });
    
    var panel = new Ext.Panel({
        layout      : 'border',
        items    : [form],
        width       : 450,
        height      : 550,
        buttons: [{
            text: 'Save',
            type: 'submit',
            handler: function(){
                if (Ext.getCmp('new_xmp_form').getForm().isValid()){

                    var my_obj = this;

                    Ext.getCmp('new_xmp_form').getForm().submit({
                        params: {xmp_id: xmp_id},
                        url: submit_url,
                        success: function(data){
                            Ext.getCmp('xmp_list').getStore().reload();
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

var open_rights_win = function(current_rights) {

    var win_title, submit_url, rights_id, rights_name, success_msg;

    if (!current_rights) {
        win_title = 'Add Rights Value';
        submit_url = '/dam_admin/save_rights/';
        rights_id = 0;
        rights_name = 'newRightsValue';
        success_msg = 'Rights value added successfully.';
    }
    else {
        win_title = 'Edit Descriptor';        
        submit_url = '/dam_admin/save_rights/';
        rights_id = current_rights.get('id');
        rights_name = current_rights.get('name');
        success_msg = 'Rights value edited successfully.';
    }

    var rights_prop_store = new Ext.data.ArrayStore({
        fields: ['xmp_id', 'name', 'value']
    });
    
    var properties_store = new Ext.data.JsonStore({
        url: '/dam_admin/get_rights_properties/',
        baseParams: {rights_id: rights_id},
        fields: ["xmp_id", "name", "value"],
        root: 'elements',
        autoLoad: true,
        listeners: {
            load: function() {
                this.each(function(r) {
                    rights_prop_store.loadData([[r.get('xmp_id'), r.get('name'), r.get('value')]], true);
                });
            }
        }
    });

    var open_add_xmp_value = function() {

        var xmp_store = new Ext.data.JsonStore({
            baseParams: {add_mode: 1},
            url: '/dam_admin/get_rights_properties/',
            fields: ["xmp_id", "name"],
            root: 'elements',
            autoLoad: true
        });

        var form = new Ext.form.FormPanel({
            frame: true,
            height: 200,
            width: 400,
            id: 'new_xmp_value_form',
            items: [{
                fieldLabel: 'XMP Property',
                xtype: 'combo',
                id: 'xmp_property',
                emptyText: 'XMP Property...',
                store: xmp_store,
                valueField: 'xmp_id',
                displayField: 'name',
                triggerAction: 'all',
                lazyRender:true,
                mode: 'local',
                allowBlank: false
            }, {
                fieldLabel: 'XMP value',
                xtype: 'textfield',
                id: 'xmp_value',
                allowBlank: false
            }],
            buttons: [{
                text: 'Save',
                type: 'submit',
                handler: function(){
                    if (Ext.getCmp('new_xmp_value_form').form.isValid()){
                        var xmp = Ext.getCmp('xmp_property').getValue();
                        var xmp_name = Ext.getCmp('xmp_property').getRawValue();                            
                        var value = Ext.getCmp('xmp_value').getValue();

                        Ext.getCmp('prop_list').getStore().loadData([[xmp, xmp_name, value]], true);

                        close_my_win(this);
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
            title: 'Add xmp value',
            items    : [form]
        });
        win.show();
    };

    var properties_list = new Ext.grid.GridPanel({
        store: rights_prop_store,
        id: 'prop_list',
        region: 'center',
        columns: [new Ext.grid.CheckboxSelectionModel(), {
            header: 'XMP Property name',
            dataIndex: 'name'
        }, {
            header: 'Value',
            dataIndex: 'value'
        }],
        viewConfig: {
            forceFit:true
        },
        bbar: [{				
            text: 'Add',
            iconCls: 'add_icon',
            handler: open_add_xmp_value
        }, {
            text: 'Remove',
            iconCls: 'clear_icon',
            id: 'remove_group_menuitem',
            handler: function() {
                var selections = Ext.getCmp('prop_list').getSelectionModel().getSelections();
                for (var x=0; x < selections.length; x++) {
                    rights_prop_store.remove(selections[x]);
                }
            }
        }]
    });
    
    var form = new Ext.form.FormPanel({
        frame: true,
        height: 50,
        id: 'new_rights_form',
        region: 'north',
        items: [{
            width: 200,
            fieldLabel: 'Rights value',
            xtype: 'textfield',
            id: 'new_rights_name',
            allowBlank: false,
            value: rights_name
        }]
    });
    
    var panel = new Ext.Panel({
        layout      : 'border',
        items    : [form, properties_list],
        width       : 600,
        height      : 500,
        buttons: [{
            text: 'Save',
            type: 'submit',
            handler: function(){
                if (Ext.getCmp('new_rights_form').form.isValid()){
                    var prop_list = Ext.getCmp('prop_list').getStore();
                    var selected_prop = [];

                    for (var x=0; x < prop_list.getCount(); x++) {
                        var r = prop_list.getAt(x);
                        selected_prop.push({xmp_id: r.get('xmp_id'), value: r.get('value')});
                    }
                    var rights_name = Ext.getCmp('new_rights_name').getValue();

                    if (selected_prop.length === 0) {
                        Ext.MessageBox.alert(win_title, 'You need to add XMP values');
                        return false;
                    }

                    var my_obj = this;
                    
                    Ext.Ajax.request({
                        url: submit_url,
                        params: {prop_list: Ext.encode(selected_prop), rights_name: rights_name, rights_id: rights_id},
                        success: function(data){
                            Ext.getCmp('list_rights').getStore().reload();
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
        resizable: false,            
        items    : [panel]
    });
    win.show();
    
};

var open_descriptor_win = function(current_descriptor) {

    var win_title, submit_url, desc_id, desc_name, success_msg;

    if (!current_descriptor) {
        win_title = 'Add Descriptor';
        submit_url = '/dam_admin/save_descriptor/';
        desc_id = 0;
        desc_name = 'newDescName';
        success_msg = 'Descriptor added successfully.';
    }
    else {
        win_title = 'Edit Descriptor';        
        submit_url = '/dam_admin/save_descriptor/';
        desc_id = current_descriptor.get('id');
        desc_name = current_descriptor.get('name');
        success_msg = 'Descriptor edited successfully.';
    }
    
    var desc_properties_store = new Ext.data.JsonStore({
        url: '/dam_admin/get_descriptor_properties/',
        baseParams: {desc_id: desc_id},
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
        region: 'west',
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

    var group_store = new Ext.data.JsonStore({
        url: '/dam_admin/get_desc_groups/',
        baseParams: {desc_id: desc_id},
        root: 'groups',
        fields: ['id', 'name', 'removable', 'selected'],
        autoLoad: true,
        listeners: {
            load: function() {
                var grid = Ext.getCmp('new_desc_group_list');
                var selected = this.query('selected', true);
                var selected_records = [];
                for (var x=0; x < selected.length; x++) {
                    selected_records.push(selected.itemAt(x));
                }
                grid.getSelectionModel().selectRecords(selected_records);
                
            }    
        }
    });

    var groups_panel = new Ext.grid.GridPanel({
        store: group_store,
        height: 100,
        region: 'center',
        id: 'new_desc_group_list',
        columns: [new Ext.grid.CheckboxSelectionModel(), {
            header: 'Group Name',
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
        items: [groups_panel, properties_list]
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
        width       : 600,
        height      : 500,
        buttons: [{
            text: 'Save',
            type: 'submit',
            handler: function(){
                if (Ext.getCmp('new_desc_form').form.isValid()){
                    var prop_list = Ext.getCmp('new_desc_prop_list').getSelectionModel().getSelections();
                    var selected_prop = [];
                    var selected_group = [];
                    var r;
                    for (var x=0; x < prop_list.length; x++) {
                        r = prop_list[x];
                        selected_prop.push(r.get('id'));
                    }
                    var desc_name = Ext.getCmp('new_desc_name').getValue();

                    var group_list = Ext.getCmp('new_desc_group_list').getSelectionModel().getSelections();
                    for (x=0; x < group_list.length; x++) {
                        r = group_list[x];
                        selected_group.push(r.get('id'));
                    }

                    if (selected_prop.length === 0 || selected_group.length === 0) {
                        Ext.MessageBox.alert(win_title, 'You need to select one or more XMP properties and one or more Descriptor Groups');
                        return false;
                    }

                    var my_obj = this;

                    Ext.Ajax.request({
                        url: submit_url,
                        params: {prop_list: Ext.encode(selected_prop), desc_name: desc_name, group_list: Ext.encode(selected_group), desc_id: desc_id},
                        success: function(data){
                            Ext.getCmp('list_desc').getStore().reload();
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
        resizable: false,
        items    : [panel]
    });
    win.show();
    
};

var open_descriptor_group_win = function(current_group) {

    var win_title, submit_url, group_id, group_name, target, success_msg;

    if (!current_group) {
        win_title = 'Add Descriptor Group';
        submit_url = '/dam_admin/save_descriptor_group/';
        group_id = 0;
        group_name = 'newGroupName';
        target = 0;
        success_msg = 'Descriptor Group added successfully.';
    }
    else {
        win_title = 'Edit Descriptor Group';        
        submit_url = '/dam_admin/save_descriptor_group/';
        group_id = current_group.get('id');
        group_name = current_group.get('name');
        target = current_group.get('target');
        success_msg = 'Descriptor Group edited successfully.';
    }
    
    var desc_properties_store = new Ext.data.JsonStore({
        url: '/dam_admin/get_desc_list/',
        baseParams: {group_id: group_id},
        fields: ["id", "name", "mapping", "groups", "selected"],
        root: 'descs',
        autoLoad: true,
        listeners: {
            load: function() {
                var grid = Ext.getCmp('new_group_prop_list');
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
        id: 'new_group_prop_list',
        columns: [new Ext.grid.CheckboxSelectionModel(), {
            header: 'Property name',
            dataIndex: 'name'
        }, {
            header: 'XMP Mapping',
            dataIndex: 'mapping'
        }],
        viewConfig: {
            forceFit:true
        }
        
    });

    var selections_panel = new Ext.Panel({
        height: 150,
        region: 'center',
        layout: 'border',
        items: [properties_list]
    });
    
    var form = new Ext.form.FormPanel({
        frame: true,
        height: 100,
        id: 'new_group_form',
        region: 'north',
        items: [{
            fieldLabel: 'Descriptor Group name',
            xtype: 'textfield',
            id: 'new_group_name',
            allowBlank: false,
            value: group_name
        }, {
            fieldLabel: 'Descriptor Group target',
            xtype: 'combo',
            id: 'new_group_target',
            emptyText: 'Metadata Panel',
            store: new Ext.data.ArrayStore({
                id: 0, 
                fields: [
                    'id',
                    'type'
                ],
                data: [[0, 'Metadata Panel'], [1, 'basic'], [2, 'variant specific (basic)'], [3, 'variant specific (full)'], [4, 'upload']]
            }),
            valueField: 'id',
            displayField: 'type',
            triggerAction: 'all',
            lazyRender:true,
            mode: 'local',
            value: target
        }]
    });
    
    var panel = new Ext.Panel({
        layout      : 'border',
        items    : [form, selections_panel],
        width       : 600,
        height      : 500,
        buttons: [{
            text: 'Save',
            type: 'submit',
            handler: function(){
                if (Ext.getCmp('new_group_form').form.isValid()){
                    var prop_list = Ext.getCmp('new_group_prop_list').getSelectionModel().getSelections();
                    var selected_prop = [];

                    for (var x=0; x < prop_list.length; x++) {
                        var r = prop_list[x];
                        selected_prop.push(r.get('id'));
                    }
                    
                    var group_name = Ext.getCmp('new_group_name').getValue();
                    var group_target = Ext.getCmp('new_group_target').getValue();

                    if (!group_target) {
                        group_target = 0;
                    }

                    if (selected_prop.length === 0) {
                        Ext.MessageBox.alert(win_title, 'You need to select one or more Descriptors');
                        return false;
                    }

                    var my_obj = this;

                    Ext.Ajax.request({                    
                        url: submit_url,
                        params: {desc_list: Ext.encode(selected_prop), group_name: group_name, group_target: group_target, group_id: group_id},
                        success: function(data){
                            Ext.getCmp('list_group').getStore().reload();
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
        resizable: false,
        items    : [panel]
    });
    win.show();
    
};
