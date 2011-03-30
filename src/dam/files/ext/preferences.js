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

var get_pref_store = function(store_url, save_url, obj, on_success, additional_item_func) {

    var my_store = new Ext.data.JsonStore({
        url:store_url,
        root:'prefs',
        fields: ['id','name','caption','name_component', 'type', 'value', 'choices'],
        listeners: {        
            load: function() {
    			
    			
                var generated_prefs = generate_pref_forms(this, save_url, undefined, on_success );
              	var account_prefs = new Ext.FormPanel({
              		id: 'account_form',
		            frame: true,
		            title: 'Account',
		            monitorValid: true,
		            labelWidth: 200, // label settings here cascade unless overridden		            
		            url: '/account_prefs/',
		            
		            buttons: [{
		                text: 'Save',
		                type: 'submit',
		                handler: function(){
		                	Ext.getCmp('account_form').getForm().submit({
		                		success: function(){
//		                			user = Ext.getCmp('username').getValue();
//		                			Ext.get('user_logged').dom.innerHTML = user;
		                			 Ext.MessageBox.alert('Save', 'Preferences saved successfully.');
		                		}
		                	}
		                );
		                
		                
		                }
		            },{
		                text: 'Cancel',
		                handler: function() {
		                	win.close();
		                	
		                   
		                }
		            }],
		            items:[
//		            	new Ext.form.TextField({
//		            		id: 'username',
//		            		fieldLabel: 'username',
//		            		name:'username',		            		
//		            		allowBlank: false
//		            	}),
		            	new Ext.form.TextField({
		            		id: 'firstname',
		            		fieldLabel: 'first name',
		            		name:'first_name'		            		
		            	}),
		            	new Ext.form.TextField({
		            		id: 'last_name',
		            		fieldLabel: 'last name',
		            		name:'last_name'		            		
		            		
		            	}),
		            	new Ext.form.TextField({
		            		id: 'email',
		            		fieldLabel: 'email',
		            		name:'email',
		            		vtype:'email',
		            		allowBlank: false
		            	}),
		            	new Ext.form.TextField({
		            		id: 'session_language',
		            		fieldLabel: 'default language',
		            		name:'session_language'		            		
		            	}),
		            	
		            	new Ext.form.FieldSet({
		            		id: 'password_fieldset',
		            		title: 'Change Password',
		            		checkboxToggle : {tag: 'input', type: 'checkbox', id: 'change_password_cb'},
		            		items: [
		            			new Ext.form.TextField({
		            				fieldLabel: 'current password',
		            				id: 'current_password',
		            				name: 'current_password',
		            				inputType: 'password',
		            				validator: function(value){
		            					if (Ext.get('change_password_cb').dom.checked && !value)
		            						return 'new password cannot be empty';
		            					else
		            						return true;
		            				}
		            			}),
		            			new Ext.form.TextField({
		            				id: 'new_password',
		            				fieldLabel: 'new password',
		            				name: 'new_password',
		            				inputType: 'password',
		            				validator: function(value){
		            				if (Ext.getCmp('current_password').getValue() && !value)
		            					return 'new password cannot be empty';
		            				else
		            					return true;
		            				}
		            			}),
		            			new Ext.form.TextField({
		            				fieldLabel: 'confirm password',
		            				name: 'confirm_password',
		            				inputType: 'password',
		            				validator: function(value){
		            					var new_password = Ext.getCmp('new_password').getValue();
		            					if (Ext.getCmp('current_password').getValue() && new_password && value != new_password)
		            						return 'confirmation password does not match';
		            					else
		            						return true;
		            				}
		            			})
		            			
		            			
		            		],
		            		listeners:{
		            			render:function(){
		            				this.toggleCollapse();		            				
		            			}
		            		}
		            	})
		            ],
		            listeners:{
		            	render:function(){
		            		var el = this.getEl();
		            		el.mask('Loading...');
		            		this.getForm().load({
            					url: '/get_account_info/',
            					success: function(){
            						el.unmask();            						
            					},
            					failure: function(){
            						el.unmask();
            						el.mask('Failed loading account data.');
            					}
            				});
		            	}
		            	
		            }
		        });
                
		        var items = [account_prefs].concat(generated_prefs);
		        
                if (additional_item_func) {
                    var gen_item = additional_item_func();
                    items.splice(0, 0, gen_item);
                }
            
                var win = new Ext.Window({
                    layout      : 'fit',
                    constrain: true,
                    width       : 500,
                    height      : 350,
                    plain       : true,
                    title: obj + ' Preferences',
                    modal: true,
                    items    : new Ext.TabPanel({
                                autoTabs       : true,
                                activeTab      : 0,
                              
                                items: items
                            })
                });
                win.show();               
            
            }
        }
    });
    
    return my_store;

};

var on_success = function(form, action) {
		
    if (Ext.getCmp('languageMenu').store) {
        Ext.getCmp('languageMenu').store.reload();
    }    
    if(ws_store && form.title == 'Media Types')
    	ws_store.reload();
    
    Ext.MessageBox.alert('Save', 'Preferences saved successfully.');
};

var get_general_form = function() {
    var current_ws = ws_store.getAt(ws_store.findBy(find_current_ws_record)).data;
    var url = '/admin_workspace/' + current_ws.pk + '/';
    var g_form = general_form('General',url,false, [current_ws.name, current_ws.description]);

    return g_form;
};

var pref_store = get_pref_store('/get_user_settings/', '/save_pref/', 'User', on_success);
var pref_ws_store = get_pref_store('/get_ws_settings/', '/save_ws_pref/', 'Workspace', on_success, get_general_form);

var generate_pref_forms = function(pref_store, submit_url, on_cancel_func, on_success_func) {

    var fields = {};

    pref_store.each(function(pref){
        var component = pref.data.name_component;  
        if (!fields[component]) {
            fields[component] = [];
        }
        if(pref.data.type == 'boolean') {

            fields[component].push(
                new Ext.form.Checkbox({
                    checked: pref.data.value == 'on',
                    name :pref.data.id,
                    fieldLabel :pref.data.caption,
                    msgTarget:'side'
                })
            );
        }
        else if (pref.data.type == 'choice'){
            var choices = pref.data.choices;
            var field_store = new Ext.data.ArrayStore({
                fields: ["id", "desc"],
                data: choices
            });
            fields[component].push(new Ext.form.ComboBox({
                store:field_store,
                editable:false,
                forceSelection:true,
                triggerAction:'all',
                hiddenName: pref.data.id,
                fieldLabel: pref.data.caption,
                displayField: 'desc',
                valueField: 'id',
                value: pref.data.value,
                msgTarget:'side',
                mode: 'local',
                lazyRender: true
                }));
        }                
        else if (pref.data.type == 'string'){
            
            fields[component].push(new Ext.form.TextField({                            
                fieldLabel: pref.data.caption,
                value: pref.data.value,
                name: pref.data.id,
                msgTarget:'side'                            
            }));
        }
            
        else if (pref.data.type == 'int'){
            
            fields[component].push(new Ext.form.NumberField({                            
                fieldLabel: pref.data.caption,
                value: pref.data.value,
                name: pref.data.id,
                msgTarget:'side'
                
            }));
        }            
            
         else if (pref.data.type == 'email'){
                        
            fields[component].push(new Ext.form.TextField({                            
                fieldLabel: pref.data.caption,
                value: pref.data.value,
                name: pref.data.id,
                validator:Ext.form.VTypes.email,
                invalidText: 'invalid email',
                msgTarget:'side'
            }));
        }                    
        else if (pref.data.type == 'multiple_choice'){
            choices = pref.data.choices;
            var checkboxes = [];
            for (var j = 0; j < choices.length; j++){
                checkboxes.push(
                    new Ext.form.Checkbox({
                    checked: pref.data.value.search(choices[j][0]) >= 0,
                    name: choices[j][1],
                    boxLabel: choices[j][1],
                    inputValue: choices[j][0]
                    })
                );
            }
            var chkboxgroup = new Ext.form.CheckboxGroup({
                allowBlank: false,
                fieldLabel :pref.data.caption,
                items: checkboxes,
                vertical: true,   
                name: pref.data.id,
                msgTarget:'under',
                columns: 3

            });

            fields[component].push(chkboxgroup);
        }
    });    

    var tabs = [];

    for (var k in fields) {
        var new_tab = new Ext.FormPanel({
            frame: true,
            title: k,
            labelWidth: 200, // label settings here cascade unless overridden
            items: fields[k],
            url: submit_url,
            buttons: [{
                text: 'Save',
                type: 'submit',
                handler: function(){
                
                    var my_form = this.findParentByType('form');                    
                    var items = my_form.items.items;
                    
                    for (var i = 0;  i < items.length; i ++){
                        if (items[i].getXType() == 'checkboxgroup'){
                            var ckboxes = items[i].items.items;
                            var values = [];
                            for(var j = 0; j< ckboxes.length; j++){
                                if(ckboxes[j].getValue()) {
                                    values.push(ckboxes[j].getRawValue()) ;
                                }
                            }
                            
                            my_form.getForm().baseParams = {};                            
                            my_form.getForm().baseParams[items[i].name] = values;
                        }
                            
                    }
                    
                     my_form.getForm().submit({
                        
                        clientValidation: true,
                        waitMsg: 'Saving...',
                        success: on_success_func
                    });
                
                }
            },{
                text: 'Cancel',
                handler: function() {
                
                    if (on_cancel_func) {
                        on_cancel_func();
                    }
                    var my_win = this.findParentByType('window');
                    my_win.close();  
                }
            }]
        });             
        tabs.push(new_tab);
    }
        
    return tabs;

};

function open_pref(){        
        
    pref_store.reload();    
}

function open_ws_pref(){
        
    pref_ws_store.reload();    
}
