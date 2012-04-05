// Initialize the state provider
Ext.state.Manager.setProvider(new Ext.air.FileProvider({
	file: 'notredam.state',
	// if first time running
	defaultState : {
		mainWindow : {
			width:780,
			height:580,
			x:10,
			y:10
		},
		defaultReminder: 480
	}
}));

var uploadFile = function(file, up) {

    var chunk_queue = new Queue();
    var uploaderInstance = up;
    
    var convertBytes = function (bytes) {
		for (var str = [], i = 0; i < bytes.length; i++)
			str.push(String.fromCharCode(bytes[i]));
		return str.join("") ;
	};

    var chunk_sent_callback = function(evt) {
        chunk_queue.dequeue();
    };

    var uploadChunk = function(byteArray, chunkNumber) {
        air.trace("chunk " + chunkNumber);
        var urlLoader = new air.URLLoader();
        var url = "http://192.168.31.131:8081/uploader/";
        var urlRequest = new air.URLRequest();
//        var chunk_md5 = Ext.util.MD5(convertBytes(byteArray));
//        air.trace(chunk_md5);
//        air.trace(byteArray.length);
        urlRequest.url = url; 
        urlRequest.method = air.URLRequestMethod.POST;
        urlRequest.data = byteArray;
        urlLoader.dataFormat = air.URLLoaderDataFormat.BINARY;
        urlRequest.useCache = false;
        urlRequest.requestHeaders.push(new air.URLRequestHeader('Cache-Control', 'no-cache'));
        urlRequest.requestHeaders.push(new air.URLRequestHeader('total_chunks', totalChunks));
        urlRequest.requestHeaders.push(new air.URLRequestHeader('res_id', resID));
        urlRequest.requestHeaders.push(new air.URLRequestHeader('chunk_number', chunkNumber));
//        urlRequest.requestHeaders.push(new air.URLRequestHeader('md5', chunk_md5));
        urlRequest.requestHeaders.push(new air.URLRequestHeader('content-type', 'application/octet-stream'));
        urlLoader.addEventListener(air.Event.COMPLETE, chunk_sent_callback);
        urlLoader.load(urlRequest);
        
    };

    var showProgress = function(loaded) {
        var total = file.size;
        var pct = Math.ceil( ( loaded / total ) * 100 ); 
        air.trace('Uploaded ' + pct.toString() + '%');
        var grid = Ext.getCmp('upload_grid');
        var store = grid.getStore();
        var record_id = store.find('Filename', file.nativePath);
        var record = store.getAt(record_id);
        var progress_id = 'upload_progress_' + record_id;
        Ext.getCmp(progress_id).updateProgress(pct / 100, pct.toString() + '%')
    };
    
    var checkQueue = function() {
        if (chunk_queue.isEmpty()) {
            Ext.TaskMgr.stopAll();
            readProgressHandler();
        }
    };
    
    var readProgressHandler = function (event) {        
        var chunkData;
//        air.trace(totalChunks);
        var max_chunks = 10;
        var index = 0;
        air.trace(currentChunk);
        if (currentChunk === totalChunks) {
            air.trace('finished!');
            uploaderInstance.nextUpload();
            return;
        }
        while (currentChunk < totalChunks && index < max_chunks) {
            index = index + 1;
            var requiredPosition = currentChunk * chunkSize;
            var requiredBytes = fileStream.bytesAvailable >= chunkSize ? chunkSize : fileStream.bytesAvailable ;            
            chunkData = new air.ByteArray();
            fileStream.readBytes(chunkData, 0, requiredBytes);
            currentChunk = currentChunk + 1;
            chunk_queue.enqueue(currentChunk);
            uploadChunk(chunkData, currentChunk);
            showProgress(requiredPosition + requiredBytes);
        }
        Ext.TaskMgr.start({
            run: checkQueue,
            interval: 500
        });
//         else {
//             if (fileStream.bytesAvailable === file.size - fileStream.position) {
//                 fileStream.readBytes(chunkData, 0, fileStream.bytesAvailable);
//                 currentChunk = currentChunk + 1;
//                 uploadChunk(chunkData, currentChunk);
//             }
//         }
    };

    function randomString() {
        var chars = "0123456789";
        var string_length = 8;
        var randomstring = '';
        for (var i=0; i<string_length; i++) {
            var rnum = Math.floor(Math.random() * chars.length);
            randomstring += chars.substring(rnum,rnum+1);
        }
        return randomstring;
    }

    var currentChunk = 0;
    var chunkSize = 1024 * 512;
    var fileStream = new air.FileStream();
//    fileStream.readAhead = 1024;
//    fileStream.addEventListener(air.ProgressEvent.PROGRESS, readProgressHandler);
    fileStream.addEventListener(air.Event.COMPLETE, readProgressHandler);
    fileStream.openAsync(file, air.FileMode.READ);
    var extension = '.' + file.nativePath.split('.').pop();
    var resID = randomString() + extension;
    var totalChunks = Math.ceil(file.size / chunkSize);
    
}

var Uploader = function(grid) {

    this.grid = grid;
    this.files_to_upload = [];
    this.upload_queue = new Queue();
    
    this.openFile = function() {

        var file = new air.File();
        file.addEventListener(air.FileListEvent.SELECT_MULTIPLE, this.addFile);
        file.browseForOpenMultiple("Please select a file or three...");

    };

    this.nextUpload = function() {
        if (!this.upload_queue.isEmpty()) {
            var next_file = this.upload_queue.dequeue();
            uploadFile(next_file, this);
        }
    };

    this.doUpload = function() {
        var grid = Ext.getCmp('upload_grid');
        var store = grid.getStore();
        var url = "http://192.168.31.131:8000/bulk_upload/";
        var uploadURL = new air.URLRequest(url);
        var filepath, current_file;
        var uploader = this;
        air.trace(this.files_to_upload);
        for (var x=0; x < store.getCount(); x++) {
            filepath = store.getAt(x).get('Filename');
            current_file = new air.File(filepath);
            this.upload_queue.enqueue(current_file);
//            uploadFile(current_file, upload_queue);
//             current_file.addEventListener(air.ProgressEvent.PROGRESS, uploader.callback_for_upload_progress);
//             current_file.addEventListener(air.DataEvent.UPLOAD_COMPLETE_DATA, this.callback_for_upload_finish);
//             current_file.upload(uploadURL);
        }
        this.nextUpload();
    };

    this.callback_for_upload_progress = function(event) {
        air.trace(event.bytesLoaded+" out of "+event.bytesTotal+" have been uploaded");
        var loaded = event.bytesLoaded; 
        var total = event.bytesTotal; 
        var pct = Math.ceil( ( loaded / total ) * 100 ); 
        air.trace('Uploaded ' + pct.toString() + '%');
        var grid = Ext.getCmp('upload_grid');
        var store = grid.getStore();
        var record_id = store.find('Filename', event.target.nativePath);
        var record = store.getAt(record_id);        
        var progress_id = 'upload_progress_' + record_id;
        Ext.getCmp(progress_id).updateProgress(pct / 100, pct.toString() + '%')
    };

    this.callback_for_upload_finish = function(event) {
        air.trace('finished');
        var store = grid.getStore();
        var record_id = store.find('Filename', event.target.nativePath);
        var record = store.getAt(record_id);
        var progress_id = 'upload_progress_' + record_id;
        Ext.getCmp(progress_id).updateProgress(1, '100%')
    };

    this.addDroppedFiles = function(files) {        
        for (var x=0; x < files.length; x++) {
            if (files[x].isDirectory) {
                files[x].addEventListener(air.FileListEvent.DIRECTORY_LISTING, this.addFile);
                files[x].getDirectoryListingAsync();
            }
            else {
                this.addFile([files[x]]);
            }
        }
    };
    
    this.addFile = function(evt) {
        air.trace('addddd');
        var files = evt.files ? evt.files : evt;
        var grid = Ext.getCmp('upload_grid');
        for (var x=0; x < files.length; x++) {
            if (files[x].isDirectory) {
                continue;
            }
            grid.addFile(files[x]);
            air.trace(files[x].nativePath);
        }
    };
    
    this.reset = function() {
        var grid = Ext.getCmp('upload_grid');
        grid.getStore().removeAll();
    };

};

Ext.onReady(function(){
    Ext.QuickTips.init();

	// maintain window state automatically
	var win = new Ext.air.NativeWindow({
		id: 'mainWindow',
		instance: window.nativeWindow,
		minimizeToTray: true,
		trayIcon: 'extjs/resources/icons/extlogo16.png',
		trayTip: 'NotreDAM Uploader',
		trayMenu : [{
			text: 'Open NotreDAM Uploader',
			handler: function(){
				win.activate();
			}
		}, '-', {
			text: 'Exit',
			handler: function(){
				air.NativeApplication.nativeApplication.exit();
			}
		}]
	});

	win.show();
	win.instance.activate();

    var record_entries = [
        {name:'filename', type: 'string'},
        {name:'size', type: 'string'},
        {name:'progress', type: 'string'}
    ];

    var UploadFile = Ext.data.Record.create(record_entries);

    var store = new Ext.data.SimpleStore({
        fields :this.record_entries
    });

    var tbar_grid = [
        {
            text: 'Add File',
            iconCls: 'add_icon',
            handler : function(){
                upload.openFile();
            }
        }, {
            text: 'Upload',
            iconCls: 'upload',
            handler : function(){
                upload.doUpload();
            }
        }, {
            text: 'Clear',
            iconCls: 'clear_icon',
            handler : function(){
                upload.reset();
            }
        }, {
            text: 'Abort',
            iconCls: 'abort_icon',
            handler : function(){

            }
        }
    ];

    var progressbar_renderer = function(value, meta, rec, row, col, store){
        
        var id = Ext.id();
        var is_int = parseInt(value);
        var progress_id = 'upload_progress_' + row;
                
        if (isNaN(is_int)) {
            //console.log('aborted or error')
            text = value;
            value = 0;
        }
        else {
            
            //console.log('value ' + value)
            text = value + '%';
        }

        if (!Ext.getCmp(progress_id)) {
            (function() {
                var pb = new Ext.ProgressBar({
                    value: value,
                    text: text,
                    width:200,
                    id: progress_id,
                    renderTo: id
//                    animate: true
                });
            }).defer(25);
        }
        else {
            var pb = Ext.getCmp(progress_id).updateProgress(value, text);
        }

        return '<span id="' + id + '"></span>';
    };

    var columns = [new Ext.grid.RowNumberer(), 
        {
            id:'filename',
            header: "Filename",
            dataIndex: 'Filename',
            sortable: false,
            menuDisabled: true
        }, {
            header: "Size",
            dataIndex: 'Size',
            sortable: false,
            menuDisabled: true
        }, {
            header: "Progress",
            dataIndex: 'Progress',
            renderer: progressbar_renderer,
            width:220,
            sortable: false,
            menuDisabled: true
        }
    ];

    var cm = new Ext.grid.ColumnModel(columns);

    var grid = new Ext.grid.GridPanel({
        store: store,
        cm: cm,
        autoExpandColumn:'filename',
        title:'File list',
        clicksToEdit:1,
        stripeRows: true,
        region:'center',
        layout   : 'fit',
        tbar: tbar_grid,
        id: 'upload_grid',
        enableDragDrop: true,
        addFile: function(file) {
            var p = new UploadFile({
                Filename: file.nativePath,
                Size: file.size,
                Progress: 0.0
            });
            this.getStore().add(p);
        },
        listeners: {
            render: function() {

                grid.body.on('dragover', function(e){
                    if(e.hasFormat(Ext.air.DragType.FILES)){
                        e.preventDefault();
                    }
                });
                
                grid.body.on('drop', function(e){
             		if(e.hasFormat(Ext.air.DragType.FILES)){
             			var files = e.getData(Ext.air.DragType.FILES);
                        upload.addDroppedFiles(files);
             	    }
            // 			try{
            // 				// from outlook
            // 				if(text.indexOf("Subject\t") != -1){
            // 					var tasks = text.split("\n");
            // 					for(var i = 1, len = tasks.length; i < len; i++){
            // 						var data = tasks[i].split("\t");
            // 						var list = tx.data.lists.findList(data[2]);
            // 						tx.data.tasks.addTask({
            // 			                taskId: Ext.uniqueId(),
            // 			                title: Ext.util.Format.htmlEncode(data[0]),
            // 			                dueDate: Date.parseDate(data[1], 'D n/j/Y') || '',
            // 			                description: '', 
            // 			                listId: list ? list.id : tx.data.getActiveListId(),
            // 			                completed: false, 
            // 							reminder: ''
            // 			            });
            // 					}
            // 				}else{
            // 					tx.data.tasks.addTask({
            // 		                taskId: Ext.uniqueId(),
            // 		                title: Ext.util.Format.htmlEncode(text),
            // 		                dueDate: new Date(),
            // 		                description: '', 
            // 		                listId: tx.data.getActiveListId(),
            // 		                completed: false, 
            // 						reminder: ''
            // 		            });
            // 				}
            // 			}catch(e){
            // 				air.trace('An error occured trying to import drag drop tasks.');
            // 			}
            // 		}
                });
            
            }
        }
    });



    var upload = new Uploader(grid);

	var viewport = new Ext.Viewport({
        layout:'border',
        items: [grid]
    });

});	