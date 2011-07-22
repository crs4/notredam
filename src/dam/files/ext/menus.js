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

Ext.onReady(function(){
    Ext.QuickTips.init();
    

    var members_configuration = function() {

        var current_ws = ws_store.getAt(ws_store.findBy(find_current_ws_record)).data.pk;

        var members_store = new Ext.data.JsonStore({
            fields: ["id", "name", "admin", "edit_metadata", "add_item", "remove_item", "editable", "edit_taxonomy", 'edit_scripts', 'run_scripts'],
            root: 'elements',
            baseParams: {ws_id: current_ws},
            proxy : new Ext.data.HttpProxy({
                method: 'POST',
                url: '/get_ws_members/'
            }),
            autoLoad: true
        });
        
        var booleditor = new Ext.grid.GridEditor(new Ext.form.ComboBox({
            triggerAction: 'all',
            typeAhead: true,
            selectOnFocus: true,
            valueField: 'data_value',
            displayField: 'display_text',
            lazyRender: true,
            mode: 'local',
            store: new Ext.data.ArrayStore({
                fields: ['data_value', 'display_text'],
                data: [[1, 'Yes'], [0, 'No']]
            })

        }));

        var members_list = new Ext.grid.EditorGridPanel({
            id: 'members_list',
            store: members_store,
			sm : new Ext.grid.RowSelectionModel(), 
            viewConfig: {
             forceFit: true
            },
            listeners: {
                beforeedit: function(e) {
                    if (!e.record.get('editable')){
                        return false;                        
                    }
                }
            },
            loadMask: true,
            columns: [{
                header: 'Username',
                dataIndex: 'name'
            }, {
                xtype: 'booleancolumn',
                header: 'Is admin',
                dataIndex: 'admin',
                align: 'center',
                trueText: 'Yes',
                falseText: 'No',
                editor: booleditor
            }, {
                header: 'Can edit metadata',
                dataIndex: 'edit_metadata',
                xtype: 'booleancolumn',
                align: 'center',
                trueText: 'Yes',
                falseText: 'No',
                editor: booleditor
            }, {
                header: 'Can add item',
                dataIndex: 'add_item',
                xtype: 'booleancolumn',
                align: 'center',
                trueText: 'Yes',
                falseText: 'No',
                editor: booleditor
            }, {
                header: 'Can remove item',
                dataIndex: 'remove_item',
                xtype: 'booleancolumn',
                align: 'center',
                trueText: 'Yes',
                falseText: 'No',
                editor: booleditor
            }, {
                header: 'Can edit catalogue',
                dataIndex: 'edit_taxonomy',
                xtype: 'booleancolumn',
                align: 'center',
                trueText: 'Yes',
                falseText: 'No',
                editor: booleditor
            },             
             {
                header: 'Can edit scripts',
                dataIndex: 'edit_scripts',
                xtype: 'booleancolumn',
                align: 'center',
                trueText: 'Yes',
                falseText: 'No',
                editor: booleditor
            },
             {
                header: 'Can run scripts',
                dataIndex: 'run_scripts',
                xtype: 'booleancolumn',
                align: 'center',
                trueText: 'Yes',
                falseText: 'No',
                editor: booleditor
            }
            
            
            
            ]
        });    

        var members_panel = new Ext.Panel({
                layout: 'fit',
                items: [members_list],
                tbar: [{				
                    text: gettext('Add'),
                    iconCls: 'add_icon',
                    handler: function() {

                        var users_store = new Ext.data.JsonStore({
                            fields: ["id", "name"],
                            root: 'users',
                            baseParams: {ws_id: current_ws},
                            proxy : new Ext.data.HttpProxy({
                                method: 'POST',
                                url: '/get_available_users/'
                            }),
                            autoLoad: true
                        });

                        var list_users = new Ext.ListView({
                            store: users_store,
                            multiSelect: true,                            
                            id: 'available_users',
                            columns: [{
                                header: 'Username',
                                dataIndex: 'name'
                            }]
                        }); 

                        var permissions_form = new Ext.form.FormPanel({
                            region: 'south',
                            bodyStyle:'padding:5px 5px 0',
                            title: 'User permissions',
                            labelWidth: 150, 
                            defaults: {width: 100},
                            height: 300,
                            autoScroll: true,
                            id: 'new_user_permissions',
                            items: [{
                                fieldLabel: 'Is admin',
                                name: 'admin',                                
                                xtype: 'checkbox'
                            }, {
                                fieldLabel: 'Can edit metadata',
                                name: 'edit_metadata',
                                xtype: 'checkbox'       
                            }, {
                                fieldLabel: 'Can add item',
                                name: 'add_item',
                                xtype: 'checkbox'       
                            }, {
                                fieldLabel: 'Can remove item',
                                name: 'remove_item',
                                xtype: 'checkbox'       
                            }, {
                                fieldLabel: 'Can edit catalogue',
                                name: 'edit_taxonomy',
                                xtype: 'checkbox'       
                            }, 
                            {
                                fieldLabel: 'Can edit scripts',
                                name: 'edit_scripts',
                                xtype: 'checkbox'       
                            },
                            {
                                fieldLabel: 'Can run scripts',
                                name: 'run_scripts',
                                xtype: 'checkbox'       
                            }
                            
                            
                            
                            ]
                        }); 

                        var list_panel = new Ext.Panel({
                            title: 'Available users (select to add)',
                            region: 'center',
                            items: [list_users]
                        });
                        
                        var win = new Ext.Window({
                            layout: 'border',
                            plain: true,
                            constrain: true,
                            modal: true,
                            width: 500,
                            height: 500,
                            title: 'Add user',
                            id: 'add_user_win',
                            items    : [list_panel, permissions_form ],
                            buttons: [{
                                text: gettext('Save'),
                                handler: function() {
                                    var values = Ext.getCmp('new_user_permissions').getForm().getFieldValues();                                    
                                    var perm_values = {editable: true, admin: 0, edit_metadata: 0, add_item: 0, remove_item: 0, edit_taxonomy: 0};
                                    if (values.admin) {
                                        perm_values.admin = 1;
                                    }
                                    if (values.edit_metadata) {
                                        perm_values.edit_metadata = 1;
                                    }
                                    if (values.add_item) {
                                        perm_values.add_item = 1;
                                    }
                                    if (values.remove_item) {
                                        perm_values.remove_item = 1;
                                    }
                                    if (values.edit_taxonomy) {
                                        perm_values.edit_taxonomy = 1;
                                    }
                                    
                                    
                                    if (values.run_scripts) {
                                        perm_values.run_scripts = 1;
                                    }
                                    
                                     if (values.edit_scripts) {
                                        perm_values.edit_scripts = 1;
                                    }
                                    var selected = Ext.getCmp('available_users').getSelectedRecords();
                                    if (selected.length == 0) {
                                        Ext.MessageBox.alert(gettext('Error'), gettext('Select one or more user(s) from the list'));
                                    }
                                    else {
                                        for (var x=0; x < selected.length; x++) {
                                            var u_id = selected[x].get('id');
                                            var u_name = selected[x].get('name');
                                            perm_values.id = u_id;
                                            perm_values.name = u_name;
                                            Ext.getCmp('members_list').getStore().add(new Ext.data.Record(perm_values));
                                        }
                                        Ext.getCmp('add_user_win').close();
                                    }
                                }                            
                            }, {
                                text: gettext('Close'),
                                handler: function() {
                                    Ext.getCmp('add_user_win').close();    
                                }                            
                            }]
                        });
                        users_store.on('load', function() {
                            var members = Ext.getCmp('members_list').getStore();
                            var members_already_chosen = [];
                            var to_delete = [];
                            for (var x=0; x < members.getCount(); x++) {
                                members_already_chosen.push(members.getAt(x).get('id'));
                            } 
                            for (var x=0; x < this.getCount(); x++) {
                                var r = this.getAt(x);
                                for (var y=0; y<members_already_chosen.length; y++) {
                                    if (r.get('id') == members_already_chosen[y]) {
                                        to_delete.push(r);
                                        break;
                                    }
                                }
                            }
                            for (var x=0; x < to_delete.length; x++) {
                                this.remove(to_delete[x]);
                            }
                            
                            if (this.getCount() > 0) {
                                win.show();                            
                            }
                            else {
                                Ext.MessageBox.alert(gettext('Error'), gettext('No more users available'));
                            }
                        });
                    }
                }, {
                    text: gettext('Remove'),
                    iconCls: 'clear_icon',
                    handler: function() {
						var selection = Ext.getCmp('members_list').getSelectionModel().getSelections();
						for (var s=0; s < selection.length; s++) {
						    if (selection[s].get('editable')) {
                                Ext.getCmp('members_list').getStore().remove(selection[s]);
                            }
                        }
                    }
                }]
        });
        var win = new Ext.Window({
            layout: 'fit',
            constrain: true,
            plain: true,
            modal: true,
            width: 950,
            height: 400,
            id: 'members_conf',
            title: 'Members configuration',
            items    : [members_panel],
            buttons: [{
                text: gettext('Save'),
                handler: function() {
                    var ws_members = Ext.getCmp('members_list').getStore();
                    var permissions = [];
                    for (var x = 0; x < ws_members.getCount(); x++) {
                        permissions.push(ws_members.getAt(x).data);
                    }
					Ext.Ajax.request({
				        url: '/save_members/',
		                params: {ws_id: current_ws, permissions: Ext.encode(permissions)},
				        success: function(data){
                            Ext.MessageBox.alert(gettext('OK'), gettext('Changes saved successfully.'));
				        },
						failure: function() {
							Ext.MessageBox.alert(gettext('Error'), gettext('An error occured while saving configuration.'));
						}
				    });                
                }                            
            }, {
                text: gettext('Close'),
                handler: function() {
                    Ext.getCmp('members_conf').close();    
                }                            
            }]            
        });
        
        win.show();
        
    };
    
    var delete_items_selection = function(selected, multiple_ws) {

        var on_delete_success = function(resp) {
	        if (resp.inbox_to_reload){
                var inbox = Ext.getCmp('inbox_tree');
                var inbox_node = inbox.getRootNode().findChild( 'text', resp.inbox_to_reload);
                
                var expanded = inbox_node.isExpanded();
                inbox.getLoader().load(inbox_node, function(){
                    if (expanded) {
                        inbox_node.expand();
                    }
                });

            }

			Ext.getCmp('media_tabs').getActiveTab().getComponent(0).getStore().reload();
            Ext.MessageBox.alert(gettext('Success'), gettext('Object(s) deleted successfully.'));

		};

        var form_url = '/delete_item/';

        console.log(selected);

        var buttons = [
            {
                text: gettext('OK'),                                                           
                handler: function() {
                    var f = Ext.getCmp('form').form;
                    
                    if (f.isValid()) {
                    
                        f.submit({
                            params: {item_ids:selected},
                            waitMsg:'Deleting...', 
                            method: "POST", 
                            
                            success: function(form, action) {
                            
                                var resp = Ext.decode(action.response.responseText);
                                on_delete_success(resp);                                                                                      
        
                                Ext.getCmp('action_win').close();

                            }, 
                            failure: function() {
                                Ext.MessageBox.alert(gettext('Error'), gettext('An error occured while removing items.'));
                            }
                        });
                        
                    } else{
                        Ext.MessageBox.alert(gettext('Error'), gettext('Please fill all the fields and try again.'));
                    }
                }
            },{
                text: gettext('Cancel'),
                handler: function() {
                   Ext.getCmp('action_win').close();
                }
            }];

        if (multiple_ws) {
            var removal_options = {
                xtype: 'radiogroup',
                fieldLabel: gettext('Delete from:'),
                items: [
                   {boxLabel: gettext('Current workspace'), name: 'choose', inputValue: 'current_w', checked: true},
                   {boxLabel: gettext('All workspaces'), name: 'choose', inputValue: 'all_w'}
                ]
            };
            
            var items = [removal_options];
            
            var form = new Ext.form.FormPanel({
                labelWidth: 65,
                url: form_url,
                bodyStyle:'padding:5px 5px 0',
                width: 350,
                height: 100,
                frame: true,
                id: 'form',
                items: items,
                buttons: buttons
            });
            
            var win = new Ext.Window({
                title: "Delete item(s)",
                closable: true, 
                constrain: true,
                modal: true, 
                layout: 'fit',
                items: [form],
                id: 'action_win',
                listeners: {
                    close: function() {
                        Ext.getCmp('media_tabs').getActiveTab().getComponent(0).getStore().reload();
                    }
                }
            });
            
            win.show();

        }
        else {
	
	        Ext.MessageBox.confirm('Confirm', 'Are you sure you want to delete the selected item(s)?', function(btn) {
				if (btn == 'yes') {
					Ext.Ajax.request({
				        url: form_url,
		                params: {item_ids: selected, choose: 'current_w'},
				        success: function(data){
				            data = Ext.decode(data.responseText);
							on_delete_success(data);
				        },
						failure: function() {
							Ext.MessageBox.alert(gettext('Error'), gettext('An error occured while removing items.'));
						}
				    });
				}
            });
	
		}

    };

    var call_back_delete = function(btn){
        if (btn == 'yes'){ 
                                
            Ext.Ajax.request({
               url: '/delete_ws/' + ws.id + '/',
               method: 'GET',
                success: function(){
                    ws.deleted = true;
                    ws_store.load();
                },
                failure: function(response){
                   Ext.Msg.alert('Deletion failed', response.responseText);
                }
            });
        }
        
    };
        
    var switch_menu;
    
    
    var states_menu = new Ext.menu.Menu({
        id:'states_menu',
        items: []        
    });    
            
    var ws_menu =  function() {
//        switch_menu = new Ext.menu.Menu({
//            id: 'switch_ws_menu',
//            items:[]
//        });
        
        return new Ext.menu.Menu({
            id: 'wsMenu',
            items: [
                {
                    id: 'new_ws_menu',
                    text: gettext('New'),
                    handler: function(){edit_ws(true);}
    
                },
                
                { id: 'delete_ws_menu',
                    text: gettext('Delete'),
                    handler: function() {
                        Ext.Ajax.request({
                            url: '/get_n_items/',
                            success: function(resp){
                                var resp = Ext.decode(resp.responseText);
                                if (resp.n_items) {
                                    Ext.MessageBox.alert(gettext('Attention'), gettext('Deletion failed. Current workspace is not empty, please move or delete the items before'));
                                }
                                else {
                                    Ext.MessageBox.confirm(gettext('Confirm'), gettext("Do you really want to remove this workspace?"), call_back_delete);
                                }
                            }
                            
                        });
                    }
                },
                
                 {
                    id: 'preferences_menu',
                    text: gettext('Configuration'),
                    menu:{
                        items:[{
                                text: gettext('Descriptors'),
                                handler: open_config_descriptors
                            
                            }, 
                        { text: gettext('Members'),                                                      
                            handler: members_configuration                    
                            
                            }, { text: gettext('Preferences'),
                            handler: function(){ open_ws_pref(); }
                        
                            },
                        { text: gettext('Renditions'),                                                      
                            handler: variants_prefs 
                            
                            }
                        ]
                    }
                }
            ]
        });
    };

    var edit_menu = new Ext.menu.Menu({
        id: 'editMenu',
        items: [
            {
                text: gettext('Select all'),
                handler: function() {
                    var view = Ext.getCmp('media_tabs').getActiveTab().getComponent(0);
                    
                    view.selectRange(view.getStore().lastOptions['start'], view.getStore().lastOptions.params['start']+view.getStore().lastOptions.params['limit']);
                    
                }
            },
            
            {
                text: gettext('Clear selection'),
                handler: function() {
                    Ext.getCmp('media_tabs').getActiveTab().getComponent(0).clearSelections();

                }
            }
           
            ]
        }
    );
    
    var menu = new Ext.menu.Menu({
        id: 'mainMenu',
        items: [
            {
                id:'new_item_menu',
                text: gettext('New'),
                handler: function() {
                    calculatePageSize();

                    upload_dialog({
                    	url: '/upload_resource/',
                    	after_upload: function(session_id){
                            var tmp_win = new Ext.Window({
                                title: 'Upload',
                                height: 100,
                                width: 200,
                                html: 'Completing upload, please wait...',
                                modal: true
                            });
                            tmp_win.show();
                            
                            var files_num = Ext.getCmp('files_list').getStore().getCount();
                    		Ext.Ajax.request({
				            	url: '/upload_session_finished/',
				            	params: {session: session_id,
                                
                                },
				            	failure: function(){
                                    tmp_win.close();
				            		Ext.Msg.alert('Error', 'An upload error occurs server side, sorry.');
//				            		Ext.getCmp('files_list').getStore().removeAll();
				            		
				            		for (var i = 0; i < files_num; i++){
				            			Ext.getCmp('progress_' + i).updateProgress(1,'failed');
				            		
				            		}
				            		
				            	},
				            	success: function(response){
                                    
                                    response_obj = Ext.decode(response.responseText);
                                    var uploads_failed, uploads_success;
                                    uploads_success = response_obj.uploads_success;
                                    uploads_failed = files_num - parseInt(uploads_success);
                                    
                                    
                                    tmp_win.close();
				            		var tab = Ext.getCmp('media_tabs').getActiveTab();
					                var view = tab.getComponent(0);
					                var selecteds = view.getSelectedRecords();
					                var store = view.getStore();
									//var uploads_failed = 0, uploads_success = 0, progressbar;
									//var files_num = Ext.getCmp('files_list').getStore().getCount();
									//for(var i = 0; i<files_num; i++){
										//progressbar = Ext.getCmp('progress_' + i);
										//if(progressbar.text == 'failed')
											//uploads_failed += 1;
										//else if (progressbar.text == 'completed')
										//uploads_success += 1;
									//}


//                                    store_tabs.loadData({'tabs':create_tabs(ws.id)}, true);
                                    var media_tabs = Ext.getCmp('media_tabs');
                                    
                                    var query;
                                    if (response_obj.inbox){
                                        query = 'Inbox:/Uploaded/' + response_obj.inbox + '/';
                                         var inbox = Ext.getCmp('inbox_tree').getRootNode();
                                         inbox.reload();
                                         
                                    }
                                    else
                                        query = '';
                                    
                                    var title = query || 'All Items';
                                    console.log('title: ' + title);
                                    var tab_to_open;
                                    Ext.each(media_tabs.items.items, function(panel){
                                        console.log('panel.title ' + panel.title);
                                        if (panel.title == title) 
                                            tab_to_open = panel;
                                    });
                                    console.log('tab_to_open');
                                    console.log(tab_to_open);
                                    if (tab_to_open){
                                        media_tabs.setActiveTab(tab_to_open.id);
                                        tab_to_open.reload();
                                    }
                                    else{
                                        tab = createMediaPanel({
                                        title: title,
                                        query: query,
                                        media_type: ['image', 'audio', 'video', 'doc'],
                                            closable: true
                            //                closable: count > 0
                            //                search_value: this.data.query || ''
                                        }, true);
                                        media_tabs.add(tab);
                                        media_tabs.setActiveTab(tab.id);
                                    
                                    }
                                    
                                    

									var buttons = []

							        buttons.push({
							            	text: 'Upload more files',
							            	handler: function(){
							            		Ext.getCmp('files_list').getStore().removeAll();
							            		Ext.getCmp('upload_finished').close();
							            		session_id = user + '_' + new Date().getTime();
							            	}							            
							            });
							      	buttons.push({
								            text: 'Show monitor',
								            handler: function(){
								            	Ext.getCmp('upload_finished').close();
								            	win.close();
								            	show_monitor();
								            }
								          });
							        buttons.push({
							            text: 'Close',
							            handler: function(){
							            	Ext.getCmp('upload_finished').close();
							            	win.close();
							            }
						            });
								          
					                var upload_finished = new Ext.Window({
										id: 'upload_finished',
							            title    : 'Upload Finished',
							            closable : true,
							            width    : 400,
							            height   : 200,
							            buttonAlign: 'center',
							            modal: true,
							            html: '<p>successfull uploads: ' + uploads_success + '</p><p>failed uploads: ' + uploads_failed +'</p>',
							            buttons: buttons
							       	});
							        upload_finished.show();
							       
							        
					                store.reload({
					                    scope: view,
					                    callback:function(){
					                        var ids = [];
					                        for(i = 0; i<selecteds.length; i++){
					                            ids.push(selecteds[i].data.pk);
					                            }
					                        this.select(ids);
					                        
					                        }
					                    });		
				            	
				            	}
				            });
                    		
                    	
                    	}
                    	
                    	
                    	
                    });
                }
            }, {
                text: gettext('Share with...'),
                id: 'addto',
                disabled: true,
                menu:  cp_ws_menu
            },
            {
                text: gettext('Move to...'),
                id: 'mvto',
                disabled: true,
                menu: mv_ws_menu
            },            
            {
                text: gettext('Sync XMP...'),
                hidden: true,
                id: 'sync_xmp',
                disabled: true,
                handler: function() {

                    var variant_store = Ext.getCmp('variantMenu').store;
                    var variants_list = [{boxLabel: gettext('All'), name: 'all', checked: true}, {boxLabel: gettext('original'), name: 'original'}];

                    variant_store.each(function(r) {
                        var variant = r.get('variant_name');
                        variants_list.push({boxLabel: variant, name: variant});                        
                    });

                    var fp = new Ext.FormPanel({
                        frame: true,
                        labelWidth: 110,
                        width: 400,
                        height: 270,
                        items: [
                            {
                                xtype: 'checkboxgroup',
                                fieldLabel: gettext('Choose renditions'),
                                columns: 3,
                                items: variants_list
                            }
                        ],
                        buttons: [{
                            text: gettext('Sync'),
                            handler: function(){
                               if(fp.getForm().isValid()){
                                    var items = get_selected_items();
                                    var chosen_variants = fp.getForm().getValues();
                                    var chosen_list = [];
                                    for (var x in chosen_variants) {
                                        chosen_list.push(x);
                                    }
                                    Ext.Ajax.request({
                                        url: '/sync_component/',
                                        params: {items: items, variants: chosen_list},
                                        success: function(data){
                                            
                                        }
                                    });          
                                }
                            }
                        },{
                            text: gettext('Cancel'),
                            handler: function(){
                                this.findParentByType('window').close();
                            }
                        }]
                    });
                                        
                    var win = new Ext.Window({
                        modal: true,
                        resizable: false,
                        constrain: true,
                        width: 400,
                        height: 300,
                        title: gettext('Synchronize XMP'),
                        items: [fp]
                    });

                    win.show();

                }
            },
            {
                text: gettext('Download'),
                id: 'download',
                disabled: true,
                handler: function(){
                    var sm =  new Ext.grid.CheckboxSelectionModel({
                        checkOnly: true,
                        singleSelect: false,
                        listeners:{
                        	selectionchange: function(){
                        		if (this.getCount() >0)
                        			Ext.getCmp('download_rendition_button').enable();
                        		else
                        			Ext.getCmp('download_rendition_button').disable();
                        	}
                        }
                    });
                    
                    var win = new Ext.Window({
                        id:'download_win',
                        height: 300,
                        width: 400,
                        layout: 'fit',
                        frame: true,
                        modal: true,
                        title: gettext('Choose renditions to download'),
                        buttons: [{
                        	id: 'download_rendition_button',
                            text: gettext('Download'),
                            disabled: true,
                            handler: function(){
                                var renditions_to_download = Ext.getCmp('renditions_to_download').getSelectionModel().getSelections();
                                var post = {
                                    items: [],
                                    renditions: [],
                                    compression_type: Ext.getCmp('compression_type').getValue()
                                };
                                Ext.each(
                                    renditions_to_download,
                                    function(){
                                        post.renditions.push(this.data.pk)
                                    }
                                );
                                    
                                var ac = Ext.getCmp('media_tabs').getActiveTab();
                                var view = ac.getComponent(0);

                                var selNodes= view.getSelectedNodes();
                                Ext.each(
                                    selNodes,
                                    function(){
                                        post.items.push(this.id);
                                    }
                                );
                                
                                if (post.items.length > 0 && post.renditions.length > 0)
                                    Ext.Ajax.request({
                                        url: '/download_renditions/',
                                        params: post,
                                        success: function(response){
                                            var obj = Ext.decode(response.responseText);
                                            window.open(obj.url);
                                            
                                        }
                                        
                                    });
                                Ext.getCmp('download_win').close();
                            }
                        }],
                        buttonAlign: 'center',
                        autoScroll: true,
                        items:[
                        	new Ext.Panel({
                        		layout: 'border',
                        		border: false,
                        		autoScroll: true,
                        		items:[
                        			new Ext.grid.GridPanel({
		                                id:'renditions_to_download',
		                                region:'center',
		                                border: false,
		                                viewConfig:{
		                                    forceFit: true,
		                                    headersDisabled: true
		                                },
		                                sm: sm,
		                                store:  new Ext.data.JsonStore({
		                                    url: '/get_variants_list',
		                                    root: 'variants',
		                                    fields: ['pk','name'],
		                                    autoLoad: true
		                                }),		                                
		                                columns:[
		                                   sm,
		                                    {
		                                        dataIndex: 'name'
		                                    }
		                                ]	
		                            }),
		                            
		                            new Ext.form.ComboBox({
		                            	id: 'compression_type',
		                            	fieldLabel: gettext('Compression'),
							        	width: 245,
							        	region: 'south',
							        	 store: new Ext.data.ArrayStore({							        	        
							        	        fields: ['name'],
							        	        data: [['zip'], ['tar.gz']]
							        	    }),				
							        	allowBlank:false,
							            forceSelection: true,
							            displayField:'name',				                        
							            triggerAction: 'all',
							            editable: false,
							            valueField: 'name',
							            mode: 'local',          
							            emptyText: 'start month',               
							            hideTrigger:false,
							            name: 'compression_type',
							            value: 'zip'
		                            })
                        		]
                        	})
                        

                        ]
                    });
                    win.show();
                }
            },
            
            {
                id:'remove_from_ws',
                text: gettext('Delete'),
                disabled: true,
                handler: function() {
                    var view = Ext.getCmp('media_tabs').getActiveTab().items.items[0];
                    var selNodes= view.getSelectedNodes();
                    if(selNodes && selNodes.length > 0){ 
                        var selected_ids = get_selected_items();

						Ext.Ajax.request({
					        url: '/check_item_wss/',
			                params: {item_ids: selected_ids},
					        success: function(data){
					            var data = Ext.decode(data.responseText);
		                        delete_items_selection(selected_ids, data.multiple_ws);
					        }
					    });

                    }
                    else {
                        Ext.MessageBox.alert(gettext('Error'), gettext('You have selected no items!'));
                    }
                }
            },
             {
                text:gettext('Set state to'),
                id: 'set_state_to',
                menu: states_menu,
                disabled: true
            }

        ]
    });

    var help = new Ext.menu.Menu({
        id: 'helpMenu',
        items: [{
            text: gettext('Tutorial'),
            handler: function() {
                window.open('http://www.opendam.org/NotreDAM/QuickGuide.html', 'tutorial');
            }
        }, {
            text: gettext('Info'),
            id: 'whoami',
            handler: function() {
                var win = new Ext.Window({
                        constrain: true,
                        modal: true,
                        resizable: false,
                        width: 400,
                        title: 'NotreDAM Info',
                        html: '<div>NotreDAM, Version <b>1.0.6</b>, Copyright 2009-2011, <a href="http://www.crs4.it/" target="_blank">CRS4</a> & <a href="http://www.sardegnaricerche.it/" target="_blank">Sardegna Ricerche.</a></div><div>Web site: <a href="http://www.notre-dam.org/" target="_blank">http://www.notredam.org/</a></div><div>Email: <a href="mailto:labcontdigit@sardegnaricerche.it">labcontdigit@sardegnaricerche.it</a> </div><br/><div>NotreDam is released under the <a href="http://www.gnu.org/licenses/gpl.html" target="_blank">GPL v.3 license</a>.</div><div>Open-sourced works used: <p><a href="http://www.extjs.com" target="_blank">ExtJS 3.0</a> (GPL v.3 license)</p><p><a href="http://www.flowplayer.org" target="_blank">FlowPlayer 3.1.5</a> (GPL v.3 license)</p><p><a href="http://www.famfamfam.com/lab/icons/silk/" target="_blank">Silk Icons</a> (Creative Commons Attribution)</p><p>MapIconMaker and DragZoom js script (Apache License 2.0)</p></div><br/><div>More information can be found in the license headers of the source files<br/> or in the LICENSE file included in this release.</div>'
                            
                });
                win.show();
            }
        }]
    });
    function create_toolbar(){
        var tb = new Ext.Toolbar();
        var style_tb = 'font-size: 11px; font-weight:bold; color:#15428B; font-family: sans-serif';
        
//        var style_tb = 'font-size: 12px; font-family: sans-serif';
        
        
        tb.add({
                text:'<span style="' + style_tb + '">' + gettext('Item') + '</span>',
                menu: menu, 
                id: 'object_menu'
            }, '-',
            {
                text:'<span style="' + style_tb + '">' + gettext('Edit') + '</span>',
                menu: edit_menu,
                style: '',
                id: 'edit_menu'
            }, '-',
            {
                text:'<span style="' + style_tb + '">' + gettext('Workspace') + '</span>',
                menu: ws_menu()
            }, '-',
            
            {
                text:'<span style="' + style_tb + '">' + gettext('Script') + '</span>',
                menu:  new Ext.menu.Menu({
                	    id: 'preferences_scripts',
                        items:[
                        	{
                                text    : gettext('New'),
                                handler : function(){window.open('/script_editor/?workspace='+ws.id)}
                            
                            },{ 
                            	text    : gettext('Edit'),                                                      
	                           	menu: new Ext.menu.Menu({
								    id: 'edit_scripts_menu',
								    items:[]
								})                 
                            },
                            	
                            
//                            { 
//                            	text    : 'Events',
//                            	handler : function(){manage_events();}
//                            },
                            { 
                            	text    : gettext('Monitor'),
                            	handler : function(){
                            		show_monitor();
                            	
                            	}
                            },
                            {
                            	id: 'runscript',
                            	disabled: true,
                            	text: gettext('Run...'),
                            	menu: new Ext.menu.Menu({
								    id: 'run_scripts_menu',
								    items:[]
								})
                            }
                            
                        ]
                    
                	})
            	
            }, '-',
            
            
            
            {
                text:'<span style="' + style_tb + '">' + gettext('Help') + '</span>',
                menu: help 
            }
        );
        tb.render('toolbar');
        
        switch_menu = new Ext.menu.Menu({
            id: 'switch_ws_menu',
            items:[],
            listeners:{
            	itemclick: function(item){
            		Ext.getCmp('switch_ws_tb').setText(item.text );
            	
            	}
            	
            }
        });
        
        var switch_ws_tb = new Ext.Toolbar({
            cls: 'x-box-layout-ct custom-tb'
            });
        
//        switch_ws_tb.add(new Ext.menu.TextItem({
//        		text: 'Workspace:'
//        	})
//        );
        
        
//        switch_ws_tb.add('Workspace: ');
        switch_ws_tb.add({
        		id: 'switch_ws_tb',
        		text: '',
                cls: 'switch-ws-button',
        		menu: switch_menu,        	
                tooltip: 'set current workspace'
        });
        switch_ws_tb.render('switch_ws_bar');

//        var switch_ws_tb = new Ext.Button({
//        	id: 'switch_ws_tb',
////        	applyTo: 'switch_ws_bar',
//        	text: '',
//        	menu: switch_menu,  
//        	
//        });
//        switch_ws_tb.render('switch_ws_bar');
    }
    
    
    create_toolbar();
    
    
    ws_store.on('load', function(){
    	
        if (ws.deleted){ //a ws has been just deleted        	            
            var ws_record = ws_store.getAt(0);
            switch_ws(ws_record);
            ws.deleted = false;
            }
        
        
        Ext.getCmp('switch_ws_tb').setText(ws.name);        
        switch_menu.removeAll();
        
        cp_ws_menu.removeAll();
        mv_ws_menu.removeAll();
            
        
        ws_store.each(function(r){
            var checked;
            if (ws.id == r.data.pk) {
                checked = true;
            }
            else{
                checked = false;
                
                
                cp_ws_menu.add(
                    new Ext.menu.Item({
                        text: r.data.name,
                        record: r,
                        handler:function(ci){
                            var selected_ids = get_selected_items();
                            Ext.Ajax.request({
                                url: '/add_items_to_ws/',
                                params:{
                                    ws_id: ci.record.data.pk,
                                    remove:false,
                                    item_id: selected_ids
                                    
                                    },
                                success: function() {
                                	
                                    Ext.MessageBox.alert(gettext('Success'), gettext('Item(s) shared successfully.'));
                                }
                                
                            });
                        }
                    })
                );
            
                mv_ws_menu.add(
                    new Ext.menu.Item({
                        text: r.data.name,
                        record: r,
                        handler:function(ci){
                            var selected_ids = get_selected_items();
                            Ext.Ajax.request({
                                url: '/add_items_to_ws/',
                                params:{
                                    ws_id: ci.record.data.pk,
                                    remove:true,
                                    item_id: selected_ids
                                    },
                                success: function(){
                                    var view = Ext.getCmp('media_tabs').getActiveTab().items.items[0];                                        
                                    view.getStore().reload();
                                    Ext.MessageBox.alert(gettext('Success'), gettext('Item(s) moved successfully.'));
                                }
                            });
                        }
                    })
                );
            }
            
            switch_menu.add(
                new Ext.menu.CheckItem(
                {
                    text: r.data.name,
                    checked: checked,
                    group: 'ws_menu',
                    handler: function(ci){switch_ws(ci.record);},
                    record: r
                })
            );
        });
        
    });
	
    ws_store.on('load', function(){
    	
        ws_permissions_store.load();
    
        states_menu.removeAll();
        
        var set_state_to = Ext.getCmp('object_menu').menu.items.get('set_state_to');
        if (this.getCount() > 0){
            set_state_to.show();
            this.each(function(r){            
                this.add(
                    new Ext.menu.CheckItem({
                        text: r.data.name,
                        record: r,
                        id: 'state_' + r.data.pk,
                        group:'states',
                        handler:function(ci){
                            var tab = Ext.getCmp('media_tabs').getActiveTab();
                            var view = tab.getComponent(0);
                            var selected_records =  view.getSelectedRecords();
                            var items = [];
                            for (var i = 0; i < selected_records.length; i++) {
                                var item_data = selected_records[i].data;
                                items.push(item_data.pk);
                            }
                            Ext.Ajax.request({
                                url:'/set_state/',
                                params:{
                                    item_id:items,
                                    state_id: ci.record.data.pk
                                },
                                scope: ci,
                                success:function(){
                                var state_id = this.id.split('_')[1];
                                for (var i = 0; i < selected_records.length; i++) {
                                    selected_records[i].set('state', state_id);                              
                                    
                                }
                                showDetails(view);
                                    
                                    
                                        
                                }
                            });
                            
                        }
                    })
                );
            
            
            }, states_menu);
    }
    else
        set_state_to.hide();
    
    }, ws_state_store);
    

});
