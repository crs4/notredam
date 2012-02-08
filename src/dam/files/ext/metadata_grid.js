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

Ext.form.LanguageField = Ext.extend(Ext.form.TextArea, {
    store: {},
    setValue: function(v) {
    	
    		
        if (!this.store) {
		    this.store = {};
        }
        var metadata_grid = this.grid;
        var lang = metadata_grid.language;
        this.store[lang] = v;
               
        if (v != ''){
        	var record_choices = metadata_grid.getStore().getAt(this.row).get('choices');
        	record_choices[lang] = v;
        	
        	metadata_grid.getStore().getAt(this.row).set('choices', record_choices);
    		metadata_grid.getStore().getAt(this.row).set('value', v);
	        Ext.form.TextArea.superclass.setValue.call(this, v);
        }
    }
});


Ext.form.CustomField = Ext.extend(Ext.form.TextField, {
    store: {},
    type: 'text',
    choice_type: false,
    choices: {},
    array: false,
    field_value: null,
	is_structure: false,
    is_choice: 'not_choice',

    generateFormField: function(field) {

        var field_def = [];

        if (field.type == 'date') {
            field_def.push({
                fieldLabel: field.name,
                name: field.id,
                xtype: 'datefield',
                selectOnFocus: true,
                format: 'm/d/Y',
                altFormats: 'd/m/Y|n/j/Y|n/j/y|m/j/y|n/d/y|m/j/Y|n/d/Y|m-d-y|m-d-Y|m/d|m-d|md|mdy|mdY|d|Y-m-d|Y/m/d'
            });
        }
        else if (field.type == 'date_and_time') {
            field_def.push(new Ext.ux.form.DateTime({
                fieldLabel: field.name,
                name: field.id,
                timeFormat: 'H:i:s',
                hiddenFormat:'m/d/Y H:i:s',
                timeConfig: {
                    altFormats: 'g:i:s',
                    allowBlank: true
                },
                dateFormat: 'm/d/Y',
                dateConfig: {
                    altFormats: 'm/d/Y|n/j/Y|n/j/y|m/j/y|n/d/y|m/j/Y|n/d/Y|m-d-y|m-d-Y|m/d|m-d|md|mdy|mdY|d|Y-m-d|Y/m/d',
                    allowBlank: true
                }
            }));
        }
        else if (field.type == 'number') {
            field_def.push({
                fieldLabel: field.name,
                name: field.id,
                xtype: 'numberfield'
            });
        }
        else if (field.type == 'boolean') {
            field_def.push({
                fieldLabel: field.name,
                name: field.id,
                xtype: 'booleanfield'
            });
        }
        else if (field.type in metadata_structures) {
            var field_list = [];
            for (var x = 0; x < metadata_structures[field.type].length; x++) {
                field_list.push(this.generateFormField(metadata_structures[field.type][x])[0]);
            }
            field_def = [{
                title: field.name,
                xtype: 'fieldset',
                autoHeight: true,
                items: field_list
            }];
        }
        else {
            field_def.push({
                fieldLabel: field.name,
                name: field.id,
                xtype: 'textfield'
            });
        }
        return field_def;
    },

    editField: function() {

        var this_field = this;
		var sm;
		var c, i, x;

        this.form_items = this.generateFormField({
            name: this.title,
            type: this.type,
            id: this.field_id
        });

        var fields_list = [];

		var fieldset = this.form_items;
		
		while (fieldset[0].xtype == 'fieldset') {
			fieldset = fieldset[0].items;
			this.is_structure = true;
		}
		
        for (c = 0; c < fieldset.length; c++) {
            if (fieldset[c].xtype != 'fieldset') {
                fields_list.push({
                    name: fieldset[c].name
                });
            }
        }
		
        var RecordValue = Ext.data.Record.create(fields_list);

        var grid_store = new Ext.data.SimpleStore({
            fields: fields_list
        });
				
        if (this.array) {

            var column_list = [];
			
			if (this.is_choice != 'not_choice') {
				sm = new Ext.grid.CheckboxSelectionModel();
				column_list.push(sm);
			}
			else {
				sm = new Ext.grid.RowSelectionModel();		
//				column_list.push(new Ext.grid.RowNumberer());
			}
						
            for (c = 0; c < fieldset.length; c++) {
                if (fieldset[c].xtype != 'fieldset') {
					if (column_list.length < 3) {
	                    column_list.push({
	                        header: fieldset[c].fieldLabel,
	                        dataIndex: fieldset[c].name,
						    menuDisabled:true,
//				            width: .30,
							sortable: false
	                    });
					}
                }
            }
			
            var cm = new Ext.grid.ColumnModel(column_list);

			if (this.is_choice != 'not_choice') {

				for (i = 0; i < this.choices.length; i++) {
					var r = new RecordValue();
					r.set(fields_list[0].name, this.choices[i]);
					r.commit();
					grid_store.add(r);
				}
				
			}
			else {
				if (this.field_value) {
					for (i = 0; i < this.field_value.getCount(); i++) {		
//						var r = new RecordValue();
//						r.set(fields_list[0].name, this.field_value.getAt(i).get(fields_list[0].name));
//						r.commit();
						var r = this.field_value.getAt(i);
						grid_store.add(r);
					}
				}
				else {
					for (i = 0; i < this.store.length; i++) {
						var r = new RecordValue();
						if (this.is_structure) {
							for (var x=0; x < fields_list.length; x++) {
								r.set(fields_list[x].name, this.store[i][fields_list[x].name]);
							}
						}
						else {
							r.set(fields_list[0].name, this.store[i]);
						}
						r.commit();
						grid_store.add(r);
					}
				}
				
			}

			var records_to_select = [];
			var r_id, r;
			
			if (this_field.is_choice != 'not_choice') {

				if (this_field.field_value) {
					for (i = 0; i < this_field.field_value.getCount(); i++) {
						r_id = grid_store.find(fields_list[0].name, this_field.field_value.getAt(i).get(fields_list[0].name));
						r = grid_store.getAt(r_id);
						records_to_select.push(r);
					}
				}
				else {
					for (i = 0; i < this_field.store.length; i++) {
						r_id = grid_store.find(fields_list[0].name, this.store[i]);
						if (r_id == -1) {
							r = new RecordValue();
							if (this_field.is_structure) {
								for (x=0; x < fields_list.length; x++) {
									r.set(fields_list[x].name, this_field.store[i][fields_list[x].name]);
								}
							}
							else {
								r.set(fields_list[0].name, this_field.store[i]);
							}
							r.commit();						
							grid_store.add(r);
						}
						else {
							r = grid_store.getAt(r_id);
						}
						records_to_select.push(r);
					}					
				}
			}			

			var grid_conf = {
				viewConfig: {
			        forceFit: true
			    },
				deferRowRender: false,
		        store: grid_store,
                columns: column_list,
				id: 'customfieldgrid',
				listeners: {
					afterrender: function() {
					    var listview = this;
						if (this_field.is_choice != 'not_choice') {
							listview.getSelectionModel().selectRecords(records_to_select);
						}
						else {
							var ddrow = new Ext.dd.DropTarget(listview.getView().mainBody, {  
							    ddGroup : 'customfield-dd',  
							    notifyDrop : function(dd, e, data){  
							        var sm = listview.getSelectionModel();  
							        var rows = sm.getSelections();  
							        var cindex = dd.getDragData(e).rowIndex;  
							        if (sm.hasSelection()) {  
							            for (i = 0; i < rows.length; i++) {  
							                grid_store.remove(grid_store.getById(rows[i].id));  
							                grid_store.insert(cindex,rows[i]);  
							            }  
							            sm.selectRecords(rows);
							        }    
							    }  
							});
						}
					}
				}
		    };

			if (this.is_choice == 'not_choice') {
				grid_conf.enableDrag = true;
				grid_conf.ddGroup = 'customfield-dd';
				grid_conf.ddText = 'Change order';
				grid_conf.sm = sm;
			}

		    var listview = new Ext.grid.GridPanel(grid_conf);

			var open_dynamic_form = function(loadRecord) {
				
                var doAdd = function() {
					var f_items = this_field.form_items;
                    var values = Ext.getCmp('customFieldForm').getForm().getFieldValues();
					if (loadRecord) {
						for (v in values) {
							loadRecord.set(v, values[v]);
						}
						loadRecord.commit();
						Ext.getCmp('customFieldForm').ownerCt.close();                        
					}
					else {
	                    listview.getStore().add(new RecordValue(values));
						Ext.getCmp('customFieldForm').getForm().reset();
					}
				};
				
				var b_caption;
				
				if (loadRecord) {
					b_caption = gettext('Save changes');
				}
				else {
					b_caption = gettext('Add');
				}

	            var form_panel = new Ext.FormPanel({
					id: 'customFieldForm',
	                frame: true,
	                labelWidth: 150,
	                items: this_field.form_items,
	                height: 200,
                    autoScroll: true,
					keys: {	
					 key: Ext.EventObject.ENTER,
					 fn: doAdd
					},
	                buttons: [{
	                    text: b_caption,
	                    handler: doAdd
	                },
	                {
	                    text: gettext('Close'),
	                    handler: function() {
	                        this.ownerCt.ownerCt.ownerCt.close();
	                    }
	                }],
					listeners: {
						render: function() {
							if (loadRecord) {
								form_panel.getForm().loadRecord(loadRecord);
                            }
						}
					} 
	
	            });


                var new_win = new Ext.Window({
                    title: 'New Entry',
                    constrain: true,
                    resizable: false,
                    closable: true,
                    modal: true,
                    layout: 'fit',
                    width: 500,
                    items: [form_panel]

                });

                new_win.show();
			};

		    var tbar = [{
				
                text: gettext('Add'),
                iconCls: 'add_icon',
                handler: function() {
					open_dynamic_form();
                }
            },
            {
                text: gettext('Clear'),
                iconCls: 'clear_icon',
                handler: function() {
						var selection = listview.getSelectionModel().getSelections();
						for (s in selection) {
							listview.getStore().remove(selection[s]);
						}
                    }
            }];

			if (this.is_choice == 'not_choice') {
				var edit_row = function(record) {
					if (record) {
						open_dynamic_form(record);
					}
					else {
						var selection = listview.getSelectionModel().getSelections()[0];
						if (selection) {
							open_dynamic_form(selection);
						}
					}
                };

				listview.on('rowdblclick', function(sm, index, record){
					edit_row();
				});
				
				tbar.splice(1, 0, {
	                text: gettext('Edit'),
	                iconCls: 'edit_icon',
	                handler: function() {
						edit_row();
					}
	            });
			}

			var panel_config = {
				height: 300,
				width: 500,
			    layout:'fit',
			    items: listview,
				title: '  ',
                buttons: [{
                    text: gettext('Save'),
					handler: function() {
                        var value_string = '';
                        var new_value, r, i;
						if (this_field.is_choice == 'not_choice') {
							this_field.field_value = listview.getStore();
							for (i = 0; i < this_field.field_value.getCount(); i++) {
		                        r = this_field.field_value.getAt(i);
								new_value = r.get(r.fields.keys[0]);
		                        value_string += new_value + ",";
		                    }
		
		                    this_field.grid.getStore().getAt(this_field.row).set('value', value_string);
		                    this_field.grid.getStore().getAt(this_field.row).set('multiplevalues', false);

						}
						else {
							var new_store = new Ext.data.SimpleStore({
				                fields: fields_list
				            });
							new_store.add(listview.getSelectionModel().getSelections());
							this_field.field_value = new_store;
							for (i = 0; i < this_field.field_value.getCount(); i++) {
		                        r = this_field.field_value.getAt(i);
								new_value = r.get(r.fields.keys[0]);
		                        value_string += new_value + ",";
		                    }
				
							this_field.choices = [];
		
							for (i = 0; i < listview.getStore().getCount(); i++) {
		                        r = listview.getStore().getAt(i);
								new_value = r.get(r.fields.keys[0]);
								this_field.choices.push(new_value);
		                    }

							this_field.grid.getStore().getAt(this_field.row).set('value', value_string);
		                    this_field.grid.getStore().getAt(this_field.row).set('multiplevalues', false);				
						}
						this.ownerCt.ownerCt.ownerCt.close();                        
					}
                },
                {
                    text: gettext('Cancel'),
                    handler: function() {
                        this.ownerCt.ownerCt.ownerCt.close();
                    }
                }]
			};

			if (this.is_choice != 'close_choice') {
				panel_config['tbar'] = tbar;
			}

			var panel = new Ext.Panel(panel_config);
			
			if (this.is_choice != 'not_choice') {

				panel.setTitle('Select items from the list below');
				
			    listview.getSelectionModel().on('selectionchange', function(view){
			        var l = view.getCount();
			        var s = l != 1 ? 's' : '';
			        panel.setTitle('Select items from the list below: <i>('+l+' item'+s+' selected)</i>');
			    });
			}
/*            var panel = new Ext.grid.GridPanel({
                store: grid_store,
                cm: cm,
                title: 'Values',
                layout: 'fit',
                height: 500,
            });
*/
        }
        else {

			grid_store.removeAll();
		
            var panel = new Ext.FormPanel({
                frame: true,
                labelWidth: 150,
                items: this.form_items,
                autoScroll: true,
				listeners: {
					render: function() {
					    var i, r, x, field_dict;
						if (this_field.field_value) {
							for (i = 0; i < this_field.field_value.getCount(); i++) {		
								r = this_field.field_value.getAt(i);
								field_dict = {};
								for (x=0; x < 1; x++) {
									field_dict[r.fields.keys[x]] = r.get(r.fields.keys[x]);
								}
								panel.getForm().loadRecord(r);
							}
						}
						else {
							for ( i = 0; i < 1; i++) {
								r = new RecordValue(this_field.store[i]);
								grid_store.add(r);
								panel.getForm().loadRecord(r);								
							}
						}
						
						
					}
				},
				
                buttons: [{
                    text: gettext('Save'),
                    handler: function() {
                        var values = this.ownerCt.ownerCt.form.getFieldValues();
						grid_store.removeAll();
						grid_store.add(new RecordValue(values));
						this_field.field_value = grid_store;
						var value_string = '';
						var r, new_value, i;
						for (i = 0; i < this_field.field_value.getCount(); i++) {
							r = this_field.field_value.getAt(i);
							new_value = r.get(r.fields.keys[0]);
							value_string += new_value + ",";
						}
						this_field.grid.getStore().getAt(this_field.row).set('value', value_string);
	                    this_field.grid.getStore().getAt(this_field.row).set('multiplevalues', false);				
						
						this.ownerCt.ownerCt.ownerCt.close();

                    }
                },
                {
                    text: gettext('Cancel'),
                    handler: function() {
                        this.ownerCt.ownerCt.ownerCt.close();
                    }
                }]
            });

        }	

        var win = new Ext.Window({
            title: this.title,
            constrain: true,
            resizable: false,
            closable: true,
            modal: true,
            layout: 'fit',
            width: 500,
            height: 300,
            items: [panel]
        });

        win.show();

    }
});

Ext.grid.MetadataRecord = Ext.data.Record.create([
{
    name: 'name'
},
{
    name: 'value'
},
{
    name: 'groupname'
},
{
    name: 'type'
},
{
    name: 'multiplevalues',
    type: 'boolean'
},
{
    name: 'array',
    type: 'boolean'
},
{
    name: 'tooltip'
},
{
    name: 'choices'
},
{
    name: 'id'
},
{
    name: 'editable'
},
{
    name: 'is_variant',
    type: 'boolean'
},
{
    name: 'is_choice'
}
]);

Ext.grid.MetadataReader = new Ext.data.JsonReader({
    root: "rows"
},
Ext.grid.MetadataRecord);

//----------------------------------------
Ext.grid.MetadataRecordObj = Ext.data.Record.create([
{
    name: 'name'
},
{
    name: 'value'
},
{
    name: 'groupname'
}
]);

Ext.grid.MetadataReaderObj = new Ext.data.JsonReader({
    root: "rows"
},
Ext.grid.MetadataRecordObj);

Ext.grid.MetadataStoreObj = function(grid) {
    this.grid = grid;
    this.store = new Ext.data.GroupingStore({
        reader: Ext.grid.MetadataReaderObj,
        sortInfo: {
            field: 'name',
            direction: "ASC"
        },
        groupField: 'groupname',
        url: '/kb/get_hierarchy/',
        recordType: Ext.grid.MetadataRecordObj,
        listeners: {
            beforeload: function(store, options) {
                var metadata_grid = Ext.getCmp('obj_metadata_panel');
                store.baseParams.obj = metadata_grid.variant;
            }
        }

    });
    Ext.grid.MetadataStoreObj.superclass.constructor.call(this);
};

Ext.extend(Ext.grid.MetadataStoreObj, Ext.util.Observable, {

    // private
    getProperty: function(row) {
        return this.store.getAt(row);
    },

    // private
    isEditableValue: function(val) {
        return false;
    },

    // private
    setValue: function(prop, value) {
        this.store.getById(prop).set('value', value);
    }

});


//-----------------------------

Ext.grid.MetadataStore = function(grid, advanced) {
    this.grid = grid;
    this.store = new Ext.data.GroupingStore({
        baseParams: {
            advanced: advanced
        },
        reader: Ext.grid.MetadataReader,
        sortInfo: {
            field: 'name',
            direction: "ASC"
        },
        groupField: 'groupname',
        url: '/get_metadata/',
        //        autoLoad: true,
        recordType: Ext.grid.MetadataRecord,
        saveChangedRecords: function(grid, options) {
            var save_url = '/save_descriptors/';
            if (this.baseParams.advanced) {
                save_url = '/save_metadata/';
            }

            if (this.getModifiedRecords().length > 0) {
                var last_items;

                if (options) {
                    last_items = options.params.old_items;
                }
                else {
                    last_items = this.lastOptions.items;
                }
                var store = this;
                    
                Ext.MessageBox.show({
                    title: gettext('Save Changes?'),
                    msg: gettext('You are closing the metadata tab that has unsaved changes. <br />Would you like to save your changes?'),
                    buttons: Ext.MessageBox.YESNO,
                    fn: function(button) {

                        var params;

                        if (options) {
                            params = options;
                        }
                        else {
                            params = store.lastOptions;
                        }
                        params['ignore'] = true;
                        if (button == 'no') {
                            store.rejectChanges();
                            grid.customEditors = {};
                            store.load(params);
                        }
                        if (button == 'yes') {

                        	grid.saveMetadata(save_url, last_items, params);
                            
                        }
                    },
                    animEl: 'mb4',
                    icon: Ext.MessageBox.QUESTION
                });
                                                
                return false;
            }
            else {
                grid.customEditors = {};
            }
            
            return true;
        
        },
        listeners: {
            beforeload: function(store, options) {
                if (options.ignore) {
                    return true;
                }
                var metadata_grid_id = 'metadata_panel';
                if (store.baseParams.advanced) {
                    metadata_grid_id = 'xmp_panel';
                }
                var metadata_grid = Ext.getCmp(metadata_grid_id);
                store.baseParams.obj = metadata_grid.variant;

                var event = store.saveChangedRecords(metadata_grid, options);
                return event;
            }
        }

    });
    Ext.grid.MetadataStore.superclass.constructor.call(this);
};

Ext.extend(Ext.grid.MetadataStore, Ext.util.Observable, {

    // private
    getProperty: function(row) {
        return this.store.getAt(row);
    },

    // private
    isEditableValue: function(val) {
        if (Ext.isDate(val)) {
            return true;
        } else if (typeof val == 'object' || typeof val == 'function') {
            return false;
        }
        return true;
    },

    // private
    setValue: function(prop, value) {
        this.store.getById(prop).set('value', value);
    }

});


Ext.grid.MetadataColumnModel = function(grid, store, expander) {
    this.grid = grid;
    var g = Ext.grid;
    g.MetadataColumnModel.superclass.constructor.call(this, [
	expander,
    {
        id: 'name',
        header: "Metadata",
        width: 40,
        sortable: true,
        dataIndex: 'name'
    },
    {
        header: "Value",
        width: 60,
        sortable: true,
        dataIndex: 'value'
    },
    {
        header: "Schemas",
        width: 20,
        dataIndex: 'groupname'
    }
    ]);
    this.store = store;

	this.expander = expander;

    var f = Ext.form;

    this.editors = {
        'date': new g.GridEditor(new f.DateField({
            selectOnFocus: true,
            format: 'm/d/Y',
			altFormats: 'd/m/Y|n/j/Y|n/j/y|m/j/y|n/d/y|m/j/Y|n/d/Y|m-d-y|m-d-Y|m/d|m-d|md|mdy|mdY|d|Y-m-d|Y/m/d'
        })),
        'string': new g.GridEditor(new f.TextField({
            selectOnFocus: true
        })),
        'number': new g.GridEditor(new f.NumberField({
            selectOnFocus: true,
            style: 'text-align:left;'
        })),
        'boolean': new g.GridEditor(new f.ComboBox({
            triggerAction: 'all',
            typeAhead: true,
            selectOnFocus: true,
            store: ['yes', 'no']
        })),
        'date_and_time': new g.GridEditor(new Ext.ux.form.DateTime({
            timeFormat: 'H:i:s',
            hiddenFormat:'m/d/Y H:i:s',
            timeConfig: {
                altFormats: 'g:i:s',
                allowBlank: true
            },
            dateFormat: 'm/d/Y',
            dateConfig: {
				altFormats: 'm/d/Y|n/j/Y|n/j/y|m/j/y|n/d/y|m/j/Y|n/d/Y|m-d-y|m-d-Y|m/d|m-d|md|mdy|mdY|d|Y-m-d|Y/m/d',
                allowBlank: true
            }
        }))
    };
    this.renderCellDelegate = this.renderCell.createDelegate(this);
    this.renderPropDelegate = this.renderProp.createDelegate(this);
	this.renderExpander = this.expander.renderer.createDelegate(this);
};

Ext.extend(Ext.grid.MetadataColumnModel, Ext.grid.ColumnModel, {
    // private - strings used for locale support
    nameText: 'Name',
    valueText: 'Value',
    dateFormat: 'd M Y',
    datetimeFormat: 'd M Y H:i:s',
    sortInfo: {
        field: 'name'
    },

    // private
    renderDate: function(dateVal) {
        return dateVal.dateFormat(this.dateFormat);
    },

    // private
    renderDateTime: function(dateVal) {
        return dateVal.dateFormat(this.datetimeFormat);
    },

    // private
    renderBool: function(bVal) {
        return bVal ? 'true': 'false';
    },

    // private
    isCellEditable: function(colIndex, rowIndex) {
        var p = this.store.getProperty(rowIndex);
        var editable = p.data['editable'];

        return colIndex == 2 && editable;
    },

    // private
    getRenderer: function(col) {
		if (col == 0) {
			return this.renderExpander ;
		} else if (col == 1) {
			return this.renderPropDelegate;
		}
		else {
			return this.renderCellDelegate;
		}
    },

    // private
    renderProp: function(v, metadata, record, rowIndex, colIndex, store) {
        var p = this.store.getProperty(rowIndex);
        var editable = p.data['editable'];
        var type = p.data['type'];
        var is_variant = p.data['is_variant'];
        if (colIndex == 1) {
            var prop_name = '';
            if (editable) {
                prop_name = this.getPropertyName(v);
            }
            else {
                prop_name = "<i>" + this.getPropertyName(v) + "</i>";
            }
            if (type == 'lang') {
                prop_name = prop_name + '<img style="margin-left: 3px; position: relative; vertical-align: middle;" src="/files/images/language_icon.png"/>';
            }
            if (is_variant) {
                prop_name = prop_name + '<img style="margin-left: 2px; position: relative; vertical-align: middle;" src="/files/images/variant_icon.png"/>';
            }
            return prop_name;
        }
        else {
            return this.getPropertyName(v);
		}
    },

    // private
    renderCell: function(val, metadata, record, rowIndex, colIndex, store) {
        var p = this.store.getProperty(rowIndex);
        var n = p.data['id'];
        var type = p.data['type'];
        var rv = val;
        var editable = p.data['editable'];
        var choices = p.data['choices'];
        var multiple = p.data['multiplevalues'];
		var is_choice = p.data['is_choice'];
        var generated_html = '';
        var cell_store;
        if (multiple) {
            return '<b>(multiple values)</b>';
        }
        else if (this.grid.customEditors[n]) {
            if (type != 'lang') {
                if (is_choice == 'close_choice' && !p.data['array']) {
                    var combo = this.grid.customEditors[n].field;
                    var rec = combo.findRecord(combo.valueField, val);
                    var value = rec ? rec.get(combo.displayField) : '';
                    return Ext.util.Format.htmlEncode(value);
                }
                else {
					if (this.grid.customEditors[n].field.is_structure) {
						generated_html = '<b>(structure...)</b>';
					}
					else {
	                    generated_html = '<div style="overflow: auto;">';
	                    cell_store = this.grid.customEditors[n].field.field_value;
                        if (cell_store) {
                            for (var i = 0; i < cell_store.getCount(); i++) {
                                var r = cell_store.getAt(i);
                                generated_html += '<div>' + r.get(r.fields.keys[0]) + '</div>';
                            }
                        }
	                    generated_html += '</div>';
					}
                }
            }
            else {
                cell_store = this.grid.customEditors[n].field.store;
                if (cell_store[this.grid.language]) {
                    generated_html = '<div style="overflow: auto; white-space:normal;">';
                    generated_html += '' + cell_store[this.grid.language] + '';
                    generated_html += '</div>';
                }
            }
            return generated_html;
        } else if (Ext.isDate(val)) {
            if (type == 'date') {
                rv = this.renderDate(val);
            }
            else if (type == 'date_and_time') {
                rv = this.renderDateTime(val);
            }
        } else if (type == 'lang') {
            for (var lang in choices) {
                if (lang == this.grid.language) {
                    generated_html = '<div style="overflow: auto; white-space:normal;">';
                    generated_html += '' + choices[this.grid.language] + '';
                    generated_html += '</div>';
                }
            }
            if (generated_html) {
                return generated_html;
            }
            else {
                rv = "";
            }
        } else if (is_choice == 'open_choice' || p.data['array'] == true || type in metadata_structures) {
            if (val == "") {
                rv = val;
            }
            else {
                if (type in metadata_structures) {
                    return '<b>(structure...)</b>';
                }
                else {
	                generated_html = '<div style="overflow: auto;">';
	                for (var i = 0; i < val.length; i++) {
	                    generated_html += '<div>' + val[i] + '</div>';
                    }
	                generated_html += '</div>';
	                return generated_html;
	            }

            }
        }

        return Ext.util.Format.htmlEncode(rv);
    },

    getMetadataValues: function() {
        var metadata_values = {};
        var modified_list = this.store.store.getModifiedRecords();
        for (var i = 0; i < modified_list.length; i++) {
            var p = modified_list[i];
            var n = p.data['id'];
            var type = p.data['type'];
            var rv = p.data['value'];
	        var is_choice = p.data['is_choice'];
	        var cell_store;
            if (this.grid.customEditors[n]) {
                var tmp = [];
                if (type != 'lang') {
                    if (is_choice == 'close_choice' && !p.data['array']) {
                        metadata_values[n] = this.grid.customEditors[n].getValue();
                    }
                    else {
                        cell_store = this.grid.customEditors[n].field.field_value;
                        for (var x = 0; x < cell_store.getCount(); x++) {
                            var r = cell_store.getAt(x);
                            if (r.fields.keys.length == 1) {
                                tmp.push(r.get(r.fields.keys[0]));
                            }
                            else {
                                var field_struct = {};

                                for (var f=0; f < r.fields.keys.length; f++) {
                                	var r_value = r.get(r.fields.keys[f]);
                                    if (Ext.isDate(r_value)) {
                                        r_value = r_value.dateFormat('m/d/Y');
                                    }
                                    field_struct[r.fields.keys[f]] = r_value;
                                }
                                
                                tmp.push(field_struct);
							}
						}
                        if(cell_store.getCount() == 0 && modified_list.length > 0){ // empty list for each metadata modified_list
                        	metadata_values[n] = [];
                        }
                    }
                }
                else {
                    cell_store = this.grid.customEditors[n].field.store;
                    for (var lang in cell_store) {
                        tmp.push([cell_store[lang], lang]);
                    }
                }
                if (tmp.length > 0) {
                    metadata_values[n] = tmp;
                }
            } else {
                if (rv != "") {
                    if (type == 'date_and_time') {
                        if (Ext.isDate(rv)) {
                            metadata_values[n] = rv.dateFormat('m/d/Y H:i:s');
                        }
                    }
                    else if (type == 'date') {
                        if (Ext.isDate(rv)) {
                            metadata_values[n] = rv.dateFormat('m/d/Y');
                        }
                    }
                    else {
                        metadata_values[n] = rv;
                    }
                }
            }
        }
        return metadata_values;
    },


    // private
    getPropertyName: function(name) {
        var pn = this.grid.propertyNames;
        return pn && pn[name] ? pn[name] : name;
    },

    // private
    getCellEditor: function(colIndex, rowIndex) {
        var p = this.store.getProperty(rowIndex);
        var n = p.data['id'];
        var type = p.data['type'];
        var title = p.data['name'];
        var is_array = p.data['array'];
        var choices = p.data['choices'];
        var is_choice = p.data['is_choice'];

        if (this.grid.customEditors[n]) {
            return this.grid.customEditors[n];
        }

		if (type == 'lang') {
        //            this.grid.customEditors[n] = new Ext.grid.GridEditor(new Ext.form.MetadataArrayField({title: title, triggerAction: 'all', typeAhead: true, selectOnFocus: true, store: p.data['value'], field_type: type, choices: p.data['choices'], 'grid': this.grid, 'row': rowIndex}));
	        this.grid.customEditors[n] = new Ext.grid.GridEditor(new Ext.form.LanguageField({
	            grid: this.grid,
	            selectOnFocus: true,
	            store: p.data['choices'],
	            'row': rowIndex
	        }));
	        this.grid.customEditors[n].on('beforecomplete',
            function(editor, value, startValue) {
                editor.setValue(value);
            });
			return this.grid.customEditors[n];
        }
        else if (is_choice == 'close_choice' && !is_array) {
			this.grid.customEditors[n] = new Ext.grid.GridEditor(new Ext.form.ComboBox({
                triggerAction: 'all',
                typeAhead: true,
                selectOnFocus: true,
                mode: 'local',
                valueField: 'data_value',
                displayField: 'display_text',
				lazyRender: true,
                store: new Ext.data.ArrayStore({
                    fields: ['data_value', 'display_text'],
                    data: p.data['choices']
                })
            }));
			return this.grid.customEditors[n];
	    }	
        else if ((is_array && type != 'lang' ) || type in metadata_structures) {

            this.grid.customEditors[n] = new Ext.grid.GridEditor(new Ext.form.CustomField({
                title: title,
                type: type,
                array: is_array,
                choices: choices,
                grid: this.grid,
                selectOnFocus: true,
                store: p.data['value'],
                'row': rowIndex,
                field_id: n,
                is_choice: is_choice
            }));
            this.grid.customEditors[n].on('startedit',
            function() {
                this.field.editField();
            });
            return this.grid.customEditors[n];

        }
        else if (type == 'date') {
            return this.editors['date'];
        } else if (type == 'date_and_time') {
            return this.editors['date_and_time'];
        } else if (type == 'int') {
            return this.editors['number'];
        } else if (type == 'bool') {
            return this.editors['boolean'];
        }
        else {
           return this.editors['string'];
       }

    }
});

Ext.ToolTip.prototype.onTargetOver =
    Ext.ToolTip.prototype.onTargetOver.createInterceptor(function(e) {
        this.baseTarget = e.getTarget();
    });
Ext.ToolTip.prototype.onMouseMove =
    Ext.ToolTip.prototype.onMouseMove.createInterceptor(function(e) {
        if (!e.within(this.baseTarget)) {
            this.onTargetOver(e);
            return false;
        }
    });

//---------------------------------------
Ext.grid.MetadataGridObj = Ext.extend(Ext.grid.GridPanel, {

    // private config overrides
    enableColumnMove: false,
    clicksToEdit: 1,
    enableHdMenu: false,
    loadMask: true,
    language: 'en-US',
    variant: 'original',
    hideHeaders: true,
    trackMouseOver: false,
    stripeRows: true,
    // private
    initComponent: function() {
        this.customEditors = this.customEditors || {};
        this.lastEditRow = null;
        var store = new Ext.grid.MetadataStoreObj(this);
        this.propStore = store;
		this.expander = new Ext.ux.grid.RowExpander({
	        tpl : new Ext.XTemplate(
				'<tpl for=".">',
				'<br/>',
				'<tpl for=".">',				
			    '<p style="padding-left: 15px; padding-bottom: 2px;"><b>',
                                '{[gettext(values.caption)]}',
                                ':</b>',
				'<span>{value}</span></p>',
				'</tpl>',
				'</tpl>'
	        ),
			listeners: {
				beforeexpand: function(re, record, body, rowIndex) {
					if (!record.get('type') in metadata_structures) {
						return false;
					}
					else {
						if (record.get('value') == '') {
							return false;
						}
					}
				}
			}
	    });
        var cm = new Ext.grid.MetadataColumnModel(this, store, this.expander);
        this.cm = cm;
        this.ds = store.store;
		this.plugins = this.expander;
        Ext.grid.MetadataGrid.superclass.initComponent.call(this);

        this.selModel.on('beforecellselect',
        function(sm, rowIndex, colIndex) {
            if (colIndex === 0) {
                this.startEditing.defer(200, this, [rowIndex, 1]);
                return false;
            }
        },
        this);
    },
    onRender: function() {
        Ext.grid.EditorGridPanel.prototype.onRender.apply(this, arguments);
    }
});
//---------------------------------------
Ext.grid.MetadataGrid = Ext.extend(Ext.grid.EditorGridPanel, {

    // private config overrides
    enableColumnMove: false,
    clicksToEdit: 1,
    enableHdMenu: false,
    loadMask: true,
    language: 'en-US',
    variant: 'original',
    hideHeaders: true,
    trackMouseOver: false,
    advanced: false,
    stripeRows: true,
    // private
    initComponent: function() {
        this.customEditors = this.customEditors || {};
        this.lastEditRow = null;
        var store = new Ext.grid.MetadataStore(this, this.advanced);
        this.propStore = store;
		this.expander = new Ext.ux.grid.RowExpander({
	        tpl : new Ext.XTemplate(
				'<tpl for=".">',
				'<br/>',
				'<tpl for=".">',				
			    '<p style="padding-left: 15px; padding-bottom: 2px;"><b>',
                                '{[gettext(values.caption)]}',
                                ':</b>',
				'<span>{value}</span></p>',
				'</tpl>',
				'</tpl>'
	        ),
			listeners: {
				beforeexpand: function(re, record, body, rowIndex) {
					if (!record.get('type') in metadata_structures) {
						return false;
					}
					else {
						if (record.get('value') == '') {
							return false;
						}
					}
				}
			}
	    });
        var cm = new Ext.grid.MetadataColumnModel(this, store, this.expander);
        this.cm = cm;
        this.ds = store.store;
		this.plugins = this.expander;
        Ext.grid.MetadataGrid.superclass.initComponent.call(this);

        this.selModel.on('beforecellselect',
        function(sm, rowIndex, colIndex) {
            if (colIndex === 0) {
                this.startEditing.defer(200, this, [rowIndex, 1]);
                return false;
            }
        },
        this);
    },
    onRender: function() {
        Ext.grid.EditorGridPanel.prototype.onRender.apply(this, arguments);
        this.addEvents("beforetooltipshow");
        this.tooltip = new Ext.ToolTip({
            renderTo: Ext.getBody(),
            target: this.view.mainBody,
            anchor: 'right',
            trackMouse: true,
            listeners: {
                beforeshow: function(qt) {
                    var v = this.getView();
                    var row = v.findRowIndex(qt.baseTarget);
                    return this.fireEvent("beforetooltipshow", this, row);
                },
                scope: this
            }
        });
    },
    saveMetadata: function(url, items, new_params) {
        this.getEl().mask('Saving metadata...');
        var values = this.getColumnModel().getMetadataValues();
        var conn = new Ext.data.Connection();
        var last_items;
        if (items) {
            last_items = items;
        }
        else {
            last_items = this.getStore().lastOptions.params['items'];
        }
        var metadata_obj = this.variant;
        var this_grid = this;
        conn.request({
            method:'POST', 
            url: url,
            params: {metadata: Ext.encode(values), items: last_items, obj:metadata_obj},
            success: function(data, textStatus){
                this_grid.getStore().commitChanges();
                this_grid.getEl().unmask();
                Ext.MessageBox.alert(gettext('Status'), gettext('Changes saved successfully.'));
                if (new_params) {
                    this_grid.customEditors = {};
                    this_grid.getStore().load(new_params);
                }
            },
            failure: function (XMLHttpRequest, textStatus, errorThrown) {
                this_grid.getEl().unmask();
                Ext.MessageBox.alert(gettext('Status'), gettext('Saving failed!'));
            }            
         });    
    
    },
    listeners: {
        render: function(g) {
            var grid_store = this.propStore;        
            g.on("beforetooltipshow", function(grid, row) {
                if (row) {
                    var record = grid_store.getProperty(row);
                    var qtip = record.data['tooltip'];
                    if (qtip) {
                        grid.tooltip.body.update(qtip);
                    }
                    else {
                        return false;                    
                    }
                }
                else {
                    return false;
                }
            
            });
        }
    }
});
Ext.reg("metadatagrid", Ext.grid.MetadataGrid);
Ext.reg("metadatagridObj", Ext.grid.MetadataGridObj);
