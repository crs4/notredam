
function upload_dialog(){
	var uploader;
	var file_counter = 0;
	
	var win = new Ext.Window({
            title    : 'Upload',
            closable : true,
            width    : 800,
            height   : 350,
            plain    : true,
            layout   : 'fit',
            buttonAlign: 'left',
            
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
				        				size = file.size/1024;
				        				files.push({
				        					id: file_counter,
				        					file: file,
				        					filename: file.name,
				        					size: size
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
            		files = Ext.get('files_to_upload-file').dom.files;
            		var session_id = user + '_' + new Date().getTime();
            		var files_length = files.length;
            		
            		var params = {
            			variant:'original',
            			session: session_id,
            			total: files_length 
            		};
            		
            		for(var i = 0; i < files_length; i++){
            			
            			params.counter = i + 1;
            			var final_params = Ext.urlEncode(params);
            			var xhr = new XMLHttpRequest();
            			xhr.file_id = i;
            			xhr.onreadystatechange = function(){            
				            if (xhr.readyState == 4)
					        	if (xhr.status == 200){
					        		console.log(this.file_id);
					        		console.log(Ext.getCmp('files_list').getStore().getAt(this.file_id));
					        		Ext.getCmp('files_list').getStore().getAt(this.file_id).data.status = 'ok';
					        	}
					        	else{
					        	
					        	}
					        		
					    	
				        };
            			
            			
            			xhr.open("POST", '/upload_resource/?'+ final_params, true);
				        xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");
				        xhr.setRequestHeader("X-File-Name", encodeURIComponent(files[i].name));
				        xhr.setRequestHeader("Content-Type", "application/octet-stream");
				        xhr.send(files[i]);
            		
            		}
            	
            	}
            	
            }],
            
            items: new Ext.list.ListView({
            	id: 'files_list',
            	store: new Ext.data.JsonStore({
            		root: 'files',
            		fields:['id', 'file', 'filename', 'size', 'status']            		
            	}),
            	 columns: [{
			        header: 'File',			        
			        dataIndex: 'filename'
			    	},
			    	{
			        header: 'Size',			        
			        dataIndex: 'size'			        
				    },
			    	{
			        header: 'Status',			        
			        dataIndex: 'status'			        
			    }]
            })


        });
	win.show();
	
		

	
};