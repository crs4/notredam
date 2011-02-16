function upload_dialog(cfg){
	var uploader = this;
	
	var config = Ext.apply({
		singleSelect: false,
		url: '/upload_resource/',
		after_upload: function(session_id){},
		variant:'original',
		item: null,
	}, cfg);
	
	Ext.apply(this, config);
	
	this.upload_file = function(){
		var _show_monitor =  function (){
			_close_upload();
			show_monitor();
		}; 
        		
		var _close_upload =  function (){    			
			this.close();
			
		};
		
		var	_upload_more = function(){
			Ext.getCmp('files_list').getStore().removeAll();
		};
		
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
			variant: uploader.variant,
			session: session_id,
			total: files_length,
			item: uploader.item
		};            		
		
		
		
		function _upload_file(i, files, session_id, params){
    		if (i >= files.length){
    			uploader.after_upload(session_id);
    			
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
		        	_upload_file(i+1, files, session_id, params);
		        }
		      
		        	
		    	
	        };
			
			
			xhr.open("POST", this.url + '?'+ final_params, true);
	        xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");
	        xhr.setRequestHeader("X-File-Name", encodeURIComponent(file.name));
	        xhr.setRequestHeader("Content-Type", "application/octet-stream");
	        
	        var file_record = Ext.getCmp('files_list').getStore().getAt(i);
	        file_record.set('status', 'inprogress');
	        file_record.commit();
	        
	        xhr.send(file);
	
		};
		
		_upload_file(0, files, session_id, params);
	
	};
	
	var file_counter = 0;
	
	this.win =  new Ext.Window({
			id: 'upload_win',
            title    : 'Upload',
            closable : true,
            width    : 800,
            height   : 350,
            //plain    : true,
            layout   : 'fit',
            buttonAlign: 'left',
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
				        	singleSelect: config.singleSelect,
				        	
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
					uploader.upload_file();
				    	
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
	this.win.show();
	
		

	
};