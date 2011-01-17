
function upload_dialog(){
	var uploader;
	var win = new Ext.Window({
            title    : 'Upload',
            closable : true,
            width    : 800,
            height   : 350,
            plain    : true,
            layout   : 'fit',
            buttonAlign: 'left',
            
            tbar:[{
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
            			if (i == files_length -1)
            				params.counter = i + 1;
            			
            			var final_params = Ext.urlEncode(params);
            			var xhr = new XMLHttpRequest();
            			xhr.open("POST", '/upload_resource/?'+ final_params, true);
				        xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");
				        xhr.setRequestHeader("X-File-Name", encodeURIComponent(files[i].name));
				        xhr.setRequestHeader("Content-Type", "application/octet-stream");
				        xhr.send(files[i]);
            		
            		}
            	
            	}
            	
            }],
            items: new Ext.ux.form.FileUploadField({			        
			        id: 'files_to_upload',
			        buttonOnly: true,
            })

//            items    : [
//            		new Ext.BoxComponent({
//					    autoEl: {
//					        tag: 'div',
//					        id: 'upload'
//					    }
//					})
//
//            ],
//            modal:true,
//            listeners:{
//            	afterrender: function(){
//            		var session_id = user + '_' + new Date().getTime();
//	            	var uploader = new qq.FileUploader({
//					    action: '/upload_resource/',
//					    element: Ext.get('upload').dom,
//					    params:{
//					    	variant:'original',
//					    	session: session_id
//					    }
//					    
//					});
//            	
//            	
//            	}
//            }
        });
	win.show();
	
		

	
};