Ext.ux.Select = function(config) {
 	this.values = config.values; 	
 	console.log(config);
    // call parent constructor
    Ext.ux.Select.superclass.constructor.call(this, config);
 
}; 

Ext.extend(Ext.ux.Select, Ext.form.ComboBox, {	
    initComponent:function() {
    	var values = this.values;
    	
    	 Ext.apply(this, {
    	 	store:  new Ext.data.ArrayStore({        
		        fields: [
		            'value'
		        ],
		        data: values
		    }),
		    value: values[0]
    	 });
    	
    	Ext.ux.Select.superclass.initComponent.call(this);
    },
    allowBlank: false,
    autoSelect: true,
    editable: false,
    triggerAction: 'all',
    lazyRender:true,
    forceSelection: true,
    mode: 'local',
    valueField: 'value',
    displayField: 'value'
    
 
}); 

Ext.reg('select', Ext.ux.Select);


Ext.ux.CBFieldSet = function(config) {
	
	Ext.ux.CBFieldSet.superclass.constructor.call(this, config);
};


Ext.extend(Ext.ux.CBFieldSet, Ext.form.FieldSet, {
	 initComponent:function() {
	 	 var cb_id = Ext.id();
	 	 Ext.apply(this, {
	 	 	cb_id: cb_id,
	 	 	checkboxToggle: {tag: 'input', type: 'checkbox', name: this.checkboxName || this.id+'-checkbox', id: cb_id},
	 	 });
	 	Ext.ux.CBFieldSet.superclass.initComponent.call(this);
	 },
	
	 
	 collapsed: true,
	 onCheckClick: function(){
	 	var cb = Ext.get(this.cb_id);

	 	if (cb.dom.checked){
	 		this.expand();
	 		Ext.each(this.items.items, function(item){
	 			item.enable();
	 		});
	 	}
	 	else{
	 		this.collapse();
	 		Ext.each(this.items.items, function(item){
	 			item.disable();
	 		});
	 		
	 	
	 	}
	 }
	
});

Ext.reg('cbfieldset', Ext.ux.CBFieldSet);

var MDAction =  function(opts, layer) {	
	this.id = opts.id || Ext.id();
	
	this.inputs = opts.inputs || [];
	this.outputs = opts.outputs || [];
	opts.terminals = [];
	this.params = opts.params;

	
	
	for(var i = 0 ; i < opts.inputs.length ; i++) {
		var input = this.inputs[i];
		opts.terminals.push({
			"name": input, 
			"direction": [-1,0], 
			"offsetPosition": {"left": -14, "top": 3+30*(i+1) }, 
			"ddConfig": {
				"type": "input",
				"allowedTypes": ["output"]
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
			"alwaysSrc": true
		});
	}
	
	
	
	MDAction.superclass.constructor.call(this, opts, layer);

}; 
YAHOO.lang.extend(MDAction, WireIt.Container, {
	height: 150,
	resizable: true,
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
		
	
		
	},
	
	render: function(){
		
	 	WireIt.FormContainer.superclass.render.call(this);
	 	this.form = new Ext.form.FormPanel({
	 		renderTo: this.bodyEl,
//	 		height: 150,
	 		autoHeight: true,
	 		autoScroll: true,
	 		border: false,
	 		items: this.params
//	 		items:[{
//	 			xtype:'fieldset',
////		        columnWidth: 0.5,
//		        title: 'Resize',
//		        
//		        autoHeight:true,
//		        checkboxToggle: true, 
//		        items:[{
//		        	xtype: 'textfield',
//		        	fieldLabel: 'height'
//		        	
//		        }]
//		     },
//		     {
//	 			xtype:'fieldset',
////		        columnWidth: 0.5,
//		        title: 'Crop',
//		        
//		        autoHeight:true,
//		        checkboxToggle: true, 
//		        items:[{
//		        	xtype: 'textfield',
//		        	fieldLabel: 'height'
//		        	
//		        }]
//		     }
//		     
//	 		]
	 	})
	}

});

//var AdaptImage = function(opts, layer) {
//	opts.inputs = ['in'];
//	opts.outputs = ['out'];
//	opts.title =  ['AdaptImage'];
//	
//	
//	opts.fields= [ 
//			{type: 'select', inputParams: {label: 'source_variant', name: 'source_variant', selectValues: ['original'] } },
//			{type: 'select', inputParams: {label: 'output_variant', name: 'output_variant', selectValues: ['thumbnail','preview',  'fullscreen'], value: opts.output_variant } },
//			{inputParams: {label: 'height', name: 'height', required: false, value: opts.height_value } }, 
//			{inputParams: {label: 'width', name: 'width', required: false, value: opts.width_value} } 
//			
//		];
//	
//	AdaptImage.superclass.constructor.call(this, opts, layer);
//};	 
//
//YAHOO.lang.extend(AdaptImage, MDAction, {
//	
//	
//
//});
//
//var SmartContainer = function(opts, layer) {
//	
////		this.inputs = opts.inputs ;
////		this.outputs = opts.outputs;
//	SmartContainer.superclass.constructor.call(this, opts, layer);
//	
//};
//YAHOO.lang.extend(SmartContainer, WireIt.FormContainer, {
//	
//	
//	
////		inputs: ['lol'],
////		outputs: [],
//	
//	render: function() {
//		SmartContainer.superclass.render.call(this);
//		this.inputs = ['in'];
//		this.outputs = ['out'];
//		for(var i = 0 ; i < this.inputs.length ; i++) {
//			var input = this.inputs[i];
//			this.terminals.push({
//				"name": input, 
//				"direction": [-1,0], 
//				"offsetPosition": {"left": -14, "top": 3+30*(i+1) }, 
//				"ddConfig": {
//					"type": "input",
//					"allowedTypes": ["output"]
//				}
//			});
//			this.bodyEl.appendChild(WireIt.cn('div', null, {lineHeight: "30px"}, input));
//		}
//		
//		for(i = 0 ; i < this.outputs.length ; i++) {
//			var output = this.outputs[i];
//			this.terminals.push({
//				"name": output, 
//				"direction": [1,0], 
//				"offsetPosition": {"right": -14, "top": 3+30*(i+1+this.inputs.length) }, 
//				"ddConfig": {
//					"type": "output",
//					"allowedTypes": ["input"]
//				},
//				"alwaysSrc": true
//			});
//			this.bodyEl.appendChild(WireIt.cn('div', null, {lineHeight: "30px", textAlign: "right"}, output));
//		}
//		
//			
//	}
//	
//});
//var extract_features, adapt_1, adapt_2, adapt_3, test_form;


var ActionManager = {
	actions:{},
	add: function(action){
		this.actions[action.id] = action;
	},
	remove: function(action){
		this.actions[action.id] = null;
	
	},
	getJson: function(){
		var actions_json = {}, action;
		for(action_id in this.actions){
			if (action_id){
				console.log('action_id'  + action_id);
				action = this.actions[action_id];
				
				actions_json[action_id] = {
					params: action.getParams(),
					'in': action.getInputs(),
					out: action.getOutputs()
				
				}
				
			
			}
		}
		
		
		return actions_json;
	
	}
};

var baseLayer;

Ext.onReady(function(){
	
	new Ext.grid.GridPanel({
		renderTo:'actions-container',
		title: 'Actions',
		layout: 'fit',
		autoHeight: true,
		enableDragDrop: true,
		ddGroup: 'wireit',
		
		
			store: new Ext.data.JsonStore({
				url:'/get_actions/',
				fields:['name', 'params'],
				autoLoad: true,
				root: 'scripts'	
			}),
			columns:[{
				name: 'Script',
				dataIndex: 'name'
			}],
		hideHeaders: true,
		viewConfig: {
        forceFit: true}

		
	});
	
	var layer_el = Ext.get('wire-layer');
	
	baseLayer = new WireIt.Layer({
		layerMap: false,
		parentEl: layer_el
	});
		
	YAHOO.inputEx.spacerUrl = "/files/WireIt-0.5.0/lib/inputex/images/space.gif";
 
                // Example 1
              
                
//    adapt_1 = new AdaptImage({
//            position:[500,140],
//            legend:'thumbnail',
//            height_value : 100,
//            width_value : 100,
//            output_variant: 'thumbnail'
//            
//    }, baseLayer); 
//    
//    adapt_2 = new AdaptImage({
//            position:[500,340],
//            legend:'preview',
//            height_value : 300,
//            width_value : 300,
//            output_variant: 'preview'
//            
//    }, baseLayer); 
//    
//    adapt_3 = new AdaptImage({
//            position:[500,540],
//            legend:'fullscreen',
//            height_value : 800,
//            width_value : 600,
//            output_variant: 'fullscreen'
//            
//    }, baseLayer); 
//    
//    
//    
//    
//    extract_features  = new MDAction({
//            id: 'extract',
//            position:[50,140],
//            height: 200,
//            width: 200,
//            title: ['ExtractFeatures'],
//            outputs: ['out'],
//            inputs: ['in'],
//            
//            
//            fields: [
//            {type: 'select', inputParams: {label: 'source_variant', name: 'source_variant', selectValues: ['original'] } }
////                              {type: 'select', inputParams: {label: 'Title', name: 'title', selectValues: ['Mr','Mrs','Mme'] } },
////                              {inputParams: {label: 'Firstname', name: 'firstname', required: true } }, 
////                              {inputParams: {label: 'Lastname', name: 'lastname', value:'Dupont'} }, 
////                              {type:'email', inputParams: {label: 'Email', name: 'email', required: true}}, 
////                              {type:'boolean', inputParams: {label: 'Happy to be there ?', name: 'happy'}}, 
////                              {type:'url', inputParams: {label: 'Website', name:'website', size: 25}} 
//            ],
//            legend: ''
//                    
//                    
//            }, baseLayer);
                    
                    
            
            
//            var w1 = new WireIt.Wire(adapt_1.terminals[0], extract_features.terminals[1], layer_el)
//            var w2 = new WireIt.Wire(adapt_2.terminals[0], extract_features.terminals[1], layer_el)
//            var w3 = new WireIt.Wire(adapt_3.terminals[0], extract_features.terminals[1], layer_el)
//            w1.drawBezierCurve();
//            w2.drawBezierCurve();
//            w3.drawBezierCurve();
            
    
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
			            position:[drop_x,drop_y],
//			            legend:'thumbnail',
			           
		            	inputs: ['in'],
		            	outputs: ['out'],
			            params: params
			            
			    }, baseLayer);
			    
			    ActionManager.add(action);
          		
          		
          	} 
          	
          });
            	   

	
	
});

	