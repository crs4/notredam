
function upload_dialog(){
	var uploader;
	var file_counter = 0;
	
	var win = new Ext.Window({
            title    : 'Upload',
            closable : true,
            width    : 800,
            height   : 350,
            //plain    : true,
            layout   : 'fit',
            buttonAlign: 'left',
            //frame: true,
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
				        	buttonText: 'Browse',
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
            	handler: function(){
            		
            		var session_id = user + '_' + new Date().getTime();
            		
            		
            		
            		
            		var files = Ext.getCmp('files_list').getStore().query('status', 'to_upload').items;
            		var files_length = files.length;
            		var file;
            		var params = {
            			variant:'original',
            			session: session_id,
            			total: files_length 
            		};
            		
            		for(var i = 0; i < files_length; i++){
            			file = files[i].data.file;
            			
            			params.counter = i + 1;
            			var final_params = Ext.urlEncode(params);
            			var xhr = new XMLHttpRequest();
            			xhr.file_id = files[i].data.id;
            			xhr.onreadystatechange = function(){
            				
            				var file_record = Ext.getCmp('files_list').getStore().query('id', this.file_id).items[0];
            				console.log('onreadystatechange '+ this.file_id + ': ' + xhr.readyState);
				            if (xhr.readyState == 4)
					        	if (xhr.status == 200){
					        		console.log('----------------finished upload of ' + this.file_id);
					        		file_record.set('status', 'ok');
					        		file_record.commit();
					        	}
					        	else if(xhr.status == 500){
					        		file_record.set('status', 'failed');
				        		file_record.commit();
					        }
					      
					        	
					    	
				        };
            			
            			
            			xhr.open("POST", '/upload_resource/?'+ final_params, false);
				        xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");
				        xhr.setRequestHeader("X-File-Name", encodeURIComponent(file.name));
				        xhr.setRequestHeader("Content-Type", "application/octet-stream");
				        
				        var file_record = Ext.getCmp('files_list').getStore().getAt(i);
				        file_record.set('status', 'inprogress');
				        file_record.commit();
				        
				        xhr.send(file);
				        if (xhr.status == 200){
			        		console.log('----------------finished upload of ' + this.file_id);
			        		file_record.set('status', 'ok');
			        		file_record.commit();
			        	}
			        	else if(xhr.status == 500){
			        		file_record.set('status', 'failed');
		        		file_record.commit();
				        }
				        
				        
				        
				        
            		
            		}
            	
            	}
            	
            },
            {
            	text: 'Abort',
            	handler: function(){
            		var files = Ext.getCmp('files_list').getStore().query('status', 'to_upload').items;
            		
            		Ext.each(files, function(file){
            			file.set('status', 'aborted');	
            			file.commit();
            		
            		});
            		
            			
            	
            		
            	
            	}
            
            }
            ],
            
            items: new Ext.list.ListView({
            	id: 'files_list',
            	frame: true,
            	store: new Ext.data.JsonStore({
            		root: 'files',
            		fields:['id', 'file', 'filename', 'size', 'status']            		
            	}),
            	 columns: [{
			        header: 'File',			        
			        dataIndex: 'filename',
			        cls: 'upload-row',
			    	},
			    	{
			        header: 'Size',			        
			        dataIndex: 'size',
			        width: .3,
			        cls: 'upload-row',
				    },
			    	{
			        header: 'Status',			        
			        dataIndex: 'status'	,
			        width: .07,
			        //cls: 'upload-row',
			        tpl: '<p class="upload_{status}"/>'
			    }]
            })


        });
	win.show();
	
		

	
};