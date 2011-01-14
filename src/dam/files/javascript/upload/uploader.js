
function upload_dialog(){
	var uploader;
	var win = new Ext.Window({
            title    : 'Upload',
            closable : true,
            width    : 800,
            height   : 350,
            plain    : true,
            layout   : 'fit',

            items    : [
            		new Ext.BoxComponent({
					    autoEl: {
					        tag: 'div',
					        id: 'upload'
					    }
					})

            ],
            modal:true,
            listeners:{
            	afterrender: function(){
            		var session_id = user + '_' + new Date().getTime();
	            	var uploader = new qq.FileUploader({
					    action: '/upload_resource/',
					    element: Ext.get('upload').dom,
					    params:{
					    	variant:'original',
					    	session: session_id
					    }
					    
					});
            	
            	
            	}
            }
        });
	win.show();
	
		

	
};