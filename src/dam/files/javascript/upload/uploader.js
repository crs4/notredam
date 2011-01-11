
var Upload = function(upload_url, single_file, post_params, done_callback) {
	
    this.record_entries = [    
        {name:'queue_id', type: 'int'},    
        {name:'filename', type: 'string'},
        {name:'size', type: 'string'}
    ];
    
    this.metadata_upload_records = [];

    this.reset = function() {

        this.swfu.cancelQueue();

        upload_grid = Ext.getCmp('upload_grid');
        if (upload_grid)
            upload_grid.getStore().removeAll();
    
    };

    this.abort = function() {

        this.swfu.stopUpload();
    
    };

    this.getFileSize = function(file){
        
        var size = file.size;
        var dim;
        
        var KB = 1024;
        var MB = Math.pow(KB,2);
        var GB = Math.pow(KB,3);
            
        if (size < MB){
            dim = 'KB';
            size = size/KB;
        }
        else
            if  (size < GB){
                dim = 'MB';
                size = size/MB;
            }
            else{
                dim = 'GB';
                size = size/GB;
            }

        size = Math.round(size*10)/10;
            
        size = '' + size +  ' ' + dim;

        return size;
            
    };

    this.updateGrid = function(file, value, value_text) {
    
        var upload_grid = Ext.getCmp('upload_grid');

        if (upload_grid) {
            var store = upload_grid.getStore();
            var r_index = store.find('queue_id', file.index);
            var r = store.getAt(r_index);
            var progressBar = Ext.getCmp('progress_' + r_index);
            progressBar.updateProgress(value, value_text);
        }

    };

    this.fileQueuedHandler = function(file) {
    
        var upload_grid = Ext.getCmp('upload_grid');

        if (upload_grid) {
            var p = new Ext.data.Record({
                queue_id: 0,
                filename: file.name,
                size: file.size,
                progress: 0.0
            });
            upload_grid.getStore().add(p);
        }
    };
    
    this.uploadStartHandler = function(file) {

        var upload_grid = Ext.getCmp('upload_grid');

        if (upload_grid) {

            var store = upload_grid.getStore();

            var r_index = store.find('queue_id', file.index);
            var r = store.getAt(r_index);
            
            var fields = this.customSettings.uploader.metadata_upload_records;
            var record_name, value;
            
            for (var i=0; i < fields.length; i++) {
                record_name = 'metadata_' + fields[i].id;
                value = r.get(record_name);
                if (value) {
                    this.addFileParam(file.id, record_name, value);
                }
            }
                        
        }

    };

    
    this.uploadSuccessHandler = function(file) {

        var value = 1;
        var text = 'Completed';

        this.customSettings.uploader.updateGrid(file, value, text);
        
    };

    this.uploadProgressHandler = function(file, bytesUploaded, bytesTotal) {

        var progress = bytesUploaded/bytesTotal;

        var value = progress;
        var text = Math.round(progress*100) + '%';

        this.customSettings.uploader.updateGrid(file, value, text);
        
    };
    
    this.queueCompleteHandler = function(upload_count) {

        if (done_callback){
        	done_callback();
        }else{
	    	Ext.MessageBox.alert('Upload',  upload_count + ' object(s) uploaded successfully.');    
	
	        var tab = Ext.getCmp('media_tabs').getActiveTab();
	        var view = tab.getComponent(0);
	        var selecteds = view.getSelectedRecords();
	        var store = view.getStore();
	        store.reload({
	            scope: view,
	            callback:function(){
	                ids = []
	                for(i = 0; i<selecteds.length; i++){
	                    ids.push(selecteds[i].data.pk)
	                    }
	                this.select(ids)
	                
	                }
	            });
        }
    
    };

    this.uploadErrorHandler = function(file, errorCode, message) {

        var value = 0;
        var text = 'Error';

        try {    
            switch (errorCode) {
                case SWFUpload.UPLOAD_ERROR.HTTP_ERROR:
                    text = "Upload Error: " + message;
                    break;
                case SWFUpload.UPLOAD_ERROR.UPLOAD_FAILED:
                    text = "Upload Failed.";
                    break;
                case SWFUpload.UPLOAD_ERROR.IO_ERROR:
                    text = "Server (IO) Error";
                    break;
                case SWFUpload.UPLOAD_ERROR.SECURITY_ERROR:
                    text = "Security Error";
                    break;
                case SWFUpload.UPLOAD_ERROR.UPLOAD_LIMIT_EXCEEDED:
                    text = "Upload limit exceeded.";
                    break;
                case SWFUpload.UPLOAD_ERROR.FILE_VALIDATION_FAILED:
                    text = "Failed Validation.  Upload skipped.";
                    break;
                case SWFUpload.UPLOAD_ERROR.FILE_CANCELLED:
                    text = 'Aborted';
                    break;
                case SWFUpload.UPLOAD_ERROR.UPLOAD_STOPPED:
                    text = 'Aborted';
                    break;
                default:
                    text = "Unhandled Error: " + errorCode;
                    break;
            }
            
            this.customSettings.uploader.updateGrid(file, value, text);
            
        } catch (ex) {
            console.log(ex);
        }
    }

    this.initUploader = function() {

        var obj = this;
        var i;

        for (i = 0; i < this.metadata_upload_records.length; i++){
            this.record_entries.push({name: 'metadata_' + this.metadata_upload_records[i].id, type: 'string'});
        }

        this.record_entries.push({name:'progress', type: 'string'})

        this.UploadFile = Ext.data.Record.create(this.record_entries);

        var store = new Ext.data.SimpleStore({
            fields :this.record_entries
        });

        var progressbar_renderer = function(value, meta, rec, row, col, store){
            
            var id = Ext.id();
            var is_int = parseInt(value)
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

        var columns = [
            new Ext.grid.RowNumberer(), {
                id:'filename',
                header: "Filename",
                dataIndex: 'filename',
                sortable: false,
                menuDisabled: true
            }, 
            {
                header: "Size",
                dataIndex: 'size',
                sortable: false,
                menuDisabled: true
            }
        ];

        for(i = 0; i < this.metadata_upload_records.length; i++) {
            columns.push({
                header: this.metadata_upload_records[i].name,
                sortable: false,
                menuDisabled: true,
                dataIndex: 'metadata_' + this.metadata_upload_records[i].id,
                editor: new Ext.form.TextField({
                    allowBlank: true
                })
            });
        }

        columns.push({
            header: "Progress",
            dataIndex: 'progress',
            renderer: progressbar_renderer,
            width:220,
            sortable: false,
            menuDisabled: true
        });
                
        var cm = new Ext.grid.ColumnModel(columns);

        var tbar_grid = [
        	new Ext.ux.form.FileUploadField({
		        buttonOnly: true,
		        id: 'add_files',
		        buttonText: 'Add Files',
		        iconCls: 'add_icon',
		        
		        name:'Filedata',
		        
		        listeners: {
		            fileselected: function(fb, v){
		            	console.log(fb);
		            	console.log(v);
		            	obj.fileQueuedHandler(fb.fileInput.dom.files[0])

		            }
		        }
		    }),
        
            new Ext.Button({
                text: 'Upload',
                iconCls: 'upload',
                handler: function() {
//                    Ext.getCmp("upload_form").getForm().submit()
					var input =Ext.getCmp('add_files').fileInput.dom;
					input.setAttribute('disabled', 'true');
					 sendMultipleFiles({
                		url: '/upload_resource/',
                    // list of files to upload
                    	files:input.files});

					
					
					
                	
//                    var swfu = obj.swfu;
//
//            		var stats = swfu.getStats();
//                    var queued = stats.files_queued;
//                    
//                    var start = stats.successful_uploads + stats.upload_errors
//                    
//                    Ext.Ajax.request({
//                        url:'/get_upload_url/',
//                        params: {n: queued},
//                        success: function(resp){
//                            var resp_json = Ext.util.JSON.decode(resp.responseText)
//                            var urls = resp_json.urls;
//                            var file;
//                            var x=0;
//                            for (var i=start; i < queued + start; i++) {
//                                file = obj.swfu.getFile(i);
//                                obj.swfu.addFileParam(file.id, 'unique_url', urls[x++]);
//                            }
//                            
//                            obj.swfu.startUpload();
//                        },
//                        failure: function() {
//                            console.log('error retrieving urls');
//                        }
//                    });
                }   
            }),
            {
                text: 'Clear',
                iconCls: 'clear_icon',
                handler : function(){
                    obj.reset();
                }
            }, {
                text: 'Abort',
                iconCls: 'abort_icon',
                handler : function(){
                    obj.abort();
                }
            }
        ];
                
        this.grid = new Ext.grid.EditorGridPanel({
            store: store,
            cm: cm,
            autoExpandColumn: 'filename',
            clicksToEdit: 1,
            stripeRows: true,
            height: 300,
            layout: 'fit',
            tbar: tbar_grid,
            id: 'upload_grid',
            listeners: {
                beforeedit:function(obj){
                    var prg = Ext.getCmp('progress_' + obj.row)
                    if (prg.value == 0)                             
                        return true;
                    return false;                    
                }                
            }
        });

        this.win = new Ext.Window({
            title    : 'Upload',
            closable : true,
            width    : 800,
            height   : 350,
            plain    : true,
            layout   : 'fit',
            items    : [
//            	new Ext.ux.UploadPanel()

            new Ext.form.FormPanel({
            	id: 'upload_form',
            	 fileUpload: true,
            	items:[this.grid,
            		new Ext.form.Hidden({
            			name: 'session',
            			value: document.cookie.split('=')[1] + '_' +  new Date().getTime()
            		})
            	
            	],
            	url: '/upload_item/'
            	})
            ],
            modal:true
        });
    
        this.win.show();
    
    }
        
    this.getGrid  = function(){
        return this.grid;
    };

    this.openUpload = function(menu_item) {

        var obj = this;
    
        var metadata_upload_store = new Ext.data.JsonStore({
            url:'/get_metadata_upload/',
            fields: ['name', 'pk'],
            root: 'schemas'
        });
            
        metadata_upload_store.load({
            callback: function(){
                this.each(function(r){obj.metadata_upload_records.push({id: r.data.pk, name:r.data.name, type: 'string'});});
                obj.initUploader();
            }
        });

    };
    

};

function upload_dialog(){
	var win = new Ext.Window({
            title    : 'Upload',
            closable : true,
            width    : 800,
            height   : 350,
            plain    : true,
            layout   : 'fit',
            items    : [
//            		new Ext.BoxComponent({
//					    autoEl: {
//					        tag: 'div',
//					        id: 'upload'
//					    }
//					}),
//            	
            new Ext.form.FormPanel({
            	id: 'upload_form',
            	items:[

            		new Ext.ux.form.FileUploadField({				        
				        width: 400,
				        name: 'FileData'
				    }),
				    new Ext.form.Hidden({
				    	name:'variant',
				    	value: 'original'
				    
				    	
				    }),
				    
				    new Ext.form.Hidden({
				    	name:'session',
				    	value: 'test'
				    
				    	
				    })
				    
            	],
            	buttons:[{
            		text: 'Upload',
            		handler: function(){
            			var up = new Uploader(Ext.get('upload_form').dom);
            			up.send();
            		}
            		
            		
            		}
            	]
            
            })
            
            
//            	new Ext.ux.UploadPanel({
//            				 buttonsAt:'tbar'
//							 ,id:'uppanel'
//							 ,url:'/upload_resource/'
//							 ,path:'root'
//							 ,maxFileSize:1048576
////			 ,enableProgress:false
////			 ,singleUpload:true
//
//            	
//            	})
            ],
            modal:true
//            listeners:{
//            	afterrender: function(){
//	            	var uploader = new qq.FileUploader({
//					    action: '/upload_resource/',
//					    element: Ext.get('upload').dom,
//					    params:{
//					    	variant:'original',
//					    	session: 'ffffu'
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