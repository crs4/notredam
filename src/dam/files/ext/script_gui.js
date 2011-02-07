var MDAction =  function(opts, layer) {	
	
	this.inputs = opts.inputs || [];
	this.outputs = opts.outputs || [];
	opts.terminals = [];
	opts.height = 50;
	opts.resizable = true;
	
	
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
YAHOO.lang.extend(MDAction, WireIt.FormContainer, {

});

var AdaptImage = function(opts, layer) {
	opts.inputs = ['in'];
	opts.outputs = ['out'];
	opts.title =  ['AdaptImage'];
	
	
	opts.fields= [ 
			{type: 'select', inputParams: {label: 'source_variant', name: 'source_variant', selectValues: ['original'] } },
			{type: 'select', inputParams: {label: 'output_variant', name: 'output_variant', selectValues: ['thumbnail','preview',  'fullscreen'], value: opts.output_variant } },
			{inputParams: {label: 'height', name: 'height', required: false, value: opts.height_value } }, 
			{inputParams: {label: 'width', name: 'width', required: false, value: opts.width_value} } 
			
		];
	
	AdaptImage.superclass.constructor.call(this, opts, layer);
};	 

YAHOO.lang.extend(AdaptImage, MDAction, {
	
	

});

var SmartContainer = function(opts, layer) {
	
//		this.inputs = opts.inputs ;
//		this.outputs = opts.outputs;
	SmartContainer.superclass.constructor.call(this, opts, layer);
	
};
YAHOO.lang.extend(SmartContainer, WireIt.FormContainer, {
	
	
	
//		inputs: ['lol'],
//		outputs: [],
	
	render: function() {
		SmartContainer.superclass.render.call(this);
		this.inputs = ['in'];
		this.outputs = ['out'];
		for(var i = 0 ; i < this.inputs.length ; i++) {
			var input = this.inputs[i];
			this.terminals.push({
				"name": input, 
				"direction": [-1,0], 
				"offsetPosition": {"left": -14, "top": 3+30*(i+1) }, 
				"ddConfig": {
					"type": "input",
					"allowedTypes": ["output"]
				}
			});
			this.bodyEl.appendChild(WireIt.cn('div', null, {lineHeight: "30px"}, input));
		}
		
		for(i = 0 ; i < this.outputs.length ; i++) {
			var output = this.outputs[i];
			this.terminals.push({
				"name": output, 
				"direction": [1,0], 
				"offsetPosition": {"right": -14, "top": 3+30*(i+1+this.inputs.length) }, 
				"ddConfig": {
					"type": "output",
					"allowedTypes": ["input"]
				},
				"alwaysSrc": true
			});
			this.bodyEl.appendChild(WireIt.cn('div', null, {lineHeight: "30px", textAlign: "right"}, output));
		}
		
			
	}
	
});
var extract_features, adapt_1, adapt_2, adapt_3, test_form;


Ext.onReady(function(){
	
	var layer_el = Ext.get('wire-layer');
	
	var demoLayer = new WireIt.Layer({
		layerMap: false,
		parentEl: layer_el
	});
		
	YAHOO.inputEx.spacerUrl = "/files/WireIt-0.5.0/lib/inputex/images/space.gif";
 
                // Example 1
              
                
    adapt_1 = new AdaptImage({
            position:[500,140],
            legend:'thumbnail',
            height_value : 100,
            width_value : 100,
            output_variant: 'thumbnail'
            
    }, demoLayer); 
    
    adapt_2 = new AdaptImage({
            position:[500,340],
            legend:'preview',
            height_value : 300,
            width_value : 300,
            output_variant: 'preview'
            
    }, demoLayer); 
    
    adapt_3 = new AdaptImage({
            position:[500,540],
            legend:'fullscreen',
            height_value : 800,
            width_value : 600,
            output_variant: 'fullscreen'
            
    }, demoLayer); 
    
    
    
    
    extract_features  = new MDAction({
            id: 'extract',
            position:[50,140],
            height: 200,
            width: 200,
            title: ['ExtractFeatures'],
            outputs: ['out'],
            inputs: ['in'],
            
            
            fields: [
            {type: 'select', inputParams: {label: 'source_variant', name: 'source_variant', selectValues: ['original'] } }
//                              {type: 'select', inputParams: {label: 'Title', name: 'title', selectValues: ['Mr','Mrs','Mme'] } },
//                              {inputParams: {label: 'Firstname', name: 'firstname', required: true } }, 
//                              {inputParams: {label: 'Lastname', name: 'lastname', value:'Dupont'} }, 
//                              {type:'email', inputParams: {label: 'Email', name: 'email', required: true}}, 
//                              {type:'boolean', inputParams: {label: 'Happy to be there ?', name: 'happy'}}, 
//                              {type:'url', inputParams: {label: 'Website', name:'website', size: 25}} 
            ],
            legend: ''
                    
                    
            }, demoLayer);
                    
                    
            
            
//            var w1 = new WireIt.Wire(adapt_1.terminals[0], extract_features.terminals[1], layer_el)
//            var w2 = new WireIt.Wire(adapt_2.terminals[0], extract_features.terminals[1], layer_el)
//            var w3 = new WireIt.Wire(adapt_3.terminals[0], extract_features.terminals[1], layer_el)
//            w1.drawBezierCurve();
//            w2.drawBezierCurve();
//            w3.drawBezierCurve();
            
            
            	   

	
	
});

	