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
	console.log('stampaaaaaaaaaaaaa');
	Ext.getCmp('dataview_watermarks').getStore().load();
}

function generate_details_forms(panel, grid, selected, actionsStore, media_type) {
		
    var name_action = selected.data.name;
    var parameters = selected.get('parameters');
    var i = 0;
    watermarking_position = 0; // 0 mean undefined
    var recApp;
    console.log('generate_detail_form')
    console.log(selected.data);

// remove all component
    panel.removeAll()

    //add new component
    if (name_action == 'watermark'){
    	//watermark

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
					console.log('watermarks number');
					console.log(this.data.items.length);
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
        				            	console.log(selected.data);
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
	    			    	                console.log(Ext.getCmp(watermarking_position_id));
	    			    	            }
					        		    console.log(selected.data);
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
                        			width : 433,
                        			handler: function() {
                        				var up = new Upload('/upload_watermark/', true, {}, _update_watermarks);
                        				up.openUpload();
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
	                				}
	                    	    ]
	                    	})
	                    ]
    	            }]
    	        }         
    			);

   	
    }else{
    	for (i=0;i<parameters.length;i++){
//	    	cercare il name_action nella gridlistactions, e verificare se ha values
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
		    		panel.add(new Ext.form.ComboBox({                            
		    			fieldLabel   : parameters[i].name.replace("_"," "),
		    			store        : recAppValues,
						triggerAction: 'all',
						value        : val,
						name         : parameters[i].name
		    	    }));
	    	}
	    	else if (parameters[i].type == 'number'){
	    		panel.add(new Ext.form.NumberField({                            
	    	          fieldLabel: parameters[i].name.replace("_"," "),
	    	          value     : parameters[i].value,
	    	          name      : parameters[i].name,
	    	          msgTarget :'side'                            
	    	      	}));
	    	}
	    	else if (parameters[i].type == 'string'){
		    	panel.add(new Ext.form.TextField({                            
		          fieldLabel  : parameters[i].name.replace("_"," "),
		          value       : parameters[i].value,
		          name        : parameters[i].name,
		          msgTarget   : 'side'                            
		      	}));
	    	}
	    }
    }
//reload panel
	console.log('panel');
	console.log(panel);
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
	console.log("_pull_data");

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
    	console.log(newParams);
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
	    }]
	});
	return [tabs]
}

function _get_scripts_fields(name, description){

	console.log('_get_scripts_fields');
	console.log(name);
	console.log(description);
	var field_name = new Ext.form.TextField({
        fieldLabel: 'Name',
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
			console.log(rec);
			pipeline['actions_media_type'][type]['actions'][j] = {};
			pipeline['actions_media_type'][type]['actions'][j]['type'] = params.name;
			pipeline['actions_media_type'][type]['actions'][j]['parameters'] = {};
			for(k=0;k<params.parameters.length;k++){
				console.log(params.parameters[k]);
				pipeline['actions_media_type'][type]['actions'][j]['parameters'][params.parameters[k].name] = params.parameters[k].value;
			}
		});
	}
	console.log('pipeline');
	console.log(pipeline);
	return pipeline;
	
}
function new_script(create, name, description, id_script){
	//create true new_script
	//create false edit_script
	var tabs = _get_tabs();

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
            text: 'Save',
            type: 'submit',
            handler: function(){
    			var my_win = this.findParentByType('window');  
    			var type = my_win.get('media_type_tabs').getActiveTab().id.slice(4);
    			_pull_data(Ext.getCmp('my_action_'+type).getSelectionModel(), type);
    			var pipeline = save_data_script(name, description, my_win);

	    		if(create){
//					console.log('chiamata new_script');
//					console.log(pipeline);
	        		//chiamata ajax
	        		Ext.Ajax.request({
	                    url: '/new_script/',
	                    params:{ 
	        				name        : pipeline['name'],
	        				description : pipeline['description'],
	        				state : pipeline['state'] = "",
	        				actions_media_type : Ext.encode(pipeline['actions_media_type'])
	        			},
	                    success: function(response) {
	                        if (Ext.decode(response.responseText)['success']){
	                        	Ext.MessageBox.alert('Success', 'Script saved.');
	                        	my_win.close();
	                        }else
	                        	Ext.MessageBox.alert('Script NOT saved');
	                    }
	                });
				}else{
//					console.log('chiamata edit_script');
//					console.log(pipeline);
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
	                        	Ext.MessageBox.alert('Success', 'Script saved.');
	                        	my_win.close();
	                        }else
	                        	Ext.MessageBox.alert(Ext.decode(response.responseText));
	                    }
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
        	console.log(newRec);
        	my_win.get('media_type_tabs').get(name_tab).get('my_action_'+type).getStore().add(newRec);
		}

	}
}

//Show windows form scripts data ()
function script_detail_form(id_script, name, description, flag, main_win){
	var title;
	
	if (flag == false){
		title = 'New Script';
		var fields = _get_scripts_fields('','');
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
//	        labelWidth: 75, // label settings here cascade unless overridden
	        frame:true,
//	        bodyStyle:'padding:5px 5px 0',
//	        width: 450,
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
		    		//if(field_name.value) not work
		    		if (flag){
		        		Ext.Ajax.request({
		                    url: '/rename_script/',
		                    params:{ 
		        				name        : fields[0].getValue(),
		        				description : fields[1].getValue(),
		        				script : id_script
		        			},
		                    success: function(response) {
		                        if (Ext.decode(response.responseText)['success']){
		                        	Ext.MessageBox.alert('Success', 'Changes saved!');
		                        	my_win.close();
		    		        		main_win.get('open_form').get('my_scripts').getStore().reload();
		                        	
		                        }else
		                        	Ext.MessageBox.alert(Ext.decode(response.responseText));
		                    }
		                });
		    		}else//New script
		    		if(fields[0].value != ""){
			    		new_script(true, fields[0].getValue(), fields[1].getValue());
			    		my_win.close();
		    		}else{
						Ext.Msg.show({
							   title:'Warning',
							   msg: 'You must define name!',
							   buttons: Ext.Msg.OK,
							   icon: Ext.MessageBox.WARNING
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
	        		    fields   : ['id', 'name', 'description', 'actions_media_type']
	        	    }),
	        	    columns          : [
	        		        	        { id : 'name',  header: "Name", dataIndex: 'name', sortable: true},
	        		        	        { id : 'description',  header: "Description", dataIndex: 'description'}
	        	    ],
	        	    stripeRows       : true,
	        	    autoExpandColumn : 'name',
	        		frame            : true,
	                hideHeaders      : true,
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
			    		new_script(false, data.name, data.description, data.id);
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
	            		Ext.Ajax.request({
	                        url: '/delete_script/',
	                        params:{ 
	            				script : selScript.data.id
	            			},
	                        success: function(response) {
	                            if (Ext.decode(response.responseText)['success'])
	                				Ext.MessageBox.alert('Script deleted');
	                            else
	                            	Ext.MessageBox.alert('Script NOT deleted');
	                        }
	                    });
	            		my_win.get('open_form').get('my_scripts').getStore().reload();
		    		}
//            		my_win.close();
		     	}
	        },{
	            text: 'Change paramenters',
	            id: 'change_paramenters_script_button',
	            handler: function(){
	        		var my_win = this.findParentByType('window');
		    		if (my_win.get('open_form').get('my_scripts').getSelectionModel().hasSelection()){
			    		var data = my_win.get('open_form').get('my_scripts').getSelectionModel().getSelected().data;
		        		script_detail_form(data.id, data.name, data.description, true, my_win);

		    		}
	            }
	        }]          
	});
	manage_script_win.show(); 
}

function manage_events(){

	var sm = new Ext.grid.CheckboxSelectionModel();
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
				        		    fields     : ['id', 'name'],
				        		    autoLoad   : true
				        		}),
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
						                        	console.log(response.responseText)
						        					var scripts = Ext.decode(response.responseText);
						                        	var i;
						                        	console.log(scripts['scripts']);
						                        	if (scripts['scripts'].length > 0 ){
					                        			var store = grid_scripts.getStore();
					                        			var recApp = [];
						                        		for(i=0; i<scripts['scripts'].length;i++){
						                        			recApp.push(store.getAt(store.findExact('id', scripts['scripts'][i].id)));
						                        		}
						                        		console.log(recApp);
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
	       		    fields   : ['id', 'name', 'description', 'actions_media_type']
        	    }),
		        cm: new Ext.grid.ColumnModel({
		            defaults: {
		                width   : 120,
		                sortable: true
		            },
		            columns: [
		                sm,
		                { id : 'name',         header: "Name",        dataIndex: 'name'},
	        	        { id : 'description',  header: "Description", dataIndex: 'description'}
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
//			        			console.log(event);
//				        		console.log(scripts);
			        		for(i=0;i<scripts.length;i++){
			        			scripts_id.push(scripts[i].data.id);
			        		}
//				        		console.log(scripts_id);
//			        		set_script_associations/
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

