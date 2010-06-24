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

// Helper class for organizing the buttons
var ActionRecord = Ext.data.Record.create([ // creates a subclass of Ext.data.Record
    {name: 'name'},
    {name: 'media_type'},
    {name: 'parameters'}
]);


function scripts_store(){

	var actionMem = new Ext.data.JsonStore({
//	    url: '/get_actions/',
	    root   : 'actions',
	    fields : ['name', 'media_type', 'parameters']
	});
	
// Column Model shortcut array
	var cols = [
		{ id : 'name',  header: "Action", dataIndex: 'name'}
	];

	this.get_actionMem = function() {
		return actionMem
	}

	this.get_actionStore = function(media_type) {
		return 	new Ext.data.JsonStore({
		    url        : '/get_actions/',
		    baseParams : { 'media_type': media_type},
		    method     : 'POST',
		    root       : 'actions',
		    fields     : ['name', 'media_type', 'parameters'],
		    autoLoad   : true
		});
	}

	this.get_cols = function() {
		return cols
	}
	this.get_sourceStore = function(media_type){
		return new Ext.data.JsonStore({
		    url        : '/get_variants_list/',
		    method     :'POST',
		    autoLoad   :true,
		    baseParams : { 'media_type': media_type, type: 'source' },
		    root       : 'variants',
		    fields     : ['pk',  'name', 'is_global']
	    });
	}
}

function reset_watermarking(){	
    for (i=1; i<10; i++){
        Ext.get('square'+i).setStyle({
            background: 'none',
            opacity: 1
            });
    }
}

function _set_hidden_position_percent(id){
	var pos_x = ((id-1) % 3) * 33 + 5;
	var pos_y = (parseInt((id-1) / 3)) * 33 + 5;
	console.log(pos_x);
	console.log(pos_y);
	Ext.getCmp('panel_watermarks_views').get('hidden_pos_x_percent').setValue(parseInt(pos_x));
	Ext.getCmp('panel_watermarks_views').get('hidden_pos_y_percent').setValue(parseInt(pos_y));
}

function watermarking(id){	
    reset_watermarking();
    _set_hidden_position_percent(id);
    Ext.get('square'+id).setStyle({
        background: 'green',
        opacity: 0.6
        });
    watermarking_position = id;
}

function _update_watermarks(){  
	Ext.getCmp('dataview_watermarks').getStore().load();
}

function _check_form_detail_script(my_win){
	//verificare che tutti i campi siano selezionati.
	console.log('check');
	var flag = true;
	var StoreGridTabs = {}; // for (key in dict)
	for (i=0;i<my_win.get('media_type_tabs').items.items.length;i++){
		var name_tab = my_win.get('media_type_tabs').items.items[i].id;
		var type = name_tab.slice(4);
		StoreGridTabs[name_tab] = my_win.get('media_type_tabs').get(name_tab).get('my_action_'+type).getStore();
//		pipeline['actions_media_type'][type]['source_variant'] = my_win.get('media_type_tabs').get(name_tab).get('my_panel_source_'+type).get('my_combo_source_'+type).getRawValue();
//		pipeline['actions_media_type'][type]['actions'] = [];
//		j = -1;
		StoreGridTabs[name_tab].each(function(rec){
//			j++;
			params = rec.data;
			console.log(params);
			for(k=0;k<params.parameters.length;k++){
				if (!params.parameters[k].value){
					console.log('parametro null.');
					console.log(params.parameters);
					flag = false;
				}
			}
		});
	}
	return flag;
}

function _global_generate_details_form(grid, selected, actionsStore, media_type, parameters, name_action )
{
    var i = 0;
    var recApp;
    var item_array = new Array();
    
    for (i=0;i<parameters.length;i++){
//    	cercare il name_action nella gridlistactions, e verificare se ha values
        recApp = actionsStore.getAt(actionsStore.findExact('name', name_action));
        
        //in sendbymail restituisce in ordine inverso.
        if (parameters[i].name != recApp['data']['parameters'][i].name){
        	var j = 0;
        	while (parameters[i].name != recApp['data']['parameters'][j].name) {
        		  j++;
        	}
        }else j = i;
        
    	if (recApp['data']['parameters'][j]['values']){
    		var val;
    		var recAppValues = recApp['data']['parameters'][j]['values'][media_type];
    		
    		if (parameters[i]['value']) 
    			val = parameters[i]['value'];
    		else 
    			val = recApp['data']['parameters'][j]['values'][media_type][0];
    		console.log(val);
    		item_array.push(new Ext.form.ComboBox({                            
    			fieldLabel   : parameters[i].name.replace("_"," "),
    			store        : recAppValues,
				triggerAction: 'all',
				value        : val,
				name         : parameters[i].name
    	    }));
    	}
    	else if (parameters[i].type == 'number'){
    		item_array.push(new Ext.form.NumberField({                            
    	          fieldLabel: parameters[i].name.replace("_"," "),
    	          value     : parameters[i].value,
    	          name      : parameters[i].name,
    	          msgTarget :'side'                            
    	      	}));
    	}
    	else if (parameters[i].type == 'string'){
    		item_array.push(new Ext.form.TextField({                            
	          fieldLabel  : parameters[i].name.replace("_"," "),
	          value       : parameters[i].value,
	          name        : parameters[i].name,
	          msgTarget   : 'side'                            
	      	}));
    	}
    }
    
	return item_array;
}

function _watermark_generate_details_forms(panel, grid, selected, actionsStore, media_type, parameters)
{
	watermarking_position = 0; // 0 mean undefined

	watermarking_position_id = Ext.id();
    
	var children_box_position = [];
	for(i=1; i<= 9; i++){
	    children_box_position.push({
	        tag:'div',
	        id: 'square' + i,
	        cls: 'position_watermarking',
	        onclick: String.format('watermarking({0}); Ext.getCmp("{1}").setValue({0})', i, watermarking_position_id)
	    })
	}

	var box_position_div = {
	    tag:'div',
	    cls: 'container_position_watermarking',
	    children:children_box_position
	}; 

	var id_watermark = Ext.id();
	var storeview = new Ext.data.JsonStore({
	    url      : '/get_watermarks/',
	    method   :'POST',
	    root     : 'watermarks',
	    fields   : ['id', 'file_name', 'url'],
	    listeners :{ 
	    	load : function(){
				i = 0;
				while (parameters[i]['name'] != 'filename' && i<parameters.length)
					i++;
				if (parameters[i]['name'] == 'filename' && parameters[i]['value']){
					Ext.getCmp('dataview_watermarks').select(this.find('id', parameters[i]['value']));
					Ext.getCmp('panel_watermarks_views').get('hidden_file_name').setValue(parameters[i]['value']);
				}
	    	}
		}
    });
	storeview.load();

	panel.add(
			{ 
	            layout:'column', 
	            items:[{ 
	                columnWidth:.27, 
	                layout: 'form', 
	                hideLabels: true,
	                items: [
	                	new Ext.form.Field({
    			    	    id : watermarking_position_id,
    			    	    name: 'watermarking_position',
    			    	    autoCreate:{
    			    	        tag:'div',
    				    	    cls: 'container_position_watermarking',
    				    	    children:children_box_position
    				        },
    			    	    listeners:{
    			    	        render: function(){
    				            	i = 0;
    				        		while (parameters[i]['name'] != 'pos_x_percent' && i<parameters.length){
    				        			i++;
    				        		}	
				        			if (parameters[i]['name'] == 'pos_x_percent' && parameters[i]['value']){      			    	            	
        				        		var pos_x = ((parameters[i]['value'] - 5) / 33) + 1;
	                					var pos_y = ((parameters[i+1]['value'] - 5) / 33) + 1;
        				        		watermarking_position = (pos_y-1) * 3 + pos_x;
    			    	            	watermarking(watermarking_position);                    
    			    	                Ext.getCmp(watermarking_position_id).setValue(watermarking_position);
    			    	            }else    				        			
    				        		if(watermarking_position != 0){
    				        			watermarking(watermarking_position);                    
    			    	                Ext.getCmp(watermarking_position_id).setValue(watermarking_position);
    			    	            }
    			    	            else{
    			    	                watermarking(1);
    			    	                Ext.getCmp(watermarking_position_id).setValue(1);
    			    	            }
    				        	}                
    				        }            
    		    		})    	                	
	                ] 
	            },{
                columnWidth:.73, 
                layout: 'form', 
                items: [
                    	new Ext.Panel({
                    	    id : 'panel_watermarks_views',
                    		frame:true,
                    	    title:'Select Watermark',
                    	    autoScroll : true,
                    	    height : 140,
                    	    bbar : [new Ext.Button({
                    			text : 'Upload',
                    			width : 216,
                    			handler: function() {
                    				var up = new Upload('/upload_watermark/', true, {}, _update_watermarks);
                    				up.openUpload();
                    			}
                    		}),
                    		new Ext.Button({
                    			text : 'Delete',
                    			width : 216,
                    			handler: function() {
                	        		if (Ext.getCmp('dataview_watermarks').getSelectedRecords().length > 0){
                        				Ext.Ajax.request({
                    	                    url: '/delete_watermark/',
                    	                    params:{ 
                    	        				watermark : Ext.getCmp('dataview_watermarks').getSelectedRecords()[0].data.id
                    	        			},
                    	                    success: function(response) {
                    	                        if (Ext.decode(response.responseText)['success']){
                    	                        	Ext.MessageBox.alert('Success', 'Watermark removed.');
                    	                        	_update_watermarks();
                    	                        }else
                    	                        	Ext.MessageBox.alert(Ext.decode(response.responseText));
                    	                    }
                    	                });
                	        		}else
                	        			Ext.MessageBox.alert('Success', 'Select one watermark!');
                    			}
                    		})
                    	    ],
                    	    items:[
                				new Ext.DataView({
                					id : 'dataview_watermarks',
                					enable : true,
                					autoHeight:true,
                					autoScroll : true,
                					singleSelect: true,
                		            itemSelector: 'div.watermark-wrap',
                				    store: storeview,
                		    	    tpl : new Ext.XTemplate(
                		    	    		'<tpl for=".">',
                		    	            '<div class="watermark-wrap" id="{id}">',
                		    			    '<div class="watermark"><img src="{url}" title="{file_name}" width="50" height="50"></div></div>',
                		    	        '</tpl>'
                		    		),
                				    emptyText: 'No images to display',
                				    listeners :{ 
                						click  : function(index, node, e){
                							//set filename to hidden.
                							Ext.getCmp('panel_watermarks_views').get('hidden_file_name').setValue(index.getSelectedRecords()[0].data.id);
                						}
                					}	                					
                				}),{
                					xtype:'hidden', 
                					id : 'hidden_file_name',
                					name:'filename'
                				},{
                					xtype:'hidden', 
                					id : 'hidden_pos_x_percent',
                					name:'pos_x_percent'
                				},{
                					xtype:'hidden', 
                					id : 'hidden_pos_y_percent',
                					name:'pos_y_percent'
                				},{
                					xtype:'hidden', 
                					id : 'hidden_alpha',
                					name:'alpha',
                					value: '1'
                				}
                    	    ]
                    	})
                    ]
	            }]
	        }         
			);

	return panel;
}

function _crop_generate_details_forms(panel, grid, selected, actionsStore, media_type, parameters, name_action)
{
	console.log(name_action);
	panel2 = new Ext.Panel({
    	frame:true,
	});
	panel.add(
			{ 
	            layout:'column', 
	            items:[{ 
	                columnWidth:.5,
	                layout : 'form',
	                items: [{
	                    xtype: 'checkbox',
	                    boxLabel: 'Custom',
	                    listeners: {
	                		check : function(checked){
	    						if (checked){
		                			//able all input text 
	    							console.log()
	    						}else{
	    							//disable all input text
	    						}
	                		}
	                	}
	                },_global_generate_details_form(grid, selected, actionsStore, media_type, parameters, name_action )]
	            },{
	            	columnWidth:.5,
	            	layout : 'form',
	                items : [{
						xtype: 'radiogroup',
						fieldLabel: 'Standard crop',
			            columns: 1,
						items: [
						    {boxLabel: 'Item 1', name: 'rb-auto', inputValue: 1},
						    {boxLabel: 'Item 2', name: 'rb-auto', inputValue: 2, checked: true},
						    {boxLabel: 'Item 3', name: 'rb-auto', inputValue: 3},
						    {boxLabel: 'Item 4', name: 'rb-auto', inputValue: 4}
						]
	                	}
	                ]
	            }]
	        }         
	);

	return panel;
	
}

function generate_details_forms(panel, grid, selected, actionsStore, media_type) {

	console.log('generate_details_forms');
    var name_action = selected.data.name;
    var parameters = selected.get('parameters');
    var array_field;
//  console.log('generate_detail_form')
// remove all component
    panel.removeAll()

    //add new component
    if (name_action == 'watermark'){
    	panel = _watermark_generate_details_forms(panel, grid, selected, actionsStore, media_type, parameters, name_action );
    }else if (name_action == 'crop'){
    	panel = _crop_generate_details_forms(panel, grid, selected, actionsStore, media_type, parameters, name_action );
    }else{
    	
    	array_field = _global_generate_details_form(grid, selected, actionsStore, media_type, parameters, name_action );
    	panel.add(array_field);
    }
//reload panel
	panel.doLayout();
}

function newRecord(data, media_type){
	//why copy() not work
	var cloned_parameters = [];
	var tmp = {};
	for (var i=0; i < data.parameters.length; i++) {
		current_param = data.parameters[i];
		tmp = {};
		tmp['name']  = current_param['name'];
		tmp['type']  = current_param['type'];
		if (current_param['values']){
			tmp['values'] = current_param['values'][media_type];
		}else{
			tmp['value'] = current_param['value'];
		}
		cloned_parameters.push(tmp);
	}
	return new ActionRecord({name: data.name, parameters: cloned_parameters});
}

function _pull_data(sm,media_type){
//	console.log("_pull_data");

	if 	(sm.getSelected()){
		var newParams = [];
		var appParams = {};
		var r = sm.getSelected();
    	var params = r.get('parameters');

    	for (i=0;i<params.length;i++){
    		appParams = params[i];
    		appParams['value'] = Ext.getCmp('detailAction_'+media_type).getForm().getFieldValues()[appParams.name];
    		newParams.push(appParams); 
	    }
//    	console.log(newParams);
	    r.set('parameters',newParams);
	    r.commit();
	}
}

function _get_layout_tab(obj, media_type){
	var cols = obj.get_cols();
	var actionStore = obj.get_actionStore(media_type);
	var actionMem = obj.get_actionMem();
	var sourceStore = obj.get_sourceStore(media_type);

	var comboSource = new Ext.Panel({
		id          : 'my_panel_source_'+ media_type,
	    region      : 'north',
	    height      : 35,
	    layout      : 'hbox',
		layoutConfig: {
            pack:'center',
            align:'middle'
        },
        frame : true,
	    items  :[
	            new Ext.form.ComboBox({
	        		id           : 'my_combo_source_'+ media_type,
	        		store        : sourceStore,
				    displayField : 'name',
				    typeAhead    : true,
				    mode         : 'local',
				    triggerAction: 'all',
				    resizable    : false,
				    autoSelect   : true,
				    value : 'original' //TODO 
				})
	    ]
	});
	
	var my_action = new Ext.grid.GridPanel({
	    region           : 'west',
        title            : 'Your script action',
        id               : 'my_action_'+media_type ,
		width            : 300,
	    store            : actionMem,
	    columns          : cols,
	    stripeRows       : true,
	    autoExpandColumn : 'name',
		frame            : true,
        hideHeaders      : true,
		sm               : new Ext.grid.RowSelectionModel({
								singleSelect : true,
								listeners    :{
									beforerowselect : function(sm,rowIndex, keepExisting, record){
								        //pull data
//										console.log('before');
								        _pull_data(sm,media_type);

							        	return true;
									}, 
									selectionchange : function(){
							        	//show form details
										if (this.getSelected()){
								        	generate_details_forms(Ext.getCmp('detailAction_'+media_type),this.grid, this.getSelected(),Ext.getCmp('action_list_'+media_type).getStore(), media_type);
										}

										
									}			
								}
							})

	});

	var action_list = new Ext.grid.GridPanel({
	    region           : 'east',
        title            : 'List available action',
        id               : 'action_list_'+media_type ,
		width            : 300,	
	    store            : actionStore,
	    columns          : cols,
	    stripeRows       : true,
	    autoExpandColumn : 'name',
		frame            : true,
        hideHeaders      : true,
		sm               : new Ext.grid.RowSelectionModel({singleSelect : true})
    });

	var detailAction = new Ext.FormPanel({
        title       : 'Details',
        id          : 'detailAction_'+media_type,
	    region      : 'south',
	    height      : 180,
	    frame       : true
	});

	var button_panel =new Ext.Panel({
        region  : 'center',
        id      : 'buttons_panel_'+media_type, 
        html    : '<div style="text-align:center; padding-top:80;"><img style="margin:2px" src="/files/images/up2.gif" onclick="Ext.getCmp(' +"'buttons_panel_"+media_type +"'" +' ).move_to_up()" /><br/><img style="margin:2px" src="/files/images/down2.gif" onclick="Ext.getCmp(' +"'buttons_panel_"+media_type +"'" +' ).move_to_down()"/><img style="margin:2px" src="/files/images/left2.gif" onclick="Ext.getCmp(' +"'buttons_panel_"+media_type +"'" +' ).move_to_left()" /><br/><img style="margin:2px" src="/files/images/right2.gif" onclick="Ext.getCmp(' +"'buttons_panel_"+media_type +"'" +' ).move_to_right()"/> </div>',
        
	    move_to_up:function(){
	        var grid = Ext.getCmp('my_action_'+media_type);
	        var record_selected = grid.getSelectionModel().getSelected();
	        if(record_selected){
	            var rank = grid.getStore().indexOf(record_selected);
	            if (rank > 0){
	                grid.getStore().remove(record_selected);
	                grid.getStore().insert(rank - 1, record_selected);
	                grid.getSelectionModel().selectRecords([record_selected]);
	            }
	        }
	            
	    },   

	    move_to_down: function(){
	        var grid = Ext.getCmp('my_action_'+media_type);
	        var record_selected = grid.getSelectionModel().getSelected();
	        if(record_selected ){
	            var rank = grid.getStore().indexOf(record_selected);
	            if (rank < grid.getStore().getCount() - 1){
	                grid.getStore().remove(record_selected);
	                grid.getStore().insert(rank +1, record_selected);
	                grid.getSelectionModel().selectRecords([record_selected]);
	            }
	        }
	        
	    },

        move_to_left: function (){
	        var selected_grid = Ext.getCmp('action_list_'+media_type);
	        var available_grid = Ext.getCmp('my_action_'+media_type);
	        if (selected_grid.getSelectionModel().hasSelection()){
	        	//define parameters through form
	        	var selected  = selected_grid.getSelectionModel().getSelected();
	        	//why copy() not work
	        	var newRec = newRecord(selected.data,media_type);
	        	
	        	available_grid.getStore().add(newRec);
	        	available_grid.getSelectionModel().selectLastRow();
	        }else{
				// Show a dialog using config options:
				Ext.Msg.show({
				   title:'Warning',
				   msg: 'You must select one row!',
				   width: 300,
				   buttons: Ext.Msg.OK,
				   icon: Ext.MessageBox.WARNING
				});	        				
			}
	     },  

	    move_to_right: function(){
	        var selected_grid = Ext.getCmp('my_action_'+media_type);
	        var available_grid = Ext.getCmp('action_list_'+media_type);
	        if (selected_grid.getSelectionModel().hasSelection()){
	        	var selected  = selected_grid.getSelectionModel().getSelected();
	        	selected_grid.getStore().remove(selected);
	        	Ext.getCmp('detailAction_'+media_type).removeAll();
	        }
	     }
        
    }); 	

    return [comboSource, my_action, button_panel, action_list, detailAction];
}

function _get_tabs(){
	
	var objImage =  new scripts_store();
	var objVideo =  new scripts_store();
	var objAudio =  new scripts_store();
	var objDoc   =  new scripts_store();
	var layoutImage   = _get_layout_tab(objImage,'image');
	var layoutVideo   = _get_layout_tab(objVideo,'video');
	var layoutAudio   = _get_layout_tab(objAudio,'audio');
	var layoutDoc     = _get_layout_tab(objDoc,'doc');
	
	var tabs = new Ext.TabPanel({
		id: 'media_type_tabs',
		activeTab : 'tab_image',
		defaults:{layout:'fit'},
		items: [{
	        title: 'Image',
	        id : 'tab_image',
	        layout: 'border',
	    	items : [layoutImage]
	    },{
	        title: 'Video',
	        id : 'tab_video',
	        layout: 'border',
	        items : [layoutVideo]
	    },{
	        title: 'Audio',
	        id : 'tab_audio',
	        layout: 'border',
	    	items : [layoutAudio]
	    },{
	        title: 'Doc',
	        id : 'tab_doc',
	        layout: 'border',
	    	items : [layoutDoc]
	    }
	    ],
	    listeners :{
			beforetabchange : function(newTab, currentTab) {
				var type = currentTab.id.slice(4);
				_pull_data(Ext.getCmp('my_action_'+type).getSelectionModel(), type);
	    	}
	    } 	    
	    	

	});
	return [tabs]
}

function _get_scripts_fields(name, description){

	console.log('_get_scripts_fields');
	
	var field_name = new Ext.form.TextField({
        fieldLabel: 'Name',
        id : 'script_id',
        name: 'name', 
        allowBlank:false,
        enableKeyEvents: true,
        listeners: {render: function() {this.focus(true, 100);},
            keydown: function(field, e){
                var my_win = this.findParentByType('window');
            }
        }
    });
    
    var field_description = new Ext.form.TextArea({
        fieldLabel: 'Description',        
        name: 'description',
        allowBlank:true,
        height: 100
    });

    return [field_name,field_description];
    
}

function save_data_script(name, description, my_win){
	//Post:
	//name=name
	//description=description
	//pipeline={view scripts_test.py}
	var i = 0; //count
	var j,k; //count
	var pipeline = {};
	pipeline['name'] = name;
	pipeline['description'] = description;
	//pipeline['event'] = "";
	pipeline['state'] = "";
	pipeline['actions_media_type'] = {};
	var StoreGridTabs = {}; // for (key in dict)
	for (i=0;i<my_win.get('media_type_tabs').items.items.length;i++){
		var name_tab = my_win.get('media_type_tabs').items.items[i].id;
		var type = name_tab.slice(4);
		StoreGridTabs[name_tab] = my_win.get('media_type_tabs').get(name_tab).get('my_action_'+type).getStore();
		pipeline['actions_media_type'][type] = {};
		pipeline['actions_media_type'][type]['source_variant'] = my_win.get('media_type_tabs').get(name_tab).get('my_panel_source_'+type).get('my_combo_source_'+type).getRawValue();
		pipeline['actions_media_type'][type]['actions'] = [];
		j = -1;
		StoreGridTabs[name_tab].each(function(rec){
			j++;
			params = rec.data;
			pipeline['actions_media_type'][type]['actions'][j] = {};
			pipeline['actions_media_type'][type]['actions'][j]['type'] = params.name;
			pipeline['actions_media_type'][type]['actions'][j]['parameters'] = {};
			for(k=0;k<params.parameters.length;k++){
				pipeline['actions_media_type'][type]['actions'][j]['parameters'][params.parameters[k].name] = params.parameters[k].value;
			}
		});
	}
//	console.log('pipeline');
//	console.log(pipeline);
	return pipeline;
	
}

function reload_main_data_view(){
	var tab = Ext.getCmp('media_tabs').getActiveTab();
    var view = tab.getComponent(0);
    var store = view.getStore();
    store.reload();
}
function new_script(create, name, description, id_script, is_global, run){
	//create true new_script
	//create false edit_script
	var tabs = _get_tabs();
	if (run)
		text_button_submit = 'Save and Run';
	else
		text_button_submit = 'Save';
	
    var edit_script_win = new Ext.Window({
        id:'general_form',
        constrain   : true,
        title       : name,
        layout      : 'fit',
	    width       : 650,
	    height      : 570,
        modal: true,
        resizable : false,
        items:[tabs],
        buttons: [{
            id: 'save_details_button',
            text: text_button_submit,
            type: 'submit',
            handler: function(){
    			var my_win = this.findParentByType('window');  
    			var type = my_win.get('media_type_tabs').getActiveTab().id.slice(4);
    			_pull_data(Ext.getCmp('my_action_'+type).getSelectionModel(), type);
    			if (_check_form_detail_script(my_win)){
					var pipeline = save_data_script(name, description, my_win);
	
					if(create){
	    				script_detail_form(null, null, null, false, pipeline, my_win, run);
					}else{
		        		//chiamata ajax

						Ext.Ajax.request({
		                    url: '/edit_script/',
		                    params:{ 
		        				name        : pipeline['name'],
		        				description : pipeline['description'],
		        				script : id_script,
		        				actions_media_type : Ext.encode(pipeline['actions_media_type'])
		        			},
		                    success: function(response) {
		                        if (Ext.decode(response.responseText)['success']){
		                        	if (is_global){
		    		        			Ext.Msg.show({
		    		        				   title:'Option.',
		    		        				   msg: 'This global script is saved, do you want to run on all objects in the workspace?',
		    		        				   width: 300,
		    		        				   buttons: Ext.Msg.YESNO,
		    		        				   fn: function(btn){
				    		        			    if (btn == 'yes'){
				    		        			    	//run script
				    		        			    	Ext.Ajax.request({
				                					        url: '/run_script/',
				                			                params: {
				    		        			    			script_id : id_script,
				                								run_again : true
				                							},
				                					        success: function(data){
				                								reload_main_data_view();
				                					        }
				                						});
				    		        			    }
		    		        					},
		    		        				   animEl: 'elId',
		    		        				   icon: Ext.MessageBox.QUESTION
		    		        				});	
		    		        		}else
		    		        			Ext.MessageBox.alert('Success', 'Script saved.');
		                        		my_win.close();
		                        }else
		                        	Ext.MessageBox.alert(Ext.decode(response.responseText));
		                    }
		                });
			    	}
    			}else{
    				Ext.Msg.show({
    					   title:'Warning',
    					   msg: 'Fill in all fields relating to shares.',
    					   width: 300,
    					   buttons: Ext.Msg.OK,
    					   icon: Ext.MessageBox.WARNING
    					});	 
    			}

            }
        },{
            text: 'Cancel',
            id: 'reset_details_button',
            handler: function(){
                var my_win = this.findParentByType('window');
                my_win.close();
            }
        }]
    });

    edit_script_win.show();     
}

function newRecordLoad(data,type){
	var cloned_parameters = [];
	var tmp = {};
//	console.log(data.parameters);
	//for get list of actions
	for (name in data.parameters) {
		tmp = {};
		tmp['name']  = name;
		if (!isNaN(data.parameters[name])){
			tmp['type']  = 'number';
		}else
			tmp['type']  = 'string';

		if (data.parameters[name])
			tmp['value'] = data.parameters[name];
			//get list of values if exist
//			if()
//				tmp['values'] = 
		else
			tmp['value'] = "";
		cloned_parameters.push(tmp);
	}

	return new ActionRecord({name: data.type, parameters: cloned_parameters});

}

function load_data_script(data){
//	console.log('load');
//	console.log(data);
	var i;//count
	var type, name_tab;
	var my_win = Ext.getCmp('general_form');
	for(type in data['actions_media_type']){
		name_tab = 'tab_' + type;
		my_win.get('media_type_tabs').get(name_tab).get('my_panel_source_'+type).get('my_combo_source_'+type).setValue(data['actions_media_type'][type]['source_variant']);
		//load actions
		for(i=0;i<data['actions_media_type'][type]['actions'].length;i++){
        	var newRec = newRecordLoad(data['actions_media_type'][type]['actions'][i],type);
        	my_win.get('media_type_tabs').get(name_tab).get('my_action_'+type).getStore().add(newRec);
		}

	}
}

//Show windows form scripts data ()
function script_detail_form(id_script, name, description, flag, pipeline, main_win, run){
	var title;
	
	if (flag == false){
		title = 'New Script';
		var fields = _get_scripts_fields(name, description);
	}else{
		title = 'Change parameters';
		var fields = _get_scripts_fields(name, description);
	}
	
	var script_detail_win = new Ext.Window({
	    constrain   : true,
	    title       : title,
	    layout      : 'fit',
	    width       : 450,
	    height      : 240,
	    modal: true,
	    resizable : false,
	    items:[new Ext.FormPanel({
	        id : 'form_detail_script',
	    	frame:true,
	        defaults: {width:300},
	        defaultType: 'textfield',
	        items:[fields]
	    })],
	    listeners :{ 
	    	render : function(){
				if (flag){
					fields[0].setValue(name);
					fields[1].setValue(description);
				}
			}
		},
        buttons: [{
	        id: 'ok_name_description_button',
	        text: 'Ok',
	        type: 'submit',
	        handler: function(){
		    		var my_win = this.findParentByType('window');
		    		var my_form = Ext.getCmp('form_detail_script');
		    		//if(field_name.value) not work
		    		if (flag){
		    			my_form.getForm().submit({
		    				url: '/rename_script/',
		                    params:{ 
		        				name        : fields[0].getValue(),
		        				description : fields[1].getValue(),
		        				script : id_script
		        			},
		                    success: function(form, action) {
//		        				console.log(form);
//		        				console.log(action);
	                        	Ext.MessageBox.alert('Success', 'Changes saved!');
	                        	my_win.close();
	    		        		main_win.get('open_form').get('my_scripts').getStore().reload();
		                    },
		        			failure: function(form, action) {
		                    	Ext.MessageBox.alert(Ext.decode(action.response.responseText));
		                    }

		    			});
		    		}else{
		    			//New script
		    			my_form.getForm().submit({
		    				url: '/new_script/',
		                    params:{ 
		        				name        : fields[0].getValue(),
		        				description : fields[1].getValue(),
		        				state : pipeline['state'] = "",
		        				actions_media_type : Ext.encode(pipeline['actions_media_type'])
		        			},
		                    success: function(form, action) {
	                        	if (run){//this script must be run now.
	                        		var selected_ids = get_selected_items();
            						Ext.Ajax.request({
            					        url: '/run_script/',
            			                params: {
            								items: selected_ids,
            								script_id : Ext.decode(action.response.responseText)['id']
            							},
            					        success: function(data){
            								reload_main_data_view();
            					        }
            						});		                    
	                        	}
	                        	my_win.close();
	                        	main_win.close();
		        			},
		        			failure: function(form, action) {
		                    	Ext.MessageBox.alert('Script NOT saved, please insert Name.');
		                    }

		    			});
		    		}
	    		
	            }
	        },{
	        text: 'Cancel',
	        id: 'reset_name_description_button',
	        handler: function(){
	            var my_win = this.findParentByType('window');
	            my_win.close();
	        }
	    }]          
	});
	script_detail_win.show(); 
	
}

function manage_script(){
	//show choose window
	var manage_script_win = new Ext.Window({
	    constrain   : true,
	    title       : 'Choose your script',
	    layout      : 'fit',
	    width       : 400,
	    height      : 440,
	    modal       : true,
	    resizable   : false,
	    items:[new Ext.FormPanel({
	        id      :'open_form',
		    layout  : 'fit',
	        frame   :true,
	        items:[ 
	           	new Ext.grid.GridPanel({
	                id          : 'my_scripts' ,
	        	    store            : new Ext.data.JsonStore({
	        		    url      : '/get_scripts/',
	        		    method   :'POST',
	        		    autoLoad :true,
	        		    root     : 'scripts',
	        		    fields   : ['id', 'name', 'description', 'actions_media_type', 'already_run', 'is_global']
	        	    }),
	        	    columns          : [
	        		        	        { id : 'name',  header: "Name", dataIndex: 'name', sortable: true, width   : 120},
	        		        	        { id : 'description',  header: "Description", dataIndex: 'description', width : 185},
	        		        	        { id : 'is_global',  header: "Global", dataIndex: 'is_global', width : 45}
	        	    ],
	        	    stripeRows       : true,
	        	    autoExpandColumn : 'name',
	        		frame            : true,
//	                hideHeaders      : true,
	        		sm               : new Ext.grid.RowSelectionModel({
	        								singleSelect : true
	        							})

	           	})
	        ]
	    })],
        buttons: [{
	        text: 'Open',
	        type: 'submit',
	        handler: function(){
		    		var my_win = this.findParentByType('window');
//		    		if(field_name.value) not work
		    		//Open script
		    		if (my_win.get('open_form').get('my_scripts').getSelectionModel().hasSelection()){
			    		var data = my_win.get('open_form').get('my_scripts').getSelectionModel().getSelected().data;
			    		my_win.close();
			    		new_script(false, data.name, data.description, data.id, data.is_global, false);
			    		load_data_script(data);
		    		}
	            }
	        },{
	        text: 'Cancel',
	        handler: function(){
		            var my_win = this.findParentByType('window');
		            my_win.close();
	        	}
	        },{
		        text: 'Delete',
		        id: 'delete_script_button',
		        handler: function(){
		            var my_win = this.findParentByType('window');
		    		if (my_win.get('open_form').get('my_scripts').getSelectionModel().hasSelection()){
			            var selScript = my_win.get('open_form').get('my_scripts').getSelectionModel().getSelected();
			            console.log(selScript);
	            		if (!selScript.data.is_global){
				            Ext.Ajax.request({
		                        url: '/delete_script/',
		                        params:{ 
		            				script : selScript.data.id
		            			},
		                        success: function(response) {
//		                            if (Ext.decode(response.responseText)['success'])
//		                				Ext.MessageBox.alert('Script deleted');
//		                            else
//		                            	Ext.MessageBox.alert('Script NOT deleted');
		                        }
		                    });
		            		my_win.get('open_form').get('my_scripts').getStore().reload();
		    			}else{
		    				Ext.Msg.show({
		    					   title:'Warning',
		    					   msg: 'Selected script can not be deleted.',
		    					   width: 300,
		    					   buttons: Ext.Msg.OK,
		    					   icon: Ext.MessageBox.WARNING
		    					});
		    			}
		    		}
		     	}
	        },{
	            text: 'Change paramenters',
	            id: 'change_paramenters_script_button',
	            handler: function(){
	        		var my_win = this.findParentByType('window');
		    		if (my_win.get('open_form').get('my_scripts').getSelectionModel().hasSelection()){
			    		var data = my_win.get('open_form').get('my_scripts').getSelectionModel().getSelected().data;
		        		script_detail_form(data.id, data.name, data.description, true, null, my_win);

		    		}
	            }
	        }]          
	});
	manage_script_win.show(); 
}

function manage_events(){

	var sm = new Ext.grid.CheckboxSelectionModel();

	Ext.QuickTips.init();

	//show choose window
	var manage_events_win = new Ext.Window({
	    constrain   : true,
	    title       : 'Manage Events',
	    layout      : 'border',
	    width       : 400,
	    height      : 440,
	    modal       : true,
	    resizable   : false,
	    items:[
	           new Ext.Panel({
					id          : 'id_panel_events',
				    region      : 'north',
				    height      : 35,
				    layout      : 'hbox',
					layoutConfig: {
			            pack:'center',
			            align:'middle'
			        },
			        frame : true,
				    items  :[
				            new Ext.form.ComboBox({
				        		id           : 'id_combo_events',
				        		store        : new Ext.data.JsonStore({
				        		    url        : '/get_events/',
				        		    method     : 'POST',
				        		    root       : 'events',
				        		    fields     : ['id', 'name', 'description'],
				        		    autoLoad   : true
				        		}),
				        		tpl: '<tpl for="."><div ext:qtip="{description}" class="x-combo-list-item">{description}</div></tpl>',
							    displayField : 'name',
							    typeAhead    : true,
							    mode         : 'local',
							    triggerAction: 'all',
							    resizable    : false,
							    valueField   : 'id',
							    listeners    : {
						        	select : function(combo, record, index){
				            			var grid_scripts = Ext.getCmp('grid_panel_scripts');
				            			Ext.Ajax.request({
						                    url: '/get_event_scripts/',
						                    params:{ 
						        				event_id  : record.data.id
						        			},
						                    success: function(response) {
						        					var scripts = Ext.decode(response.responseText);
						                        	var i;
						                        	if (scripts['scripts'].length > 0 ){
					                        			var store = grid_scripts.getStore();
					                        			var recApp = [];
						                        		for(i=0; i<scripts['scripts'].length;i++){
						                        			recApp.push(store.getAt(store.findExact('id', scripts['scripts'][i].id)));
						                        		}
					                        			grid_scripts.getSelectionModel().selectRecords(recApp);
						                        	}else
						                        		grid_scripts.getSelectionModel().clearSelections();
						                    }
						                });
				            		}
				            	}
							})
				       ]
	           }),
		       new Ext.grid.GridPanel({
		        region  : 'center',
		        id      : 'grid_panel_scripts',
		        sm      : sm,
		        columnLines  : true,
		        frame        :true,
		        title        :'Selected scripts',
        	    store        : new Ext.data.JsonStore({
	       		    url      : '/get_scripts/',
	       		    method   :'POST',
	       		    autoLoad :true,
	       		    root     : 'scripts',
	       		    fields   : ['id', 'name', 'description', 'actions_media_type', 'already_run', 'is_global']
        	    }),
		        cm: new Ext.grid.ColumnModel({
		            defaults: {
		                width   : 120,
		                sortable: true
		            },
		            columns: [
		                sm,
		                { id : 'name',         header: "Name",        dataIndex: 'name'},
	        	        { id : 'description',  header: "Description", dataIndex: 'description', width : 185},
	        	        { id : 'is_global',    header: "Global",      dataIndex: 'is_global',      width : 45}
		            ]
		        }),
		        tbar:[{
		            text:'Save change',
		            tooltip:'Save change',
		            handler: function(){
		        		var my_win = this.findParentByType('window');
		        		var i;
		        		var scripts_id = [];
		        		event = Ext.getCmp('id_combo_events').getValue();
		        		scripts = Ext.getCmp('grid_panel_scripts').getSelectionModel().getSelections();
		        		if (event){
			        		for(i=0;i<scripts.length;i++){
			        			scripts_id.push(scripts[i].data.id);
			        		}
			        		Ext.Ajax.request({
			                    url: '/set_script_associations/',
			                    params:{ 
			        				event_id  : event,
			        				script_id : scripts_id
			        			},
			                    success: function(response) {
			                        if (Ext.decode(response.responseText)['success']){
			                        	Ext.MessageBox.alert('Success', 'Assosiation saved.');
			                        }else
			                        	Ext.MessageBox.alert('Assosiation NOT saved.');
			                    }
			                });
		        		}else
		        			Ext.MessageBox.alert('Selected one event.');
		        	}
		        },'-']
		    })
	    ],
		buttons: [{
		   text: 'Done',
		   type: 'submit',
		   handler: function(){
		       var my_win = this.findParentByType('window');
		       my_win.close();
			}
		   },{
		   text: 'Cancel',
		   handler: function(){
		       var my_win = this.findParentByType('window');
		       my_win.close();
		   	}
		   }]          
    });
 
	manage_events_win.show();
}

