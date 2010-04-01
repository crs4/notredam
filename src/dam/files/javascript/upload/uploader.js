
var Upload = function() {

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
            var p = new this.customSettings.uploader.UploadFile({
                queue_id: file.index,
                filename: file.name,
                size: this.customSettings.uploader.getFileSize(file),
                progress: 0.0
            });
            upload_grid.getStore().add(p);
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

    this.record_entries = [
        {name:'queue_id', type: 'int'},    
        {name:'filename', type: 'string'},
        {name:'size', type: 'string'}
    ];

    this.record_entries.push({name:'progress', type: 'string'})
    this.UploadFile = Ext.data.Record.create(this.record_entries);

    var obj = this;

    var store = new Ext.data.SimpleStore({
        fields :this.record_entries
    });

    var progressbar_renderer = function(value, meta, rec, row, col, store){
        
        var id = Ext.id();
        is_int = parseInt(value)
        
        if (isNaN(is_int)) {
            text = value;
            value = 0;
        }
        else {
            text = value + '%';
        }
        (function() {
            progress_id = 'progress_' + row
            new Ext.ProgressBar({
                renderTo: id,
                value: value,
                animate: true,
                text: text,
                width:200,
                id: progress_id
                });
                //console.log('progress_id' + progress_id)
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
                
                
    columns.push( {
        header: "Progress",
        dataIndex: 'progress',
        renderer: progressbar_renderer,
        width:220,
        sortable: false,
        menuDisabled: true
    });
                
    var cm = new Ext.grid.ColumnModel(columns);

    var tbar_grid = [{
            text: 'Add File',
            iconCls: 'add_icon',
            listeners: {
                render: function() {
                    var element = this.getEl();
                    element.child('em').insertFirst({tag: 'span', id: 'btnUploadHolder'});                    

                    var settings_object = {
                        upload_url : "/flex_upload/",
                        flash_url : "/files/javascript/swfupload/swfupload.swf",
                        file_queue_limit : 0,
                        button_placeholder_id: "btnUploadHolder",
			    		button_window_mode: SWFUpload.WINDOW_MODE.TRANSPARENT,
                    	button_action : SWFUpload.BUTTON_ACTION.SELECT_FILES,
                        button_width: element.getWidth(),
                        button_height: element.getHeight(),
                        file_queued_handler : obj.fileQueuedHandler,
//                        upload_start_handler : obj.uploadStartHandler,
                        upload_progress_handler: obj.uploadProgressHandler,
                        upload_error_handler: obj.uploadErrorHandler,
                        upload_success_handler: obj.uploadSuccessHandler,
//                        upload_complete_handler: obj.uploadCompleteHandler,
                        custom_settings: {
                            uploader: obj
                        }
                    };
                    
                    obj.swfu = new SWFUpload(settings_object);
                    
                }
            }
        },
        new Ext.Button({
            text: 'Upload',
            iconCls: 'upload',
            handler: function() {
                obj.swfu.startUpload();
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
       }];
            
                
    this.grid = new Ext.grid.EditorGridPanel({
        store: store,
        cm: cm,
        autoExpandColumn:'filename',
        clicksToEdit:1,
        stripeRows: true,
        height:300,
        layout   : 'fit',
        tbar: tbar_grid,
        id: 'upload_grid',
        listeners:{
            beforeedit:function(obj){
                //console.log('beforeedit');
                //console.log('obj.record.data.Progress');
                //console.log(obj.record.data.Progress);
                prg = Ext.getCmp('progress_' + obj.row)
                //console.log('prg.value ' + prg.value)
                if (prg.value == 0)                             
                    return true;
                //console.log('edit forbidden');
                return false;
                
                }
            
            }            
    });
            
    this.win = new Ext.Window({
        title    : 'Upload',
        closable : true,
        width    : 800,
        height   : 350,
        //border : false,
        plain    : true,
        layout   : 'fit',
        items    : [this.grid],
        modal:true,           
        
        listeners:{
            close: function(){
                if(obj.new_keywords){
                    keywords_tree = Ext.getCmp('keywords_tree')
                    root = keywords_tree.getRootNode()
                    new_keywords = root.findChild('text', 'New Keywords')
                    tree_loader.load(new_keywords, function(){new_keywords.expand()})
                }
            }
            
        }
    });
    
        
    this.getGrid  = function(){
        return this.grid;
    };

    this.openUpload = function(menu_item) {
        this.win.show(menu_item);
    };
    
    this.uploadStart = function(file) {
        console.log(file);
    };


};
