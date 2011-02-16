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


DEBUG_SCRIPT = false;
/**
  * Helper class for organizing the buttons
  */
var ActionRecord = Ext.data.Record.create([ // creates a subclass of Ext.data.Record
    {name: 'name'},
    {name: 'media_type'},
    {name: 'parameters'}
]);

/**
 * @class This class develop store for the type items. 
 */
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

/**
 * This function develop reset of watermark position. 
 * @return
 */
function reset_watermarking(){	
    for (i=1; i<10; i++){
        Ext.get('square'+i).setStyle({
            background: 'none',
            opacity: 1
            });
    }
}

/**
 * This function insert value into hidden input for watermark position. 
 * @param id
 * @return
 */
function _set_hidden_position_percent(id){
	var pos_x = ((id-1) % 3) * 33 + 5;
	var pos_y = (parseInt((id-1) / 3)) * 33 + 5;
	
	if (DEBUG_SCRIPT){
		console.log(pos_x);
		console.log(pos_y);
	}
	
	Ext.getCmp('panel_watermarks_views').get('hidden_pos_x_percent').setValue(parseInt(pos_x));
	Ext.getCmp('panel_watermarks_views').get('hidden_pos_y_percent').setValue(parseInt(pos_y));
}


/**
 * This function set position of watermark. 
 * @param id
 * @return
 */
function watermarking(id){	
    reset_watermarking();
    _set_hidden_position_percent(id);
    Ext.get('square'+id).setStyle({
        background: 'green',
        opacity: 0.6
        });
    watermarking_position = id;
}

/**
 * This function update data view of watermark. 
 * @return
 */

function _update_watermarks(){  
	Ext.getCmp('dataview_watermarks').getStore().load();
}

/**
 * This function verify that all fields of all action are fill. 
 * @param my_win
 * @return
 */

function _check_form_detail_script(my_win){
	//verificare che tutti i campi siano selezionati.
	if (DEBUG_SCRIPT)
		console.log('check');
	var flag = true;
	var ratio = false;
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
			if (DEBUG_SCRIPT){
				console.log(params);
			}
			for(k=0;k<params.parameters.length;k++){
				if (!params.parameters[k].value && params.parameters[k].type != 'boolean'){
					if (DEBUG_SCRIPT){
						console.log('parametro null.');
						console.log(params.parameters[k]);
					}
					flag = false;
				}
				if (params.parameters[k].name == "ratio"){
					var str = params.parameters[k].value;
					var index = params.parameters[k].value.indexOf(':');
        			if 	( !(parseInt(str.slice(0,index)) + "" == str.slice(0,index)) || !(parseInt(str.slice(index+1,str.length)) + "" == str.slice(index+1,str.length))){
        				flag = false;
        			}
				}
				if (params.parameters[k].name == "mail"){
					flag = true;
				}
			}
		});
	}
	return flag;
}

/**
 * This function generate detail form except for crop and watermark action. 
 * @param grid
 * @param selected
 * @param actionsStore
 * @param media_type
 * @param parameters
 * @param name_action
 * @return
 */

function _global_generate_details_form(grid, selected, actionsStore, media_type, parameters, name_action )
{
    var i = 0;
    var recApp;
    var item_array = new Array();
    var dict;
	var val;
	var recAppValues;
	
	if(DEBUG_SCRIPT){
    	console.log(name_action);
    	console.log('parameters');
		console.log(parameters);
	}
    for (i=0;i<parameters.length;i++){
//    	cercare il name_action nella gridlistactions, e verificare se ha values
        recApp = actionsStore.getAt(actionsStore.findExact('name', name_action));
        //in sendbymail restituisce in ordine inverso.
        if (DEBUG_SCRIPT){
        	console.log('recApp[data]');
        	console.log(recApp['data']);
        }
        if (parameters[i].name != recApp['data']['parameters'][i].name){
        	var j = 0;
        	while (parameters[i].name != recApp['data']['parameters'][j].name) {
        		  j++;
        	}
        }else j = i;
        
        if (recApp['data']['parameters'][j]['values']){
    		if (recApp['data']['parameters'][j]['name'] == 'output'){
    			dict = recApp['data']['parameters'][j]['values'][media_type];
    			recAppValues = [];
    			for (key in dict) {
    				if (dict.hasOwnProperty(key)) { 
    					recAppValues.push(dict[key]);
    					val = dict[key];
    				}
    			}
	    		if (parameters[i]['value']) 
	    			val = dict[parameters[i]['value']];  			
    		}else{
	    		recAppValues = recApp['data']['parameters'][j]['values'][media_type];
	    		if (parameters[i]['value']) 
	    			val = parameters[i]['value'];
	    		else 
	    			val = recApp['data']['parameters'][j]['values'][media_type][0];
    		}
    		var width_combobox;
    		if (name_action == 'set rights'){
    			width_combobox = 300;
    		}else
    			width_combobox = 140;
    			
    		item_array.push(new Ext.form.ComboBox({                            
    			fieldLabel   : parameters[i].name.replace("_"," "),
    			store        : recAppValues,
				triggerAction: 'all',
				value        : val,
				name         : parameters[i].name,
				width        : width_combobox
    	    }));
    	}
    	else if (parameters[i].type == 'number'){
    		item_array.push(new Ext.form.NumberField({                            
    	          fieldLabel: parameters[i].name.replace("_"," "),
    	          value     : parameters[i].value,
    	          name      : parameters[i].name,
    	          msgTarget :'side',                            
    	          width     : 140
    	      	}));
    	}
    	else if (parameters[i].type == 'string' && parameters[i].name != 'ratio'){
    		if (name_action != 'send by mail'){
	    		item_array.push(new Ext.form.TextField({                            
				    fieldLabel  : parameters[i].name.replace("_"," "),
				    value       : parameters[i].value,
				    name        : parameters[i].name,
				    msgTarget   : 'side',                            
				    width       : 140                            
			    }));
    		}else {
	    		item_array.push(new Ext.form.TextField({                            
				    fieldLabel  : parameters[i].name.replace("_"," "),
				    value       : parameters[i].value,
				    name        : parameters[i].name,
				    vtype       : 'email',
				    msgTarget   : 'side',                            
				    width       : 140                            
			    }));
    		}
    	}else if (parameters[i].type == 'boolean' && media_type == 'image'){ //for check embedded xmp
    		item_array.push(new Ext.form.Checkbox({                            
  	          fieldLabel  : parameters[i].name.replace("_"," "),
  	          checked     : parameters[i].value,
  	          value       : parameters[i].value,
  	          name        : parameters[i].name,
  	          msgTarget   : 'side',
  	          listeners   : {
    			  	check : function(checked){
    					this.value = checked;
    			  	}
    		  }
  	      	}));    		
    	}
    }
    
	return item_array;
}

/**
 * This function generate detail form watermark action. 
 * @param panel
 * @param grid
 * @param selected
 * @param actionsStore
 * @param media_type
 * @param parameters
 * @return
 */

function _watermark_generate_details_forms(panel, grid, selected, actionsStore, media_type, parameters, name_action)
{
	
	watermarking_position = 0; // 0 mean undefined

	watermarking_position_id = Ext.id();
    
	var i, j;
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
				while (parameters[i]['name'] != 'watermark_filename' && i<parameters.length)
					i++;
				if (parameters.length>0 && parameters[i]['name'] == 'watermark_filename' && parameters[i]['value']){
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
    				            	j = 0;
    				        		while (parameters[j]['name'] != 'pos_y_percent' && j<parameters.length){
    				        			j++;
    				        		}	
				        			if (parameters[i]['name'] == 'pos_x_percent' && parameters[i]['value']){      			    	            	
        				        		var pos_x = ((parameters[i]['value'] - 5) / 33) + 1;
	                					var pos_y = ((parameters[j]['value'] - 5) / 33) + 1;
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
                    	                        	Ext.Msg.show({title:'Success', msg: 'Watermark removed.', width: 300,
         					        				   buttons: Ext.Msg.OK, icon: Ext.MessageBox.INFO });
                    	                        	_update_watermarks();
                    	                        }else
                    			        			Ext.Msg.show({title:'Warning', msg: Ext.decode(response.responseText), width: 300,
                    			        				   buttons: Ext.Msg.OK, icon: Ext.MessageBox.WARNING });
                    	                    }
                    	                });
                	        		}else
        			        			Ext.Msg.show({title:'Warning', msg: 'Select one watermark!', width: 300,
     			        				   buttons: Ext.Msg.OK, icon: Ext.MessageBox.WARNING });
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
                					name:'watermark_filename'
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

/**
 * This function generate detail form crop action. 
 * @param panel
 * @param grid
 * @param selected
 * @param actionsStore
 * @param media_type
 * @param parameters
 * @param name_action
 * @return
 */

function _crop_generate_details_forms(panel, grid, selected, actionsStore, media_type, parameters, name_action)
{
	panel.add(
			{ 
	            layout:'column', 
	            items:[{ 
	                columnWidth:.3,
	                layout : 'form',
	                items: [{
						xtype: 'radiogroup',
						id : 'radio_custom_crop',
						fieldLabel: 'Standard crop',
			            columns: 1,
						items: [
						    {boxLabel: '1:1 Square', name: 'type-crop', value: '1:1', id: '1:1'},
						    {boxLabel: '2:3', name: 'type-crop', value: '2:3', id: '2:3'},
						    {boxLabel: '3:4', name: 'type-crop', value: '3:4', id: '3:4'},
						    {boxLabel: '4:5', name: 'type-crop', value: '4:5', id: '4:5'},
						    {boxLabel: '  Custom', 
  					    	 name: 'type-crop', 
					    	 value: 'custom', 
					    	 id: 'custom'
					    	 }
						],
						listeners : {
	                		change  : function (newValue, oldValue){
	                			if(newValue.getValue().value != 'custom'){
	                				//disable panel_custom_fields
	                				Ext.getCmp('crop_width_custom').setDisabled(true);
	                				Ext.getCmp('crop_height_custom').setDisabled(true);
	                			}else{
	                				//enable panel_custom_fields
	                				Ext.getCmp('crop_width_custom').setDisabled(false);
	                				Ext.getCmp('crop_height_custom').setDisabled(false);
	                			}
	                		},
	                		afterrender : function(){
	                			if (parameters[0]['value'] == '1:1' || parameters[0]['value']== '2:3' || parameters[0]['value']== '3:4' || parameters[0]['value']== '4:5')
	                				this.setValue(parameters[0]['value'], true);
	                			else{
	                				this.setValue('custom', true);
	                				if (parameters[0]['value']){
		                				var str = parameters[0]['value'];
		                				var index = str.indexOf(':');
		                				Ext.getCmp('crop_width_custom').value = str.slice(0,index);
		                				Ext.getCmp('crop_height_custom').value = str.slice(index+1,str.length);
									}
	                			}
	                		}
	                	}
	                }]
	            },{columnWidth:.038,
	            	layout : 'form',
	            	items :[{
        	            xtype     : 'numberfield',
        	            id        : 'crop_width_custom',
        	            hideLabel : true,
        	            height    : 18,
        	            style     :'margin-top:104px',
        	            width     : 20
            		}]
        	      },{columnWidth:.01,
	            	layout : 'form',
	            	style :'margin-top:105px',
	            	items :[{
                            xtype : 'label',
                            text  : ':',
                            width : 3
	            	}]
        	      },{columnWidth:.05,
	            	layout : 'form',
	            	items :[{
	                    xtype     : 'numberfield',
	                    id        : 'crop_height_custom',
	                    hideLabel : true,
	                    height    : 18,
        	            style     :'margin-top:104px',
	                    width     : 20
	                }]
        	      }
	            ]
	        }         
	);

	return panel;
	
}

/**
 * 
 * @param panel
 * @param grid
 * @param selected
 * @param actionsStore
 * @param media_type
 * @param parameters
 * @param name_action
 * @return
 */
function _extract_video_thubnail_generate_details_forms(panel, grid, selected, actionsStore, media_type, parameters, name_action ){
    if (DEBUG_SCRIPT){
		console.log('_extract_video_thubnail_generate_details_forms');
	    console.log(parameters);
    }
	var i = 0;
    var recApp;
    var item_array = new Array();
    recApp = actionsStore.getAt(actionsStore.findExact('name', name_action));
    
    for (i=0;i<parameters.length;i++){

    	if (parameters[i]['name'] == 'max_height'){
    		var max_height = new Ext.form.NumberField({                            
  	          fieldLabel: parameters[i].name.replace("_"," "),
  	          value     : parameters[i].value,
  	          name      : parameters[i].name,
  	          msgTarget :'side',                            
  	          width     : 140
  	      	});    		
    	}else if (parameters[i]['name'] == 'max_width'){
    		var max_width = new Ext.form.NumberField({                            
  	          fieldLabel: parameters[i].name.replace("_"," "),
  	          value     : parameters[i].value,
  	          name      : parameters[i].name,
  	          msgTarget :'side',                            
  	          width     : 140
  	      	});    		
    	}else if (parameters[i]['name'] == 'output_format'){
    		var val;
            //restituisce in ordine inverso devo recuperare l'indice.
            if (parameters[i].name != recApp['data']['parameters'][i].name){
            	var j = 0;
            	while (parameters[i].name != recApp['data']['parameters'][j].name) {
            		  j++;
            	}
            }else j = i;
            
    		if (DEBUG_SCRIPT)
    			console.log(recApp['data']['parameters']);
    		
    		var recAppValues = recApp['data']['parameters'][j]['values'][media_type];
    		if (parameters[i]['value']) 
    			val = parameters[i]['value'];
    		else 
    			val = recApp['data']['parameters'][j]['values'][media_type][0]; 
    		
    		var output_format = new Ext.form.ComboBox({                            
    			fieldLabel   : parameters[i].name.replace("_"," "),
    			store        : recAppValues,
				triggerAction: 'all',
				value        : val,
				name         : parameters[i].name,
				width        : 140
    	    });    		
    	}else if (parameters[i]['name'] == 'mail'){
    		var mail = new Ext.form.TextField({                            
  	          value       : parameters[i].value,
  	          id          : 'mail_radiobutton',
  	          name        : parameters[i].name,
  	          msgTarget   : 'side',  
	            style     :'margin-top:75px',
	            hideLabel : true,
  	          width       : 140                            
  	      	});    		
    	}else if(parameters[i]['name'] == 'output'){

    		var val;
            if (parameters[i].name != recApp['data']['parameters'][i].name){
            	var j = 0;
            	while (parameters[i].name != recApp['data']['parameters'][j].name) {
            		  j++;
            	}
            }else j = i;

            
			dict = recApp['data']['parameters'][j]['values'][media_type];
			recAppValues = [];
			for (key in dict) {
				if (dict.hasOwnProperty(key)) { 
					recAppValues.push(dict[key]);
					val = dict[key];
				}
			}
    		if (parameters[i]['value']) 
    			val = dict[parameters[i]['value']]; 
    		    		
			var output = new Ext.form.ComboBox({                            
    			store        : recAppValues,
    			id           : 'output_radiobutton',
				triggerAction: 'all',
				value        : val,
				name         : parameters[i].name,
	            hideLabel    : true,
				width        : 140
    	    });     		
    	}
    }
    
	panel.add({ 
        layout:'column', 
        items:[{ 
            columnWidth:.4,
            layout : 'form',
            items: [max_height,
                    max_width,
                    output_format,
                    {
						xtype: 'radiogroup',
						id : 'radio_output_extract',
						fieldLabel: 'Output',
			            columns: 1,
						items: [
						    {boxLabel: 'Mail', name: 'type-output', value: 'mail', id: 'mail'},
						    {boxLabel: 'Output', name: 'type-output', value: 'output', id: 'output'}
						],
						listeners : {
	                		change  : function (newValue, oldValue){
	                			if(newValue.getValue().value == 'mail'){
	                				Ext.getCmp('output_radiobutton').setDisabled(true);
	                				Ext.getCmp('mail_radiobutton').setDisabled(false);
	                			}else{
	                				//enable panel_custom_fields
	                				Ext.getCmp('mail_radiobutton').setValue('');
	                				Ext.getCmp('mail_radiobutton').setDisabled(true);
	                				Ext.getCmp('output_radiobutton').setDisabled(false);
	                			}
	                		},
	                		afterrender : function(){
	                			
	                			if (DEBUG_SCRIPT){
	                				console.log('after render');
	                				console.log(Ext.getCmp('mail_radiobutton').getValue());
	                			}
	                			if (Ext.getCmp('mail_radiobutton').getValue() == ''){
	                				this.setValue('output',true);
	                			}else{
	                				this.setValue('mail',true);
	                			}
	                		}
	                	}
                    }
            ]
        },
        { columnWidth:.5,
          layout : 'form',
          items : [
				mail,
				output
          ]
	     }]
	});   

	return panel;
}

/**
 * This function generate detail form. 
 * @param panel
 * @param grid
 * @param selected
 * @param actionsStore
 * @param media_type
 * @return
 */

function generate_details_forms(panel, grid, selected, actionsStore, media_type) {

    var name_action = selected.data.name;
    var parameters = selected.get('parameters');
    var array_field;

    //  remove all component
    panel.removeAll()
    if (DEBUG_SCRIPT){
    	console.log(name_action);
    	console.log(selected);
    }
    //add new component
    if (name_action == 'watermark'){
    	panel = _watermark_generate_details_forms(panel, grid, selected, actionsStore, media_type, parameters, name_action);
    }else if (name_action == 'crop'){
    	panel = _crop_generate_details_forms(panel, grid, selected, actionsStore, media_type, parameters, name_action );
    }else if (name_action == 'extract video thumbnail'){
    	panel = _extract_video_thubnail_generate_details_forms(panel, grid, selected, actionsStore, media_type, parameters, name_action );
    }else{
    	array_field = _global_generate_details_form(grid, selected, actionsStore, media_type, parameters, name_action );
    	panel.add(array_field);
    }
    
    if (DEBUG_SCRIPT){
    	console.log('generate_details_forms finished');
    }   
//reload panel
	panel.doLayout();
}

/**
 * This method create a new record because the copy() not work, but make a move. 
 * @param data data to insert in new record
 * @param media_type type of tabPanel ('image', 'movie')
 * @return
 */

function newRecord(data){
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

/**
 * This function pull data from form and memorize data.
 * @param sm selection row of data grid
 * @param media_type type of media ('image', 'movie'...)
 * @return
 */
function _pull_data(sm, actionsStore){

//	var i,j;
//	if (DEBUG_SCRIPT){
//		console.log('pull_data init');
//		console.log(sm.getSelected());
//	}
//	
//	if 	(sm.getSelected()){
//		var newParams = [];
//		var appParams = {};
//		var r = sm.getSelected();
//		
//		var params = r.get('parameters');		
//		
//		for (i=0;i<params.length;i++){
//    		appParams = params[i];
//    		if (DEBUG_SCRIPT)
//    			console.log(appParams.name);
//    		if (appParams.name == 'ratio'){
//    			appParams = {};
//    			appParams['name']  = 'ratio';
//    			appParams['type']  = 'string';
//    			appParams['value'] = Ext.getCmp('detailAction_'+media_type).getForm().getFieldValues()['radio_custom_crop'].value;
//    			if (appParams['value'] == 'custom'){
//    				var w = Ext.getCmp('crop_width_custom').getValue();
//    				var h = Ext.getCmp('crop_height_custom').getValue();
//    				appParams['value'] = w+':'+h;
//    			}
//    		}else if (appParams.name == 'output'){
//    			//recuperare dizionario
//    			
//    			dict = Ext.getCmp('action_list_'+media_type).getStore().getAt(actionsStore.findExact('name', 'save'))
//    			for (key in dict['data']['parameters'][2]['values'][media_type]) {
//    				if (dict['data']['parameters'][2]['values'][media_type].hasOwnProperty(key)) {
//    					if (dict['data']['parameters'][2]['values'][media_type][key] == Ext.getCmp('detailAction_'+media_type).getForm().getFieldValues()[appParams.name]){
//    						appParams['value'] = key;
//    					}
//    				}
//    			}
//    		}else{
//    			appParams['value'] = Ext.getCmp('detailAction_'+media_type).getForm().getFieldValues()[appParams.name];
//    		}
//    		newParams.push(appParams);
//    	}
//		if (DEBUG_SCRIPT){
//			console.log("_pull_data finished");
//			console.log(newParams);
//		}
//	    r.set('parameters',newParams);
//	    r.commit();
//	}else{
////		console.log('else sm.getSelected()');
//	}
}

/**
 * 
 * @param obj
 * @param media_type
 * @return
 */
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
								        _pull_data(sm,Ext.getCmp('action_list').getStore());
							        	return true;
									}, 
									selectionchange : function(){
							        	//show form details
										if (this.getSelected()){
								        	generate_details_forms(Ext.getCmp('detailAction_'+media_type),this.grid, this.getSelected(), Ext.getCmp('action_list_'+media_type).getStore(), media_type);
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

/**
 * 
 * @return
 */
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
			beforetabchange : function(panel, newTab, currentTab) {
				if (currentTab){
					
					if (DEBUG_SCRIPT){
						console.log('beforetabchange');
						console.log(Ext.getCmp('my_action_'+currentTab.id.slice(4)));
						console.log(currentTab.id.slice(4));
					}						
					
					var type = currentTab.id.slice(4);

					_pull_data(Ext.getCmp('my_action_'+type).getSelectionModel(), type, Ext.getCmp('action_list_'+type).getStore());
					Ext.getCmp('detailAction_'+type).removeAll();
					Ext.getCmp('my_action_'+type).getSelectionModel().clearSelections();
				}
	    	}
	    } 	    
	    	

	});
	return [tabs]
}

/**
 * 
 * @param name
 * @param description
 * @return
 */
function _get_scripts_fields(name, description){
	
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

/**
 * 
 * @param name
 * @param description
 * @param my_win
 * @return
 */
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
	if (DEBUG_SCRIPT){
		console.log('pipeline');
		console.log(pipeline);
	}
	return pipeline;
	
}

/**
 * 
 * @return
 */
function reload_main_data_view(){
	var tab = Ext.getCmp('media_tabs').getActiveTab();
    var view = tab.getComponent(0);
    var store = view.getStore();
    store.reload();
}

/**
 * 
 * @param create
 * @param name
 * @param description
 * @param id_script
 * @param is_global
 * @param run
 * @return
 */
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
    			_pull_data(Ext.getCmp('my_action_'+type).getSelectionModel(), type, Ext.getCmp('action_list_'+type).getStore());
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
//		                        	if (is_global){
//		    		        			Ext.Msg.show({
//		    		        				   title:'Option.',
//		    		        				   msg: 'This global script is saved, do you want to run on all objects in the workspace?',
//		    		        				   width: 300,
//		    		        				   buttons: Ext.Msg.YESNO,
//		    		        				   fn: function(btn){
//				    		        			    if (btn == 'yes'){
//				    		        			    	//run script
//				    		        			    	Ext.Ajax.request({
//				                					        url: '/run_script/',
//				                			                params: {
//				    		        			    			script_id : id_script,
//				                								run_again : true
//				                							},
//				                					        success: function(data){
//				                								reload_main_data_view();
//				                					        }
//				                						});
//				    		        			    }
//		    		        					},
//		    		        				   animEl: 'elId',
//		    		        				   icon: Ext.MessageBox.QUESTION
//		    		        				});	
//		    		        		}else
        	                        	Ext.Msg.show({title:'Success', msg: 'Script saved.', width: 300,
					        				   buttons: Ext.Msg.OK, icon: Ext.MessageBox.INFO });
		                        		my_win.close();
		                        }else
    			        			Ext.Msg.show({title:'Warning', msg: Ext.decode(response.responseText), width: 300,
  			        				   buttons: Ext.Msg.OK, icon: Ext.MessageBox.WARNING });
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

/**
 * 
 * @param data
 * @param type
 * @return
 */
function newRecordLoad(data,type){
	var cloned_parameters = [];
	var tmp = {};
	//for get list of actions
	for (name in data.parameters) {
		tmp = {};
		tmp['name']  = name;
		if (!isNaN(data.parameters[name])){
			if (name == 'embed_xmp')
				tmp['type']  = 'boolean';
			else
				tmp['type']  = 'number';
		}else
			tmp['type']  = 'string';

		if (data.parameters[name])
			tmp['value'] = data.parameters[name];
			//get list of values if exist
		else
			tmp['value'] = "";

		cloned_parameters.push(tmp);
	}
	


	return new ActionRecord({name: data.type, parameters: cloned_parameters});

}

/**
 * 
 * @param data
 * @return
 */
function load_data_script(data){

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

/**
 * Show windows form scripts data
 * @param id_script
 * @param name
 * @param description
 * @param flag
 * @param pipeline
 * @param main_win
 * @param run
 * @return
 */

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
	                        	Ext.Msg.show({title:'Success', msg: 'Changes saved!', width: 300,
			        				   buttons: Ext.Msg.OK, icon: Ext.MessageBox.INFO });
	                        	my_win.close();
	    		        		main_win.get('open_form').get('my_scripts').getStore().reload();
		                    },
		        			failure: function(form, action) {
			        			Ext.Msg.show({title:'Warning', msg: Ext.decode(action.response.responseText), width: 300,
			        				   buttons: Ext.Msg.OK, icon: Ext.MessageBox.WARNING });
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
			        			Ext.Msg.show({title:'Warning', msg: 'Script NOT saved, please insert Name.', width: 300,
			        				   buttons: Ext.Msg.OK, icon: Ext.MessageBox.WARNING });
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

/**
 * 
 * @return
 */
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
		    		if (DEBUG_SCRIPT) 
		    			console.log('Open');
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

/**
 * 
 * @return
 */
function _save_association()
{
	var i;
	var scripts_id = [];
	
	if (DEBUG_SCRIPT){
		console.log('save_association');
		console.log('event');
		console.log(Ext.getCmp('id_combo_events').getValue());
		console.log(Ext.getCmp('id_combo_events').getStore().getAt(Ext.getCmp('id_combo_events').getStore().findExact('name',event)));
	}
	event = Ext.getCmp('id_combo_events').getValue();
	
	scripts = Ext.getCmp('grid_panel_scripts').getSelectionModel().getSelections();
	if (event){
		for(i=0;i<scripts.length;i++){
			scripts_id.push(scripts[i].data.id);
		}
		Ext.Ajax.request({
	        url: '/set_script_associations/',
	        params:{ 
				event_id  : Ext.getCmp('id_combo_events').getStore().getAt(Ext.getCmp('id_combo_events').getStore().findExact('name',event)).data.id,
				script_id : scripts_id
			},
	        success: function(response) {
	            if (Ext.decode(response.responseText)['success']){
	    			Ext.Msg.show({title:'Success', msg: 'Association saved.', width: 300,
	    				   buttons: Ext.Msg.OK, icon: Ext.MessageBox.INFO });
	            }else
	    			Ext.Msg.show({title:'Warning', msg: 'Association NOT saved.', width: 300,
	    				   buttons: Ext.Msg.OK, icon: Ext.MessageBox.WARNING });
	        }
	    });
	}else
		Ext.Msg.show({title:'Warning', msg: 'Selected one event.', width: 300,
			   buttons: Ext.Msg.OK, icon: Ext.MessageBox.WARNING });
}

/**
 * 
 * @return
 */
function manage_events(){

	var sm = new Ext.grid.CheckboxSelectionModel();
	var flag = false;
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
				    items  :[new Ext.form.Label({
				    			text : "Select event :   "
				    		}),
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
//							    valueField   : 'id',
							    listeners    : {
						        	select : function(combo, record, index){
//				            			console.log(combo.getStore());
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
		        bbar:[{
		            text:'Save change',
		            tooltip:'Save change for this action',
		            handler: function(){
		        		_save_association();
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
	   }]          
    });
 
	manage_events_win.show();
}



function edit_script(is_new){
//	var cols = [
//		{ id : 'name',  header: "Action", dataIndex: 'name'}
//	];
//	var my_action = new Ext.grid.GridPanel({
//	    region           : 'west',
//        title            : 'Your script action',
//        id               : 'my_action' ,
//		width            : 300,
//		border		     : false,
//	    store            : new Ext.data.JsonStore({
//	    					fields:['name', 'parameters'],
//	    					root: 'actions'
//	    					}),
//	    columns          :cols,
//	    stripeRows       : true,
//	    autoExpandColumn : 'name',
//		frame            : true,
//        hideHeaders      : true,
//		sm               : new Ext.grid.RowSelectionModel({
//								singleSelect : true,
//								listeners    :{
//									 
//									selectionchange : function(){
//										var record = this.getSelected();
//										var details_form = Ext.getCmp('detailAction');
//										details_form.removeAll();
//										
//										Ext.each(record.data.parameters, function(param){
//											//console.log(param);
//											if (param.type == 'int')
//												details_form.add(new Ext.form.NumberField({
//												fieldLabel: param.name
//													
//													
//												}))
//											
//										});
//										details_form.doLayout();
//								        
//									}			
//								}
//							})
//
//	});
//
//	var action_list = new Ext.grid.GridPanel({
//	    region           : 'east',
//        title            : 'Available action',
//        id               : 'action_list',
//		width            : 300,	
//		border		     : false,
//	    store            : new Ext.data.JsonStore({
//	    					fields:['name', 'parameters'],
//	    					url: '/get_actions/',
//	    					autoLoad: true,
//	    					root: 'actions'
//	    					}),
//	    columns          : cols,
//	    stripeRows       : true,
//	    autoExpandColumn : 'name',
//		frame            : true,
//        hideHeaders      : true,
//		sm               : new Ext.grid.RowSelectionModel({singleSelect : true})
//    });
//
//	var detail_action = new Ext.FormPanel({
//        title       : 'Details',
//        id          : 'detailAction',
//	    region      : 'south',
//	    height      : 180,
//	    frame       : true,
//	    border		: false
//	});
//
//	var button_panel =new Ext.Panel({
//        region  : 'center',
//        border: false,
//        id      : 'buttons_panel', 
//        html    : '<div style="text-align:center; padding-top:80;"><img style="margin:2px" src="/files/images/up2.gif" onclick="Ext.getCmp(\'buttons_panel\').move_to_up()" /><br/><img style="margin:2px" src="/files/images/down2.gif" onclick="Ext.getCmp(\'buttons_panel\').move_to_down()"/><img style="margin:2px" src="/files/images/left2.gif" onclick="Ext.getCmp(\'buttons_panel\').move_to_left()" /><br/><img style="margin:2px" src="/files/images/right2.gif" onclick="Ext.getCmp(\'buttons_panel\').move_to_right()"/> </div>',
//        
//	    move_to_up:function(){
//	        var grid = Ext.getCmp('my_action');
//	        var record_selected = grid.getSelectionModel().getSelected();
//	        if(record_selected){
//	            var rank = grid.getStore().indexOf(record_selected);
//	            if (rank > 0){
//	                grid.getStore().remove(record_selected);
//	                grid.getStore().insert(rank - 1, record_selected);
//	                grid.getSelectionModel().selectRecords([record_selected]);
//	            }
//	        }
//	            
//	    },   
//
//	    move_to_down: function(){
//	        var grid = Ext.getCmp('my_action');
//	        var record_selected = grid.getSelectionModel().getSelected();
//	        if(record_selected ){
//	            var rank = grid.getStore().indexOf(record_selected);
//	            if (rank < grid.getStore().getCount() - 1){
//	                grid.getStore().remove(record_selected);
//	                grid.getStore().insert(rank +1, record_selected);
//	                grid.getSelectionModel().selectRecords([record_selected]);
//	            }
//	        }
//	        
//	    },
//
//        move_to_left: function (){
//	        var selected_grid = Ext.getCmp('action_list');
//	        var available_grid = Ext.getCmp('my_action');
//	        if (selected_grid.getSelectionModel().hasSelection()){
//	        	//define parameters through form
//	        	var selected  = selected_grid.getSelectionModel().getSelected();
//	        	//why copy() not work
//	        	
//	        	available_grid.getStore().loadData({actions:[{name: selected.data.name, parameters: selected.data.parameters}]}, true);
//	        	available_grid.getSelectionModel().selectLastRow();
//	        }else{
//				// Show a dialog using config options:
//				Ext.Msg.show({
//				   title:'Warning',
//				   msg: 'You must select one row!',
//				   width: 300,
//				   buttons: Ext.Msg.OK,
//				   icon: Ext.MessageBox.WARNING
//				});	        				
//			}
//	     },  
//
//	    move_to_right: function(){
//	        var selected_grid = Ext.getCmp('my_action');
//	        var available_grid = Ext.getCmp('action_list');
//	        if (selected_grid.getSelectionModel().hasSelection()){
//	        	var selected  = selected_grid.getSelectionModel().getSelected();
//	        	selected_grid.getStore().remove(selected);
//	        	Ext.getCmp('detailAction_'+media_type).removeAll();
//	        }
//	     }
//        
//    }); 	
//
//	var script_form = new Ext.form.FormPanel({
//		frame:true,		
//		region: 'north',
//		border: false,
//		height:40,
//		items:[
//			new Ext.form.TextField({
//				id:'script_name',
//				name: 'name',
//				fieldLabel: 'Name',
//				allowBlank: false,
//				width: 200
//			})
//		]
//	});
	
	
	var actions_store, win;
	
	function create_window(available_actions){
		var menu_actions = [];
		Ext.each(available_actions, function(action_name){
			menu_actions.push({
				text: action_name,
				handler: function(){}
				
			});
			
		});
//		console.log(available_actions);
//		console.log(menu_actions);
//		
		return new Ext.Window({
	        id:'edit_script',        
	        title       : 'Edit Script',
	        layout      : 'fit',
		    width       : 650,
		    height      : 570,
	        modal: true,
	        resizable : false,
	        border: false,
	        items:[
	        	
	        	new Ext.Panel({
	        		
	        		
	        		layout: 'border',
	        		items: [
	        			new Ext.form.FormPanel({
	        				region: 'north',
	        				height: 100,
					        bodyStyle:'padding:5px 5px 0',
	        				defaults: {width:400},
	        				border: false,
	        				 
	        				 
	        				items:[
	        					new Ext.form.TextField({
	        						fieldLabel: 'Name',
	        						name: 'name'
	        					}),
	        					new Ext.form.TextArea({
	        						fieldLabel: 'Description',
	        						name: 'description'
	        					})
	        				]
	        			}),
		        		new Ext.Panel({
			        		region: 'center',
			        		height: 400,
			        		title: 'Actions',
	//		        		border: false,
			        		tbar:[{
			        				text: 'Add',
			        				menu: menu_actions
			        			},
			        			
			        			{
			        				text: 'Remove'
			        			}
			        		],
			        		items:	new Ext.list.ListView({
			        			
			        			hideHeaders: true,
			        			store: new Ext.data.JsonStore({
			        				root: 'actions',
			        				fields: ['name'],
			        				url: '/get_pipeline/'
			        				
			        			}),
			        			columns:[{
			        				dataIndex: 'name',
			        				header: 'Actions'
			        			}
			        			]
			        			
			        		})
		        			
		        		})
		        			        		
	        		]
	        	
	        	})
	        ],
	        buttons:[
	        	{
	        		text: 'Save'
	        	},
	        	{
	        		text: 'Cancel'
	        	}
	        ]
	        
		});
	
	};
	
	
	actions_store = new Ext.data.JsonStore({
		url: '/get_available_actions/',
		root: 'actions',
		fields: ['name', 'params'],
		listeners: {
			load: function(store, actions){
				var available_actions = [];
				console.log(actions);
				Ext.each(actions, function(action){
					available_actions.push(action.data.name);
					
				
				});
				console.log(available_actions);
				win = create_window(available_actions);
				win.show();
			
			},
			exception: function(){
				win = create_window([]);
				win.show()
			
			}
		}
	
	});
	actions_store.load();	
	
	
	
}

function show_items (process_id, type){
	var query = String.format('process:{0}:{1}',process_id, type)
	var media_tab = Ext.getCmp('media_tabs').getActiveTab();
	 media_tab.getSearch().setValue(query);
	set_query_on_store({query: query});

};

function show_monitor(){
		var win_id = 'script_monitor';
		if (Ext.WindowMgr.get(win_id))
			return;
			
		 var expander = new Ext.ux.grid.RowExpander({
	        tpl : new Ext.Template(
	            '<p>Launched By: <b>{launched_by}</b></p>',
	            '<p>Total Items: <a href="javascript:show_items(\'{id}\', \'total\')"><b>{total_items}</b></a></p>',
	            '<p>Items Completed: <a href="javascript:show_items(\'{id}\', \'completed\')"><b>{items_completed}</b></a></p>',
	            '<p>Items Failed: <a href="javascript:show_items(\'{id}\', \'failed\')"><b>{items_failed}</b></a></p>'
	        )
	    });
		var win = new Ext.Window({
			id: win_id,
			title: 'Script Monitor',
			height: 500,
			width: 800,
			layout: 'fit',
			collapsible: true,			
			
			update_progress: function(){
				var store = Ext.getCmp('script_monitor_list').getStore();
				var script_in_progress = store.queryBy(function(r){
					return (r.data.progress < 100)
				}).items;
				if (script_in_progress.length > 0){				
					
					return true;
				}
				else
					return false;
			
			},
			
			items:[
				
			
				new Ext.grid.GridPanel({
					autoScroll: true,
					id: 'script_monitor_list',
					plugins: expander,
					store: new Ext.data.JsonStore({
					    	url: '/script_monitor/',				    	
					    	fields:[
					    		'id',
					    		'name',
					    		'time_elapsed',
					    	
					    		'progress',
					    		'type',
					    		'total_items',
					    		'items_completed',
					    		'items_failed',
					    		'start_date',
					    		'end_date',
					    		'launched_by'
					    	],
					    	root: 'scripts'
					    }),		
					    viewConfig: {
    						forceFit: true
    					},
    					
					    columns: [
					    	expander,
					    {
					        header: 'Name',											       
					        dataIndex: 'name',
					        width: 250,
					        sortable: true,
					        menuDisabled: true
					    },
					    
					    {
					        header: 'Type',											        
					        dataIndex: 'type',
					        menuDisabled: true
					        
					    },
					    
//					    {
//					        header: 'Launched By',											        
//					        dataIndex: 'launched_by'												        
//					    },
					    {
					        header: 'Start Date',											        
					        dataIndex: 'start_date',
					        type: 'date',
					        sortable: true,
					        menuDisabled: true
					        
					    },
					    
					    {
					        header: 'End Date',											        
					        dataIndex: 'end_date',
					        type: 'date',
					        sortable: true,
					        menuDisabled: true
					        
					    },
					    
					    
					    new Ext.ux.grid.ProgressColumn({
						    header : "Progress",
						    dataIndex : 'progress',
						    width : 120,
					        menuDisabled: true,
						    renderer : function(v, p, record) {
							    var style = '';
							    var textClass = (v < 55) ? 'x-progress-text-back' : 'x-progress-text-front' + (Ext.isIE6 ? '-ie6' : '');
							
							    //ugly hack to deal with IE6 issue
							    var failures;
							    if (record.data.items_failed > 0)
							    	failures = String.format('({0} items failed)', record.data.items_failed);
							    else
							    	failures = '';
							    var text = String.format('</div><div class="x-progress-text {0}" style="width:100%;" id="{1}">{2}</div></div>',
							      textClass, Ext.id(), v + this.textPst + failures
							    );
							    text = (v<96) ? text.substring(0, text.length - 6) : text.substr(6);
							
							    if (this.colored == true) {
							      if (v <= 100 && v > 66)
							        style = '-green';
							      if (v < 67 && v > 33)
							        style = '-orange';
							      if (v < 34)
							        style = '-red';
							    }
							
							    p.css += ' x-grid3-progresscol';
							    return String.format(
							      '<div class="x-progress-wrap"><div class="x-progress-inner"><div class="x-progress-bar{0}" style="width:{1}%;">{2}</div>' +
							      '</div>', style, v, text
							    );
							  }
//						    textPst : '%', // string added to the end of the cell value (defaults to '%')
//						    actionEvent: 'click', // click event (defaults to 'dblclick')
//						    colored : true, // True for pretty colors, false for just blue (defaults to false)
//						    editor : new Ext.form.TextField() // Define an editor if you want to edit
						  })

					   
					    ]
				
				})
			]
			
			
		
		});
		
		win.show();
		Ext.getCmp('script_monitor_list').getStore().load();
		
		
};
