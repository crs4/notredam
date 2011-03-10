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






//function generate_variant(variant_id, item_id){
//    function call_back_generate(btn){         
//        if (btn == 'yes'){ 
//            
//            
//            Ext.Ajax.request({
//               url: '/force_variant_generation/' + variant_id + '/' + item_id + '/' ,
//               method: 'GET',
//                success:function(){
//                    var detail_tabs = Ext.getCmp('media_tabs');
//                    var active_tab =  detail_tabs.getActiveTab();
//                    var view = active_tab.items.items[0];
//                    var sel_node = view.getSelectedRecords()[0];
//                    
//                    view.getStore().reload({
//                        scope:view,
//                        callback:function(){
//                            var index = this.getStore().find('pk', sel_node.data.pk);
//                            this.select(index);
//                            
//                            
//                            }
//                    });
//                
//                }
//            });
//        }
//        
//        }
//    var data = Ext.getCmp('variant_summary').getStore().query('pk', variant_id).items[0].data;
//    Ext.MessageBox.confirm('Confirm', "Are you sure you generate the variant '" +data.variant_name+ "'? The current one will be lost.", call_back_generate);
//}
//
function import_variant(variant_id){
    var variant = Ext.getCmp('variant_summary').getStore().query('pk', variant_id).items[0].data;
//    var up = new Upload('/upload_variant/', true,
//        {rendition_id:variant.pk, item_id:variant.item_id}
//    );
//    up.openUpload();    
     upload_dialog({
     	singleSelect: true,
     	url: '/upload_variant/',
     	variant: variant.variant_name,
     	item: variant.item_id,
     	after_upload: function(){
     		var ac = Ext.getCmp('media_tabs').getActiveTab();
		    var view = ac.getComponent(0);
		    var store = view.getStore();
		    record = store.query('pk', variant.item_id).items[0];
		    record.set('status', 'in_progress');
		    record.commit();
		    task.run();

     		this.close();	
     	}
     	
     	
     });
    
}
//
//var store_variant = new Ext.data.JsonStore({
//        url: '/get_variants/',
//        id:'store_variant',
//        totalProperty: 'totalCount',
//        root: 'variants',
//        idProperty: 'pk',
//        fields:['pk', 'name', 'thumb_url', 'resource_url', 'auto_generated', 'media_type', 'imported',  'item_id' , 'variant_id','work_in_progress',
//                {name: 'shortName', mapping: 'name', convert: shortName}
//    ]
//});
//  
//var variant_tbar = new Ext.Toolbar({
//    
//    items: [
//        {id:'view_button',
//        text: 'View',
//        disabled: true,
//        listeners:{
//            click: function(){
//                var data = variant_gridpanel.getSelectionModel().getSelected().data;
//                window.open(data.resource_url);
//                
//            }
//        } 
//      
//    },
//    {id:'download_button',
//        text: 'Download',
//        disabled: true,
//        listeners: {
//            click: function(){
//                var data = variant_gridpanel.getSelectionModel().getSelected().data;
//                window.open(data.resource_url + '?download=1');
//                
//                }
//            }
//    },
//    {text:'Actions',
//        id: 'actions_button',
//        disabled: true,
//        menu:[
//            {id:'generate_button',
//                text: 'Generate',
//               listeners: {
////                        click: generate_variant()
//               }
//            },
//            {id:'import_button',
//                text: 'Import',
//                listeners: {
//                    click: function(){
//                        var variant = variant_gridpanel.getSelectionModel().getSelected().data;
//                        var up = new Upload([],'/get_upload_url/', true, function(){
////                                    reload_variant(variant.item_id)
//                            },
//                            {variant_id:variant.variant_id, item_id:variant.item_id}
//                            );
//                        up.openUpload();
//                        
//                    }
//                }
//            }
//        ]
//    }
////            {xtype: 'tbseparator'}, 
////            {
////                id:'refresh_button',
////                iconCls:'refresh_button',
////                icon:'/files/ext/resources/images/default/grid/refresh.gif',                        
////                listeners: {
//////                        click: click_refresh
////                }
////            }
//    ]}
//);
//
//       
//
//var variant_gridpanel = new Ext.grid.GridPanel({
//    id: 'variant_grid',
//    store: store_variant,
//    region:'north',
//    height: 300,
//    columns:  [{id:'variant_name', header: "name", dataIndex: 'name'}],
//     sm: new Ext.grid.RowSelectionModel({
//        singleSelect: true,
//        listeners:{
//            rowdeselect: function(){
//                variant_tbar.disable();
//                var details_grid = Ext.getCmp('variant_details_grid');
//                details_grid.getStore().removeAll();
//                },
//            rowselect: function(sm, rowIndex, record){
//                variant_tbar.enable();
//                if(ws_permissions_store.find('name', 'admin') < 0 && ws_permissions_store.find('name', 'add_item') < 0) {
//                    Ext.getCmp('actions_button').disable();
//                }
//                if (!record.data.auto_generated) {
//                    Ext.getCmp('generate_button').disable();
//                }
//                else {
//                    Ext.getCmp('generate_button').enable();
//                }
//                if (!record.data.pk){
//                    Ext.getCmp('view_button').disable();
//                    Ext.getCmp('download_button').disable();
//                }
//                else{
//                    Ext.getCmp('view_button').enable();
//                    Ext.getCmp('download_button').enable();
//                }
//                
//                if (record.data.pk){
//                    var details_grid = Ext.getCmp('variant_details_grid');
//                    details_grid.getStore().load({params:{component_id: record.data.pk}});
//                }
//            }
//        
//        }
//     }),
//    viewConfig:{
//        forceFit: true,
//        getRowClass: function(record, index) {
//            var work_in_progress = record.get('work_in_progress');
//            var auto_generated = record.get('auto_generated');
//            var pk = record.get('pk');
//            var css_class = '';
//            if (work_in_progress )  {
//                css_class += 'work_in_progress';
//            }
//            if(!auto_generated) {
//                css_class += ' source_variant';
//            }
//            if(!pk) {
//                css_class += ' variant_notfound';
//            }            
//            return css_class;
//        }
//
//    },
//    hideHeaders: true,
//    tbar:variant_tbar
//        
//});
//    
//var store_variant_metadata = new Ext.data.JsonStore({
//    url: '/get_variant_metadata/',
//    id:'store_variant',
//    totalProperty: 'totalCount',
//    root: 'metadata',
////            idProperty: 'pk',
//    fields:['namespace','name', 'value', 'caption']
//});
//
//store_variant.on('load', function(){variant_tbar.disable(); store_variant_metadata.removeAll();});
//
//var variant_details_grid = new Ext.grid.GridPanel({
//    id: 'variant_details_grid',
//    title: 'Metadata',
//    store: store_variant_metadata ,
//    region:'center',
//    columns:  [
//            {id:'name',header: "name", width: 100, sortable: true, dataIndex: 'caption'},
//            {id:'value',header: "value", width: 100, sortable: true, dataIndex: 'value'}
//            ],
//     sm: new Ext.grid.RowSelectionModel({
//            singleSelect: true
//         
//         }),
//    viewConfig:{
//        forceFit: true
//        },
//    hideHeaders: true
//    });
//        
//var variant_panel = new Ext.Panel({
//    id:'variant_panel',
//    title: 'variants',
//    layout:'border',
//    items: [variant_gridpanel, variant_details_grid]
//});
//
//var variant_store_fields = ['pk','name', 'rank', 'original'] ;
//
//var VariantRankPanel= function(config){
//    Ext.apply(this,{
//            id: Ext.id(),
//            width:540,
//            height: 120,
//            layout: 'border',
//        store: new Ext.data.JsonStore({
//                url: '/get_variant_sources/',
//                fields: variant_store_fields,
//                root: 'variants'
//                
//                
//                }),
//        items:[
//            new Ext.grid.GridPanel({
//                viewConfig: {
//                    forceFit: true
//                    },
//                width: 255,
//                title: 'available',
//                id: 'available' ,
//            store:  new Ext.data.JsonStore({
////                url: '/get_variant_sources/',
//                data: {'variants': []},
////                baseParams: {variant_id: config.variant_id},
//                fields: variant_store_fields,
//                root: 'variants'
//                
//                }),
//        region: 'west',
//        hideHeaders: true,        
//        columns:  [{id:'variant_name', header: "name",   dataIndex: 'name'}],
//        sm: new Ext.grid.RowSelectionModel({
//            singleSelect: true
//            })
//        }),
//              new Ext.Panel({
//                id: 'buttons_panel_' + config.media_type,
//                region:'center', 
//                html: '<div style="text-align:center; padding-top:20;"><img style="margin:2px" src="/files/images/up2.gif" onclick="Ext.getCmp(' +"'buttons_panel_"+config.media_type +"'" +' ).move_to_up()" /><br/><img style="margin:2px" src="/files/images/down2.gif" onclick="Ext.getCmp(' +"'buttons_panel_"+config.media_type +"'" +' ).move_to_down()"/><img style="margin:2px" src="/files/images/left2.gif" onclick="Ext.getCmp(' +"'buttons_panel_"+config.media_type +"'" +' ).move_to_left()" /><br/><img style="margin:2px" src="/files/images/right2.gif" onclick="Ext.getCmp(' +"'buttons_panel_"+config.media_type +"'" +' ).move_to_right()"/> </div>',
//                
//            move_to_up:function(){
//                var grid = Ext.getCmp('selected');
//                var record_selected = grid.getSelectionModel().getSelected();
//                if(record_selected ){
//                    var rank = grid.getStore().indexOf(record_selected);
//                    if (rank > 0){
//                        grid.getStore().remove(record_selected);
//                        grid.getStore().insert(rank - 1, record_selected);
//                        grid.getSelectionModel().selectRecords([record_selected]);
//                    }
//                }
//                    
//            },   
//
//            move_to_down: function(){
//                var grid = Ext.getCmp('selected');
//                var record_selected = grid.getSelectionModel().getSelected();
//                if(record_selected ){
//                    var rank = grid.getStore().indexOf(record_selected);
//                    if (rank < grid.getStore().getCount() - 1){
//                        grid.getStore().remove(record_selected);
//                        grid.getStore().insert(rank +1, record_selected);
//                        grid.getSelectionModel().selectRecords([record_selected]);
//                    }
//                }
//                
//                },
//
//            
//            
//            move_to_right: function(){
//                var selected_grid = Ext.getCmp('selected');
//                var available_grid = Ext.getCmp('available');
//                var selecteds  = available_grid.getSelectionModel().getSelections();
//                for (var i =0; i< selecteds.length; i++){
//                    available_grid.getStore().remove(selecteds[i]);
//                    selected_grid.getStore().add(selecteds[i]);
//                    selected_grid.getSelectionModel().selectRecords([selecteds[i]]);
//                    } 
//                
//            },
//
//                move_to_left: function (){
//                    var selected_grid = Ext.getCmp('selected');
//                    var available_grid = Ext.getCmp('available');
//                    var selecteds  = selected_grid.getSelectionModel().getSelections() ;
//                    for (i =0; i< selecteds.length; i++){
//                        if (!selecteds[i].data.original){
//                            selected_grid.getStore().remove(selecteds[i]);
//                            available_grid.getStore().add(selecteds[i]);
//                        }
//                        }
//                 }  
//                
//          }),
//         
//         new Ext.grid.GridPanel({
//            width:255,
//            viewConfig: {
//                forceFit: true
//            },
//            store:  new Ext.data.JsonStore({
//                data: {'variants': []},
//                fields:variant_store_fields,
//                root: 'variants'
//            }),
//
//        hideHeaders: true,        
//        columns:  [{id:'variant_name', header: "name",   dataIndex: 'name'}],
//        sm: new Ext.grid.RowSelectionModel({
//            singleSelect: true
//            }),
//        buttonAlign: 'center',
//        id: 'selected',
//        region:'east', 
//        title: 'selected'
//             }) 
//        ]
//        });
//
//   // And Call the superclass to preserve baseclass functionality
//    VariantRankPanel.superclass.initComponent.apply(this, arguments);
//    if (config.variant_id) {
//        this.store.baseParams = {variant_id: config.variant_id};
//    }
//    else {
//        this.store.baseParams = {media_type: config.media_type};
//    }
//    this.store.on('load', function(){
//            var reorder_grid = this.items.items[2];
//            var available_grid = this.items.items[0];
//            reorder_grid.getStore().removeAll();
//            available_grid.getStore().removeAll();
//        
//            this.store.each(function(r){
//                if(r.data.rank > 0) {
//                    reorder_grid.getStore().add(r);
//                }
//                else {
//                   available_grid.getStore().add(r);
//                }
//           });
//        }, this);
//
//    this.store.load();
//    
//};
//
//Ext.extend(VariantRankPanel, Ext.Panel, {});
//Ext.reg("variantrankpanel", VariantRankPanel);
//
////Ext.reg("presetfieldset", PresetFieldset);
//
//var PresetFieldsetTest=  Ext.extend(Ext.form.FieldSet, {
//    constructor: function(config) {
//        config = Ext.apply(
//            {
//        id: 'presets',
//        title:'Preset', 
//        autoHeight: 'auto',
//        xtype: 'presetfieldset', 
//        items: [{
//            id: 'preset_list',
//            style: 'margin-bottom:15px;',
//            store: config.preset_store,
//           editable: false,
//            value: config.preset_selected, 
//            name: 'preset',
//            displayField:'name',
//            hiddenName: 'preset',
//            mode: 'local',
//            fieldLabel: 'name',
//            triggerAction: 'all',
//            allowBlank:false, 
//            forceSelection: true,
//            xtype: 'combo', 
//            listeners: {
//                select: function( combo, record, index ) {
//                    
//                    Ext.Ajax.request({
//                        url: '/get_preset_parameters/',
//                        params: {preset_id: record.data.field1, variant_id: Ext.getCmp('grid_variants').getSelectionModel().getSelected().data.pk},
//                        success: function(resp){
//                            var resp = Ext.decode(resp.responseText);
//                            
//                            var prefs = resp.data;
//                                
//                            var preset_fieldset = Ext.getCmp('presets');
//                            var to_remove = [];
//                            for (i = 0; i < preset_fieldset.items.items.length; i++){
//                                
//                                if(preset_fieldset.items.items[i].id != 'preset_list') {
//                                    to_remove.push(preset_fieldset.items.items[i]);
//                                }
//                            }
//                            
//                            for (i = 0; i < to_remove.length; i++) {
//                                preset_fieldset.remove(to_remove[i]);
//                            }
//                            for (i = 0; i < resp.length; i ++ ) {
//                                preset_fieldset.add(resp[i]);
//                            }
//                            Ext.getCmp('form_panel').doLayout();
//                        }
//                });
//            }
//        }
//    }
//                  
//                  
//    ] 
//    }, config);
//        
//        PresetFieldsetTest.superclass.constructor.call(this, config);
//        
//        for (var i = 0; i < config.parameters.length; i ++) {
//            this.add(config.parameters[i]);
//        }
//    }
//    
//});
//
////Ext.reg("presetfieldset", PresetFieldset);
//Ext.reg("presetfieldset", PresetFieldsetTest);
//
//IntField=  Ext.extend(Ext.form.NumberField, {
//    constructor: function(config) {
//        config = Ext.apply(
//            {
//                allowBlank: false, 
//                allowDecimal: false, 
//                enableKeyEvents: true, 
//                minValue:1,
//             
//                listeners: {
//                    specialkey: function(field, e){
//                        if (e.getKey() == e.DOWN && field.getValue() > 1) {
//                            field.setValue(field.getValue() - 1);
//                        }
//                        if(e.getKey() == e.UP) {
//                            field.setValue(field.getValue() + 1);
//                        }
//                    },
//                    render: function(comp){
//                        Ext.QuickTips.register({
//                            target:  comp,
//                            title: '',
//                            text:  'use &uarr; or &darr; to increase or decrease',
//                            enabled: true
//                        });
//                        
//                    }
//                }
//                      
//        
//            }, config);
//        IntField.superclass.constructor.call(this, config);
//        
//        
//    }
//    
//});
//
////Ext.reg("presetfieldset", PresetFieldset);
//Ext.reg("intfield", IntField);
//
//var UploadField= function(config){
//    Ext.apply(this,{
//        autoHeight: true,
//        autoWidth: true,
//        width:'auto',
//        items:[
//            new Ext.form.TextField({})
//        ]
//    });
//    
//    UploadField.superclass.initComponent.apply(this, arguments);
//    
//};
//
//Ext.extend(UploadField, Ext.Panel, {});
//Ext.reg("uploadfield", UploadField);
//
function variants_prefs(){
    var ws_win;
//    
//    var url_submit = '/save_prefs/';
//    var url_prefs = '/get_variant_prefs/';
//    var url_store =  '/get_variants_list/';
//    
//    var form_panel =   new Ext.FormPanel({
//        id: 'form_panel',
//        region: 'center',
//        url: url_submit,
//        formId: 'basic_form_panel',
//        autoScroll: true,
//        media_type: 'image',
//        buttons: [                                
//            {
//                id: 'save_button',
//                text: 'Save',
//                type: 'submit',
//                handler: function(){ 
//                    Ext.getCmp('form_panel').submit_func();
//                    }
//            },
//            {
//                text: 'Close',
//                handler: function(){
//                    ws_win.close();
//                }
//            
//            }
//            ],
//        
//        submit_func:  function(record_to_load){
//            var grid = Ext.getCmp('grid_variants');
//            var form = Ext.getCmp('form_panel');
//            var store = grid.getStore();
//            
//        var record = grid.getSelectionModel().getSelected();
//        var form = this.getForm();
//        if (grid.sources){
//            if (record.data.pk) {
//                return;
//            }
//            Ext.Ajax.request({
//                url: '/new_variant/',
//                params: {media_type:form.media_type,  is_source: true, name: record.data.name},
//                scope: grid,
//                success: function(){
//                    store = this.getStore();
//                    store.load({
//                        scope: this,
//                        callback: function(){
//                            Ext.Msg.alert("", 'Variants saved successfully.'); 
//                            this.getSelectionModel().selectLastRow();
////                            this.startEditing( this.getStore().getCount() - 1, 0)
//                            
//                            }
//                        });
//                    
//                    }
//                });
//                            
//                
//        }
//            
//        else{
//            var order_grid = Ext.getCmp('selected');
//
//            var sources = [];
//            var rank = 1;
//            order_grid.getStore().each(function(r){
//                sources.push({pk: r.data.pk, rank: rank});
//                rank += 1;
//            });
//
//            if(form.baseParams) {
//                form.baseParams.sources = Ext.encode(sources);
//            }
//            else {
//                form.baseParams = {sources:Ext.encode(sources)};
//            }
//        if (!form.baseParams) {
//            form.baseParams= {};
//        }            
//            
//        if (record.data.pk) {
//            form.baseParams.variant = record.data.pk ;
//        }
//        else{
//    //                        media_type = Ext.getCmp('variant_tabs').getActiveTab().title
//            form.baseParams.name =  record.data.name;
//            form.baseParams.media_type=  this.media_type;
//        
//        }
//        
//    //                    this.getForm().baseParams = base_params
//            
//        form.current_values = form.getValues();
//        
//        form.submit({
//            scope: this,
//            success: function(form, action){
//                if (grid.sources) {
//                    Ext.Msg.alert("", 'Variant saved successfully.'); 
//                }
//                else{
//                    
//                    Ext.Msg.alert("", 'Preferences saved successfully. Variants will be re-generated, it could take a while.'); 
//                
//    
//                    if (action.result.pk){
//                        record.set('pk', action.result.pk);                    
//                    }
//                    
//                    record.commit();
//                    if (record_to_load) {
//                        grid.getSelectionModel().selectRecords([record_to_load]);
//                    }
//                    var media_tabs_panel = Ext.getCmp('media_tabs');
//                    var active_tab =  media_tabs_panel.getActiveTab();
//                    var view = active_tab.items.items[0];
//                    var selecteds = view.getSelectedRecords();
//                    var store = view.getStore();
//                    store.reload({
//                        scope: view,
//                        callback:function(){
//                            var ids = [];
//                            for(var i = 0; i<selecteds.length; i++){
//                                ids.push(selecteds[i].data.pk);
//                            }
//                            this.select(ids);         
//                        }
//                    });
//                               
//                }
//                if (Ext.getCmp('variantMenu').store) {
//                    Ext.getCmp('variantMenu').store.reload();
//                }
//            }
//                
//                
//        });
//            
//    }
//    
//    }
//        
//});
//                
//    
//    var grid_variants = new Ext.grid.EditorGridPanel({
//        id: 'grid_variants',
//        sources: false,
////        sources: false,
//        viewConfig: {
//            forceFit: true
//            },
////            form_panel: form_panel,
//        store:  new Ext.data.JsonStore({
//                url: url_store,
//                autoLoad: true,
//                baseParams: {media_type:'image', type: 'generated'},
//                
//                fields:['pk','name', 'is_global'] ,
//                root: 'variants',
//                listeners: {
//                    load: function(store, records,  options){
//                        
//                        if (records.length> 0) {
//                            Ext.getCmp('grid_variants').getSelectionModel().selectFirstRow();
//                        }
//                    }
//                }
//                
//                }),
//        width:150,
//        hideHeaders: true,
//        layout: 'fit',
////        height:500,
//        region:'west',
//        columns:  [{id:'variant_name', header: "name", width: 95,  dataIndex: 'name', editor: new Ext.form.TextField({selectOnFocus:true, allowBlank: false})}],
//        sm: new Ext.grid.RowSelectionModel({
//            singleSelect: true,
//            
//            listeners: {            
//                rowdeselect:function(){
//                    var delete_btn = Ext.getCmp('delete_variant_button');
//                    delete_btn.disable();
//                    },
//                 rowselect: function(sm, index, record){
//                    var delete_btn = Ext.getCmp('delete_variant_button');
//                     
//                    if (record.data.is_global){
//                        delete_btn.disable();
//                    }
//                    else {
//                        delete_btn.enable();
//                    }
//                    if (!sm.grid.sources) {
//                        load_variant_pref(record);
//                    }
//                    
//                }
//            
//            }
//        }),
//        bbar:new Ext.Toolbar({
//            height:28,
//            items:[{
//            text: 'Add', 
//            
//            handler: function(){
//                    var grid = Ext.getCmp('grid_variants');
//                    var form = Ext.getCmp('form_panel');
//                    var store = grid.getStore();
//                    var record_constructor = store.recordType;
//                    var new_variant = new record_constructor({pk: null, name: 'new variant', is_global: false});
//                    new_variant.markDirty();
//                    store.add(new_variant);
//                    
//                    grid.getSelectionModel().selectLastRow();
//                    grid.startEditing( store.getCount() - 1, 0);
//                    Ext.getCmp('form_panel').getForm().current_values = {};
//                        
//                    }
//            
//            
//            
//            }, 
//            {
//                id:'delete_variant_button',
//                text: 'Delete',
//                
//                handler: function(){
//                   var grid = Ext.getCmp('grid_variants');
//                   var record = grid.getSelectionModel().getSelected();
//                    if (!record.data.is_global){
//                        Ext.Msg.confirm('Delete variant', 'Are you sure you want to delete the selected variant?', 
//                        function(btn){
//                            if(btn == 'yes'){
//                                Ext.Ajax.request({
//                                    scope: grid,
//                                    url: '/delete_variant/',
//                                    params: {variant_id:record.data.pk},
//                                    success:function(){
//                                        this.getStore().load({
//                                            scope: this
//                                            
//                                            });
//                                        }
//                                    });
//                                
//                                }
//                            
//                            });
//                        
//                        }
//                    
//                    }
//                
//                }]
//                
//            }),
//        buttonAlign: 'center',
//        listeners:{
//                afteredit: function(e){
//                    
//                    if (e.record.data.pk) {
//                        Ext.Ajax.request({
//                            url: '/edit_variant/',
//                            params: {variant_id: e.record.data.pk, name: e.value},
//                            callback: function(){
//                                if (this.data.pk) {
//                                    this.commit();
//                                }
//                            },
//                            scope: e.record
//                            
//                            });
//                    }
//                },
//            beforeedit: function(e){
//                if (e.record.data.is_global) {
//                    return false;
//                }
//                else {
//                    return true;
//                }
//            }
//            
//        },
//        
//        cell_clicked: function(record){
//            if (this.current_cell_record == record) {
//                return;
//            }
//        }
//        
//    });
//                
//    
//    function select_variant(prefs, record){
//
//        form_panel.removeAll(true);        
//        
//        for(var j=0; j< prefs.length; j++){
//            
//            try{
//                form_panel.add(prefs[j]);
//                
//            }
//            catch(e){
//            }
//            
//        }
//        
//        form_panel.getForm().getEl().unmask();
//        form_panel.getEl().unmask();
//        
//        try{
//            form_panel.doLayout();
//        }
//        catch(e){
//        }
//        
//        var form = form_panel.getForm();
//        if (record.data.pk)  {
//            form.current_values = form.getValues();
//        }
//        else { //new variant...
//            form.current_values = {};
//        }            
//    }
//    
//    var load_variant_pref = function(record){                
//            
//            var form = form_panel.getForm();
//            form.getEl().unmask();
//            form_panel .getEl().mask('Loading');
//            form.current_values = form.getValues();
//            var params;
//            if (record.data.pk) {
//                params = {variant_id: record.data.pk};
//            }
//            else{
//                var tab_panel = Ext.getCmp('variant_tabs');
//                
//                params = {media_type: form_panel.media_type};
//                
//            }
//            Ext.Ajax.request({
//                url: '/get_variant_prefs/',
//                params: params,
//                success: function(resp){
//                    var resp = Ext.decode(resp.responseText);
//                    var prefs = resp.data;
//                    select_variant(prefs,  record );
//                    }
//                
//                });
//                
//        };
//    
//    
//    function switch_toolbar(id, item){        
//        Ext.getCmp(id).setText( item.text);   
//    }    
//    
    
    function edit_window(variant_id){
    	var win;
    	var form = new Ext.form.FormPanel({
    		id:'form_variant',
    		buttonAlign: 'center',
            frame: true,
            monitorValid: true,
            clienValidation: true,
            items:[new Ext.form.TextField({
                fieldLabel: 'name' ,
                name: 'name',
                id: 'name',
                allowBlank: false
                }),
                new Ext.form.CheckboxGroup({
                    id:'media_type_selection',
                    allowBlank: false,
                    validationEvent: 'click',
                    fieldLabel: 'Media Type',
                    columns: 2,
                    listeners:{
                		invalid: function(){
                			console.log('invalid');
                		},
                		valid: function(){
                			console.log('valid');
                		}                	
                	
                	},
                    items: [
                        {boxLabel: 'Image', name: 'image', id: 'image'},
                        {boxLabel: 'Video', name: 'video',id: 'video'},
                        {boxLabel: 'Audio', name: 'audio', id:'audio'},
                        {boxLabel: 'Doc', name: 'doc', id: 'doc'}
                    ]
                })
                
                ],
                buttons:[{
                	text: 'Save',
                	handler: function(){
                	var params;
                	if (variant_id)
                		params = {variant_id: variant_id};
                	else
                		params = {}
                	
                		Ext.getCmp('form_variant').getForm().submit({
                			clientValidation: true,
                		    url: '/edit_variant/',
                		    params: params,
                		    success: function(){
                				Ext.getCmp('variant_grid').getStore().reload();
                				win.close();
                			},
                			failure: function(form, action) {
                				console.log('action.failureType');
                				console.log(action);
                				console.log(form);
                			}
});
                	}
                },
                {
                	text: 'Cancel',
                	handler: function(){
                		win.close();
                	} 
                	
                	
                }]
        });
    	Ext.getCmp('form_variant').getForm().on('beforeaction', function(){
    		Ext.getCmp('media_type_selection').validate();
    		
    	});
    	
    	win =new Ext.Window({
            layout      : 'fit',
            constrain: true,
            title: '<p style="text-align:center">Add Rendition</p>',
            width       : 350,
            height      : 200,
            modal: true,
            items:[form]
        });
    	
    	if (variant_id)
    		form.getForm().load({
    			url: '/get_variant_info/',
    			params:{
    				variant_id: variant_id
    			}
    			
    		});
        win.show();
    }
    
    function create_tab(){
    	var store = new Ext.data.JsonStore({
    	    autoDestroy: true,
    	    url: '/get_variants_list/',
    	    root: 'variants',
    	    multiSelect: false,
    	    autoLoad: true,
            baseParams: {type: ''},
                
    	    fields: ['pk','name', 'is_global']

    	});
    	var list_variant = new Ext.grid.GridPanel({
//    		layout:'fit',
    	    store: store,
            id: 'variant_grid',
    	    hideHeaders: true,
    	    viewConfig:{
    	    	forceFit:true
    	    },
    	    columns: [{
    	        header: 'variant',    	       
    	        dataIndex: 'name',
                editable: true,
                editor:  new Ext.form.TextField()
    	        
    	    }],
    	    sm: new Ext.grid.RowSelectionModel({
    	    	listeners:{
    	    		selectionchange: function(sm){
	    	    		variant_selected = sm.getSelected();
	    	    		console.log(variant_selected);
	    	    		
	    	    		if (variant_selected){
	    	    			if (!variant_selected.data.is_global){
	    	    				Ext.getCmp('edit_variant').enable();
	    	    				Ext.getCmp('remove_variant').enable();
	    	    				return;
	    	    			}
	    	    			
	    	    				
	    	    		}
	    	    		
    	    			Ext.getCmp('edit_variant').disable();
	    				Ext.getCmp('remove_variant').disable();
    	    		
	    	    			
    	    	
    	    		}
    	    	
    	    	}
    	    })
    	});

        var type_id = 'variant_type';
    	
        return new Ext.Panel({
    		layout:'fit',
    		items:[list_variant],
    		tbar:[
    		      {
                    text: 'Add',                   
                    handler: function(){
    		    	  edit_window();
                    }
                 },
    			{
    			text: 'Edit',
    			id: 'edit_variant',
    			handler: function(){
                	 var variant_selected = Ext.getCmp('variant_grid').getSelectionModel().getSelected();
                	 if (variant_selected)
                		 edit_window(variant_selected.data.pk);
                   },
//               
                 disabled: true
    		},
    		{
    			text: 'Remove',
    			id: 'remove_variant',
                disabled: true,
                handler: function(){
    			var variant_selected = Ext.getCmp('variant_grid').getSelectionModel().getSelected();
           	 	if (variant_selected)
	           	 	Ext.Msg.confirm(
	           	 	   'Delete Rendtion',
	           	 	   'Are you sure you want to delete the rendition "' +variant_selected.data.name+ '"?',
	           	 	   function(btn){
	           	 			console.log(btn);
		           	 		if (btn == 'yes')
			           	 		Ext.Ajax.request({
			           	 			url: '/delete_variant/',
			           	 			params:{
			           	 				variant_id:variant_selected.data.pk
			           	 			},
			           	 			callback: function(){
			           	 			Ext.getCmp('variant_grid').getStore().reload();
			           	 			}
			           	 			
			           	 		});
	           	 		}
	           	 	   
	           	 	   
	           	 	);
    			
    			}
    		}
    		]
    		
    		
    	});
    	
    	
    };
    
    ws_win = new Ext.Window({
        layout      : 'fit',
        constrain: true,
        title: '<p style="text-align:center">Workspace configuration: renditions</p>',
        width       : 400,
        height      : 300,
        modal: true,
        items:[
        create_tab()]

                
    });

    ws_win.show();
    
}
//
//

