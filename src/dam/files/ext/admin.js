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

        //var tabs = generate_pref_forms(this, '/save_system_pref/');
        var sm = new Ext.grid.CheckboxSelectionModel({
            checkOnly: true,
            listeners: {
                    selectionchange: function(){
                        console.log('selectionchange');
                        var languages_selected = this.getSelections();                     
                        Ext.getCmp('default_language').loadLanguages(languages_selected);
                    },
                    rowdeselect: function(sm, rowindex, record){
                        if (this.getCount() == 0)
                            this.selectRow(rowindex);
                        
                        
                    }
            }
        });
        
        var default_language;
        var languages_selected_list = settings_store.query('name', 'supported_languages').items[0].data.value.split(',');
        
        var supported_languages_grid = new Ext.grid.GridPanel({
            id: 'supported_languages_grid',
            title: 'Supported Languages', 
            padding: 'padding-bottom:5px;',           
            store: new Ext.data.ArrayStore({
                
                fields: ["id", "desc"],
                editable: false,
                data: settings_store.query('name', 'supported_languages').items[0].data.choices,                
                listeners: {
                    load: function(r){
                        store = this;
                        default_language_value = this.query('id', settings_store.query('name', 'default_metadata_language').items[0].data.value).items[0].data.id;
                        data_default_language = [];
                        Ext.each(languages_selected_list, function(lang_id){
                            
                            data_default_language.push([lang_id, store.query('id', lang_id).items[0].data.desc]);
                        });
                       
                        default_language = new Ext.form.ComboBox({
                            id: 'default_language',
                            triggerAction: 'all',
                            fieldLabel: 'Default Language',
                            mode: 'local',
                            value: default_language_value,
                            name: settings_store.query('name', 'default_metadata_language').items[0].data.id,
                            loadLanguages: function(languages_records){
                                console.log('languages_records');
                                console.log(languages_records);
                                var tmp = [];
                                //Ext.each([settings_store.query('name', 'supported_languages').items[0].data.value], function(el){                          
                                Ext.each(languages_records, function(el){                                                            
                                    tmp.push([el.data.id, el.data.desc]);                                   
                                    
                                });
                              
                                this.getStore().loadData(tmp);
                                console.log('tmp ' + tmp);
                                console.log('this.getValue() ' + this.getValue());
                               var current_record =  this.getStore().query('id', this.getValue()).items;
                               console.log('current_record.length');
                               console.log(current_record.length);
                              
                               
                               if (current_record.length == 0)
                                    this.setValue(tmp[0][0]);
                            },
                            forceSelection: true,
                            store: new Ext.data.ArrayStore({
                                 fields: ["id", "desc"],
                                 data: data_default_language
                            }),
                            valueField: 'id',
                            displayField: 'desc',
                            hiddenName: settings_store.query('name', 'default_metadata_language').items[0].data.id,
                            listeners: {
                                afterrender: function(){
                                    
                                    //var languages_to_show = [];
                                    //var languages_selected_id = settings_store.query('name', 'supported_languages').items[0].data.value;
                                    //Ext.each(settings_store.query('name', 'supported_languages').items[0].data.choices, function(lang){
                                        //if (lang[0] == languages_selected_id)
                                            //languages_to_show.push(lang);
                                    //});
                                    //
                                    //this.loadLanguages(languages_to_show);
                            }
                            },
                        });
                        
                        
                    }
                }
            }),
            sm: sm,
             columns: [
                sm,                   
                {id: 'desc', header: 'desc', width: 200, dataIndex: 'desc'},
               
            ],
            hideHeaders: true,
            viewConfig: {
            forceFit: true
            },
            height: 120,
            width: 500,
            listeners: {               
                viewready: function(){
                    
                    var languages_selected = this.getStore().queryBy(function(record){                            
                            return languages_selected_list.indexOf(record.data.id) >= 0;
                    });                    
                   
                    this.getSelectionModel().suspendEvents();
                    this.getSelectionModel().selectRecords(languages_selected.items);
                    this.getSelectionModel().resumeEvents();
                    
                }
            }
            
        });
        
        date_format = new Ext.form.ComboBox({
            id: 'date_format',
            triggerAction: 'all',
            fieldLabel: 'Date Format',
            mode: 'local',
            value: settings_store.query('name', 'date_format').items[0].data.value,
            name: settings_store.query('name', 'date_format').items[0].data.id,
            hiddenName: settings_store.query('name', 'date_format').items[0].data.id,
            forceSelection: true,
            store: new Ext.data.ArrayStore({
                 fields: ["id", "desc"],
                 data: settings_store.query('name', 'date_format').items[0].data.choices
            }),
            valueField: 'id',
            displayField: 'desc',
            editable: false
          
        });

         thumb_caption = new Ext.form.ComboBox({
            id: 'thumbnail_caption',
            triggerAction: 'all',
            fieldLabel: 'Thumbnail Caption',
            mode: 'local',
            value: settings_store.query('name', 'thumbnail_caption').items[0].data.value,
            name: settings_store.query('name', 'thumbnail_caption').items[0].data.id,   
            hiddenName: settings_store.query('name', 'thumbnail_caption').items[0].data.id,        
            
            forceSelection: true,
            store: new Ext.data.ArrayStore({
                 fields: ["id", "desc"],
                 data: settings_store.query('name', 'thumbnail_caption').items[0].data.choices
            }),
            valueField: 'id',
            displayField: 'desc',
            editable: false
          
        });
        
        
        var new_tab = new Ext.FormPanel({
            frame: true,
            title: 'Options',
            id: 'options_form',
            labelWidth: 200, // label settings here cascade unless overridden
            items: [supported_languages_grid, default_language, date_format, thumb_caption],
            url: '/save_system_pref/',
            buttons: [{
                text: 'Save',
                type: 'submit',
                handler: function(){
                    //var my_form = Ext.getCmp('options_form').getForm();
                    var my_form = this.findParentByType('form');  
                    //console.log(my_form);                  
                    //var items = my_form.items.items;
                    //
                    //for (var i = 0;  i < items.length; i ++){
                        //if (items[i].getXType() == 'checkboxgroup'){
                            //var ckboxes = items[i].items.items;
                            //var values = [];
                            //for(var j = 0; j< ckboxes.length; j++){
                                //if(ckboxes[j].getValue()) {
                                    //values.push(ckboxes[j].getRawValue()) ;
                                //}
                            //}
                            //
                            //my_form.getForm().baseParams = {};                            
                            //my_form.getForm().baseParams[items[i].name] = values;
                        //}
                            //
                    //}
                    
                    var supported_languages = [];
                    Ext.each(Ext.getCmp('supported_languages_grid').getSelectionModel().getSelections(), function(lang){
                        supported_languages.push(lang.data.id);
                    });
                    var params = {};
                    //params[settings_store.query('name', 'supported_languages').items[0].data.id] = supported_languages.join(',');
                    params[settings_store.query('name', 'supported_languages').items[0].data.id] = supported_languages;
                     my_form.getForm().submit({
                         params: params,
                        
                        clientValidation: true,
                        waitMsg: 'Saving...',
                        success: function(){
                             Ext.MessageBox.alert('Save', 'Preferences saved successfully.');
                        }
                    });
                
                }
            },{
                text: 'Cancel',
                handler: function() {
                
                    if (on_cancel_func) {
                        on_cancel_func();
                    }
                    var my_win = this.findParentByType('window');
                    my_win.close();  
                }
            }]
        });             
                //tabs[0].title = Ext.getCmp('configuration_panel').title;
                Ext.getCmp('configuration_panel').add({
                        xtype: 'panel',                        

                        defaults: {autoScroll:true},
                        layout: 'fit',
                        items: new_tab
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
                } 
                //{
                    //layout: 'fit',
                    //title: 'Workspaces',
                    //iconCls: 'x-icon-configuration',
                    //style: 'padding: 10px;',
                    //items: [ws_panel]
                //},
                ]
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
                    title: 'Licences',
                    iconCls: 'x-icon-rights',
                    style: 'padding: 10px;',
                    layout: 'fit',
                    items: [rights_panel]
                }]
            }]
        }]
    });
        
});
