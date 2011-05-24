renditions_store = new Ext.data.JsonStore({
	storeId: 'renditions_store',
	root: 'variants',
	fields: ['name', 'media_type', 'auto_generated'],
	url: '/get_variants_list/'
});

var utils_data = {'actions': [{
	name: 'input rendition',	
	xtype: 'inputrendition',
	width:200
	}
]};

Ext.ux.StoreMenu = function(config){
    
    Ext.ux.StoreMenu.superclass.constructor.call(this, config);    
    var menu = this;
    var store_cfg = config.store_cfg;
    Ext.apply(store_cfg, {
        autoLoad: true,
        listeners: {
            load: function(store, records){               
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
Ext.extend(Ext.ux.StoreMenu, Ext.menu.Menu, {
    });



Ext.ux.FieldSetContainer = function(config) {
			
 	if(config.dynamic)
		Ext.each(config.items, function(item){
			item.dynamic = true;
		});
 	
    Ext.ux.FieldSetContainer.superclass.constructor.call(this, config);     	
 	
 	this.form = this.ownerCt;
 	
 	//Ext.apply(config, this);
 	
}; 

Ext.extend(Ext.ux.FieldSetContainer, Ext.Panel, {
	border: false,
	layout: 'form',
	//initComponent: function(){
		//console.log('initComponent1');
		//if (this.dynamic)
			//this._set_dynamic();
		//Ext.ux.FieldSetContainer.superclass.initComponent.call(this);     	
		//console.log('initComponent2');
	//},
	 onRender:function(ct, position) {
		
		//if(this.dynamic)
			this._set_dynamic();
		Ext.ux.FieldSetContainer.superclass.onRender.call(this, ct, position);    
	},
	
	get_name: function(){
		var names = [];
		Ext.each(this.items.items, function(item){			
			names.push(item.name);		
		});
		console.log('names');
		console.log(names);
		return names;
		
	},	
	get_dynamic_field: function(){
		
		var dynamic_fields = [];
		Ext.each(this.items.items, function(item){
			
			dynamic_fields = dynamic_fields.concat(item.get_dynamic_field());
			
		});
				
		return dynamic_fields;
		
	},
	_set_dynamic: function(){
		
		Ext.each(this.items.items, function(item){
			console.log(item);
			item._set_dynamic();
		});
	},
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

Ext.ux.DynamicFieldSet = function(config) {
	if (config.allow_dynamic == undefined)
		config.allow_dynamic = true;
		
	Ext.ux.DynamicFieldSet.superclass.constructor.call(this, config);    
	
};
Ext.extend(Ext.ux.DynamicFieldSet, Ext.form.FieldSet, {
	initComponent: function(){
		if (this.allow_dynamic == undefined)
		this.allow_dynamic = true;
		
		Ext.ux.DynamicFieldSet.superclass.initComponent.call(this);    
	},
	_add_dynamic_icon: function(){
		if (this.allow_dynamic){
			this.dynamic_icon = this.getEl().createChild({
				tag: 'img',
				cls: 'dynamic_input ' + (this.dynamic? '' :' dynamic_input_unselected dynamic_input_hidden'),
				src: '/files/images/icons/fam/application_xp_terminal.png',
				style: 'float: right; z-index:2000; position: relative; top: -40px',
				//style: 'float: right; padding-right:5px; z-index:2000;',
				//style: 'z-index:2000; position: absolute; top:40%; left:92%',
				
				title: 'Dynamic Input: value will be set run time',
				onclick: String.format('Ext.getCmp(\'{0}\').toggleDynamize();', this.id)
				
			});
			
			var dynamic_icon = this.dynamic_icon;
			this.getEl().on('mouseenter', function(){	
				
				if(dynamic_icon && !dynamic_icon.hasClass('x-item-disabled'))		
						dynamic_icon.removeClass('dynamic_input_hidden');					
				});
				
				this.getEl().on('mouseleave', function(){
					if (dynamic_icon && dynamic_icon.hasClass('dynamic_input_unselected'))
						dynamic_icon.addClass('dynamic_input_hidden');					
				});
			}
		},
		onRender : function(ct, position){
			Ext.ux.DynamicFieldSet.superclass.onRender.call(this, ct, position);		
		
		   if(this.allow_dynamic) 
				this._add_dynamic_icon();	
		},
		toggleDynamize: function(){		
			
			if (this.dynamic_icon.hasClass('x-item-disabled'))
				return;
			
			if (this.dynamic){
				Ext.each(this.items.items, function(item){
					console.log('item');
					console.log(item);
					this.enable();
				});
				
				this.dynamic_icon.removeClass('dynamic_input_selected');
				this.dynamic_icon.addClass('dynamic_input_unselected');	
				this.dynamic_icon.addClass('dynamic_input_hidden');
				
				this.dynamic = false;
			} 
			
			else{
				
				Ext.each(this.items.items, function(item){
					this.disable();
				});
				
				this.dynamic_icon.removeClass('dynamic_input_unselected');
				this.dynamic_icon.addClass('dynamic_input_selected');	
				
				this.dynamic = true;
			}
		},		
		disableAll: function(){
			
			this.dynamic_icon.addClass('x-item-disabled');
			this.dynamic_icon.addClass('dynamic_input_hidden');					
		   
			
		},
		enableAll: function(){
			
			this.dynamic_icon.removeClass('x-item-disabled');			
		   
			
		},
		_set_dynamic: function(){		
			this.dynamic = true;
		}

}); 


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
			
			var new_values = this.ownerCt.values[value];	
			
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

Ext.extend(Ext.ux.SelectFieldSet, Ext.ux.DynamicFieldSet, {
	data_loaded: function(data){
//		Ext.ux.SelectFieldSet.superclass.data_loaded.call(this, data);
		
		this.select_field._select(data.output_preset);
		this.ownerCt.getForm().setValues(data); //temporary, since form items are deleted and new ones are added, i have to reload the data 
		Ext.each(this.items.items, function(item){
		if (item.data_loaded)
			item.data_loaded(data);
		});
		
	},
	
	
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
	name: 'watermarking_position',
    initComponent: function(){
       
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
    }


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
    allowBlank: false,
    autoSelect: true,
   
    editable: false,
    triggerAction: 'all',
    lazyRender:true,
    forceSelection: true,
    mode: 'local',
    _set_dynamic: function(){
		this.dynamic = true;
	}
    
    
 
}); 

Ext.reg('select', Ext.ux.Select);


Ext.ux.CBFieldSet = function(config) {		
	if (config.allow_dynamic == undefined)
		config.allow_dynamic = true;
		
	if (!config.dynamic && config.allow_dynamic)
		config.collapsed = true;		
	else
		config.collapsed = false;
	Ext.ux.CBFieldSet.superclass.constructor.call(this, config);
	
};

Ext.extend(Ext.ux.CBFieldSet, Ext.ux.DynamicFieldSet, {	
	
	initComponent: function(){
		console.log('aaaaaaaa');
		Ext.ux.CBFieldSet.superclass.initComponent.call(this);
		console.log('this.dynamic ' +this.dynamic);
		console.log('this.allow_dynamic ' +this.allow_dynamic);
		if (!this.dynamic && this.allow_dynamic)
			this.collapsed = true;		
		else
			this.collapsed = false;
		
	},
	
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
	 	 	checkboxToggle: {tag: 'input',id: cb_id,  type: 'checkbox'}
	 	 });
	 	Ext.ux.CBFieldSet.superclass.initComponent.call(this);
	
	 },
	 
	expand: function(){
	
		Ext.ux.CBFieldSet.superclass.expand.call(this);
		if (!this.dynamic)
			Ext.each(this.items.items, function(item){			
	 			item.enable();
	 	});
		
	},
	
	onRender : function(ct, position){
       
       if(this.allow_dynamic) 
			Ext.ux.CBFieldSet.superclass.onRender.call(this, ct, position);		
		else
			Ext.form.FieldSet.superclass.onRender.call(this, ct, position);		
        //this._add_dynamic_icon();		
       
        console.log('disabling...');
		if (this.collapsed)
			Ext.each(this.items.items, function(item){			
				console.log('disabling...');
	 			item.disable();
	 	});
    },
    
	collapse: function(){
		
		if(this.dynamic){
			this.toggleDynamize();
		}
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
	
	initComponent: function(){		
		Ext.ux.MovableCBFieldSet.superclass.initComponent.call(this);
		var config = this.initialConfig; 
		
		this.add({
		xtype: 'hidden',
		name: config.order_field_name,
		value: config.order_field_value,
		
//			this field is hidden and readonly, it is used to hold the ordered list of the actions [resize, crop, watermark]
		setValue: function(new_value){
			
		
			if (config.name == new_value)
				this.setRawValue(new_value);

		}
	});
	
	},
	
	get_dynamic_field: function(){
		if (this.dynamic)
			return [this.name];
		else
			return [];
	},
	
	check_expand: function(){
		
		if(this.dynamic){
				this.expand();
				return;
		}
		
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

        Ext.ux.MovableCBFieldSet.superclass.onRender.call(this, ct, position);
		if (this.movable && this.allow_dynamic){
			this.header.insertFirst({tag: 'img', src: '/files/images/icons/arrow-down.gif', style: 'margin-bottom: -4px; margin-left: -3px', onclick: String.format('Ext.getCmp(\'{0}\').move_down();', this.id)});
			this.header.insertFirst({tag: 'img', src: '/files/images/icons/arrow-up.gif', style: 'margin-bottom: -4px; margin-left: -2px',onclick: String.format('Ext.getCmp(\'{0}\').move_up();', this.id)});
		}
		
		//this._add_dynamic_icon();			
		
        //var o = typeof this.checkboxToggle == 'object' ?
                //this.checkboxToggle :
                //{tag: 'input', type: 'checkbox', name: this.checkboxName || this.id+'-checkbox'};
        //this.checkbox = this.header.insertFirst(o);
        //this.checkbox.dom.checked = !this.collapsed;
        //this.mon(this.checkbox, 'click', this.onCheckClick, this);
    //
        
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

                if(value && item.name != cbf.initialConfig.order_field_name && item != cbf.position)
                
                        values[item.name] = value;
        });
 		
 		container.remove(this); 	
 		new_obj = container.insert(position, copy);
 		new_obj.dynamic = this.dynamic;
 	
 		container.doLayout();
 		
 		
 		container.form.getForm().setValues(values);
 		if (new_obj.dynamic)
			new_obj.expand();
		else
			new_obj.check_expand();
// 		this.position.setValue(position);
 		
 		
	 },
	move_up: function(){

		this.move(this.get_position()  - 1);
	},
	move_down: function(){
//		console.log(this.position_field.getValue());
		this.move(this.get_position()  + 1);
	}
	
});

Ext.reg('movablecbfieldset', Ext.ux.MovableCBFieldSet);


Ext.ux.WatermarkFieldSet = function(config){
	var pos_x_percent = new Ext.form.Hidden({
		name: config.wm_x_name || 'pos_x_percent'
	});
	
	var pos_y_percent = new Ext.form.Hidden({
		name: config.wm_x_name || 'pos_y_percent'
	});
	
		
	var wm_id = new Ext.form.TextField({
        'id': 'wm_id',
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
                
                if(this.ownerCt.pos_x_percent.getValue() && this.ownerCt.pos_y_percent.getValue())
					 this.ownerCt.watermarking(this.ownerCt._get_square(this.ownerCt.pos_x_percent.getValue(), this.ownerCt.pos_y_percent.getValue()));
    	 		 
    	 		 
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
        'items':[ wm_id, {
                 'xtype': 'watermarkbrowsebutton',
                 'text': 'Browse',
                 values: config.renditions
                } ] }),
        position,        
        pos_x_percent,
        pos_y_percent
		];
	
	Ext.ux.WatermarkFieldSet.superclass.constructor.call(this, config);
	Ext.apply(this, {
		pos_x_percent: pos_x_percent,
        pos_y_percent: pos_y_percent,       
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

    _get_square: function(xpercent, ypercent) {
        var x = Math.round(((xpercent - 5)/100) * 3) + 1;
        var y = Math.round(((ypercent - 5)/100) * 3);
        return  3*y + x;
    },
	
	data_loaded: function(values){        
		
		if(this.pos_x_percent && this.pos_y_percent){
			this.watermarking(this._get_square(this.pos_x_percent.getValue(), this.pos_y_percent.getValue()));
          
        }
			
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
        if(!id)
            return;
	    this._reset_watermarking();
	    this._set_hidden_position_percent(id);
	    try{
          
	    	Ext.get(this.position.boxes[id -1].id).setStyle({
	        background: 'green',
	        opacity: 0.6
	        });
	    		    
	    }
	    catch(e){
            console.log(e)
	    }
	    
	}
	


});

Ext.reg('watermarkfieldset', Ext.ux.WatermarkFieldSet);



Ext.ux.MultiRenditions = function(config) {
	config.storeId =config.storeId || 'renditions_store';
	this.dynamic = config.dynamic || false;
	this.allow_dynamic = config.allow_dynamic || true;
	
	this.store = Ext.StoreMgr.get(config.storeId);
	
	renditions = this.store.queryBy(function(record){
		var media_type_check = false, auto_generated = false;
		if (record.data.media_type == config.media_type )
			media_type_check = true;
		if (record.data.auto_generated == config.auto_generated)
			auto_generated = true;
		if (media_type_check && auto_generated)
			return true;
		return true;
	});
	
	
		
 	values = [];
 	
 	Ext.each(renditions.items, function(r){		
		values.push([r.data.name]);
	}); 	
    this.values = values;
    
    
 	Ext.apply(config, {
 		store: new Ext.data.ArrayStore({        
	        fields: config.fields || ['value'],
	        data: this.values
	    }),
	    valueField: config.valueField || 'value',
		displayField: config.displayField || 'value'
		
	    
	    
	    
 	});
 	
    // call parent constructor
    Ext.ux.MultiRenditions.superclass.constructor.call(this, config);
    
 
}; 

Ext.extend(Ext.ux.MultiRenditions,  Ext.ux.form.SuperBoxSelect, {
    allowBlank: false,
    mode: 'local',
    width: 220,
    
    onRender:function(ct, position) {
    	var h = this.hiddenName;
    	this.hiddenName = null;
        Ext.ux.form.SuperBoxSelect.superclass.onRender.call(this, ct, position);
        this.hiddenName = h;
        this.manageNameAttribute();
       
        var extraClass = (this.stackItems === true) ? 'x-superboxselect-stacked' : '';
        if(this.renderFieldBtns){
            extraClass += ' x-superboxselect-display-btns';
        }
        this.el.removeClass('x-form-text').addClass('x-superboxselect-input-field');
        
        this.wrapEl = this.el.wrap({
            tag : 'ul'
        });
        
        var width = this.width -56;
        
        this.outerWrapEl = this.wrapEl.wrap({
            tag : 'div',
            cls: 'x-form-text x-superboxselect ' + extraClass,
            style: 'width: ' + width +'px !important;'
            
        });
        
        if (!this.fieldLabel){		
				this.outerWrapEl.parent().parent().setStyle({paddingLeft:0});		
			}
        
        this.inputEl = this.el.wrap({
            tag : 'li',
            cls : 'x-superboxselect-input'
        });
        
        if(this.renderFieldBtns){
            this.setupFieldButtons().manageClearBtn();
        }
        
        this.setupFormInterception();
    }
    
    
});	

Ext.reg('multiselect', Ext.ux.MultiRenditions);


