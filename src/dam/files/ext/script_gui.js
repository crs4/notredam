
function random_color(){
	var color = '#', num;
	for (var i = 0; i <6; i++){
		num = Math.round(Math.random()*15);
		color += num.toString(16);	
	}
    return color;
    
}

var saved_params = {};


function params_equal(p1, p2){
		
	return Ext.encode(p1) == Ext.encode(p2);
};

var MDAction =  function(opts, layer) {	
	
	this.id = opts.id || Ext.id(null, opts.title);
	this['in'] = opts['in'];
	opts.width = opts.width || 200;
	
	this.no_label = opts.no_label || false;
		
	opts.inputs = opts.inputs || [];
	this.out = opts.out; 
	this.inputs = opts.inputs || [];
	this.outputs = opts.outputs || [];
	opts.terminals = [];
	this.params = Ext.decode(Ext.encode(opts.params)); //just for working on a copy of params
	opts.resizable = false;
	this.label = opts.label || opts.title;
	this.dynamic = opts.dynamic || [];
	
	for(var i = 0 ; i < opts.inputs.length ; i++) {
		var input = this.inputs[i];
		opts.terminals.push({
			"name": input, 
			"label":'previous',
			"direction": [-1,0], 
			"offsetPosition": {"left": -14, "top": 3+23*(i+1) }, 
			"ddConfig": {
				"type": "input",
				"allowedTypes": ["output"]
			} ,
			wireConfig:{
				color: random_color()
			}
		});
	}
	for(i = 0 ; i < this.outputs.length ; i++) {
		var output = this.outputs[i];
		opts.terminals.push({
			"name": output, 
			"label": 'next',
			"direction": [1,0], 
			"offsetPosition": {"right": -14, "top": 3+10*(i+1+this.inputs.length) }, 
			"ddConfig": {
				"type": "output",
				"allowedTypes": ["input"]
			},
			"alwaysSrc": true,
			wireConfig:{
				color: random_color()
			}
		});
	}
	
	
	
	MDAction.superclass.constructor.call(this, opts, layer);
	layer.containers.push(this);

}; 
Ext.extend(MDAction, WireIt.Container, {
	
	getXY: function(){
		return Ext.get(this.el).getXY();
	},
	_set_output_label: function(prefix){
		this.output_label = Ext.id(null, prefix);		
	},
	get_output_label: function(){						
			if (this.output_label)
				return this.output_label;
			
			var values = this.form.getForm().getValues();
			
			//this.output_label = Ext.id(null, (values.output_variant || this.title));			
			
			this._set_output_label(this.label.value)
			return this.output_label;
			
	},
	get_dynamic_fields: function(){
		
		var dynamic = [];
		Ext.each(this.form.items.items, function(item){
			
			dynamic = dynamic.concat(item.get_dynamic_field());
			
		});
		
		return dynamic;
	},
	getOutputs: function(){
		var outputs = [];
		var output_wires= this.getTerminal(this.outputs).wires;
		if (output_wires.length > 0)
			outputs.push(this.get_output_label());
		
		return outputs;

	},
	
	getInputs: function(){
		var inputs = [];
		var input_wires= this.getTerminal(this.inputs).wires;
		Ext.each(input_wires, function(wire){
			if (wire)
				inputs.push(wire.label);
		});
		return inputs;

	},	
	getParams: function(){
		return this.form.getForm().getValues();
		
	},	
	onAddWire: function(e, args){
		var wire = args[0];
		
		var terminal_next = wire.terminal2;
		var terminal_prev = wire.terminal1;
		
		var field_prev = terminal_prev.container.form.getForm().findField('output_variant_name') || terminal_prev.container.form.getForm().findField('source_variant_name');
		var field_next = terminal_next.container.form.getForm().findField('source_variant_name');
		
		if (field_prev && field_next){
			if (field_prev.dynamic && field_next.toggleDynamize)
				field_next.setDynamic(true);				
			
			else
				field_next.setValue(field_prev.getValue());
			
		}
		
		
		wire.label =terminal_prev.container.get_output_label();		
		
		
	},
	
	render: function(){
		
	 	MDAction.superclass.render.call(this);
	 	var create_label = !this.no_label;
	 	var action = this;
	 	var params_objs = []
	 	Ext.each(this.params, function(param){
			
			param.allow_dynamic = true;			
			param.plugins = [Ext.ux.plugin_dynamic_field];
			
			var param_obj = new Ext.ComponentMgr.types[param.xtype](param);
			
			param_obj.check_dynamic(action.dynamic);
			params_objs.push(param_obj);
			
		});
	 	
	 	var form = new Ext.form.FormPanel({
//	 		renderTo: this.bodyEl,
	 		bodyStyle: {paddingTop: 10},
	 		autoHeight: true,
	 		autoScroll: true,
	 		border: false,
	 		items: params_objs,
	 		
	 		//collapsible: true,
	 		listeners:{
	 			afterrender:function(){
					
					action.form.doLayout();
				
	 			}
	 		}
	 	});
	 	this.form = form;
	 	
	 	
	 	
	 	var panel_body = Ext.get(this.bodyEl).parent('.WireIt-Container');	
			
		this.form_container = Ext.Element(panel_body).createChild({
		//var form_container = panel_body.createChild({
			tag: 'div',
			cls: 'dynamic_input_hidden',
			style: 'z-index: 100;\
			 border: 1px solid black; \
			 width: 350px;'										
		});
		
		
		
		this.form.render(this.form_container);
	 	 		
	 	
	 	items = [];
	 	if (create_label){
			this.label = new Ext.form.TextField({
				value: this.label,
				width: 150,
				listeners:{
					change: function(field, new_value){								
						var output_wires = action.getTerminal(action.outputs).wires;
						action._set_output_label(new_value);
						
						Ext.each(output_wires, function(wire){						
							wire.label = action.get_output_label();					
							
						});
						
					}
				}		
			});
			
			var BUTTON_EDIT = 'Show', BUTTON_HIDE = 'Hide';
			var composite_label = new Ext.form.CompositeField({
				items:[
					this.label,
					new Ext.Button({
						text: BUTTON_EDIT,
						
						handler: function(){
							if (this.getText() == BUTTON_EDIT){
								if (action.form_container){
									action.form_container.removeClass('dynamic_input_hidden');
									action.form.doLayout();
								}								
								this.setText(BUTTON_HIDE);								
								
							}
							else{
								
								if (action.form_container)									
									action.form_container.addClass('dynamic_input_hidden');
								this.setText(BUTTON_EDIT);
							
							}
							
						}
					})
				]
	 		
	 		});
			items.push(composite_label);
		}
 		
 		//items.push(form);
	 	var panel = new Ext.Panel({
	 		renderTo: this.bodyEl,
	 		items: items,
	 		border: false
	 	
	 	});
	}

});

var InputRendition =  function(opts, layer) {
	opts.width = 200;	
	InputRendition.superclass.constructor.call(this, opts, layer);
}

Ext.extend(InputRendition, MDAction, {
		
		update_connected_actions: function(){
			
			var value = this.source_rendition.getValue();
			Ext.each(this.terminals[0].wires, function(wire){
				if (wire.terminal2){
					var field = wire.terminal2.container.form.getForm().findField('source_variant_name')
					if (field){
						field.setValue(value);
						
					}
				}
				
			});
		},
		
		render: function(){
		
	 	MDAction.superclass.render.call(this);
	 	
	 	var action = this;

	 	this.source_rendition = new Ext.ux.MultiRenditions({   
			name: 'source_variant_name',
			width:150,
			//width: 200,
			media_type: 'image',		
			description: 'input-variant',
			plugins: [plugin_dynamic_field],
			listeners: {
				change: function(combo, new_value, old_value){
					action.update_connected_actions();
				}
			}
			
		});
		
		
		
	 	var form = new Ext.form.FormPanel({
//	 		renderTo: this.bodyEl,
	 		//bodyStyle: {paddingTop: 10},
	 		autoHeight: true,
	 		autoScroll: true,
	 		border: false,
	 		items: this.source_rendition
	 	});
	 	this.form = form;
	 	var panel = new Ext.Panel({
	 		renderTo: this.bodyEl,
	 		items: form,
	 		border: false
	 	
	 	});
	},
	
	onAddWire: function(e, args){
		
		var wire = args[0];
		
		var terminal_next = wire.terminal2;
		var terminal_prev = wire.terminal1;
		
		var values = terminal_prev.container.form.getForm().getValues();
		
		var field = terminal_next.container.form.getForm().findField('source_variant_name')
		if (field){
			field.setValue(values.source_variant_name);
			field.disableAll();
		}
		
		wire.label =terminal_prev.container.get_output_label();		
		
		
	},
	onRemoveWire: function(e, args){
		var wire = args[0];
		
		var terminal_next = wire.terminal2;
		var terminal_prev = wire.terminal1;
		
		var field = terminal_next.container.form.getForm().findField('source_variant_name')
		if (field){
			
			field.enableAll();
		}
		
		
	}
});

Ext.reg('inputrendition',InputRendition)

var baseLayer, store, layer_el;

function save_script(params){
	var invalid = false;
	var action_invalid;
	var tmp;
	
	for (var i = 0; i < baseLayer.containers.length; i++){
		tmp = baseLayer.containers[i];
		if (!tmp.form.getForm().isValid()){
			action_invalid = tmp.label.getValue();
			invalid = true
		}
		
	}
	if(invalid){
		Ext.Msg.alert('Save', String.format('Saving failed. Please check action "{0}", some of its required fields are missing.', action_invalid));
		return;
	}
	
	Ext.Ajax.request({
		url: '/edit_script/',
		params: params,
		success: function(response){
//		  	Ext.MsgBox.msg('','Script saved');
			Ext.Msg.alert('Save', 'Script saved successfully.');
			saved_params = baseLayer.getJson();
			if (! script_pk)
				script_pk = Ext.decode(response.responseText).pk;
			try{
				window.opener.scripts_jsonstore.reload();
			}
			catch(e){}
		},
		failure: function(response){
//		            			Ext.MsgBox.msg('','Save failed');
            msg = Ext.decode(response.responseText).errors;
			Ext.Msg.alert('Save', 'Saving script  failed: ' + msg ); 
		}
		
		
	});


};

//YAHOO.inputEx.spacerUrl = "/files/WireIt-0.5.0/lib/inputex/images/space.gif";

Ext.onReady(function(){
	Ext.get('switch_ws_bar').setStyle({marginTop: 10});
	Ext.get('switch_ws_bar').dom.innerHTML = workspace.name;
	
	var store = new Ext.data.JsonStore({
		url:'/get_actions/',
		fields:['name', 'params'],
//			autoLoad: true,
		root: 'scripts'	,
		sortInfo: {
		    field: 'name',
		    direction: 'ASC'
		}
	});
	
	new Ext.Viewport({
		layout: 'border',
		items:[
			header,			
			new Ext.TabPanel({
				region: 'east',
				width: 200,
				activeTab: 0,
				items: [
					new Ext.grid.GridPanel({
						id: 'actions_grid',					
						title: 'Actions',
						layout: 'fit',						
						enableDragDrop: true,
						ddGroup: 'wireit',								
						store: store,
						columns:[{
							name: 'Script',
							dataIndex: 'name'
						}],
						hideHeaders: true,
						sm: new Ext.grid.RowSelectionModel({
							singleSelect: true
						}),
						viewConfig: {
							forceFit: true
						}
				
					
				}),
				new Ext.grid.GridPanel({
					id: 'utils_grid',					
					title: 'Utils',
					layout: 'fit',					
					
					enableDragDrop: true,
					ddGroup: 'wireit',		
					
					store: new Ext.data.JsonStore({
						fields: ['name', 'params' ,'xtype'],
						root: 'actions',
						data: utils_data,
						autoLoad: true
					}),
					columns:[{
						name: 'utils',
						dataIndex: 'name'
					}],
					hideHeaders: true,
					sm: new Ext.grid.RowSelectionModel({
						singleSelect: true
					}),
					viewConfig: {
						forceFit: true
					}
			
					
				})
				
				]
			}),
			new Ext.Panel({
				region: 'center',
				items: new Ext.BoxComponent({
			    autoEl: {
			        tag: 'div',
			        id: "wire-layer",
			        'class':"wireit"
			        
			    },
						
				region: 'center',
				listeners:{
					afterrender: function(){
						layer_el = this.getEl();						
						baseLayer = new WireIt.Layer({
							layerMap: false,
							parentEl: layer_el
							
						});
						
						baseLayer.getJson =  function(){
								var actions_json = {};
								
								Ext.each(this.containers, function(action){
									if (action){
										
										var posXY = action.getXY();										
										actions_json[action.id] = {
											params: action.getParams(),
											'in': action.getInputs(),
											out: action.getOutputs(),
											dynamic: action.get_dynamic_fields(),
											//dynamic: [],
											script_name: action.options.title,
											x: posXY[0],
											y: posXY[1],
											label: action.label.getValue()
											
										}					
									
									}
							}
							
							
							);
								return actions_json;
						
						};
	

          new Ext.dd.DropZone(Ext.get('wire-layer'),{
          	ddGroup: 'wireit',
          	onContainerOver: function(){
          		return this.dropAllowed;
          	},
          	onContainerDrop: function( source, e, data ){          		
          		
          		var drop_x = e.xy[0] ;
				var drop_y = e.xy[1];
				var name = data.selections[0].data.name;
				var params_to_load = data.selections[0].data.params;	
			
          		if (data.grid.id == 'actions_grid'){
							
					var fields = [];
					var action = new MDAction({
							title: name,
							label: params_to_load.label,
							position:[drop_x,drop_y],
	//			            legend:'thumbnail',							
							inputs: ['in'],
							outputs: ['out'],
							params: params_to_load,
							
							
					}, baseLayer);
				}
				
				else if(data.grid.id == 'utils_grid'){
				
					var action = new Ext.ComponentMgr.types[data.selections[0].data.xtype]({
						title: name,						
						position:[drop_x,drop_y],					   
						width: 250,
						outputs: ['out'],
						params: params_to_load
				}, baseLayer);
					
				}
          		
          		
			   
          	} 
          	
          });
           
          renditions_store.load({ //before loading actions, we need to load the renditions, in this way we have the values ready for the renditions input/ouput
			callback: function(){
				store.load({
					callback:function(){
						if (script_name)
							Ext.getCmp('script_name').setValue(script_name);
						
						if (params){
							
							var action;
							for (action_name in params){
								if (action_name){

									action = params[action_name];
									
									var action_stored = store.query('name', action.script_name).items;
									
									if(action_stored.length > 0){
										action_stored = action_stored[0];
										var action_box = new MDAction({
											title: action_stored.data.name,
											//position:[20,20],
					//			            legend:'thumbnail',
											'in': action['in'],
											'out': action['out'],
											inputs: ['in'],
											outputs: ['out'],
											position: [action.x -1, action.y - 56],
											params: action_stored.data.params,
											label: action.label,
											dynamic: action.dynamic
											
											
										}, baseLayer); 
										action_box.form.getForm().setValues(action.params);
										
										Ext.each(action_box.form.items.items, function(field){          						
											if (field.data_loaded)
												field.data_loaded(action.params);
												
										});
										
									}
									
									
								}
							}
							var w;
							Ext.each(baseLayer.containers, function(action){
							
								Ext.each(baseLayer.containers, function(inner_action){
									
									Ext.each(action['out'], function(out){
										Ext.each(inner_action['in'], function(_in){
											
											if (out && out == _in){
												w = new WireIt.Wire(action.getTerminal('out'), inner_action.getTerminal('in'), layer_el.dom.childNodes[0], {color: action.getTerminal('out').options.wireConfig.color});
		//								
												w.drawBezierCurve();	
											}
											
										});
										
									});
									if(action['out'][0] &&  action['out'][0] == inner_action['in'][0] ){
										
										
										
									}	
								});
							
							
							});
							saved_params = baseLayer.getJson();
						}
					}
				  
				  });
			}
			});
          
						
						
						
					}
				}
			
			}),
				tbar: new Ext.Toolbar({
//				   region: 'north',
				    
				    height: 25,
				    items: [
					    {
						    xtype: 'tbtext', 
						    text: 'Script Name: '
					    } ,
				   		{
					   		id: 'script_name',
				            xtype: 'textfield',
				            name: 'name',
				            allowBlank: false
			//	            emptyText: 'new script'
			        	},
                        {xtype: 'tbseparator'},
                       
                        {    
							id: 'events_container',                       
                            text:'Events',   
                            handler: function(){
								if (Ext.query('.dynamic_input_selected').length >0)
									Ext.each(Ext.getCmp('events').items.items, function(i){i.disable()});
								else
									Ext.each(Ext.getCmp('events').items.items, function(i){i.enable()});
							},
                            
                            menu: new Ext.ux.StoreMenu({
                                id: 'events',
                                store_cfg: {
                                    url: '/get_events/',
                                    root:'events',
                                    fields: ['id', 'text', 'checked'],
                                    baseParams:{
                                        script_id: script_pk
                                    }
                                },                                
                                item_text_field: 'name',
                                item_cfg: {
                                        hideOnClick: false,
                                        xtype: 'menucheckitem',
                                        handler: function(event){
                                            
                                            (function(){
                                                var record = event.ownerCt.store.getById(event.id);
                                               
                                                record.set('checked', event.checked);
                                                record.commit();
                                            }).defer(100);
                                        }
                                },                               
                                getValue: function(){
                                    var records_checked = this.store.query('checked', true);                                    
                                    var values = []
                                    Ext.each(records_checked.items, function(record){
                                        values.push(record.data.text);
                                    });
                                    return values;
                                }
                            })
                            
                        },
                        
                        {                           
                            text:'Type',                            
                             menu: new Ext.ux.StoreMenu({
                                 id: 'media_types',
                                 store_cfg: {
                                    url: '/get_types/',
                                     root:'types',
                                     idProperty: 'text',
                                     fields: ['value', 'text', 'checked'],
                                     baseParams:{
                                         script_id: script_pk
                                     }
                                 },                                
                                 item_text_field: 'name',
                                 item_cfg: {
                                         hideOnClick: false,
                                         xtype: 'menucheckitem',
                                         handler: function(obj){
                                             
                                             (function(){
                                                 var record = obj.ownerCt.store.getById(obj.text);
                                              
                                                 record.set('checked', obj.checked);
                                                 record.commit();
                                             }).defer(100);
                                         }
                                 },                                                               
                                 getValue: function(){
                                     var records_checked = this.store.query('checked', true);                                    
                                     var values = []
                                     Ext.each(records_checked.items, function(record){
                                         values.push(record.data.value);
                                     });
                                     return values;
                                 }
                             })

                            
                            
                        },
			        	
				        	
				        	{xtype: 'tbseparator'},
				        	
				        {				            
				            text: 'Save',
				            id: 'save_button',
				            icon: '/files/images/icons/save.gif',
				            handler: function(){
				            	var button = Ext.getCmp('save_button');
				            	if (Ext.getCmp('script_name').isValid()){
			            				
			            				var submit_params =  {
											pk: script_pk,
											name: Ext.getCmp('script_name').getValue(),
											events: Ext.getCmp('events').getValue(),
											media_types: Ext.getCmp('media_types').getValue(),
											params: Ext.encode(baseLayer.getJson())		            			
										};
										save_script(submit_params);	   		
										            		
				            	}
				            	else
				            		Ext.Msg.alert('Save', 'Saving script failed, invaild name');
				            }
				        },{
				        	text: 'Delete',
				        	icon: '/files/images/icons/fam/delete.gif',
				        	handler: function(){
				        		if (script_pk)
					        		Ext.Msg.show({
					        			title:'Delete Script?',
									   msg: 'Are you sure you want to delete this script?',
									   buttons: Ext.Msg.YESNO,
									   fn: function(btn){
										   	if (btn == 'yes'){
										   		
												Ext.Ajax.request({
													url: '/delete_script/',
													params:{
														pk: script_pk
													},
													success: function(){
														window.opener.scripts_jsonstore.reload({
															callback: function(){
																window.close();
															}
														});
														
													
													}
												});
										   		
										   	}
									   },
								   
								   icon: Ext.MessageBox.QUESTION}
				        		
				        		);
				        		
				        	}
				        
				        }
				    ]
				})
				
				
			
			})
						
		
		
		]
	});
	
	
});

	
