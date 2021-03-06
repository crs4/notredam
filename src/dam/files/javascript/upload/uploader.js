
function upload_dialog(cfg){
	var uploader = this;
	
	var config = Ext.apply({
		singleSelect: false,
		url: '/upload_resource/',
		after_upload: function(session_id){},
		variant:'original',
		item: null,
        accept: []
	}, cfg);
	
	Ext.apply(this, config);
	
	this.upload_file = function(){
		var files_store = Ext.getCmp('files_list').getStore();
		var files_num = files_store.getCount();
		if (files_num === 0) {
			return;
                }
		files = files_store.data.items;
	
		
		var session_id = user + '_' + new Date().getTime();
		
		var files_length = files.length;
		var file;
		
		var params = {
			variant: uploader.variant,
			session: session_id,
			total: files_length,
			item: uploader.item
		};       
		
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
		  
		function _upload_file(i, files, session_id, params){
    		if (i >= files.length){
    			uploader.after_upload(session_id);
    			
    			return;
    		}
    		file = files[i].data.file;
			
			params.counter = i + 1;
			var final_params = Ext.urlEncode(params);
                        var xhr;
	                try { 
			    xhr = new XMLHttpRequest(); // FF, Chrome, IE7 or greater
                        } catch(e0) {
                             console.log(' \n==> Exception in new xhr e0: ' + e0);
                             try {
			       xhr = new ActiveXObject("MSXML2.XMLHTTP");
                             } catch(e1) {
                               try {
                                   console.log(' \n==> Exception in new xhr e1: ' + e1);
			           xhr = new ActiveXObject("Microsoft.XMLHTTP");
                                } catch(e2) {
                                     xhr = false;
                                     console.log(' \n==> Exception in new xhr e2: ' + e2);
                                }
                             }
                        }
			xhr.file_id = files[i].data.id;
			xhr.onreadystatechange = function(){
				
				var file_record = Ext.getCmp('files_list').getStore().query('id', this.file_id).items[0];
				//console.log('onreadystatechange '+ this.file_id + ': ' + xhr.readyState);
	            if (xhr.readyState == 4){
		        	if (xhr.status == 200){					        		
//		        		file_record.set('status', 'ok');
//						file_record.set('progress', 100);
//		        		file_record.commit();
		        		Ext.getCmp('progress_' + i).updateProgress(1, 'completed');
		        	}
		        	else if(xhr.status == 500){
//		        		file_record.set('status', 'failed');
//	        			file_record.commit();
		        		Ext.getCmp('progress_' + i).updateProgress(1, 'failed');
		        	}
		        	_upload_file(i+1, files, session_id, params);
		        }
		      
		        	
		    	
	        };
	        if (!Ext.isIE) { 
	        xhr.upload.onprogress = function(evt){
	        	if (evt.lengthComputable) {
	        		var complete = evt.loaded / evt.total;
		        	var percentComplete = Math.round((complete)*100);
		        	Ext.getCmp('progress_' + i).updateProgress(complete, percentComplete + '%');
	        	}
	        	
	        };
                } else {
                Ext.getCmp('progress_0').updateProgress(1, '100%');
                } 
	        
			
	        var progressbar = Ext.getCmp('progress_' + i);
	        if (progressbar.text == 'completed' || progressbar.text == 'aborted'){
	        	return _upload_file(i+1, files, session_id, params);
	        	
	        	}
	        	
	        	
			xhr.open("POST", this.url + '?'+ final_params, true);
	        xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");
	        xhr.setRequestHeader("X-File-Name", encodeURIComponent(file.name));
	        xhr.setRequestHeader("Content-Type", "application/octet-stream");
	        //xhr.setRequestHeader("Content-Length", file.size);
	        //var sepcode ="gc0p4Jq0M2Yt08jU534c0p";
            
	        /*xhr.setRequestHeader("Content-Type", "multipart/form-data; boundary=" + sepcode);
	        var sep = '--' + sepcode;
	        var crlf="\r\n";
	        
	        //var fbody = crlf + sep + 'Content-Disposition: form-data; name="lol"\r\n10' +  sep + '--';
	        var fbody =sep+crlf;
	        fbody+="Content-Disposition: form-data; name=\"field1\""+crlf+crlf;
	        fbody+="test field 1"+crlf;
	        
	        fbody+=sep;
			//file binario, un gif per esempio
			fbody+=crlf;
			// name = file2 nome del file smile.gif
			
			fbody += 'content-disposition: attachment; name="pics"; filename="file1.jpeg"' + crlf;
			fbody+="Content-Transfer-Encoding: base64"+crlf;
			// tipo del contenuto del file
			fbody+="Content-Type: image/gif"+crlf+crlf;
			//fbody += 'Content-Type: application/octet-stream' ;
			console.log(file);
			fbody += file.toString();
			
			//fbody+=crlf;
			// end del body
	        
	        
	        
	        fbody += sep + '--';
	        xhr.send(fbody);*/
	        //var formData = new FormData();
			//formData.append("username", "Groucho");
			//formData.append("accountnum", 123456);
			//formData.append("pics", file);
			//xhr.send(formData);
            //console.log('xhr send: ' + xhr.send());
	     if (!Ext.isIE) { 
            xhr.send(file);
             } else {
		 var mysession = user + '_' + new Date().getTime();
                 Ext.getCmp('form_upload').getForm().submit({
                 	params:{session:mysession},
			success: function(){
				cfg.after_upload(mysession);
			},
		        failure: function() {Ext.Msg.alert('Error','An upload error occurs server side, sorry.');}	
			});
             }

	        //xhr.send('\r\n--gc0p4Jq0M2Yt08jU534c0p' + 'Content-Disposition: form-data; name="paramname"; filename="foo.txt" Content-Type: text/plain\r\n ... file contents here ...' + '--gc0p4Jq0M2Yt08jU534c0p--');
	
		};
		
		_upload_file(0, files, session_id, params);
	
	};	
	var file_counter = 0;
	
    var progressbar_renderer = function(value, meta, rec, row, col, store){
    	
    	
	    var id = Ext.id();
	    var is_int = parseInt(value);
	    var text;
	    
	    if (isNaN(is_int)) {
	        text = value;
	        value = 0;
	    }
	    else {
	        text = value + '%';
	    }
	    
	    (function() {
	        var progress_id = 'progress_' + row;
	        new Ext.ProgressBar({
	            renderTo: id,
	            value: value,
	            animate: true,
	            text: text,
	            width: 200,
	            id: progress_id
	        });
	    }).defer(25);
	    
	    return '<span id="' + id + '"></span>';
	}

       
	
	
	this.win =  new Ext.Window({
			id: 'upload_win',
            title    : 'Upload',
            resizable: true,
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
                            new Ext.form.FormPanel({
                                id: 'form_upload',
                                url: config.url,
                                renderTo: 'upload',
                                fileUpload: true,
                                //width:100,
                                layout:'fit',
                                //frame: true,
                                //cls: 'x-toolbar',
                                bodyStyle : 'background-color:#D0DEF0; border-width:0;',
                                //baseClass: 'x-toolbar',
                                //frame: true,
                                items:
                                new Ext.ux.form.FileUploadField({			        
                                id: 'files_to_upload',
                                buttonOnly: true,
                                
                                singleSelect: config.singleSelect,
                                
                                buttonCfg: {
                                    icon: '/files/images/icons/fam/add.gif',
                                    text: 'Browse'
                                },
                                listeners:{
                                    fileselected: function(fb, v){
                                        
                                        var files = [];
                                        var size;
                                        if (self.accept.length > 0){
                                            var accepted = true;
                                             Ext.each(Ext.get('files_to_upload-file').dom.files, function(file){
                                                var inner_accepted = false;
                                                Ext.each(self.accept, function (ext){
                                                    var regexp = new RegExp('\.'+ ext+'$');
                                                    if (regexp.test(file.name)){
                                                        
                                                        inner_accepted = true;
                                                        return false;
                                                    }   
                                                });
                                                if (!inner_accepted){
                                                    accepted = false;
                                                    return false;
                                                }
                                                 
                                               });
                                            if(!accepted){
                                                Ext.Msg.alert('Error', 'Please choose an archive file');
                                                return;
                                            }
                                                
                                        }    
                                        if (Ext.isIE) {
                                            my_files = v.replace(/^.*[\\\/]/, '');
                                        } else {
                                            my_files = Ext.get('files_to_upload-file').dom.files;
                                        }
              
                                        //Ext.each(Ext.get('files_to_upload-file').dom.files, function(file){
                                        Ext.each(my_files, function(file){
                                            if (Ext.isIE) {
                                                var my_size = 1000;
                                                var afile = {'name': my_files, 'size' : my_size};
                                                files.push({
                                                    id: file_counter,
                                                    file: afile,
                                                    filename: my_files,
                                                    size: 1000,
                                                    status: 'to_upload',
                                                    progress: 0
                                               });
                                            } else { 
                                                size = parseInt(file.size/1024) + ' KB';
                                                files.push({
                                                    id: file_counter,
                                                    file: file,
                                                    filename: file.name,
                                                    size: size,
                                                    status: 'to_upload',
                                                    progress: 0
                                                });
                                            }
                                            file_counter += 1;				        				
                                        });
                                        
                                        Ext.getCmp('files_list').getStore().loadData({
                                            files: files
                                        }, true);
                                    }
                                }
                                })
                            })
				    			
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
            		var files_num = Ext.getCmp('files_list').getStore().getCount();
            		for(var i = 0; i<files_num; i++) {
            			Ext.getCmp('progress_'+i).updateProgress(1, 'aborted');
            		}
            			
            	
            		
            	
            	}
            
            }
            ],
            
            items: new Ext.Panel({
            	id: 'files_list_container',
            	border: false,
            	layout: 'fit',
            	autoScroll: true,
            	items:new Ext.grid.GridPanel({
            	id: 'files_list',
            	
//            	frame: true,
            	layout: 'fit',
            	autoHeight: true,
//            	height: 300,
            	border: false,
            	viewConfig: {
            		forceFit: true,
            		border: false
            	
            	},
            	store: new Ext.data.JsonStore({
            		root: 'files',
            		fields:['id', 'file', 'filename', 'size', 'status', 'progress']            		
            	}),
            	 columns: [{
			        header: 'File',			        
			        dataIndex: 'filename',
			        sortable: false,			        
			        menuDisabled: true
//			        cls: 'upload-row'
			    	},
			    	{
			        header: 'Size',			        
			        dataIndex: 'size',
			        width: 25,
			        sortable: false,
			        menuDisabled: true
//			        cls: 'upload-row'
				    },
			    	{
			        header: 'Progress',			        
			        dataIndex: 'progress'	,
			        width: 60,
			        sortable: false,
			        menuDisabled: true,
			        //cls: 'upload-row',
//			        tpl: '<p class="upload_{status}"/>'
			        renderer: progressbar_renderer
			    }]
            }) 
            
            }) 
            
            


        });
	this.win.show();
	
		

	
};
