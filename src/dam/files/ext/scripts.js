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

function edit_script(is_new){
	
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
				
				Ext.each(actions, function(action){
					available_actions.push(action.data.name);
					
				
				});
				
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
function show_failures(process_id, pipe_name){
	Ext.Ajax.request({
		url: '/get_failures_info/',
		params: {
			process_id: process_id			
		},
		success: function(response){
			var win = new Ext.Window({
				title: 'Debug script ' + pipe_name,
				height: 600,
				width: 800,
				html: response.responseText ,
				frame: true,
				autoScroll: true
			});
			
			win.show();
			
		}
	});

	show_items(process_id, 'failed');

}

function show_monitor(){
		var win_id = 'script_monitor';
		if (Ext.WindowMgr.get(win_id))
			return;
			
		 var expander = new Ext.ux.grid.RowExpander({
			enableCaching: false,
	        tpl : new Ext.Template(
	            '<p>Launched By: <b>{launched_by}</b></p>',
	            '<p>Total Items: <a href="javascript:show_items(\'{id}\', \'total\')"><b>{total_items}</b></a></p>',
	            '<p>Items Completed: <a href="javascript:show_items(\'{id}\', \'completed\')"><b>{items_completed}</b></a></p>',
	            '<p>Items Failed: <a href="javascript:show_items(\'{id}\', \'failed\')"><b>{items_failed}</b></a></p>'
	        )
	    });
	    
	    var items_columns_renderer = function(items_type){
//	    items_type = 'total' or 'completed' or 'failed'
	    	return function(value, metaData, record, rowIndex, colIndex, store){
		    	
		    	if (value > 0){
		    		var id = record.data.id;
		    		
		    		return String.format('<a href="javascript:show_items(\'{0}\', \'{1}\')"><b>{2}</b></a>', id,items_type,  value);
		    	}
		    	return value;
		    
		    }; 
	    }; 
	    
	    
		var win = new Ext.Window({
			id: win_id,
			title: 'Script Monitor',
			height: 500,
			width: 900,
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
//					plugins: expander,
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
//					    	expander,
					    {
					        header: 'Name',											       
					        dataIndex: 'name',
					        width: 150,
					        sortable: true,
					        menuDisabled: true
					    },
					    
//					    {
//					        header: 'Event',											        
//					        dataIndex: 'type',
//					        menuDisabled: true,
//					        width: 70
//					        
//					        
//					    },
					    
//					    {
//					        header: 'Launched By',											        
//					        dataIndex: 'launched_by'												        
//					    },
					    {
					        header: 'Start Date',											        
					        dataIndex: 'start_date',
					        type: 'date',
					        width: 100,
					        sortable: true,
					        menuDisabled: true
					        
					    },
					    
					    {
					        header: 'End Date',											        
					        dataIndex: 'end_date',
					        type: 'date',
					        width: 100,
					        sortable: true,
					        menuDisabled: true
					        
					    },
					    
					    {
					        header: 'items completed',											        
					        dataIndex: 'items_completed',
					        width: 100,
					        menuDisabled: true,
					        renderer: items_columns_renderer('completed')
					        
					    },
					    
					    {
					        header: 'items failed',											        
					        dataIndex: 'items_failed',
					        menuDisabled: true,
					        width: 100,
					        renderer: function(value, metaData, record, rowIndex, colIndex, store){
					        	var id = record.data.id;
					        	var pipe_name = record.data.name;
					        	if (value == 0)
					        		return value;
					        	
							    return String.format('<a href="javascript:show_failures(\'{0}\', \'{2}\')"><b>{1}</b></a>', id,value, pipe_name);
							}
					    },
					    {
					        header: 'total items',											        
					        dataIndex: 'total_items',
					        menuDisabled: true,
					        width: 100,
					        renderer: items_columns_renderer('total')
					        
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
