/**
 * All Store
 */		
function init_store_class_data(id_class, add_class){
	//var ws_record = ws_store.getAt(ws_store.findBy(find_current_ws_record));
	if (id_class != 'root_obj_tree'){
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
	}else{
		load_detail_class(this, id_class, add_class);
	}
}

function store_get_class_attributes(id_class){
	//var ws_record = ws_store.getAt(ws_store.findBy(find_current_ws_record));
	return new Ext.data.JsonStore({
	    url: '/kb/get_class_attributes/'+id_class+'/',
	    autoLoad:true,
	    root: 'rows',
	    fields:['id','name','type','maybe_empty','default_value','order','notes','min','max','length','choices', 'multivalued', 'target_class', 'inherited']
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
				load_detail_obj(this, obj_id, add_obj, null);
			}
		}
	});
	obj_store.load();
}

function get_store_obj_attributes(class_id, obj_id){
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
	    fields:['id','name','type','multivalued','maybe_empty','default_value','order','notes', 'value', 'choices', 'target_class', 'min', 'max','length', 'notes']
	});	
}

function get_TF_store(){
	return new Ext.data.SimpleStore({
        fields: ['id','name'],
        data: [
          [true,"True"],[false,"False"]]
    });
}

var ws_admin_store = new Ext.data.JsonStore({
	    url: '/kb/get_workspaces_with_edit_vocabulary/',
	    id:'id_ws_admin_store',
	    autoLoad:true,
	    root: 'workspaces',
	    fields:['pk','name','description']
	});

function get_treeLoader_vocabulary(){
	return new Ext.tree.TreeLoader({
        dataUrl:'/kb/get_nodes_real_obj/',
        draggable: false
    });
}

function get_AsyncTreeNode(){
	return new Ext.tree.AsyncTreeNode({
        text: gettext('Base classes'),
        id:'root_obj_tree',
        expanded: true,
        allowDrag:false,
        allowDrop:true,
        editable: false,
        type:'object',
        iconCls: 'object-class'
    });
}

function save_and_close_win_att_class(attributes_grid, insert_value, win_att_class){
	
	if (!insert_value){ // class scope
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
		},{
		    name: 'target_class'
		}]);
		
		if (Ext.getCmp('type_comb_class').getValue() == 'date'){//fit date format
			if (Ext.getCmp('id_min').getValue()){min_value = Ext.getCmp('id_min').getValue().format('Y-m-d');}else{min_value = null;}
    		if (Ext.getCmp('id_max').getValue()){max_value = Ext.getCmp('id_max').getValue().format('Y-m-d');}else{max_value = null;}
			if (Ext.getCmp('id_default_value').getValue()){default_value = Ext.getCmp('id_default_value').getValue().format('Y-m-d');}else{default_value = null;}
		}else{
			if (Ext.getCmp('id_min')){min_value = Ext.getCmp('id_min').getValue();}else{min_value = null;}
    		if (Ext.getCmp('id_max')){max_value = Ext.getCmp('id_max').getValue();}else{max_value = null;}
			if (Ext.getCmp('id_default_value')){default_value = Ext.getCmp('id_default_value').getValue();}else{default_value = null;}
		}
		if (Ext.getCmp('id_max_length')){max_length = Ext.getCmp('id_max_length').getValue();}else{max_length = null;}
		if (Ext.getCmp('id_choices')){//string list
			choices = Ext.getCmp('id_choices').getValue().split(',');
			if (choices[choices.length-1] == ""){
				delete(choices[choices.length-1]);
				choices.splice(choices.length-1, 1);
			}
		}else{choices = null;}
		if (Ext.getCmp('id_target_class')){target_class = Ext.getCmp('id_target_class').getValue()}else{target_class = null;}
		if (this.text == gettext('Apply')){
			attributes_grid.getSelectionModel().getSelected().set('name',name_textField.getValue());
			attributes_grid.getSelectionModel().getSelected().set('default_value',default_value);
			attributes_grid.getSelectionModel().getSelected().set('order',order_slider.getValue());
			attributes_grid.getSelectionModel().getSelected().set('notes',notes_textField.getValue());
			attributes_grid.getSelectionModel().getSelected().set('type',type_combo.getValue());
			attributes_grid.getSelectionModel().getSelected().set('multivalued',multivalued_chekbox.getValue());
			attributes_grid.getSelectionModel().getSelected().set('maybe_empty',empty_chekbox.getValue());
			attributes_grid.getSelectionModel().getSelected().set('min',min_value);
			attributes_grid.getSelectionModel().getSelected().set('max',max_value);
			attributes_grid.getSelectionModel().getSelected().set('length',max_length);
			attributes_grid.getSelectionModel().getSelected().set('target_class',target_class);
		}else{
    		attributes_grid.store.add(new Attribute({
    			id			: Ext.getCmp('name_attribute').getValue().replace(/ /g, "_"),
    			name		: Ext.getCmp('name_attribute').getValue(),
    			default_value: default_value,
    			order		: Ext.getCmp('slider_order').getValue(),
    			notes		: Ext.getCmp('id_notes_attribute').getValue(),
    			type		: Ext.getCmp('type_comb_class').getValue(),
    			multivalued : Ext.getCmp('id_multivalued_chekbox').getValue(),
    			maybe_empty : Ext.getCmp('id_empty_chekbox').getValue(),
    			min			: min_value,
    			max			: max_value,
    			length		: max_length,
    			choices		: choices,
    			target_class: target_class
    		}));
		}
	}else{ //obj scope
		if(attributes_grid.getSelectionModel().getSelected().data.type == 'choice'){//case where choice is multivalued
			var txt = "";
			for(i=0; i < Ext.getCmp('id_record_value').getSelectionModel().getSelections().length; i++){
				txt = txt + Ext.getCmp('id_record_value').getSelectionModel().getSelections()[i].data.name + ',';
			}
			txt = txt.substring(0,txt.length-1);
			attributes_grid.getSelectionModel().getSelected().set('value',txt);
		}else if(Ext.getCmp('id_multivalued_chekbox').getValue() == true){//case where multivalued true
			var txt = new Array();
			for(i=0; i < Ext.getCmp('id_record_value').getStore().getCount(); i++){
				txt.push(Ext.getCmp('id_record_value').getStore().getAt(i).data.name);
			}
			attributes_grid.getSelectionModel().getSelected().set('value',txt);
		}else if (Ext.getCmp('id_multivalued_chekbox').getValue() == false){//objref multivalued false
			if (Ext.getCmp('id_record_value').getStore().getCount() == 1){
				attributes_grid.getSelectionModel().getSelected().set('value', Ext.getCmp('id_record_value').getStore().getAt(0).data.name);
			}else{
				attributes_grid.getSelectionModel().getSelected().set('value', null);
			}
		}
	}
	win_att_class.close();
}

function close_window_insert_attribute(){
	Ext.getCmp('id_win_add_attribute').close();
}

function show_win_single_attribute_date_string(year_value, month_value, day_value, check_period, title, close_window, attributes_grid, win_att_class){
	var win_select_class_target = new Ext.Window({
        id		:'id_win_define_date_string',
		layout	: 'form',
		resizable : false,
		defaults: {  // defaults are applied to items, not the container
		    autoScroll:true
		},
        width	: 400,
        height	: 200,
        title	: title,
        modal	: true,
      	items	:[{
	  				xtype: 'spacer',
		  			height: 8
    			}
    			,year_value, month_value, day_value, check_period],
        buttons	:[{
            text: 'Done',
            handler: function() {
	        	if (Ext.getCmp('id_year_value').getValue() && Ext.getCmp('id_month_value').getValue() && Ext.getCmp('id_day_value').getValue()){
	        		var str_final = Ext.getCmp('id_check_period').getValue().inputValue +
									Ext.getCmp('id_year_value').getValue() + "-"+
									Ext.getCmp('id_month_value').getValue() + "-"+
									Ext.getCmp('id_day_value').getValue();
					var Attribute = Ext.data.Record.create([{
		        		name: 'name'
		        	}]);
					Ext.getCmp('id_record_value').store.add(new Attribute({name: str_final}));
		        	win_select_class_target.close();
	        	}else{
	        		Ext.Msg.alert('Warning', 'You have to insert some value.');
	        	}
				if(close_window){
					save_and_close_win_att_class(attributes_grid, true, win_att_class);
				}
        	}
        },{
            text: 'Close',
            handler: function() {
				check_add_button_add_option();
				check_remove_button_add_option();
        		win_select_class_target.close();
        		if(close_window){
					save_and_close_win_att_class(attributes_grid, true, win_att_class);
        		}
        	}
        }]
    });
	win_select_class_target.show();	
}




function show_win_single_attribute(params, title, close_window, attributes_grid, win_att_class){
	var win_select_class_target = new Ext.Window({
        id		:'id_win_select_class_target',
		layout	: 'form',
		resizable : false,
		defaults: {  // defaults are applied to items, not the container
		    autoScroll:true
		},
        width	: 300,
        height	: 120,
        title	: title,
        modal	: true,
      	items	:[{
	  				xtype: 'spacer',
		  			height: 8
    			}
    			,params],
        buttons	:[{
            text: 'Done',
            handler: function() {
	        	var Attribute = Ext.data.Record.create([{
	        		name: 'name'
	        	}]);
    			if (Ext.getCmp('type_comb_class').getValue() == 'date'){//fit date format
	        		Ext.getCmp('id_record_value').store.add(new Attribute({name: Ext.getCmp('id_record_value_single_box').getValue().format('Y-m-d')}));
	        	}else{
	        		Ext.getCmp('id_record_value').store.add(new Attribute({name: Ext.getCmp('id_record_value_single_box').getValue()}));
	        	}
	        	win_select_class_target.close();
        		if(close_window){
					save_and_close_win_att_class(attributes_grid, true, win_att_class);
        		}
        	}
        },{
            text: 'Close',
            handler: function() {
				check_add_button_add_option();
				check_remove_button_add_option();
        		win_select_class_target.close();
        		if(close_window){
					save_and_close_win_att_class(attributes_grid, true, win_att_class);
        		}
        	}
        }]
    });
	win_select_class_target.show();
}

function view_tree_vocabulary_to_obj_ref(textField_id, multivalued){

	var text_app;
	var tree_loader_obj = get_treeLoader_vocabulary();
    var Tree_Obj_Root = get_AsyncTreeNode();
  	var sm = new Ext.tree.DefaultSelectionModel();
    var tree_vocabulary_to_obj_ref = new Ext.tree.TreePanel({
		id:'id_tree_vocabulary_to_obj_ref',
		title:gettext('Select target classes'),
		containerScroll: true,
		width: 100,
		autoScroll:true,
		loader: tree_loader_obj,
		rootVisible: true,
		selModel: sm
	});	
	tree_vocabulary_to_obj_ref.setRootNode(Tree_Obj_Root);
	new Ext.tree.TreeSorter(tree_vocabulary_to_obj_ref, {
	    dir: "ASC",
	    folderSort: true
	});

	var win_select_class_target = new Ext.Window({
        id		:'id_win_select_class_target',
		layout	: 'fit',
		defaults: {               // defaults are applied to items, not the container
		    autoScroll:true
		},
		resizable : false,
        width	: 220,
        height	: 320,
        title	:gettext('Vocabulary'),
        modal	: true,
      	items	:[tree_vocabulary_to_obj_ref],
        buttons	:[{
            text: 'Done',
            handler: function() {
	        	var Attribute = Ext.data.Record.create([{
	        		name: 'name'
	        	}]);
        		if (textField_id == 'id_target_class'){
            		if (Ext.getCmp('id_tree_vocabulary_to_obj_ref').getSelectionModel().selNode && Ext.getCmp('id_tree_vocabulary_to_obj_ref').getSelectionModel().selNode.attributes.leaf == false){
            			Ext.getCmp('id_target_class').setValue(Ext.getCmp('id_tree_vocabulary_to_obj_ref').getSelectionModel().selNode.attributes.id);
            			win_select_class_target.close();
            		}else{
            			Ext.Msg.alert('Status', 'Select a class.');
            		}
        		}else{
            		if (Ext.getCmp('id_tree_vocabulary_to_obj_ref').getSelectionModel().selNode && Ext.getCmp('id_tree_vocabulary_to_obj_ref').getSelectionModel().selNode.attributes.leaf == true){
        	        	Ext.getCmp('id_record_value').store.add(new Attribute({name: Ext.getCmp('id_tree_vocabulary_to_obj_ref').getSelectionModel().selNode.attributes.id}));
            			win_select_class_target.close();
            		}else{
            			Ext.Msg.alert('Status', 'Select an object.');
            		}
        		}
        	}
        },{
            text: 'Close',
            handler: function() {
        		win_select_class_target.close();
        	}
        }]
    });
	win_select_class_target.show();
}

function get_store_grid_insert(data_list){
	// input list (['aaa','aaaa'])and return storage for grid (list of list ([['aaaa'],['aaaa']]) it is necessary for grid)
	var data_objref, app1;
	if(!isEmpty(data_list)){
		data_objref= new Array();
		if (data_list && typeof (data_list) == "object"){
			for(i=0; i<data_list.length;i++){
				app1 = new Array();
				app1.push(data_list[i]);
				data_objref.push(app1);
			}
		}else{
			app1 = new Array();
			app1.push(data_list);
			data_objref.push(app1);
		}
		var st_value = new Ext.data.ArrayStore({
	        fields: [
	           {name: 'name'},
	        ]
	    });
		st_value.loadData(data_objref);
		
		return st_value
	}else
		return []
}

function check_add_button_add_option(){
	if (Ext.getCmp('id_multivalued_chekbox').getValue() == false && Ext.getCmp('id_record_value').getStore().getCount() > 0){
		Ext.getCmp('id_add_attributes_class').disable();
	}else{
		Ext.getCmp('id_add_attributes_class').enable();
	}
}

function check_remove_button_add_option(){
	if (Ext.getCmp('id_record_value').getStore().getCount() == 0){
		Ext.getCmp('id_remove_attributes_class').disable();
		if(Ext.getCmp('id_movedown_attributes_class')){
			Ext.getCmp('id_movedown_attributes_class').disable();
			Ext.getCmp('id_moveup_attributes_class').disable();
		}
	}
}

function logic_to_insert_single_value(type, close_window, attributes_grid, win_att_class){
	
	if (type == 'objref'){
		view_tree_vocabulary_to_obj_ref('id_record_value', Ext.getCmp('id_multivalued_chekbox').getValue());
	}else if (type == 'bool'){
		var record_value = new Ext.form.ComboBox({
			id  : 'id_record_value_single_box',
	        store: get_TF_store(), // end of Ext.data.SimpleStore
	        fieldLabel: gettext('Select value ..'),
	        width: 130,
	        emptyText: gettext('Select ..'),
	        displayField: 'name',
	        valueField: 'id',
	        mode: 'local',
	        editable: false,
	        allowBlank:true,
	        triggerAction: 'all'
		});
		show_win_single_attribute(record_value, 'Insert Value', close_window, attributes_grid, win_att_class);
	}else if (type == 'string' || type == 'uri'){
		var record_value = new Ext.form.TextField({
			name: 'Insert value',
			id  : 'id_record_value_single_box',
			fieldLabel: gettext('Insert value'),
	        allowBlank:true
		});
		show_win_single_attribute(record_value, 'Insert Value', close_window, attributes_grid, win_att_class);
	}else if (type == 'date'){
		var record_value = new Ext.form.DateField({
			name: 'Insert value',
			id  : 'id_record_value_single_box',
			fieldLabel: gettext('Insert value'),
			format: 'Y-m-d',
	        allowBlank:true
		});
		show_win_single_attribute(record_value, 'Insert Value', close_window, attributes_grid, win_att_class);
	}else if(type == 'int'){
		var record_value = new Ext.form.NumberField({
			name: 'Insert value',
			id  : 'id_record_value_single_box',
			fieldLabel: gettext('Insert value'),
	        allowBlank:true
		});
		show_win_single_attribute(record_value, 'Insert Value', close_window, attributes_grid, win_att_class);


	}else if(type == 'date-like-string'){ 

		var year_value = new Ext.form.NumberField({
			name: 'Insert value',
			id  : 'id_year_value',
			fieldLabel: gettext('Insert year'),
	        allowBlank:false
		});

		var month_value = new Ext.form.ComboBox({
			id  : 'id_month_value',
	        store: new Ext.data.SimpleStore({
	            fields: ['id','name'],
	            data: [
	              ["01","01"],["02","02"],["03","03"],["04","04"],["05","05"],["06","06"],["07","07"],["08","08"],["09","09"],["10","10"],["11","11"],["12","12"]]
	        }), // end of Ext.data.SimpleStore
	        fieldLabel: gettext('Select month'),
	        width: 130,
	        emptyText: gettext('Select ..'),
	        displayField: 'name',
	        valueField: 'id',
	        mode: 'local',
	        editable: false,
	        allowBlank:false,
	        triggerAction: 'all'
		});

		var day_value = new Ext.form.ComboBox({
			id  : 'id_day_value',
	        store: new Ext.data.SimpleStore({
	            fields: ['id','name'],
	            data: [
	              ["01","01"],["02","02"],["03","03"],["04","04"],["05","05"],["06","06"],["07","07"],["08","08"],["09","09"],["10","10"],
	              ["11","11"],["12","12"],["13","13"],["14","14"],["15","15"],["16","16"],["17","17"],["18","18"],["19","19"],["20","20"],
	              ["21","21"],["22","22"],["23","23"],["24","24"],["25","25"],["26","26"],["27","27"],["28","28"],["29","29"],["30","30"],
	              ["31","31"]]
	        }), // end of Ext.data.SimpleStore
	        fieldLabel: gettext('Select day'),
	        width: 130,
	        emptyText: gettext('Select ..'),
	        displayField: 'name',
	        valueField: 'id',
	        mode: 'local',
	        editable: false,
	        allowBlank:false,
	        triggerAction: 'all'
		});

		var check_period = new Ext.form.RadioGroup({
			id  : 'id_check_period',
			columns: 1,
			fieldLabel: 'Choise period',
			items:[
                    {boxLabel: 'After Christ', name: 'rb-cristo', inputValue: '+', checked: true},
                    {boxLabel: 'Before Christ', name: 'rb-cristo', inputValue: '-'} 
            ]
		});

    	show_win_single_attribute_date_string(year_value, month_value, day_value, check_period, 'Insert Value', close_window, attributes_grid, win_att_class);



	}
	if (Ext.getCmp('id_multivalued_chekbox').getValue() == false){//FIXME getStore().getCount() not update in realtime
		Ext.getCmp('id_add_attributes_class').disable();
	}
}

function get_grid_insert_value(value, type, title){
	var store_grid = get_store_grid_insert(value);
	var sm = new Ext.grid.CheckboxSelectionModel({
		singleSelect: true,
		listeners:{
			rowselect: {fn:function(sm){
				Ext.getCmp('id_remove_attributes_class').enable();
			}},
			rowdeselect: {fn:function(sm){
				Ext.getCmp('id_remove_attributes_class').disable();
			}}
		}
	});
	var grid_value = new Ext.grid.GridPanel({
        id:'id_record_value',
    	store: store_grid,
        sm: sm,
        autoExpandColumn: 'name',
        defaults: {
            sortable: true,
            menuDisabled: true,
            width: 100
        },
        title:title,
        cm: new Ext.grid.ColumnModel([
                                sm,
                                {id:'name',header: "Value", width: 110, sortable: true, dataIndex: 'name'},
        ]),
        bbar:[{
            text:'Add',
            id: 'id_add_attributes_class',
            tooltip:'Add a new value',
            iconCls:'add_icon',
            handler: function() {
        		logic_to_insert_single_value(type, false, false, false);
        	
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
	                        var sel=grid_value.getSelectionModel().getSelected();
	                    	grid_value.store.remove(sel);
	                    	check_remove_button_add_option();
			            	check_add_button_add_option();
	                }
        		);
        	}
        }],
        listeners:{
        	afterrender: { fn:function(){
        			check_add_button_add_option();
        			check_remove_button_add_option();
        		}
        	}
        },
        height: 150
    });
	
	return grid_value
}

function check_add_class(add_class, insert_value, add_attribute, record_value){
	if (!add_class && !add_attribute && !insert_value){
		record_value.disabled = true;
	}
}
function add_option(value, attribute_detail_panel, data, insert_value, add_class, add_attribute){
	//initializing
	attribute_detail_panel.removeAll();
	var min_number_value = null;
	var max_number_value = null;
	var default_v = null;
	var min_date_value = null;
	var max_date_value = null;
	var max_length_value = null;
	var choices_value = null;
	var target_class_value=null;
	var i;
	
	if (value == 'int'){
		if (data){
			min_number_value = data.min;
			max_number_value = data.max;
			default_v = data.default_value;
		}
		var min_number = new Ext.form.NumberField({
			name: 'min_number',
			id  : 'id_min',
			fieldLabel: gettext('Min value'),
			value: min_number_value,
	        allowBlank:true
		});
		var max_number = new Ext.form.NumberField({
			name: 'max_number',
			id  : 'id_max',
			fieldLabel: gettext('Max value'),
			value: max_number_value,
	        allowBlank:true
		});
		var default_value = new Ext.form.NumberField({
			name: 'default_value',
			id  : 'id_default_value',
			fieldLabel: gettext('Default value'),
			value: default_v,
	        allowBlank:true
		});
		check_add_class(add_class, insert_value, add_attribute, min_number);
		check_add_class(add_class, insert_value, add_attribute, max_number);
		check_add_class(add_class, insert_value, add_attribute, default_value);
		attribute_detail_panel.add(min_number);
		attribute_detail_panel.add(max_number);
		attribute_detail_panel.add(default_value);
		if (insert_value){
			record_value = get_grid_insert_value(data.value, value, 'Insert values');
			min_number.disable();
			max_number.disable();
			default_value.disable();
			check_add_class(add_class, insert_value, add_attribute, record_value);
			attribute_detail_panel.add(record_value);
		}
	}else if (value == 'date'){
		if (data){
			min_date_value = data.min;
			max_date_value = data.max;
			default_v = data.default_value;
		}
		var min_date = new Ext.form.DateField({
			name: 'min_date',
			id  : 'id_min',
			fieldLabel: gettext('Min date'),
			format: 'Y-m-d',
			value: min_date_value,
	        allowBlank:true
		});
		var max_date = new Ext.form.DateField({
			name: 'max_date',
			id  : 'id_max',
			fieldLabel: gettext('Max date'),
			format: 'Y-m-d',
			value: max_date_value,
	        allowBlank:true
		});
		var default_value = new Ext.form.DateField({
			name: 'default_value',
			id  : 'id_default_value',
			format: 'Y-m-d',
			fieldLabel: gettext('Default value'),
			value: default_v,
	        allowBlank:true
		});
		check_add_class(add_class, insert_value, add_attribute, min_date);
		check_add_class(add_class, insert_value, add_attribute, max_date);
		check_add_class(add_class, insert_value, add_attribute, default_value);
		attribute_detail_panel.add(min_date);
		attribute_detail_panel.add(max_date);
		attribute_detail_panel.add(default_value);
		if (insert_value){
			record_value = get_grid_insert_value(data.value, value, 'Insert values');
			min_date.disable();
			max_date.disable();
			default_value.disable();
			check_add_class(add_class, insert_value, add_attribute, record_value);
			attribute_detail_panel.add(record_value);
		}
	}else if (value == 'string' || value == 'uri'){
		if (data){
			max_length_value = data.length;
		}
		var max_length = new Ext.form.NumberField({
			name: 'max_length',
			id  : 'id_max_length',
			fieldLabel: gettext('Max length'),
			value: max_length_value,
	        allowBlank:false
		});
		check_add_class(add_class, insert_value, add_attribute, max_length);
		attribute_detail_panel.add(max_length);
		if (insert_value){
			record_value = get_grid_insert_value(data.value, value, 'Insert values');
			max_length.disable();
			check_add_class(add_class, insert_value, add_attribute, record_value);
			attribute_detail_panel.add(record_value);
		}
	}else if (value == 'objref'){
		if (data){
			target_class_value = data.target_class;
		}
		var target_class = new Ext.form.TextField({
			name: 'target_class',
			id  : 'id_target_class',
			fieldLabel: gettext('Insert target class'),
	        allowBlank:false,
	        readOnly:false,
			emptyText:gettext('Double click here'),
	        value: target_class_value,
	        handleMouseEvents: true,
	        listeners: {'render': function(cmp) { 
	            cmp.getEl().on('dblclick', function( event, el ) {
	            	view_tree_vocabulary_to_obj_ref('id_target_class', false);
	            });            
	          }
			}
		});
		check_add_class(add_class, insert_value, add_attribute, target_class);
		attribute_detail_panel.add(target_class);
		if (insert_value){//can select only objects.
			record_value = get_grid_insert_value(data.value, value, 'Select objects references');
			target_class.disable();
			check_add_class(add_class, insert_value, add_attribute, record_value);
			attribute_detail_panel.add(record_value);			
		}
	}else if(value == 'bool'){
		if (data){
			default_v = data.default_value;
		}
		var default_value = new Ext.form.ComboBox({
			id  : 'id_default_value',
	        store: get_TF_store(),// end of Ext.data.SimpleStore
	        width: 130,
	        emptyText: gettext('Select ..'),
	        displayField: 'name',
	        valueField: 'id',
	        mode: 'local',
	        editable: false,
			value: default_v,
			fieldLabel: gettext('Default value'),
	        allowBlank:true,
	        triggerAction: 'all'
		});
		check_add_class(add_class, insert_value, add_attribute, default_value);
		attribute_detail_panel.add(default_value);
		if (insert_value){
			var record_value = get_grid_insert_value(data.value, value, 'Insert values');
			default_value.disable();
			check_add_class(add_class, insert_value, add_attribute, record_value);
			attribute_detail_panel.add(record_value);
		}
	}else if(value == 'choice'){
		if (data){
			choices_value = data.choices;
			default_v = data.default_value;
		}
		var choices = new Ext.form.TextField({
			name: 'choices',
			id  : 'id_choices',
			emptyText:gettext('Separates by ,'),
			fieldLabel: gettext('Choices'),
			value: choices_value,
	        allowBlank:false
		});
		var default_value = new Ext.form.TextField({
			name: 'default_value',
			id  : 'id_default_value',
			fieldLabel: gettext('Default value'),
			value: default_v,
	        allowBlank:true
		});
		check_add_class(add_class, insert_value, add_attribute, choices);
		check_add_class(add_class, insert_value, add_attribute, default_value);
		attribute_detail_panel.add(choices);
		attribute_detail_panel.add(default_value);
		if (insert_value){
			// choices_value is a list, creating store
			st_choices_value = get_store_grid_insert(choices_value);
			
			if(Ext.getCmp('id_multivalued_chekbox').getValue()){
				var sm_choices_value = new Ext.grid.CheckboxSelectionModel({});
			}else{
				var sm_choices_value = new Ext.grid.CheckboxSelectionModel({singleSelect:true});
			}
			// create the grid
			var record_value = new Ext.grid.GridPanel({
		        id:'id_record_value',
		    	store: st_choices_value,
		        sm: sm_choices_value,
		        autoExpandColumn: 'name',
		        defaults: {
		            sortable: true,
		            menuDisabled: true,
		            width: 100
		        },
		        title:gettext('Select values'),
		        cm: new Ext.grid.ColumnModel([
		                                sm_choices_value,
		                                {id:'name',header: "Value", width: 110, sortable: true, dataIndex: 'name'},
		        ]),
		        height: 150
		    });
			choices.disable();
			default_value.disable();
			check_add_class(add_class, insert_value, add_attribute, record_value);
			attribute_detail_panel.add(record_value);
		}

	}else if (value == 'date-like-string'){
		if (insert_value){
			record_value = get_grid_insert_value(data.value, value, 'Insert values');
			check_add_class(add_class, insert_value, add_attribute, record_value);
			attribute_detail_panel.add(record_value);
		}


	}
	attribute_detail_panel.doLayout();
}

function isEmpty(obj) {
	/*
	 * Verify if the obj passed is empty on not.
	 * @return true if it is empty else false
	 */
	if (typeof obj == 'undefined' || obj === null || obj === '') return true;
	if (typeof obj == 'number' && isNaN(obj)) return true;
	if (obj instanceof Date && isNaN(Number(obj))) return true;
	return false;
}

function add_single_attribute(edit, attributes_grid, insert_value, add_class, add_attribute){
	var name_textField_value, empty_chekbox_value, empty_chekbox_value, multivalued_chekbox_value, notes_textField_value, title, text_button, max_value_slider;
	
	if (edit){
		name_textField_value = attributes_grid.getSelectionModel().getSelected().data.name;
		empty_chekbox_value = attributes_grid.getSelectionModel().getSelected().data.maybe_empty;
		multivalued_chekbox_value = attributes_grid.getSelectionModel().getSelected().data.multivalued;
		notes_textField_value = attributes_grid.getSelectionModel().getSelected().data.notes;
		title = gettext("Edit attribute");
		text_button = gettext('Apply');
		max_value_slider = attributes_grid.getStore().getCount()-1;
		slider_value = attributes_grid.getSelectionModel().getSelected().data.order;
	}else{
		name_textField_value = null;
		empty_chekbox_value = false;
		multivalued_chekbox_value = false;
		notes_textField_value = null;
		title = gettext("New attribute");
		text_button = gettext('Add');
		max_value_slider = attributes_grid.getStore().getCount();
		slider_value = attributes_grid.getStore().getCount();
	}
	
	var name_textField = new Ext.form.TextField({
        fieldLabel: gettext('Name'),
        allowBlank:false,
        name: 'name',
        value: name_textField_value, 
        id:'name_attribute'
    });
	var type_combo = new Ext.form.ComboBox({
        id: 'type_comb_class',
        store: 
            new Ext.data.SimpleStore({
              fields: ['id','name'],
              data: [
                ["bool","Boolean"],["int","Integer"],["string","String"],["date","Date"],["date-like-string","Date Like String"],["uri","Url"],["choice","Choice"],["objref","Object Reference"]]
          }), // end of Ext.data.SimpleStore
        fieldLabel: gettext('Type'),
        width: 130,
        emptyText: gettext('Select a type ..'),
        displayField: 'name',
        valueField: 'id',
        mode: 'local',
        editable: false,
        triggerAction: 'all',
        listeners:{ 
			select:{ fn:function(combo, ewVal, oldVal){
				add_option(ewVal.data.id, Ext.getCmp('id_option_attribute_panel'), null, insert_value, add_class, add_attribute);
			}},
			render:{fn:function(combo){
				if (edit){
					combo.setValue(attributes_grid.getSelectionModel().getSelected().data.type);
					add_option(attributes_grid.getSelectionModel().getSelected().data.type, Ext.getCmp('id_option_attribute_panel'), attributes_grid.getSelectionModel().getSelected().data, insert_value, add_class, add_attribute);
				}
			}}
      	}        
	});	
	var empty_chekbox = new Ext.form.Checkbox({
        id: 'id_empty_chekbox',
        allowBlank:false,
        fieldLabel: gettext('Maybe empty'),
        checked:empty_chekbox_value, 
        name: 'empty_checkbox'
    });
	var multivalued_chekbox = new Ext.form.Checkbox({
        id: 'id_multivalued_chekbox',
        allowBlank:false,
        fieldLabel: gettext('Multivalued'),
        checked:multivalued_chekbox_value, 
        name: 'multivalued_chekbox'
    });
	var notes_textField = new Ext.form.TextArea({
        fieldLabel: gettext('Notes'),
        allowBlank:true,
        width: 130,
        name: 'notes',
        value: notes_textField_value, 
        id:'id_notes_attribute'
    });
    var order_slider = new Ext.slider.SingleSlider({
    	id:'slider_order',
        width: 130,
        increment: 1,
        minValue: 0,
        maxValue: max_value_slider,
        value: slider_value,
        hidden: true,
        plugins: new Ext.ux.SliderTip()
    });
    
    if(!add_class && !add_attribute && insert_value == false){
    	order_slider.disabled = true;
    	multivalued_chekbox.disabled = true;
    	empty_chekbox.disabled = true;
    	type_combo.disabled = true;
    }
	var attribute_detail_panel = new Ext.FormPanel({
        id:'attribute_detail_panel',
        labelWidth: 80, // label settings here cascade unless overridden
        frame:true,
        bodyStyle:'padding:5px 5px 0', 
        items: [{
        	layout:'column',
        	items:[{
        		columnWidth:.5,
                layout: 'form',
                items: [name_textField
                        ,type_combo
                        ,{
          		  			xtype: 'spacer',
          		  			height: 10
                		}
                		,order_slider]
        	},{
        		columnWidth:.5,
                layout: 'form',
                items: [empty_chekbox, multivalued_chekbox, notes_textField]
        	}]
        },{
        	xtype: 'spacer',
	  		height: 10
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
        		save_and_close_win_att_class(attributes_grid, insert_value, win_att_class);
        	}
        }]
    });
	
	if (insert_value){
		name_textField.disable();
		type_combo.disable();
		empty_chekbox.disable();
		multivalued_chekbox.disable();
		notes_textField.disable();
		order_slider.setValue(attributes_grid.getSelectionModel().getSelected().data.order);
		order_slider.disable();
		title = gettext('Insert value for this attribute');
		Ext.getCmp('attribute_detail_panel').buttons[0].text=gettext('Done');
	}
		var win_att_class = new Ext.Window({
	        id		:'id_win_add_attribute',
			layout	: 'fit',
			resizable : false,
			defaults: {               // defaults are applied to items, not the container
			    autoScroll:true
			},
	        width	: 500,
	        height	: 450,
	        title	: title,
	        modal	: true,
	      	items	:[attribute_detail_panel]
	    });
		
	if (multivalued_chekbox.checked == false && edit){
		win_att_class.show();
		
		if(Ext.getCmp('id_record_value').getStore().getCount() > 0){ //edit (remove and add)
			Ext.getCmp('id_record_value').getSelectionModel().selectFirstRow()
			var sel=Ext.getCmp('id_record_value').getSelectionModel().getSelected();
			Ext.getCmp('id_record_value').store.remove(sel);
	    	check_remove_button_add_option();
	    	check_add_button_add_option();
		}
    	logic_to_insert_single_value(attributes_grid.getSelectionModel().getSelected().data.type, true, attributes_grid, win_att_class);
		
	}else{
	    win_att_class.show();
	}
}

function moveSelectedRow(grid, direction) {
	var record = grid.getSelectionModel().getSelected();
	var bis_record;
	if (!record) {
		return;
	}
	var index = grid.getStore().indexOf(record);
	if (direction < 0) {
		index--;
		if (index < 0) {
			return;
		}else{
			bis_record = grid.getStore().getAt(index)
			bis_record.data.order = index + 1;
		}
	} else {
		index++;
		if (index >= grid.getStore().getCount()) {
			return;
		}else{
			bis_record = grid.getStore().getAt(index)
			bis_record.data.order = index - 1;
		}
	}
	grid.getStore().remove(bis_record);
	grid.getStore().insert(index, bis_record);
	grid.getStore().remove(record);
	record.data.order = index;
	grid.getStore().insert(index, record);
	grid.getSelectionModel().selectRow(index, true);
}

/**
 * Detail Class Panel
 */	
function load_detail_class(class_data, id_class, add_class){
	/*
	 * Load class data when class is selected on tree.
	 * @class_data 	store
	 * @id_class 	class id 
	 * @add_class 	It's true if is going to add new class false otherwise 
	 */
	var fields = [];
	var i; // counter for loop
	
	var id_textField = new Ext.form.TextField({
        allowBlank:true,
        name: 'id',
        id:'id_class',
        hidden:true
    });
	var name_textField = new Ext.form.TextField({
        fieldLabel: gettext('Name'),
        allowBlank:false,
        name: 'name',
        id:'name_class'
    });
	var superclass_textField = new Ext.form.TextField({
        name: 'superclass',
        id:'id_superclass_class',
        allowBlank:false,
        hidden:true
    });
	var notes_textField = new Ext.form.TextArea({
        fieldLabel: gettext('Notes'),
        allowBlank:true,
        width: 130,
        name: 'notes',
        id:'notes_class'
    });	
	//workspaces
	var sm_ws_admin = new Ext.grid.CheckboxSelectionModel({singleSelect:false});
	// create the grid
    var ws_admin_grid = new Ext.grid.GridPanel({
        id:'id_ws_admin_grid',
    	store: ws_admin_store,
        sm: sm_ws_admin,
        defaults: {
            sortable: true,
            menuDisabled: true,
            width: 100
        },
        title:gettext('Select workspaces'),
        cm: new Ext.grid.ColumnModel([
                                sm_ws_admin,
                                {id:'pk',header: "pk", width: 30, sortable: true, dataIndex: 'pk', hidden:true},
                                {id:'name',header: "Name", width: 110, sortable: true, dataIndex: 'name'},
                                {id:'description',header: "Description", width: 160, sortable: true, dataIndex: 'description'}
        ]),
        viewConfig: { //to select current ws in this grid
    		afterRender: function(){
        		this.constructor.prototype.afterRender.call(this);
        		if(id_class == 'root_obj_tree'){//adding a new root class
    				this.grid.getSelectionModel().selectRow(this.grid.getStore().findExact('pk',ws_store.getAt(ws_store.findBy(find_current_ws_record)).data.pk));
    			}else{  //adding a new class but not root_class or edit class
					var p = eval(class_data.getAt(0).data.workspaces);
					for(var k in p){
	    				this.grid.getSelectionModel().selectRow(this.grid.getStore().findExact('pk',parseInt(k)), true);
					}
    			}
    		}
    	},
        height: 150
    });
    //attributes
	var sm_attributes_grid = new Ext.grid.CheckboxSelectionModel({
		singleSelect: true,
		listeners:{
			rowselect: {fn:function(sm){
				Ext.getCmp('id_movedown_attributes_class').enable();
				Ext.getCmp('id_moveup_attributes_class').enable();
				if (sm.getSelected().data.inherited == false ){
					Ext.getCmp('id_edit_attributes_class').enable();
					Ext.getCmp('id_remove_attributes_class').enable();
				}else{
					Ext.getCmp('id_edit_attributes_class').disable();
					Ext.getCmp('id_remove_attributes_class').disable();
				}

			}},
			rowdeselect: {fn:function(sm){
				Ext.getCmp('id_edit_attributes_class').disable();
				Ext.getCmp('id_remove_attributes_class').disable();
				Ext.getCmp('id_movedown_attributes_class').disable();
				Ext.getCmp('id_moveup_attributes_class').disable();
			} }
		}
	});

	if (!add_class){
		id_textField.setValue(class_data.getAt(0).data.id);
		name_textField.setValue(class_data.getAt(0).data.name);
		notes_textField.setValue(class_data.getAt(0).data.notes);
		Ext.getCmp('details_panel').setTitle(gettext('Edit ')+name_textField.getValue()+gettext(' [class]'));
		var store_attributes_grid = store_get_class_attributes(id_class);
		var url_submit = '/api/workspace/'+ws_store.getAt(ws_store.findBy(find_current_ws_record)).data.pk+'/kb/class/'+id_class;
		superclass_textField.setValue(class_data.getAt(0).data.superclass);
		var method_request='POST';
		if(Ext.getCmp('obj_reference_tree').getNodeById(id_class).parentNode.attributes.id != 'root_obj_tree'){
			ws_admin_grid.disable();
		}
	}else{
		Ext.getCmp('details_panel').setTitle(gettext('New class'));
		var store_attributes_grid = [];
		var url_submit = '/api/workspace/'+ws_store.getAt(ws_store.findBy(find_current_ws_record)).data.pk+'/kb/class/'; 
		if (id_class != 'root_obj_tree'){
			superclass_textField.setValue(Ext.getCmp('obj_reference_tree').getSelectionModel().selNode.attributes.id);
			ws_admin_grid.disable();//only root class can be shared
		}
		var method_request='PUT';
	}

	var attributes_grid = new Ext.grid.GridPanel({
    	id: 'attribute_grid_id',
        store: store_attributes_grid,
        sm: sm_attributes_grid,
        title:gettext('Attributes'),
    	height: 180,
        cm: new Ext.grid.ColumnModel([
                                sm_attributes_grid,
                                {id:'id',header: "id", width: 30, sortable: true, dataIndex: 'id', hidden:true},
                                {id:'name',header: "Name", width: 110, sortable: true, dataIndex: 'name'},
                                {id:'type',header: "Type", width: 50, sortable: true, dataIndex: 'type'},
                                {id:'multivalued',header: "Multivalued", width: 70, sortable: false, dataIndex: 'multivalued'},
                                {id:'maybe_empty',header: "Empty", width: 50, sortable: false, dataIndex: 'maybe_empty'},
                                {id:'default_value',header: "Default", width: 60, sortable: false, dataIndex: 'default_value'},
                                {id:'min',header: "Min", width: 60, sortable: false, dataIndex: 'min'},
                                {id:'max',header: "Max", width: 60, sortable: false, dataIndex: 'max'},
                                {id:'length',header: "Length", width: 60, sortable: false, dataIndex: 'length'},
                                {id:'choices',header: "Choices", width: 60, sortable: false, dataIndex: 'choices'},
                                {id:'target_class',header: "Target Class", width: 60, sortable: false, dataIndex: 'target_class'},
                                {id:'order',header: "Order", width: 50, sortable: true, dataIndex: 'order'},
                                {id:'notes',header: "Notes", width: 150, sortable: false, dataIndex: 'notes'},
                                {id:'inherited',header: "Inherited", width: 150, sortable: false, dataIndex: 'inherited'}
        ]),
        bbar:[{
            text:'Add',
            id: 'id_add_attributes_class',
            tooltip:'Add a new attribute',
            iconCls:'add_icon',
            handler: function() {
            	add_single_attribute(false, attributes_grid, false, add_class, true);
        	}
        },'-',{
            text:'Edit',
            id: 'id_edit_attributes_class',
            tooltip:'Edit the selected row (if inherited is false)',
            iconCls:'edit_icon',
            disabled:true,
            handler: function() {
        		add_single_attribute(true, attributes_grid, false, add_class, false);
        	}
        },'-',{
            text:'Remove',
            id: 'id_remove_attributes_class',
            tooltip:'Remove the selected row',
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
        },'-',{
            text:'Move up',
            id: 'id_moveup_attributes_class',
            tooltip:'Move up the selected row',
            iconCls:'clear_icon',
            disabled:true,
            handler: function() {
                    moveSelectedRow(attributes_grid,-1);
        	}
        },'-',{
            text:'Move down',
            id: 'id_movedown_attributes_class',
            tooltip:'Move down the selected row',
            iconCls:'clear_icon',
            disabled:true,
            handler: function() {
                    moveSelectedRow(attributes_grid,1);
        	}
        }]
    });
    
    fields.push(superclass_textField);
	fields.push(id_textField);
	fields.push(name_textField);
	fields.push(notes_textField);
    fields.push(ws_admin_grid);
    fields.push(attributes_grid);
    var details_panel_class = new Ext.FormPanel({
        id:'details_panel_class',
        header : false,
        labelWidth: 110, // label settings here cascade unless overridden
        frame:true,
        bodyStyle:'padding:5px 5px 0',              
        url: url_submit,
        items: [{
        	layout:'column',
        	items:[{
        		columnWidth:.5,
                layout: 'form',
                items: [id_textField, name_textField, superclass_textField, notes_textField]
        	},{
        		columnWidth:.5,
                layout: 'form',
                items: [ws_admin_grid]
        	}]
        },{
        	xtype: 'spacer',
	  		height: 10
        },attributes_grid
        ],
        buttons: [{
            text: gettext('Save'),
            type: 'submit',
            handler: function(){
        		var my_form = this.findParentByType('form');
        		params = {};
        		params['name'] = name_textField.getValue();
        		params['notes'] = notes_textField.getValue();
        		if (id_textField.getValue()){
        			params['id'] = id_textField.getValue();
        		}
        		if(id_class != 'root_obj_tree'){
        			params['superclass'] = superclass_textField.getValue();
        		}
        		params['workspaces'] = {};
        		//owner for current ws, read-write others
        		//FIXME who is the owner?
        		for (i=0; i < ws_admin_grid.getSelectionModel().getSelections().length; i++){
        			if (ws_admin_grid.getSelectionModel().getSelections()[i].data.pk == ws_store.getAt(ws_store.findBy(find_current_ws_record)).data.pk){ //owner
        				params['workspaces'][ws_admin_grid.getSelectionModel().getSelections()[i].data.pk] = "owner";
        			}else{
        				params['workspaces'][ws_admin_grid.getSelectionModel().getSelections()[i].data.pk] = "read-write";
        			}
        		}
        		var attribute;
        		params['attributes'] = {};
        		for (i=0; i < Ext.getCmp('attribute_grid_id').getStore().getCount(); i++){
        			attribute = Ext.getCmp('attribute_grid_id').getStore().getAt(i).data;
        			params['attributes'][attribute.id] = {
        				'name': attribute.name,
        				'type': attribute.type,
        				'multivalued': attribute.multivalued,
        				'maybe_empty': attribute.maybe_empty,
        				'default_value': (isEmpty(attribute.default_value)) ? null : attribute.default_value,
        				'order': attribute.order,
        				'notes': attribute.notes
        			};
        			if (attribute.type == 'int' || attribute.type == 'date'){
        				params['attributes'][attribute.id]['min'] = (isEmpty(attribute.min)) ? null : attribute.min;
        				params['attributes'][attribute.id]['max'] = (isEmpty(attribute.max)) ? null : attribute.max;
        			}else if (attribute.type == 'string' || attribute.type == 'uri'){
        				params['attributes'][attribute.id]['length'] = (isEmpty(attribute.length)) ? null : attribute.length;
        			}else if (attribute.type == 'choice'){ 
        				params['attributes'][attribute.id]['choices'] = (isEmpty(attribute.choices)) ? null : attribute.choices;
        			}else if (attribute.type == 'objref'){ 
        				params['attributes'][attribute.id]['target_class'] = attribute.target_class; // it is mandatory
        			}
        		}
	        	if(add_class){ 
	        		Ext.Ajax.request({
	        			url:url_submit,
	        			jsonData: params,
	        			method: method_request,
	        			headers: {'Content-Type': 'application/json;charset=utf-8'},
	                    clientValidation: true,
	                    waitMsg: 'Saving...',
	                    success: function(response){
	        				//Ext.getCmp('obj_reference_tree').root.reload();
	        				//console.log(id_class);
	        				//console.log(Ext.getCmp('obj_reference_tree').getNodeById(id_class).reload());
	        				//console.log(Ext.getCmp('obj_reference_tree').getNodeById(id_class).getPath());
	        				//console.log(Ext.getCmp('obj_reference_tree').expandPath(Ext.getCmp('obj_reference_tree').getNodeById(id_class).getPath()));
	        				//Ext.getCmp('obj_reference_tree').expandPath(Ext.getCmp('obj_reference_tree').getNodeById(id_class).getPath());
	        				Ext.getCmp('obj_reference_tree').getNodeById(id_class).reload();
	        				Ext.Msg.alert('Status', 'Changes saved successfully.');
	                    	Ext.getCmp('details_panel_class').removeAll();
	                    },
	                    failure:function(response){
	                    	Ext.Msg.alert('Failure', response.responseText);
	                    }
	        		});
        		}else{
	        		Ext.Ajax.request({
	        			url:url_submit,
	        			jsonData: params,
	        			method: method_request,
	        			headers: {'Content-Type': 'application/json;charset=utf-8'},
	                    clientValidation: true,
	                    waitMsg: 'Saving...',
	                    success: function(response){
	        				//Ext.getCmp('obj_reference_tree').root.reload();
	                		if(params['superclass'] != ""){
	                			Ext.getCmp('obj_reference_tree').getNodeById(params['superclass']).reload();
	                		}else{
	                			Ext.getCmp('obj_reference_tree').getNodeById('root_obj_tree').reload();
	                		}
	                    	Ext.Msg.alert('Status', 'Changes saved successfully.');
	                    	Ext.getCmp('details_panel_class').removeAll();
	                    },
	                    failure:function(response){
	                    	Ext.Msg.alert('Failure', response.responseText);
	                    }
	        		});
        		}
        }
        },{
            text: gettext('Cancel'),
            handler: function(){
            	//clear form
            }
        }]
    });
	if (ws_permissions_store.find('name', 'admin') < 0 && ws_permissions_store.find('name', 'edit_vocabulary') < 0){
		details_panel_class.disable();
	}

	var pnl = Ext.getCmp('details_panel');
	pnl.removeAll();
	pnl.doLayout();
	pnl.add(details_panel_class);
	pnl.doLayout();
}

function update_tree_catalog(values){
	Ext.Ajax.request({
		url:'/kb/update_assosiation_treeview/',
		params:{
			id: values['id']
		},
		method: 'POST',
        clientValidation: true,
        success: function(response){
			Ext.getCmp('keywords_tree').root.reload();
        }
	});
}

/**
 * Detail Obj Panel
 */	

function load_detail_obj(obj_data, obj_id, add_obj, class_id){
	/*
	 * Load class data when class is selected on tree.
	 * @obj_data 	store obj if edit otherwise null
	 * @obj_id 		it is null if it is going to add new obj else obj_id to view and edit 
	 * @add_obj 	is true if it is going to add a new obj
	 * @class_id 	id class 
	 */
	var fields = [];
	var choices, method_request, url_submit, id_textField_value, name_textField_value, notes_textField_value, class_id_textField_value;
	var store_attributes_grid_obj;
	if (!add_obj){
		id_textField_value = obj_data.getAt(0).data.id;
		name_textField_value = obj_data.getAt(0).data.name;
		notes_textField_value = obj_data.getAt(0).data.notes;
		class_id_textField_value = obj_data.getAt(0).data.class_id;
		store_attributes_grid_obj = get_store_obj_attributes(obj_data.getAt(0).data.class_id, obj_id);
		Ext.getCmp('details_panel').setTitle(gettext('Edit ')+name_textField_value+gettext(' [object]'));
		method_request='POST';
		url_submit='/api/workspace/'+ws_store.getAt(ws_store.findBy(find_current_ws_record)).data.pk+'/kb/object/'+obj_id
	}else{
		id_textField_value = null;
		name_textField_value = null;
		notes_textField_value = null;
		class_id_textField_value = class_id;
		store_attributes_grid_obj = get_store_obj_attributes(class_id, null);
		Ext.getCmp('details_panel').setTitle(gettext('New object'));
		method_request='PUT';
		url_submit='/api/workspace/'+ws_store.getAt(ws_store.findBy(find_current_ws_record)).data.pk+'/kb/object/';
	}
	
	var id_textField = new Ext.form.TextField({
        allowBlank:true,
        name: 'id',
        value: id_textField_value, 
        id:'id_class',
        hidden: true
    });
	fields.push(id_textField);
	var name_textField = new Ext.form.TextField({
        fieldLabel: gettext('Name'),
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
	var notes_textField = new Ext.form.TextArea({
        fieldLabel: gettext('Notes'),
        allowBlank:true,
        width: 130,
        name: 'notes',
        value:notes_textField_value, 
        id:'notes_class'
    });
	fields.push(notes_textField);
    //attributes
    var attributes_grid = new Ext.grid.GridPanel({
        id:'attribute_grid_obj_id',
    	store: store_attributes_grid_obj,
        title:gettext('Attributes'),
        sm: new Ext.grid.RowSelectionModel({singleSelect: true}),
        cm: new Ext.grid.ColumnModel([
                                {id:'id',header: "id", width: 30, sortable: true, dataIndex: 'id', hidden:true},
                                {id:'name',header: "Name", width: 80, sortable: true, dataIndex: 'name'},
                                {id:'type',header: "Type", width: 50, sortable: true, dataIndex: 'type'},
                                {id:'multivalued',header: "Multivalued", width: 50, sortable: true, dataIndex: 'multivalued'},
                                {id:'maybe_empty',header: "Empty", width: 50, sortable: true, dataIndex: 'maybe_empty'},
                                {id:'value',header: "Value", width: 90, dataIndex: 'value'},
                                {id:'default_value',header: "Default", width: 70, sortable: true, dataIndex: 'default_value'},
                                {id:'choices',header: "Choices", width: 50, sortable: true, dataIndex: 'choices'},
                                {id:'target_class',header: "Target class", width: 50, sortable: true, dataIndex: 'target_class'},
                                {id:'order',header: "Order", width: 50, sortable: true, dataIndex: 'order'},
                                {id:'min',header: "Min", width: 60, sortable: false, dataIndex: 'min'},
                                {id:'max',header: "Max", width: 60, sortable: false, dataIndex: 'max'},
                                {id:'length',header: "Length", width: 60, sortable: false, dataIndex: 'length'},
                                {id:'notes',header: "Notes", width: 150, sortable: false, dataIndex: 'notes'}
                                
        ]),
        listeners: {
            'rowdblclick': function(grid, rowIndex, e){
		        var record = grid.getStore().getAt(rowIndex);  
	        	add_single_attribute(true, grid, true, false, false)
            }
        },
    	height: 220
    });
    fields.push(attributes_grid);
    var details_panel_obj = new Ext.FormPanel({
        id:'details_panel_obj',
        header: false,
        labelWidth: 110, // label settings here cascade unless overridden
        frame:true,
        bodyStyle:'padding:5px 5px 0',              
        url: method_request,
        items: [{
        	layout:'column',
        	items:[{
        		columnWidth:.5,
                layout: 'form',
                items: [name_textField]
        	},{
        		columnWidth:.5,
                layout: 'form',
                items: [notes_textField, id_textField, class_id_textField]
        	}]
        }, attributes_grid
        ],
        buttons: [{
            text: gettext('Save'),
            type: 'submit',
            handler: function(){
        		params = {};
        		params['name'] = name_textField.getValue();
        		params['notes'] = notes_textField.getValue();

        		if (id_textField.getValue()){
        			params['id'] = id_textField.getValue();
        		}
        		params['class_id'] = class_id_textField.getValue();
        		var attribute;
        		params['attributes'] = {};
        		for (var i=0; i < Ext.getCmp('attribute_grid_obj_id').getStore().getCount(); i++){
            		attribute = Ext.getCmp('attribute_grid_obj_id').getStore().getAt(i).data;
            		if (attribute.multivalued == true){//list of type
        				if (attribute.type == 'choice'){
        					params['attributes'][attribute.id] = [];
		        			choices = attribute.value.split(',');
		        			if (choices[choices.length-1] == ""){
		        				delete(choices[choices.length-1]);
		        				choices.splice(choices.length-1, 1);
		        			}
	        				params['attributes'][attribute.id] = choices;
        				}else{
        					if (attribute.value != null){
            					params['attributes'][attribute.id] = attribute.value;
        					}else {
        						params['attributes'][attribute.id] = [];
        					}
        				}
        			}else{//only one value
    					if (attribute.value != null){
    						params['attributes'][attribute.id] = attribute.value;
    					}else if(attribute.default_value != null ){
    						params['attributes'][attribute.id] = attribute.default_value;
    					}else if(attribute.maybe_empty == true){
    						params['attributes'][attribute.id] = null;
    					}
            		}
        		}
        		if (add_obj){
	        		Ext.Ajax.request({
	        			url:url_submit,
	        			jsonData: params,
	        			method: method_request,
	        			headers: {'Content-Type': 'application/json;charset=utf-8'},
	                    clientValidation: true,
	                    waitMsg: 'Saving...',
	                    success: function(response){
	        				//Ext.getCmp('obj_reference_tree').root.reload();
	        				//console.log(Ext.getCmp('obj_reference_tree').getNodeById(class_id).getPath());
	                    	//Ext.getCmp('obj_reference_tree').expandPath(Ext.getCmp('obj_reference_tree').getNodeById(class_id).getPath());
	                    	Ext.getCmp('obj_reference_tree').getNodeById(class_id).reload();
	                    	Ext.Msg.alert('Status', 'Changes saved successfully.');
	                    	Ext.getCmp('details_panel_obj').removeAll();
	                    },
	                    failure:function(response){
	                    	Ext.Msg.alert('Failure', response.responseText);
	                    }
	        		});
        		}else{
	        		Ext.Ajax.request({
	        			url:url_submit,
	        			jsonData: params,
	        			method: method_request,
	        			headers: {'Content-Type': 'application/json;charset=utf-8'},
	                    clientValidation: true,
	                    waitMsg: 'Saving...',
	                    success: function(response){
	        				//Ext.getCmp('obj_reference_tree').root.reload();
	                    	Ext.Msg.alert('Status', 'Changes saved successfully.');
	                    	Ext.getCmp('obj_reference_tree').getNodeById(params['class_id']).reload();
	                    	Ext.getCmp('details_panel_obj').removeAll();
	                    	update_tree_catalog(params);
	                    },
	                    failure:function(response){
	                    	Ext.Msg.alert('Failure', response.responseText);
	                    }
	        		});
        		}
            }
        }]
    });
	if (ws_permissions_store.find('name', 'admin') < 0 && ws_permissions_store.find('name', 'edit_vocabulary') < 0){
		details_panel_obj.disable();
	}
	var pnl = Ext.getCmp('details_panel');
	pnl.removeAll();
	pnl.doLayout();
	pnl.add(details_panel_obj);
	pnl.doLayout();
}

/**
 * Context menu
 */	
function init_contextMenuVocabulary(){
	var add_class =  new Ext.menu.Item({
		id: 'id_addClass',
		text: gettext('Class'),
		listeners:{
			click: function(item){
				init_store_class_data(item.parentMenu.parentMenu.contextNode.attributes.id, true);
			}
		}
	});
	var add_object =  new Ext.menu.Item({
		id: 'id_addObject', 
		text: gettext('Object'),
		listeners:{
			click: function(item){
				load_detail_obj(null, null, true, item.parentMenu.parentMenu.contextNode.attributes.id);
			}
		}
	});
	var add_node = new Ext.menu.Item({
		id: 'id_add', 
		text: gettext('Add'), 
		menu: [add_class, add_object]			
	});
	var delete_node = new Ext.menu.Item({
		id: 'id_delete_cls_obj', 
		text: gettext('Delete'),
		listeners:{
			click: function(item){
				var parent_node = Ext.getCmp('obj_reference_tree').getNodeById(item.parentMenu.contextNode.attributes.id).parentNode;
				if (item.parentMenu.contextNode.attributes.leaf == false){// delete a class
	        		Ext.Msg.confirm('Class Deletion', 'Class deletion cannot be undone, do you want to proceed?', 
	    	                function(btn){
	    	                    if (btn == 'yes')
	    			        		Ext.Ajax.request({
	    			        			url:'/api/workspace/'+ws_store.getAt(ws_store.findBy(find_current_ws_record)).data.pk+'/kb/class/'+item.parentMenu.contextNode.attributes.id,
	    			        			method: 'DELETE',
	    			                    clientValidation: true,
	    			                    waitMsg: 'Saving...',
	    			                    success: function(response){
	    			        				parent_node.reload();
	    			                    	Ext.Msg.alert('Status', 'Changes saved successfully.');
	    			                    	Ext.getCmp('details_panel').removeAll();
	    			                    },
	    			                    failure:function(response){
	    			                    	Ext.Msg.alert('Failure', response.responseText);
	    			                    }
	    			        		});
	    	                }
	            		);
				}else{// delete an obj
	        		Ext.Msg.confirm('Object Deletion', 'Object deletion cannot be undone, do you want to proceed?', 
	    	                function(btn){
	    	                    if (btn == 'yes')
	    			        		Ext.Ajax.request({
	    			        			url:'/api/workspace/'+ws_store.getAt(ws_store.findBy(find_current_ws_record)).data.pk+'/kb/object/'+item.parentMenu.contextNode.attributes.id,
	    			        			method: 'DELETE',
	    			                    clientValidation: true,
	    			                    waitMsg: 'Saving...',
	    			                    success: function(response){
	    			        				parent_node.reload();
	    			                    	Ext.Msg.alert('Status', 'Changes saved successfully.');
	    			                    	Ext.getCmp('details_panel').removeAll();
	    			                    },
	    			                    failure:function(response){
	    			                    	Ext.Msg.alert('Failure', response.responseText);
	    			                    }
	    			        		});
	    	                }
	            		);
				}
			}
		}
	});
	var contextMenuVocabulary = new Ext.menu.Menu({
		id:'contextMenuVocabulary',
		autoDestroy : true,
		items:[
		    add_node,
		    delete_node
		]
	});
	return contextMenuVocabulary
}

function open_knowledgeBase(){        

	ws_permissions_store.load();
/**
 * Detail Panel
 */	
	// to start with empty form
	var details_panel = new Ext.Panel({
		id:'details_panel',
		title:gettext('Details'),
	    region:'center',
	    layout:'fit'
	});
	
/**
 * Tree Panel Vocabulary on Vocabulary editor.
 */	

	var tree_loader_obj = get_treeLoader_vocabulary();
    
    var Tree_Obj_Root = get_AsyncTreeNode();

	var tree_obj_reference = new Ext.tree.TreePanel({
		id:'obj_reference_tree',
		title:gettext('Classes and Objects'),
        region:'west',
        autoDestroy : true,
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
		            var c = node.getOwnerTree().contextMenu;
					if (Ext.getCmp('obj_reference_tree').getSelectionModel().isSelected() == true || (ws_permissions_store.find('name', 'admin') < 0 && ws_permissions_store.find('name', 'edit_vocabulary') < 0)){
						c.find('text',gettext('Add'))[0].disable();
						c.find('text',gettext('Delete'))[0].disable();
					}else{
						if (node.attributes.leaf == true){
							c.find('text',gettext('Add'))[0].disable();
						}else{
							c.find('text',gettext('Add'))[0].enable();
						}
						c.find('text',gettext('Delete'))[0].enable();
					}
		            c.contextNode = node;
		            c.showAt(e.getXY());
	        }
	    },
		selModel: new Ext.tree.DefaultSelectionModel({
			listeners:{
				"selectionchange": {
					fn:function(sel, node){
						if (node){
							if (node.attributes.leaf == false){
	    						init_store_class_data(node.attributes.id, false);
							}else{
								if (node.attributes.id != 'root_obj_tree'){
									init_store_obj_data_edit(node.attributes.id, false);
								}else{
									Ext.getCmp('details_panel').removeAll();
									Ext.getCmp('details_panel').setTitle(gettext('Select a class or object to show details.'));
								}
							}
						}
					}
       			}	            		
             }
          })
	});
	tree_obj_reference.setRootNode(Tree_Obj_Root);
	
	new Ext.tree.TreeSorter(tree_obj_reference, {
	    dir: "ASC",
	    folderSort: true
	});

/**
 * reload vocabulary tree on catalogue.
 */
	function load_vocabulary_tree_on_catalogue(){
		Ext.getCmp('obj_reference_tree_catalogue').getLoader().load(Ext.getCmp('obj_reference_tree_catalogue').root);		
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
        width	: 1000,
        height	: 550,
        title	:gettext('Vocabulary'),
        modal	: true,
		resizable : false,
      	items	:[details_panel,
      	     	  tree_obj_reference
        ],
        buttons	:[{
            text: 'Close',
            handler: function() {
        		win_knowledge_base.close();
        		load_vocabulary_tree_on_catalogue()
        	},
        listeners:{
        	beforedestroy:function(){
        		load_vocabulary_tree_on_catalogue()
        		Ext.getCmp('contextMenuVocabulary').destroy();
        	}
        }
        }]
    });
	var ws_record = ws_store.getAt(ws_store.findBy(find_current_ws_record));
	win_knowledge_base.show();  
}
