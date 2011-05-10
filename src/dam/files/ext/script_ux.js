Ext.ux.StoreMenu = function(config){
    
    Ext.ux.StoreMenu.superclass.constructor.call(this, config);    
    var menu = this;
    var store_cfg = config.store_cfg;
    Ext.apply(store_cfg, {
        autoLoad: true,
        listeners: {
            load: function(store, records){               
                menu.removeAll();
                console.log(menu);
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
			console.log('value');
			console.log(this.ownerCt.values);
			var new_values = this.ownerCt.values[value];	
			console.log('new_values');
			console.log(new_values);
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
		console.log('data_loaded');
		console.log(data);
		this.select_field._select(data.output_preset);
		this.ownerCt.getForm().setValues(data); //temporary, since form items are deleted and new ones are added, i have to reload the data 
		Ext.each(this.items.items, function(item){
		if (item.data_loaded)
			item.data_loaded(data);
		});
		console.log('end loaded');
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
    console.log('WatermarkPosition constructor');
    
	Ext.ux.WatermarkPosition.superclass.constructor.call(this, config);
}; 

Ext.extend(Ext.ux.WatermarkPosition, Ext.form.Field, {
//	height: 160,
	name: 'watermarking_position',
    initComponent: function(){
        console.log('WatermarkPosition constructor');
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
	 	 	checkboxToggle: {tag: 'input',id: cb_id,  type: 'checkbox'}
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
		console.log('data_loaded');
		if(this.pos_x_percent && this.pos_y_percent){
			this.watermarking(this._get_square(this.pos_x_percent.getValue(), this.pos_y_percent.getValue()));
            console.log('data_loaded end')
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
        console.log('watermarking ' + id);  
	    this._reset_watermarking();
	    this._set_hidden_position_percent(id);
	    try{
            console.log('this.position.boxes[id -1].id '+ this.position.boxes[id -1].id);
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



Ext.ux.MultiSelect = function(config) {
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
    Ext.ux.MultiSelect.superclass.constructor.call(this, config);
    
 
}; 

Ext.extend(Ext.ux.MultiSelect,  Ext.ux.form.SuperBoxSelect, {
    allowBlank: false,
    mode: 'local',
    width: 220
    
});	

Ext.reg('multiselect', Ext.ux.MultiSelect);
