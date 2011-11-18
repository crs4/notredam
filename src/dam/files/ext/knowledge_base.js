/**
 * All Store
 */		

function init_store_class_data(id_class, add_class){
	//var ws_record = ws_store.getAt(ws_store.findBy(find_current_ws_record));
	var class_store = new Ext.data.JsonStore({
	    url: '/kb/get_specific_info_class/'+id_class+'/',
	    id:'class_store',
	    root: 'rows',
	    fields:['workspaces','name','notes','superclass','attributes','id'],
        listeners:{
			load: function() {
				load_detail_class(this, id_class, add_class);
			}
		}
	});
	class_store.load();
}

function store_get_class_attributes(id_class){
	//var ws_record = ws_store.getAt(ws_store.findBy(find_current_ws_record));
	return new Ext.data.JsonStore({
	    url: '/kb/get_class_attributes/'+id_class+'/',
	    autoLoad:true,
	    root: 'rows',
	    fields:['id','name','type','maybe_empty','default_value','order','notes','min','max','length','choices', 'multivalued', 'target_class']
	});
}

function init_store_obj_data_edit(obj_id, add_obj){
	//var ws_record = ws_store.getAt(ws_store.findBy(find_current_ws_record));
	var obj_store = new Ext.data.JsonStore({
	    url: '/kb/get_specific_info_obj/'+obj_id+'/',
	    id:'obj_store',
	    root: 'rows',
	    fields:['id','name','class_id','notes','attributes'],
        listeners:{
			load: function() {
				console.log('LOADDDD obj');
				load_detail_obj(this, obj_id, add_obj);
			}
		}
	});
	obj_store.load();
}

function store_get_obj_attributes(class_id, obj_id){
	//obj_id == null new obj else edit exixting obj 
	//var ws_record = ws_store.getAt(ws_store.findBy(find_current_ws_record));
	return new Ext.data.JsonStore({
	    url: '/kb/get_obj_attributes/',
	    autoLoad:true,
	    baseParams:{
			class_id: class_id,
			obj_id : obj_id
		},
	    root: 'rows',
	    fields:['id','name','type','multivalued','maybe_empty','default_value','order','notes', 'value']
	});	
}

var ws_admin_store = new Ext.data.JsonStore({
    url: '/get_admin_workspaces/',
    id:'ws_admin_store',
    autoLoad:true,
    root: 'workspaces',
    fields:['pk','name','description']
});

/*function remove_option(value,attribute_detail_panel){
	console.log('remove option');
	if (value == 'int'){
		attribute_detail_panel.remove(Ext.getCmp('id_min'));
		attribute_detail_panel.remove(Ext.getCmp('id_max'));
		attribute_detail_panel.remove(Ext.getCmp('id_default_value'));
		console.log('Integer Remove');
	}else if (value == 'date'){
		attribute_detail_panel.remove(Ext.getCmp('id_min'));
		attribute_detail_panel.remove(Ext.getCmp('id_max'));
		attribute_detail_panel.remove(Ext.getCmp('id_default_value'));
		console.log('remove date');
	}else if (value == 'string' || value == 'uri'){
		attribute_detail_panel.remove(Ext.getCmp('id_max_length'));
		console.log('remove Stringa o uri');
	}else if (value == 'objref'){
		console.log('OBJREF');
	}
	attribute_detail_panel.doLayout();
}
*/
function add_option(value, attribute_detail_panel, data){
	//initializing
	attribute_detail_panel.removeAll();
	var min_number_value = null;
	var max_number_value = null;
	var default_v = null;
	var min_date_value = null;
	var max_date_value = null;
	var max_length_value = null;
	
	if (value == 'int'){
		console.log('Integer');
		if (data){
			min_number_value = data.min;
			max_number_value = data.max;
			default_v = data.default_value;
		}
		var min_number = new Ext.form.NumberField({
			name: 'min_number',
			id  : 'id_min',
			fieldLabel: 'Min value',
			value: min_number_value,
	        allowBlank:true
		});
		var max_number = new Ext.form.NumberField({
			name: 'max_number',
			id  : 'id_max',
			fieldLabel: 'Max value',
			value: max_number_value,
	        allowBlank:true
		});
		var default_value = new Ext.form.NumberField({
			name: 'default_value',
			id  : 'id_default_value',
			fieldLabel: 'Default value',
			value: default_v,
	        allowBlank:true
		});
		attribute_detail_panel.add(min_number);
		attribute_detail_panel.add(max_number);
		attribute_detail_panel.add(default_value);
	}else if (value == 'date'){
		console.log('Date');
		if (data){
			min_date_value = data.min;
			max_date_value = data.max;
			default_v = data.default_value;
		}
		var min_date = new Ext.form.DateField({
			name: 'min_date',
			id  : 'id_min',
			fieldLabel: 'Min date',
			value: min_date_value,
	        allowBlank:true
		});
		var max_date = new Ext.form.DateField({
			name: 'max_date',
			id  : 'id_max',
			fieldLabel: 'Max date',
			value: max_date_value,
	        allowBlank:true
		});
		var default_value = new Ext.form.DateField({
			name: 'default_value',
			id  : 'id_default_value',
			fieldLabel: 'Default value',
			value: default_v,
	        allowBlank:true
		});
		attribute_detail_panel.add(min_date);
		attribute_detail_panel.add(max_date);
		attribute_detail_panel.add(default_value);
	}else if (value == 'string' || value == 'uri'){
		console.log('Stringa o uri');
		if (data){
			max_length_value = data.length;
		}
		var max_length = new Ext.form.NumberField({
			name: 'max_length',
			id  : 'id_max_length',
			fieldLabel: 'Max length',
			value: max_length_value,
	        allowBlank:true
		});
		attribute_detail_panel.add(max_length);
	}else if (value == 'objref'){
		console.log('OBJREF');
	}else if(value == 'bool'){
		if (data){
			default_v = data.default_value;
		}
		var default_value = new Ext.form.ComboBox({
			name: 'default_value',
			id  : 'id_default_value',
	        store: 
	            new Ext.data.SimpleStore({
	              fields: ['id','name'],
	              data: [
	                ["true","True"],["false","false"]]
	          }), // end of Ext.data.SimpleStore
	        fieldLabel: 'Type',
	        hiddenName: 'type',
	        width: 130,
	        emptyText: 'Select ...',
	        displayField: 'name',
	        valueField: 'id',
	        mode: 'local',
	        editable: false,
			value: default_v,
			fieldLabel: 'Default value',
	        allowBlank:true
		});
		attribute_detail_panel.add(default_value);
	}else if(value == 'choice'){
		if (data){
			choices_value = data.choices;
			default_v = data.default_value;
		}
		var choices = new Ext.form.TextField({
			name: 'choices',
			id  : 'id_choices',
			fieldLabel: 'Choices',
			value: choices_value,
	        allowBlank:false
		});
		var default_value = new Ext.form.TextField({
			name: 'default_value',
			id  : 'id_default_value',
			fieldLabel: 'Default value',
			value: default_v,
	        allowBlank:true
		});
		attribute_detail_panel.add(choices);
		attribute_detail_panel.add(default_value);
	}
	attribute_detail_panel.doLayout();
}


function add_single_attribute(edit, attributes_grid){
	console.log('add_single_attribute');
	//console.log(edit);
	//console.log(attributes_grid);
	
	if (edit){
//		console.log('edit: load value  --  attributegrid.data');
//		console.log(attributes_grid.getSelectionModel().getSelected());
		name_textField_value = attributes_grid.getSelectionModel().getSelected().data.name;
		empty_chekbox_value = attributes_grid.getSelectionModel().getSelected().data.maybe_empty;
		multivalued_chekbox_value = attributes_grid.getSelectionModel().getSelected().data.multivalued;
		notes_textField_value = attributes_grid.getSelectionModel().getSelected().data.notes
		title = "Edit attribute";
		text_button = gettext('Edit');
	}else{
//		console.log('add: unload value');
		name_textField_value = 'Flanders asd asd';
		empty_chekbox_value = false;
		multivalued_chekbox_value = false;
		notes_textField_value = null;
		title = "Add new attribute";
		text_button = gettext('Add');
	}
	var name_textField = new Ext.form.TextField({
        fieldLabel: 'Name',
        allowBlank:false,
        name: 'name',
        value: name_textField_value, 
        id:'name_attribute'
    });
	// create the combo instance
	var type_combo = new Ext.form.ComboBox({
        id: 'type_comb_class',
        store: 
            new Ext.data.SimpleStore({
              fields: ['id','name'],
              data: [
                ["bool","Boolean"],["int","Integer"],["string","String"],["date","Date"],["uri","Url"],["choice","Choice"],["objref","Object References"]]
          }), // end of Ext.data.SimpleStore
        fieldLabel: 'Type',
        hiddenName: 'type',
        width: 130,
        emptyText: 'Select a type...',
        displayField: 'name',
        valueField: 'id',
        mode: 'local',
        editable: false,
        triggerAction: 'all',
        listeners:{ 
			select:{ fn:function(combo, ewVal, oldVal){
				add_option(ewVal.data.id, Ext.getCmp('id_option_attribute_panel'), null);
			}},
			render:{fn:function(combo){
				if (edit){
					combo.setValue(attributes_grid.getSelectionModel().getSelected().data.type);
					add_option(attributes_grid.getSelectionModel().getSelected().data.type, Ext.getCmp('id_option_attribute_panel'), attributes_grid.getSelectionModel().getSelected().data);
				}
			}}
      	}        
	});	
	var empty_chekbox = new Ext.form.Checkbox({
        id: 'id_empty_chekbox',
        allowBlank:false,
        fieldLabel: 'Empty value',
        checked:empty_chekbox_value, 
        name: 'empty_checkbox'
    });
	var multivalued_chekbox = new Ext.form.Checkbox({
        id: 'id_multivalued_chekbox',
        allowBlank:false,
        fieldLabel: 'Multivalued',
        checked:multivalued_chekbox_value, 
        name: 'multivalued_chekbox'
    });
	var notes_textField = new Ext.form.TextArea({
        fieldLabel: 'Notes',
        allowBlank:true,
        name: 'notes',
        value: notes_textField_value, 
        id:'id_notes_attribute'
    });

	var attribute_detail_panel = new Ext.FormPanel({
        id:'attribute_detail_panel',
        labelWidth: 80, // label settings here cascade unless overridden
        frame:true,
        bodyStyle:'padding:5px 5px 0', 
//        items: fields,
        items: [{
        	layout:'column',
        	items:[{
        		columnWidth:.5,
                layout: 'form',
                items: [name_textField, type_combo]
        	},{
        		columnWidth:.5,
                layout: 'form',
                items: [empty_chekbox, multivalued_chekbox, notes_textField]
        	}]
        },{
        	xtype: 'spacer'
        },{
        	xtype:'panel',
        	id:'id_option_attribute_panel', 
        	layout:'form'
        }
        ],
        buttons: [{
            text: text_button,
            type: 'submit',
            handler: function(){
        		console.log('submit');
        		var Attribute = Ext.data.Record.create([{
        		    name: 'id'
        		},{
        		    name: 'name'
        		},{
        		    name: 'default_value'
        		},{
        		    name: 'order'
        		},{
        		    name: 'notes'
        		},{
        		    name: 'type'
        		},{
        		    name: 'multivalued'
        		},{
        		    name: 'maybe_empty'
        		},{
        		    name: 'min'
        		},{
        		    name: 'max'
        		},{
        		    name: 'length'
        		},{
        		    name: 'choices'
        		}]);
        		if (Ext.getCmp('id_default_value')){default_value = Ext.getCmp('id_default_value').getValue()}else{default_value = null}
        		console.log('default_value: '+default_value);
        		if (Ext.getCmp('id_min')){min_value = Ext.getCmp('id_min').getValue()}else{min_value = null}
        		if (Ext.getCmp('id_max')){max_value = Ext.getCmp('id_max').getValue()}else{max_value = null}
        		if (Ext.getCmp('id_max_length')){max_length = Ext.getCmp('id_max_length').getValue()}else{max_length = null}
        		if (this.text == gettext('Edit')){
        			attributes_grid.getSelectionModel().getSelected().set('id',name_textField.getValue().replace(/ /g, "_"));
        			attributes_grid.getSelectionModel().getSelected().set('name',name_textField.getValue());
        			attributes_grid.getSelectionModel().getSelected().set('default_value',default_value);
        			attributes_grid.getSelectionModel().getSelected().set('order','0');
        			attributes_grid.getSelectionModel().getSelected().set('notes',notes_textField.getValue());
        			attributes_grid.getSelectionModel().getSelected().set('type',type_combo.getValue());
        			attributes_grid.getSelectionModel().getSelected().set('multivalued',multivalued_chekbox.getValue());
        			attributes_grid.getSelectionModel().getSelected().set('maybe_empty',empty_chekbox.getValue());
        			attributes_grid.getSelectionModel().getSelected().set('min',min_value);
        			attributes_grid.getSelectionModel().getSelected().set('max',max_value);
        			attributes_grid.getSelectionModel().getSelected().set('length',max_length);
        		}else{
	        		attributes_grid.store.add(new Attribute({
	        			id			: name_textField.getValue().replace(/ /g, "_"),
	        			name		: name_textField.getValue(),
	        			default_value: default_value,
	        			order		: '0',
	        			notes		: notes_textField.getValue(),
	        			type		: type_combo.getValue(),
	        			multivalued : multivalued_chekbox.getValue(),
	        			maybe_empty : empty_chekbox.getValue(),
	        			min			: min_value,
	        			max			: max_value,
	        			length		: max_length
	        			
	        		}));
        		}
        		win_att_class.close();
            }
        },{
            text: gettext('Cancel'),
            handler: function(){
            	//clear form
        		win_att_class.close();
            }
        }]
    });

    var win_att_class = new Ext.Window({
        id		:'id_win_add_attribute',
		layout	: 'fit',
		defaults: {               // defaults are applied to items, not the container
		    autoScroll:true
		},
        width	: 500,
        height	: 250,
        title	: title,
        modal	: true,
      	items	:[attribute_detail_panel]
    });
    win_att_class.show();  
    
}
/**
 * Detail Class Panel
 */	
		
function load_detail_class(class_data, id_class, add_class){
	// class_data store
	//id_class id class
	// add_class true if add new class false otherwise
	var fields = [];
	if (!add_class){
		var id_textField_value = class_data.getAt(0).data.id;
		var name_textField_value = class_data.getAt(0).data.name;
		var can_catalog_chekbox_value = true;
		var notes_textField_value = class_data.getAt(0).data.notes;
		var title = "Edit class " + name_textField_value;
		var store_attributes_grid = store_get_class_attributes(id_class);
		var url_submit = '/api/workspace/'+ws_store.getAt(ws_store.findBy(find_current_ws_record)).data.pk+'/kb/class/'+id_class;
		var superclass_value = class_data.getAt(0).data.superclass;
	}else{
		var id_textField_value = null;
		var name_textField_value = null;
		var can_catalog_chekbox_value = false;
		var notes_textField_value = null;
		var title = "Add new class";
		var store_attributes_grid = [];
		var url_submit = '/api/workspace/'+ws_store.getAt(ws_store.findBy(find_current_ws_record)).data.pk+'/kb/class/'; 
		var superclass_value = Ext.getCmp('obj_reference_tree').getSelectionModel().selNode.attributes.id;
	}
	
	var id_textField = new Ext.form.TextField({
        fieldLabel: 'Identification',
        allowBlank:true,
        name: 'id',
        value: id_textField_value, 
        id:'id_class'
    });
	fields.push(id_textField);
	
	var name_textField = new Ext.form.TextField({
        fieldLabel: 'Name',
        allowBlank:false,
        name: 'name',
        value:name_textField_value, 
        id:'name_class'
    });
	fields.push(name_textField);
	var superclass_textField = new Ext.form.TextField({
        name: 'superclass',
        id:'id_superclass_class',
        allowBlank:false,
        value: superclass_value,
        hidden: true,
        hidden:true
    });
	fields.push(superclass_textField);
/*	var can_catalog_chekbox = new Ext.form.Checkbox({
        id: 'id_canan_catalog',
        allowBlank:false,
        fieldLabel: 'Can Catalog',
        checked:can_catalog_chekbox_value, 
        name: 'can_catalog'
    });
	fields.push(can_catalog_chekbox);*/
	var notes_textField = new Ext.form.TextArea({
        fieldLabel: 'Notes',
        allowBlank:true,
        name: 'notes',
        value:notes_textField_value, 
        id:'notes_class'
    });
	fields.push(notes_textField);
	
	//workspaces
	var sm_ws_admin = new Ext.grid.CheckboxSelectionModel();
	// create the grid
    var ws_admin_grid = new Ext.grid.GridPanel({
        store: ws_admin_store,
        sm: sm_ws_admin,
        defaults: {
            sortable: true,
            menuDisabled: true,
            width: 100
        },
        title:'Select workspaces',
        cm: new Ext.grid.ColumnModel([
                                sm_ws_admin,
                                {id:'pk',header: "pk", width: 30, sortable: true, dataIndex: 'pk'},
                                {id:'name',header: "Name", width: 110, sortable: true, dataIndex: 'name'},
                                {id:'description',header: "Description", width: 160, sortable: true, dataIndex: 'description'}
        ]),
        listeners:{
        	afterrender: {fn:function(){
        		console.log('test after render');
        		console.log(ws_store.getAt(ws_store.findBy(find_current_ws_record)).data.pk);
        		console.log(this.getSelectionModel());
        	}}
        },
        height: 150
    });
    fields.push(ws_admin_grid);
    //attributes
	var sm_attributes_grid = new Ext.grid.CheckboxSelectionModel({
		singleSelect: true,
		listeners:{
			rowselect: {fn:function(sm){
				console.log(Ext.getCmp('id_edit_attributes_class'));
				Ext.getCmp('id_edit_attributes_class').enable();
				Ext.getCmp('id_remove_attributes_class').enable();
			}},
			rowdeselect: {fn:function(sm){
				Ext.getCmp('id_edit_attributes_class').disable();
				Ext.getCmp('id_remove_attributes_class').disable();
			}}
		}
	});
    var attributes_grid = new Ext.grid.GridPanel({
    	id: 'attribute_grid_id',
        store: store_attributes_grid,
        sm: sm_attributes_grid,
        title:'Attributes',
        cm: new Ext.grid.ColumnModel([
                                sm_attributes_grid,
                                {id:'id',header: "id", width: 30, sortable: true, dataIndex: 'id'},
                                {id:'name',header: "Name", width: 110, sortable: true, dataIndex: 'name'},
                                {id:'type',header: "Type", width: 50, sortable: true, dataIndex: 'type'},
                                {id:'multivalued',header: "Multivalued", width: 70, sortable: false, dataIndex: 'multivalued'},
                                {id:'default_value',header: "Default", width: 60, sortable: false, dataIndex: 'default_value'},
                                {id:'min',header: "Min", width: 60, sortable: false, dataIndex: 'min'},
                                {id:'max',header: "Max", width: 60, sortable: false, dataIndex: 'max'},
                                {id:'length',header: "Length", width: 60, sortable: false, dataIndex: 'length'},
                                {id:'choices',header: "Choices", width: 60, sortable: false, dataIndex: 'choices'},
                                {id:'target_class',header: "Target Class", width: 60, sortable: false, dataIndex: 'target_class'},
                                {id:'order',header: "Order", width: 50, sortable: true, dataIndex: 'order'},
                                {id:'notes',header: "Notes", width: 150, sortable: false, dataIndex: 'notes'},
                                {id:'maybe_empty',header: "Empty", width: 50, sortable: false, dataIndex: 'maybe_empty'}
        ]),
        bbar:[{
            text:'Add',
            tooltip:'Add a new attribute',
            iconCls:'add_icon',
            handler: function() {
            	console.log('not implemented yet');
            	add_single_attribute(false, attributes_grid);
        	}
        }, '-', {
            text:'Edit',
            id: 'id_edit_attributes_class',
            tooltip:'Edit attribute',
            iconCls:'edit_icon',
            disabled:true,
            handler: function() {
        		console.log('not implemented yet');
        		add_single_attribute(true, attributes_grid);
        	}
        },'-',{
            text:'Remove',
            id: 'id_remove_attributes_class',
            tooltip:'Remove the selected item',
            iconCls:'clear_icon',
            disabled:true,
            handler: function() {
        		Ext.Msg.confirm('Attribute Deletion', 'Attribute deletion cannot be undone, do you want to proceed?', 
	                function(btn){
	                    if (btn == 'yes')
	                        var sel=attributes_grid.getSelectionModel().getSelected();
	                    	attributes_grid.store.remove(sel);
	                }
        		);
        	}
        }],
    	height: 180
    });
    fields.push(attributes_grid);
    var details_panel_class = new Ext.FormPanel({
        id:'details_panel_class',
        title: title,
        labelWidth: 110, // label settings here cascade unless overridden
        frame:true,
        bodyStyle:'padding:5px 5px 0',              
        url: url_submit,
//        items: fields,
        items: [{
        	layout:'column',
        	items:[{
        		columnWidth:.5,
                layout: 'form',
                items: [id_textField, name_textField, superclass_textField, /*can_catalog_chekbox,*/ notes_textField]
        	},{
        		columnWidth:.5,
                layout: 'form',
                items: [ws_admin_grid]
        	}]
        },attributes_grid
        ],
        buttons: [{
            text: gettext('Save'),
            type: 'submit',
            handler: function(){
        		console.log('submit');
        		var my_form = this.findParentByType('form');
        		// problem con layout column unusable
        		/*console.log('Form');
        		console.log(my_form);
        		var items = my_form.items.items;
        		console.log('Items');
        		console.log(items);
        		console.log('-----');
        		for (var i = 0;  i < items.length; i ++){
        			console.log(items[i].getXType());
        		}*/
        		params = {};
        		if (id_textField.getValue()){
        			params['id'] = id_textField.getValue();
        		}else{
        			params['id'] = name_textField.getValue().replace(/ /g, "_");
        		}
        		params['name'] = name_textField.getValue();
        		params['supeclass'] = superclass_textField.getValue();
        		//params['can_catalog'] = can_catalog_chekbox.getValue();
        		params['notes'] = notes_textField.getValue();
        		console.log('get selected workspaces');
        		console.log(ws_admin_grid.getSelectionModel().getSelected());
        		params['workspaces'] = {};
        		//FIXME it is necessary generalize
        		params['workspaces'][ws_admin_grid.getSelectionModel().getSelected().data.pk] = "owner";
        		console.log('attributes');
        		console.log(attributes_grid);
        		var attribute;
        		params['attributes'] = {};
        		for (var i=0; i < Ext.getCmp('attribute_grid_id').getStore().getCount(); i++){
        			console.log('i:'+i);
        			attribute = Ext.getCmp('attribute_grid_id').getStore().getAt(i).data;
        			
        			params['attributes'][attribute.id] = {
        				'name': attribute.name,
        				'type': attribute.type,
        				'multivalued': attribute.multivalued,
        				'maybe_empty': attribute.maybe_empty,
        				'default_value': attribute.default_value,
        				'order': attribute.order,
        				'notes': attribute.notes
        			};
        			//if type int od data {'min', 'max'}
        			if (attribute.type == 'int' || attribute.type == 'data'){
        				params['attributes'][attribute.id]['min'] = attribute.min;
        				params['attributes'][attribute.id]['max'] = attribute.max;
        			}else if (attribute.type == 'string' || attribute.type == 'uri'){ //if type string or uri {'length'}
        				params['attributes'][attribute.id]['length'] = attribute.length;
        			}else if (attribute.type == 'choice'){ //if type choice {'choices'}
        				params['attributes'][attribute.id]['choices'] = attribute.choice;
        			}else if (attribute.type == 'objref'){ //if type objref {'target_class'}
        				console.log('objref');
        			}
        		}
        		console.log('Params');
        		console.log(params);
        		Ext.Ajax.request({
        			url:url_submit,
        			jsonData: params,
        			method: 'PUT',
        			headers: {
                        'Content-Type': 'application/json;charset=utf-8'
                    },
                    clientValidation: true,
                    waitMsg: 'Saving...',
                    success: function(response){
        	        // return response.responseText;
        	        	//alert('succes');
        	        	//console.log(Ext.util.JSON.decode(response));
                    	Ext.getCmp('obj_reference_tree').reload();
                    },
                    failure:function(response){
        	        // return response.responseText;
        	        	//alert('failure');
        	        	//console.log(response);
                    }
        		});
/*                my_form.getForm().submit({
                    method: 'PUT',
                    clientValidation: true,
                    waitMsg: 'Saving...',
                    success: function(response){
        	        // return response.responseText;
        	        	alert('added');
        	        	console.log(response);
                    }
                });
*/
        }
        },{
            text: gettext('Cancel'),
            handler: function(){
            	//clear form
            }
        }]
    });

	var pnl = Ext.getCmp('details_panel');
	pnl.removeAll();
	pnl.doLayout();
	pnl.add(details_panel_class);
	pnl.doLayout();
}

/**
 * Detail Obj Panel
 */	

function load_detail_obj(obj_data, obj_id, add_obj){
	console.log('load_detail_obj');
	// obj_data store
	// id_class id class
	// obj_id is null if add new obj else obj_id to view and edit
	
	console.log(obj_data.getAt(0).data);
	
	var fields = [];
	if (!add_obj){
		id_textField_value = obj_data.getAt(0).data.id;
		name_textField_value = obj_data.getAt(0).data.name;
		notes_textField_value = obj_data.getAt(0).data.notes;
		class_id_textField_value = obj_data.getAt(0).data.class_id;
		store_attributes_grid_obj = store_get_obj_attributes(obj_data.getAt(0).data.class_id, obj_id);
		var title = "Edit object " + name_textField_value;
	}else{
		id_textField_value = null;
		name_textField_value = null;
		notes_textField_value = null;
		var title = "Add new object";
	}
	
	var id_textField = new Ext.form.TextField({
        fieldLabel: 'Identification',
        allowBlank:true,
        name: 'id',
        value: id_textField_value, 
        id:'id_class'
    });
	fields.push(id_textField);
	
	var name_textField = new Ext.form.TextField({
        fieldLabel: 'Name',
        allowBlank:false,
        name: 'name',
        value:name_textField_value, 
        id:'name_class'
    });
	fields.push(name_textField);
	var class_id_textField = new Ext.form.TextField({
        name: 'superclass',
        id:'id_class_id_textField',
        allowBlank:false,
        value: class_id_textField_value,
        hidden: true
    });
	fields.push(class_id_textField);
	var notes_textField = new Ext.form.TextField({
        fieldLabel: 'Notes',
        allowBlank:true,
        name: 'notes',
        value:notes_textField_value, 
        id:'notes_class'
    });
	fields.push(notes_textField);
	
    //attributes
	console.log('STORE EditorGridPanel');
	console.log(store_attributes_grid_obj);
    var attributes_grid = new Ext.grid.EditorGridPanel({
        store: store_attributes_grid_obj,
        title:'Attributes',
        cm: new Ext.grid.ColumnModel([
                                {id:'id',header: "id", width: 30, sortable: true, dataIndex: 'id'},
                                {id:'name',header: "Name", width: 80, sortable: true, dataIndex: 'name'},
                                {id:'default_value',header: "Default", width: 70, sortable: true, dataIndex: 'default_value'},
                                {id:'type',header: "Type", width: 50, sortable: true, dataIndex: 'type'},
                                {id:'multivalued',header: "Multivalued", width: 50, sortable: true, dataIndex: 'multivalued'},
                                {id:'value',header: "Value", width: 90, dataIndex: 'value',
                                 editor:{fn:function(){
                                	console.log('test');
                                	console.log(this.store);
                                	new Ext.form.TextField({
                             	 	allowBlank: false
                              	})}}
                                },
                                {id:'maybe_empty',header: "Empty", width: 50, sortable: true, dataIndex: 'maybe_empty'}
        ]),
    	height: 220
    });
    fields.push(attributes_grid);
    var details_panel_obj = new Ext.FormPanel({
        id:'details_panel_obj',
        title: title,
        labelWidth: 110, // label settings here cascade unless overridden
        frame:true,
        bodyStyle:'padding:5px 5px 0',              
        url: '/PUT/',
//        items: fields,
        items: [{
        	layout:'column',
        	items:[{
        		columnWidth:.5,
                layout: 'form',
                items: [id_textField, class_id_textField, notes_textField]
        	},{
        		columnWidth:.5,
                layout: 'form',
                items: [name_textField]
        	}]
        }, attributes_grid
        ],
        buttons: [{
            text: gettext('Save'),
            type: 'submit',
            handler: function(){
        		console.log('submit');
            }
        },{
            text: gettext('Cancel'),
            handler: function(){
            	//clear form
            }
        }]
    });

	var pnl = Ext.getCmp('details_panel');
	pnl.removeAll();
	pnl.doLayout();
	pnl.add(details_panel_obj);
	pnl.doLayout();
}


function open_knowledgeBase(){        

/**
 * Detail Panel
 */	
	// to start with empty form
	var details_panel = new Ext.Panel({
		id:'details_panel',
		title:'Details',
	    region:'center',
	    layout:'fit'
	});

	
/**
 * Tree Panel
 */	
	
	var tree_loader_obj = new Ext.tree.TreeLoader({
        dataUrl:'/kb/get_nodes_real_obj/',
        draggable: false
    });
    
    var Tree_Obj_Root = new Ext.tree.AsyncTreeNode({
        text: gettext('All'),
        id:'root_obj_tree',
        expanded: true,
        allowDrag:false,
        allowDrop:true,
        editable: false,
        type:'object'
    });
    
	var tree_obj_reference = new Ext.tree.TreePanel({
		id:'obj_reference_tree',
		title:'Classes and Objects',
        region:'west',
		containerScroll: true,
		width: 200,
		autoScroll:true,
		loader: tree_loader_obj,
		rootVisible: true,
		contextMenu: init_contextMenuVocabulary(),
	    listeners: {
	        contextmenu: function(node, e) {
//	          Register the context node with the menu so that a Menu Item's handler function can access
//	          it via its parentMenu property.
					console.log('listeners contextmenu');
					node.select();
		            var c = node.getOwnerTree().contextMenu;
		            if (node.attributes.leaf == true){
		            	c.find('text',gettext('Add'))[0].disable()
		            }else{
		            	c.find('text',gettext('Add'))[0].enable()
		            }
		            c.contextNode = node;
		            c.showAt(e.getXY());
	        }
	    },
		selModel: new Ext.tree.DefaultSelectionModel({
			listeners:{
				"selectionchange": {
					fn:function(sel, node){
						console.log('selection change');
						console.log(node);
						if (node.attributes.leaf == false){
	    						init_store_class_data(node.attributes.id, false);
						}else{
							console.log('obj part');
							console.log(sel);
							console.log(node.attributes.id);
							if (node.attributes.id != 'root_obj_tree'){
								init_store_obj_data_edit(node.attributes.id, false);
							}else{
								Ext.getCmp('details_panel_class').removeAll();//FIXME err if panel is empty.
								Ext.getCmp('details_panel_class').setTitle('Class Objects');
							}
						}
					}
       			}	            		
             },
          })
	});
	//tree_obj_reference.on('contextmenu', contextMenuShow);

	tree_obj_reference.setRootNode(Tree_Obj_Root);

/**
 * Context menu
 */	
	function init_contextMenuVocabulary(){
		console.log('Init context menu');
		var add_class =  new Ext.menu.Item({
			id: 'id_addClass',
			text: gettext('Class'),
			listeners:{
				click: function(item){
					console.log('add_class item');
					console.log(item.parentMenu.parentMenu.contextNode.attributes.id);
					init_store_class_data(item.parentMenu.parentMenu.contextNode.attributes.id, true);
				}
			}
		});
		
		var add_object =  new Ext.menu.Item({
			id: 'id_addObject', 
			text: gettext('Object'),
			listeners:{
				click: function(item){
					console.log('add_obj item');
					var n = item.parentMenu.parentMenu.contextNode;
					init_store_obj_data(item.parentMenu.parentMenu.contextNode.attributes.id,true);
				}
			}
		});
	
		var add_node = new Ext.menu.Item({
			id: 'id_add', 
			text: gettext('Add'), 
			menu: [add_class, add_object]			
		});
		var edit_node = new Ext.menu.Item({id: 'id_edit_cls_obj', text: gettext('Edit')});
		var delete_node = new Ext.menu.Item({id: 'id_delete_cls_obj', text: gettext('Delete')});
	
		var contextMenuVocabulary = new Ext.menu.Menu({
			id:'contextMenuVocabulary',
			items:[
			    add_node,
			    edit_node,
			    delete_node
			],
	        listeners: {
	            itemclick: function(item) {
						console.log('ItemClick');
						console.log(item);
						console.log(item.id);
		                switch (item.id) {
		                    case 'id_add':
		                    	console.log('add');
		                    	var n = item.parentMenu.contextNode;
		                    	break;
		                    case 'id_addClass':
		                    	console.log('addClass');
		                    	var n = item.parentMenu.contextNode;
		                    	console.log(n);
		                        break;
		                    case 'id_edit_cls_obj':
		                    	console.log('edit_cls_obj');
		                    	var n = item.parentMenu.contextNode;
		                    	console.log(n);
		                        break;
		                    case 'id_delete_cls_obj':
		                    	console.log('delete_cls_obj');
		                    	var n = item.parentMenu.contextNode;
		                    	console.log(n);
		                        break;
		                    default: 
		                        console.log('default!');
		                }
		            }
	        }
		});
		return contextMenuVocabulary
	}
/**
 * Content Windows 
 */	
	var win_knowledge_base = new Ext.Window({
        id		:'id_win_knowledge_base',
		layout	: 'border',
		defaults: {               // defaults are applied to items, not the container
		    autoScroll:true
		},
        width	: 850,
        height	: 500,
        title	:'Vocabulary',
        modal	: true,
      	items	:[details_panel,
      	     	  tree_obj_reference
        ],
        buttons	:[{
            text: 'Close',
            handler: function() {
        	win_knowledge_base.close();
        	}
        }]
    });
	var ws_record = ws_store.getAt(ws_store.findBy(find_current_ws_record));
	console.log('current workspace');
	console.log(ws_record.data.pk);
	win_knowledge_base.show();  
}
