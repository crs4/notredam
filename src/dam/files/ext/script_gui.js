function random_color(){
	var color = '#', num;
	for (var i = 0; i <6; i++){
		num = Math.round(Math.random()*15);
		color += num.toString(16);	
	}
    return color;
    
}

Ext.ux.StoreMenu = function(config){
    
    Ext.ux.StoreMenu.superclass.constructor.call(this, config);    
    var menu = this;
    var store_cfg = config.store_cfg;
    Ext.apply(store_cfg, {
        autoLoad: true,
        listeners: {
            load: function(store, records){
                console.log(records);
                menu.removeAll();
                Ext.each(records, function(record){
                    var cfg = record.data;            
                    Ext.apply(cfg, config.item_cfg);
                    menu.add(cfg);
                
                });
                
            }
        }        
    });
    this.store = new Ext.data.JsonStore(store_cfg);
    
};
Ext.extend(Ext.ux.StoreMenu, Ext.menu.Menu, {});



Ext.ux.FieldSetContainer = function(config) {
    Ext.ux.FieldSetContainer.superclass.constructor.call(this, config);    
 	this.form = this.ownerCt;
}; 

Ext.extend(Ext.ux.FieldSetContainer, Ext.Panel, {
	border: false,
	layout: 'form',
	data_loaded: function(values){
				
		var actions = values[this.order_field_name];
		Ext.each(this.items.items, function(item){
			if (item.data_loaded)
				item.data_loaded(values);
		});
		
		try{
			Ext.each(this.items.items, function(item){
				var position = actions.indexOf(item.name);
				if (item.get_position() != position)
					item.move(position);
			
			});
		}
		catch(e){}
		
		
	}
});
Ext.reg('fieldsetcontainer', Ext.ux.FieldSetContainer);

Ext.ux.SelectFieldSet = function(config) {
	var fieldLabel = config.fieldLabel;
	delete config.fieldLabel;
	var select_values = [];
	for (select in config.values)
		select_values.push([select]);
	
	var fieldset = new Ext.ux.FieldSetContainer({
	xtype: 'fieldsetcontainer',
	items: config.values[config.select_value]
	});
	
	var select_field = new Ext.ux.Select({
		
		values: select_values,
		value: config.select_value,
		name: config.select_name,
		fieldLabel: fieldLabel,
		_select : function(value){
			new_values = this.ownerCt.values[value];				
			fieldset.removeAll();
			fieldset.add(new_values);
			this.ownerCt.doLayout();
			
		},
		listeners: {
			select: function(combo, record){				
				this._select(record.data.value);
			}
			
			
		}
	});
	
	config.items = [
		select_field,
		fieldset
	];
		
    Ext.ux.SelectFieldSet.superclass.constructor.call(this, config);    
    this.fieldset = fieldset;
    this.select_field = select_field;
    this.values = config.values;
    
 	
}; 

Ext.extend(Ext.ux.SelectFieldSet, Ext.form.FieldSet, {
	data_loaded: function(data){
//		Ext.ux.SelectFieldSet.superclass.data_loaded.call(this, data);
		
		this.select_field._select(data.preset);
		this.ownerCt.getForm().setValues(data); //temporary, since form items are deleted and new ones are added, i have to reload the data 
		Ext.each(this.items.items, function(item){
		if (item.data_loaded)
			item.data_loaded(data);
		});
		
	}
	
	
});
Ext.reg('selectfieldset', Ext.ux.SelectFieldSet);



Ext.ux.ModFormPanel = function(config) {
    Ext.ux.ModFormPanel.superclass.constructor.call(this, config);    
 
}; 

Ext.extend(Ext.ux.ModFormPanel, Ext.form.FormPanel, {
	    expand_fieldset: function(field, value){
	    	if (value){
	    		var parent = field.ownerCt;
		    	if (parent instanceof Ext.ux.CBFieldSet){
		    		
		    		parent.expand();
		    	}
	    }
	    	
	    },
	    setValues : function(values){
        	var base_form = this.getForm();
        	
        	if(Ext.isArray(values)){ // array of objects
            
	            for(var i = 0, len = values.length; i < len; i++){
	                var v = values[i];
	                var f = base_form.findField(v.id);
	                if(f){
	                    f.setValue(v.value);
	                    this.expand_fieldset(f, v.value);
	                    if(base_form.trackResetOnLoad){
	                        f.originalValue = f.getValue();
	                    }
	                }
	            }
	        }else{ // object hash
	            var field, id;
	            for(id in values){
	                if(!Ext.isFunction(values[id]) && (field = base_form.findField(id))){
	                    field.setValue(values[id]);
	                    this.expand_fieldset(field, values[id]);
	                    if(base_form.trackResetOnLoad){
	                        field.originalValue = field.getValue();
	                    }
	                }
	            }
	        }
	        return this;
	    }
});


Ext.ux.WatermarkBrowseButton = function(config) {
 	
    Ext.ux.WatermarkBrowseButton.superclass.constructor.call(this, config);
    Ext.apply(this, {values : config.values});
 
}; 

Ext.extend(Ext.ux.WatermarkBrowseButton, Ext.Button, {
	getValue: function(){},
	handler: function(){
		
		
		var tpl_str = '<tpl for=".">';    
			tpl_str += '<div class="thumb-wrap" id="{pk}">';
				tpl_str += '<div class="thumb">';		 
				tpl_str += '<div style="width: 100; height: 100; background: url({url}) no-repeat bottom center; border:1px solid white;"></div>';

				tpl_str +='</div>';                
				
//				tpl_str += '<span>{shortName}</span>' 
			tpl_str += '</div>';
		
		tpl_str += '</tpl>';
		var store = new Ext.data.JsonStore({
		    	totalProperty: 'totalCount',
		        root: 'items',
		        url: '/load_items/',
		        baseParams: {
		        	media_type: 'image'
		        },
		        
		        idProperty: 'pk',
		        autoLoad: true, 
				fields:[
			        'pk', 
	                '_id', 
                	'url'
                ]
		    
		    });
		    
		var wm_win = new Ext.Window({
			title: 'Choose Watermark',
			width: 600,
			modal: true,
			items:[
				new Ext.Panel({
					tbar: [{
						id:'rendition_select',
						xtype: 'select',
						values: this.values					
					}],
					bbar: new Ext.PagingToolbar({
				        store: store,       // grid and PagingToolbar using same store
				        displayInfo: true,
				        pageSize: 10,
				        prependButtons: true
				        
				    }),
					
					items: new Ext.DataView({
				        id: 'wm_dataview',
				        itemSelector: 'div.thumb-wrap',
				        style:'overflow:auto; background-color:white;',
				        singleSelect: true,
//				        plugins: new Ext.DataView.DragSelector({dragSafe:true}),
				        height: 300,				        
				        tpl: new Ext.XTemplate(tpl_str),
				        store: store
				       
				    }),
				    buttonAlign: 'center',
				    buttons:[{
				    	text: 'Select',
				    	handler: function(){
				    		var selected = Ext.getCmp('wm_dataview').getSelectedRecords();
				    		if (selected.length > 0){
				    			var rendition = Ext.getCmp('rendition_select').getValue();
				    			
				    			Ext.getCmp('wm_id').setValue(String.format('/item/{0}/{1}/',selected[0].data._id, rendition ));
				    			wm_win.close();
				    		}
				    		
				    		
				    	
				    	}
				    	
				    }]
					   
				})
				
	 
				
			
			]
		
		});

		wm_win.show();
	
	}


});

Ext.reg('watermarkbrowsebutton', Ext.ux.WatermarkBrowseButton);


Ext.ux.WatermarkPosition = function(config){
	Ext.ux.WatermarkPosition.superclass.constructor.call(this, config);
}; 

Ext.extend(Ext.ux.WatermarkPosition, Ext.form.Field, {
//	height: 160,
	
	
	
	 initComponent:function() {
	 	
	 	var i, j, box_id;
	    var children_box_position = [];
	    for(i=1; i<= 9; i++){
	    	box_id = Ext.id();
	        children_box_position.push({
	            tag:'div',
	            id: box_id,
	            cls: 'position_watermarking',
            	onclick: String.format('Ext.getCmp(\'{2}\').ownerCt.watermarking({0});', i, this.id, this.id)

	        });
	    }
   
    	
    	
    	 Ext.apply(this, {
    	 	autoCreate:{
		        tag:'div',
	            cls: 'container_position_watermarking',
//	            style: 'height:135px;',
	            children:children_box_position            
	        },
	        boxes: children_box_position
    	 });
    	
    	Ext.ux.WatermarkPosition.superclass.initComponent.call(this);
    	
    },
	
	name: 'watermarking_position'


});

Ext.reg('watermarkposition', Ext.ux.WatermarkPosition);
    

Ext.ux.Select = function(config) {
 	this.values = config.values; 	
 	Ext.apply(config, {
 		store: new Ext.data.ArrayStore({        
	        fields: config.fields || ['value'],
	        data: config.values
	    }),
	    valueField: config.valueField || 'value',
		displayField: config.displayField || 'value'
		
	    
	    
	    
 	});
 	
    // call parent constructor
    Ext.ux.Select.superclass.constructor.call(this, config);
    
 
}; 

Ext.extend(Ext.ux.Select, Ext.form.ComboBox, {	
//    initComponent:function() {
//    	
//    	var values = this.values;
//    	
//    	 Ext.apply(this, {
//    	 	store:  new Ext.data.ArrayStore({        
//		        fields: this.fields || ['value'],
//		        data: values
//		    })
////		    value: values[0]
//    	 });
//    	
//    	Ext.ux.Select.superclass.initComponent.call(this);
//    },
    allowBlank: false,
    autoSelect: true,
    editable: false,
    triggerAction: 'all',
    lazyRender:true,
    forceSelection: true,
    mode: 'local'
    
    
 
}); 

Ext.reg('select', Ext.ux.Select);


Ext.ux.CBFieldSet = function(config) {
	config.collapsed = true;
			
	Ext.ux.CBFieldSet.superclass.constructor.call(this, config);
	
	
};


Ext.extend(Ext.ux.CBFieldSet, Ext.form.FieldSet, {	
	
	data_loaded: function(){
		var expand = false;
		Ext.each(this.items.items, function(item){
			if (item.getValue())
				expand = true;			
		});
		
		if (expand)
			this.expand();
	},
	
	initComponent:function() {
	 	 var cb_id = Ext.id();
	 	 Ext.apply(this, {
	 	 	cb_id: cb_id,
	 	 	checkboxToggle: {tag: 'input', type: 'checkbox'}
	 	 });
	 	Ext.ux.CBFieldSet.superclass.initComponent.call(this);
	
	 },
	 
	expand: function(){
	
		Ext.ux.CBFieldSet.superclass.expand.call(this);
		Ext.each(this.items.items, function(item){
	 			item.enable();
	 	});
		
	},
	
	collapse: function(){
		Ext.ux.CBFieldSet.superclass.collapse.call(this);
		Ext.each(this.items.items, function(item){
	 			item.disable();
	 	});
		
	},
	
	
	onCheckClick: function(){
	 	var cb = Ext.get(this.cb_id);

	 	if (cb.dom.checked)
	 		this.expand();
	 	else
	 		this.collapse();
	 	
	 }
	
});

Ext.reg('cbfieldset', Ext.ux.CBFieldSet);


Ext.ux.MovableCBFieldSet = function(config) {
	config.id = config.id || Ext.id();
	config.items = config.items || [];
	if (config.movable == undefined)
		config.movable = true;		
		
	Ext.ux.MovableCBFieldSet.superclass.constructor.call(this, config);
};



Ext.extend(Ext.ux.MovableCBFieldSet, Ext.ux.CBFieldSet, {
	collapsed: true,
	initComponent: function(){
		Ext.ux.MovableCBFieldSet.superclass.initComponent.call(this, config);
		var config = this.initialConfig; 
		
		this.add({
		xtype: 'hidden',
		name: config.order_field_name,
		value: config.order_field_value,
		
//			this field is hidden and readonly, it is used to hold the ordered list of the actions [resize, crop, watermark]
		setValue: function(new_value){
			
//			
			if (config.name == new_value)
				this.setRawValue(new_value);
//			else if(new_value instanceof Array){
//				
//				var container = this.ownerCt;
//				var index = new_value.indexOf(config.name);
////				if (container.get_position() != index)
//					container.move(index);
//			}
		}
	});
	
	
	
		
	},
	
	check_expand: function(){
		var expand = false;
		Ext.each(this.items.items, function(item){
			
	//			if (item.name != cbf.initialConfig.order_field_name && item.getValue())
			if (!(item instanceof Ext.form.Hidden) && item.getValue())
			
				expand = true;			
		});
		
		if (expand)
			this.expand();
		
	},
	
	data_loaded: function(values){	
		this.check_expand();
	},
	onRender : function(ct, position){
        if(!this.el){
            this.el = document.createElement('fieldset');
            this.el.id = this.id;
            if (this.title || this.header || this.checkboxToggle) {
                this.el.appendChild(document.createElement('legend')).className = this.baseCls + '-header';
            }
        }

        Ext.form.FieldSet.superclass.onRender.call(this, ct, position);
		if (this.movable){
			this.header.insertFirst({tag: 'img', src: '/files/images/icons/arrow-down.gif', style: 'margin-bottom: -4px; margin-left: -3px', onclick: String.format('Ext.getCmp(\'{0}\').move_down();', this.id)});
			this.header.insertFirst({tag: 'img', src: '/files/images/icons/arrow-up.gif', style: 'margin-bottom: -4px; margin-left: -2px',onclick: String.format('Ext.getCmp(\'{0}\').move_up();', this.id)});
		}
        var o = typeof this.checkboxToggle == 'object' ?
                this.checkboxToggle :
                {tag: 'input', type: 'checkbox', name: this.checkboxName || this.id+'-checkbox'};
        this.checkbox = this.header.insertFirst(o);
        this.checkbox.dom.checked = !this.collapsed;
        this.mon(this.checkbox, 'click', this.onCheckClick, this);
    
        
    },

	get_position: function(){
		return this.ownerCt.items.items.indexOf(this);
	
	},
	 
	 
	 move: function(position){
	 	if (! this.movable)
	 		return;
	 		
	 	var cbf = this;
	 	
	 	var container = this.ownerCt;
	 	var current_pos = this.get_position(); 
	 	if (position <0 || position > container.items.items.length || position == current_pos)
	 		return;
	 	var copy = this.initialConfig;
 		
	 	
 		
 		var values = {};
 		Ext.each(this.items.items, function(item){                              
                var value = item.getValue(); 
//                      console.log(item.name);
                if(value && item.name != cbf.initialConfig.order_field_name && item != cbf.position)
                
                        values[item.name] = value;
        });
 		
 		container.remove(this); 	
 		new_obj = container.insert(position, copy);
 		
 		container.doLayout();
 		
 		
 		container.form.getForm().setValues(values);
 		new_obj.check_expand();
// 		this.position.setValue(position);
 		
 		
	 },
	move_up: function(){
//		console.log(this.position_field.getValue());
		this.move(this.get_position()  - 1);
	},
	move_down: function(){
//		console.log(this.position_field.getValue());
		this.move(this.get_position()  + 1);
	}
//	 
//	 onRender : function(ct, position){
//        Ext.ux.MovableCBFieldSet.superclass.onRender.call(this, ct, position);
////        
//		this.header.insertFirst({tag: 'img', src: '/files/images/icons/arrow-down.gif', style: 'margin-bottom: -4px; margin-left: -7px', onclick: String.format('Ext.getCmp(\'{0}\').move_down();', this.id)});
//		this.header.insertFirst({tag: 'img', src: '/files/images/icons/arrow-up.gif', style: 'margin-bottom: -4px; margin-left: -2px',onclick: String.format('Ext.getCmp(\'{0}\').move_up();', this.id)});
//     }

	
});

Ext.reg('movablecbfieldset', Ext.ux.MovableCBFieldSet);


Ext.ux.WatermarkFieldSet = function(config){
	var pos_x_percent = new Ext.form.Hidden({
		name: config.wm_x_name || 'pos_x_percent'
	});
	
	var pos_y_percent = new Ext.form.Hidden({
		name: config.wm_x_name || 'pos_y_percent'
	});
	
	var square = new Ext.form.Hidden({
		name: 'square'
		
	});
	
	var wm_id = new Ext.form.TextField({
//        'id': 'wm_id',
        'width': config.wm_id_width || 160,
        'xtype':'textfield',
        'name': config.wm_id_name ||'wm_id',
        
        
        'description': 'image',
        'help': ''
    }); 
	
    var position = new Ext.ux.WatermarkPosition({
//    	 xtype: 'watermarkposition',
    	 listeners: {
    	 	afterrender: function(){
    	 		var square = this.ownerCt.square.getValue();
    	 		
    	 		if (square)
    	 			this.ownerCt.watermarking(square);
    	 	}
    	 }
    });
    
	config.items = [
		new Ext.form.CompositeField({
        name: wm_id.name,
        fieldLabel: 'Image',
        wm_id : wm_id,
        
        getValue: function(){
        	return this.wm_id.getValue();
        }, 
        setValue: function(value){
        	
        	this.wm_id.setValue(value);
        },
        'items':[
                 wm_id,
                {
                 'xtype': 'watermarkbrowsebutton',
                 'text': 'Browse',
                 values: config.renditions
                 
                 
                   
                }
                
        ]
        }),
		
        position,        
        pos_x_percent,
        pos_y_percent,
        square	];
	
	Ext.ux.WatermarkFieldSet.superclass.constructor.call(this, config);
	Ext.apply(this, {
		pos_x_percent: pos_x_percent,
        pos_y_percent: pos_y_percent,
        square: square,
        position: position,
        wm_id: wm_id
        
       
	});
	
}; 

Ext.extend(Ext.ux.WatermarkFieldSet, Ext.ux.MovableCBFieldSet, {
	_set_hidden_position_percent: function(id){
        var pos_x = ((id-1) % 3) * 33 + 5;
        var pos_y = (parseInt((id-1) / 3)) * 33 + 5;
        this.pos_x_percent.setValue(parseInt(pos_x));
        this.pos_y_percent.setValue(parseInt(pos_y));
	},
	
	data_loaded: function(values){        
		var square_selected = this.square.getValue();		
		if(square_selected)
			this.watermarking(square_selected);
			
		Ext.ux.WatermarkFieldSet.superclass.data_loaded.call(this, values);
		
	},
	 _reset_watermarking: function(){	 	
	 	try{
		 	for (i=0; i<9; i++){		    	
		        Ext.get(this.position.boxes[i].id).setStyle({
		            background: 'none',
		            opacity: 1
		            });
		    }
	    }
	 	catch(e){
	 	
	 	}
	    
	},
	
	watermarking: function(id){      
	    this._reset_watermarking();
	    this._set_hidden_position_percent(id);
	    try{
	    	Ext.get(this.position.boxes[id -1].id).setStyle({
	        background: 'green',
	        opacity: 0.6
	        });
	    	this.square.setValue(id);
	    
	    }
	    catch(e){
	    
	    }
	    
	}
	


});

Ext.reg('watermarkfieldset', Ext.ux.WatermarkFieldSet);



var MDAction =  function(opts, layer) {	
	this.id = opts.id || Ext.id();
	this['in'] = opts['in'];
	this.out = opts.out; 
	this.inputs = opts.inputs || [];
	this.outputs = opts.outputs || [];
	opts.terminals = [];
	this.params = opts.params;
	opts.resizable = false;
	this.label = opts.label || opts.title;

	for(var i = 0 ; i < opts.inputs.length ; i++) {
		var input = this.inputs[i];
		opts.terminals.push({
			"name": input, 
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
YAHOO.lang.extend(MDAction, WireIt.Container, {
		
	getXY: function(){
		return Ext.get(this.el).getXY();
	},
	
	getOutputs: function(){
		var outputs = [];
		var output_wires= this.getTerminal(this.outputs).wires;
		Ext.each(output_wires, function(wire){
			if (wire)
				outputs.push(wire.label);
		});
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
		wire.label = Ext.id();
		var terminal_out = wire.terminal2;
		var terminal_in = wire.terminal1;
		var values = terminal_in.container.form.getForm().getValues();
		var output_variant = values.output_variant || values.source_variant;
		
		if (output_variant){
			terminal_out.container.form.getForm().setValues({
				source_variant: output_variant
			});			
		}
		
		
		
		
	
		
	},
	
	render: function(){
		
	 	MDAction.superclass.render.call(this);
	 	
	 	var form = new Ext.form.FormPanel({
//	 		renderTo: this.bodyEl,
	 		bodyStyle: {paddingTop: 10},
	 		autoHeight: true,
	 		autoScroll: true,
	 		border: false,
	 		items: this.params,
	 		
//	 		collapsible: true,
	 		listeners:{
	 			afterrender:function(){
	 				this.collapse();
	 			
	 			}
	 		}
	 	});
	 	this.form = form;
	 	
	 	this.label = new Ext.form.TextField({
 			value: this.label,
 			width: 300 			
 		}); 		
	 	
 		var BUTTON_EDIT = 'Edit', BUTTON_HIDE = 'Hide';
	 	var panel = new Ext.Panel({
	 		renderTo: this.bodyEl,
	 		items: [
	 		
	 		
	 		new Ext.form.CompositeField({
	 			items:[
	 				this.label,
			 		new Ext.Button({
			 			text: BUTTON_EDIT,
			 			
			 			handler: function(){
			 				if (this.getText() == BUTTON_EDIT){
			 					this.setText(BUTTON_HIDE);
			 					form.expand();	
			 				}
			 				else{
			 					this.setText(BUTTON_EDIT);
			 					form.collapse();	
			 				
			 				}
			 				
			 			}
			 		})
	 			]
	 		
	 		}),
	 		
	 		form
	 		],
	 		border: false
	 	
	 	});
	}

});


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
			script_type = params.type;
			if (! script_pk)
				script_pk = Ext.decode(response.responseText).pk;
			try{
				window.opener.scripts_jsonstore.reload();
			}
			catch(e){}
		},
		failure: function(){
//		            			Ext.MsgBox.msg('','Save failed');
			Ext.Msg.alert('Save', 'Saving script  failed'); 
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
					
			new Ext.grid.GridPanel({
				region: 'east',
				title: 'Actions',
				layout: 'fit',
				width: 200,
//				autoHeight: true,
				
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
          		
          		
          		var params = data.selections[0].data.params;
          		var script_name = data.selections[0].data.name;
          		var fields = [];
          		
          		
          		var drop_x = e.xy[0];
          		var drop_y = e.xy[1];
          	
          		var action = new MDAction({
			            title: script_name,
			            label: params.label,
			            position:[drop_x,drop_y],
//			            legend:'thumbnail',
			           
		            	inputs: ['in'],
		            	outputs: ['out'],
			            params: params
			            
			    }, baseLayer);
			   
          	} 
          	
          });
           
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
//          						console.log(action_stored = action_stored[0]);
          						var action_box = new MDAction({
						            title: action_stored.data.name,
						            position:[20,20],
			//			            legend:'thumbnail',
						           	'in': action['in'],
						           	'out': action['out'],
					            	inputs: ['in'],
					            	outputs: ['out'],
					            	position: [action.x, action.y],
						            params: action_stored.data.params,
						            label: action.label
						            
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
          			
          		}
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
						    text: 'Name: '
					    } ,
				   		{
					   		id: 'script_name',
				            xtype: 'textfield',
				            name: 'name',
				            allowBlank: false
			//	            emptyText: 'new script'
			        	},
                        {
                            text:'Events',
                            menu: new Ext.ux.StoreMenu({
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
                                        hideOnClick: true,
                                        xtype: 'menucheckitem'
                                },                               
                            })
                            
                        },
                        
			        	//~ {
						    //~ xtype: 'tbtext', 
						    //~ text: 'Event: '
					    //~ } ,
			        	//~ 
			        	//~ {
					   		//~ id: 'script_type',
					   		//~ 
				            //~ xtype: 'combo',
				            //~ name: 'type',
				            //~ allowBlank: true,	             
						    //~ autoSelect: true,
						    //~ editable: false,
						    //~ triggerAction: 'all',
						    //~ lazyRender:true,
						    //~ mode: 'local',
						    //~ store:  new Ext.data.ArrayStore({        
					        	//~ fields: ['pk', 'name'],
					        	//~ data: types_available
				    		//~ }),		
					    //~ 
						    //~ value: script_type,
							    //~ 
						    //~ valueField: 'pk',
						    //~ displayField: 'name'
					            //~ 
				//~ 
				        	//~ },
				        	
				        	{xtype: 'tbspacer'},
				        	
				        {
				            // xtype: 'button', // default for Toolbars, same as 'tbbutton'
				            text: 'Save',
				            id: 'save_button',
				            icon: '/files/images/icons/save.gif',
				            handler: function(){
				            	var button = Ext.getCmp('save_button');
				            	if (Ext.getCmp('script_name').isValid()){
			            				
			            				var submit_params =  {
											pk: script_pk,
											name: Ext.getCmp('script_name').getValue(),
											type: Ext.getCmp('script_type').getValue(),
											params: Ext.encode(baseLayer.getJson())		            			
										};
									
									if (submit_params.type != script_type)
										Ext.Msg.show({
										   title:'Change Script Event?',
										   msg: 'You are changing the event to whom the script is associated. Note that only a script at once can be associated with a given event. Do you confirm the change?',
										   buttons: Ext.Msg.YESNOCANCEL,
										   fn: function(btn){
										   	if (btn == 'yes'){
												save_script(submit_params);	   		
										   		
										   	}
										   },
										   
										   icon: Ext.MessageBox.QUESTION
										});
									else
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

	
