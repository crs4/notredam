
function upload_dialog(){
	var uploader;
	var file_counter = 0;
	
	var win = new Ext.Window({
			id: 'upload_win',
            title    : 'Upload',
            closable : true,
            width    : 800,
            height   : 350,
            //plain    : true,
            layout   : 'fit',
            buttonAlign: 'left',
            _upload_more: function(){
    			Ext.getCmp('files_list').getStore().removeAll();
    			
    			
    		},
    		_show_monitor: function (){
    			this._close_upload();
    			show_monitor();
    			
    			
    		}, 
            		
    		_close_upload: function (){    			
    			this.close();
    			
    		},
            
            
//			bbar:[{
//				text: 'Upload More files'
//				
//			},
//			{
//				text: 'progress monitor'
//			}
//			],
            modal: true,
            
            tbar:[
        		new Ext.BoxComponent({
				    autoEl: {
				        tag: 'div',
				        id: 'upload'
				    },
				    listeners:{
				    	afterrender: function(){
				    		new Ext.ux.form.FileUploadField({			        
				        	id: 'files_to_upload',
				        	buttonOnly: true,
				        	renderTo: 'upload',
				        	
				        	buttonCfg: {
				        		icon: '/files/images/icons/fam/add.gif',
				        		text: 'Browse'
				        	},
				        	listeners:{
				        		fileselected: function(fb, v){
				        			
				        			var files = [];
				        			var size;
				        			Ext.each(Ext.get('files_to_upload-file').dom.files, function(file){
				        				size = parseInt(file.size/1024) + ' KB';
				        				files.push({
				        					id: file_counter,
				        					file: file,
				        					filename: file.name,
				        					size: size,
				        					status: 'to_upload'
				        				});
				        				file_counter += 1;				        				
				        			});
				        			
				        			Ext.getCmp('files_list').getStore().loadData({
				        				files: files
				        			}, true);
				        		}
				        	}
	            			});    
				    			
				    	}				    
				    }
				}),
            {
            	text: 'Upload',
            	icon:'/files/images/icons/arrow-up.gif',
            	handler: function(){
            		var files_store = Ext.getCmp('files_list').getStore();
            		var files = files_store.query('status', 'to_upload').items;
            		if (files.length == 0)
            			return;
            		files_store.filterBy(function(r){
            			return (r.data.status == 'to_upload')
            		});
            		
            		var session_id = user + '_' + new Date().getTime();
            		
            		
            		
            		var files_length = files.length;
            		var file;
            		var params = {
            			variant:'original',
            			session: session_id,
            			total: files_length 
            		};            		
            		
            		
            		
            		function upload_file(i, files, session_id, params){
	            		if (i >= files.length){
	            			Ext.Ajax.request({
			                	url: '/upload_session_finished/',
			                	params: {session: session_id},
			                	success: function(){
			                		var tab = Ext.getCmp('media_tabs').getActiveTab();
					                var view = tab.getComponent(0);
					                var selecteds = view.getSelectedRecords();
					                var store = view.getStore();
//					                win.getEl().mask('<p style="font-size:15px; margin-bottom: 50px;">Upload Finished</p><button type="button" onclick="function(){console.log(\'aaaaaaaa\')};">Upload more files</button><button>Show monitor</button><button>Close</button>')
					                var uploads_failed = Ext.getCmp('files_list').getStore().query('status', 'failed').items.length;
					                var uploads_success = Ext.getCmp('files_list').getStore().query('status', 'ok').items.length;
					                var buttons = []
					                
					                if (uploads_failed > 0) 
					                	buttons.push({
							            	text: 'Retry failed upload',							            	
							            	handler: function(){							            		
							            	}							            
							            });
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
	            			
	            			
	            			
	            			
			                    
			                
	            			return;
	            		}
	            		file = files[i].data.file;
	        			
	        			params.counter = i + 1;
	        			var final_params = Ext.urlEncode(params);
	        			var xhr = new XMLHttpRequest();
	        			xhr.file_id = files[i].data.id;
	        			xhr.onreadystatechange = function(){
	        				
	        				var file_record = Ext.getCmp('files_list').getStore().query('id', this.file_id).items[0];
	        				console.log('onreadystatechange '+ this.file_id + ': ' + xhr.readyState);
				            if (xhr.readyState == 4){
					        	if (xhr.status == 200){					        		
					        		file_record.set('status', 'ok');
					        		file_record.commit();
					        	}
					        	else if(xhr.status == 500){
					        		file_record.set('status', 'failed');
				        			file_record.commit();
					        	}
					        	upload_file(i+1, files, session_id, params);
					        }
					      
					        	
					    	
				        };
	        			
	        			
	        			xhr.open("POST", '/upload_resource/?'+ final_params, true);
				        xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");
				        xhr.setRequestHeader("X-File-Name", encodeURIComponent(file.name));
				        xhr.setRequestHeader("Content-Type", "application/octet-stream");
				        
				        var file_record = Ext.getCmp('files_list').getStore().getAt(i);
				        file_record.set('status', 'inprogress');
				        file_record.commit();
				        
				        xhr.send(file);
            	
            		};
            		
					upload_file(0, files, session_id, params);
				    	
            	}
            	
            },
            {
            	text: 'Abort',
            	icon: '/files/images/icons/fam/delete.gif',
            	handler: function(){
            		var files = Ext.getCmp('files_list').getStore().query('status', 'to_upload').items;
            		
            		Ext.each(files, function(file){
            			file.set('status', 'aborted');	
            			file.commit();
            		
            		});
            		
            			
            	
            		
            	
            	}
            
            }
            ],
            
            items: new Ext.Panel({
            	id: 'files_list_container',
            	border: false,
            	items:new Ext.list.ListView({
            	id: 'files_list',
            	frame: true,
            	store: new Ext.data.JsonStore({
            		root: 'files',
            		fields:['id', 'file', 'filename', 'size', 'status']            		
            	}),
            	 columns: [{
			        header: 'File',			        
			        dataIndex: 'filename',
			        cls: 'upload-row'
			    	},
			    	{
			        header: 'Size',			        
			        dataIndex: 'size',
			        width: .3,
			        cls: 'upload-row'
				    },
			    	{
			        header: 'Status',			        
			        dataIndex: 'status'	,
			        width: .07,
			        //cls: 'upload-row',
			        tpl: '<p class="upload_{status}"/>'
			    }]
            }) 
            
            }) 
            
            


        });
	win.show();
	
		

	
};