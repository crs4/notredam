if (!window.google || !google.gears) {
//    alert('without google gears');
    parent.location.href = "http://gears.google.com/?action=install&message=Notre-dam Plugin Installation" +  "&return=/";
}


        function error_handler(file_index, responseText){
//            $j('#file_' + file_index + '_progress').css('color' , 'red');
            
            error = 'error'
            //console.log('responseText ' + responseText)
            if (responseText && responseText.length < 40)
                error +=  ': ' + responseText
            upload_grid.getStore().getAt(file_index).set('Progress', error)                    
            
//            $j('#file_' + file_index + '_progress').text(error);
        }
                     
function Upload(fields, ajax_url, singleFile, done_upload_callback, post_params, single_upload_finished_callback,tbar_grid){
  
    this.singleFile = singleFile
    this.keyword_submitted = false
    this.new_keywords = false
    
    this.desktop = google.gears.factory.create('beta.desktop');
    this.files = new Array();
    this.upload_queue = new Queue() ;
    this.upload_done = 0;
    this.last_upload_done = 0;
    this.current_worker = null;
    this.workerPool = google.gears.factory.create('beta.workerpool');
    this.aborted = false;
    this.post_params = post_params;
    this.single_upload_finished_callback = single_upload_finished_callback
    this.done_upload_callback = done_upload_callback;
    
    this.record_entries = [
        {name:'filename', type: 'string'},
        {name:'size', type: 'string'}
    ]
    this.extra_record_entries = []
    //console.log('fields')
    //console.log(fields)
    
    if(fields){
        this.fields = fields
        for (i = 0; i<fields.length; i++){
            this.record_entries.push({id: fields[i].pk, name:fields[i].name, type: 'string'});
            this.extra_record_entries.push(fields[i]);
            }
        }
    this.record_entries.push({name:'progress', type: 'string'})
    this.UploadFile = Ext.data.Record.create(this.record_entries);
    
 

//    this.UploadFile = Ext.data.Record.create([
//        {name:'filename', type: 'string'},
//        {name:'size', type: 'string'},
//        {name:'title', type: 'string'},
//        {name:'description', type: 'string'},
//        {name:'progress', type: 'string'},
//    ]);
    

    this.send_file_to_worker = function(file_index, file){
        
//        inputs = $j('input[name^=metadata_'+ file_index+']')
	
	obj_json = {};
    if(this.fields){
        grid = Ext.getCmp('upload_grid')
        data = grid.getStore().getAt(file_index).data
        //console.log('-----------------------data')
        //console.log(data)
        
        //console.log('this.fields')
        //console.log(this.fields)
        for (i=0; i<this.fields.length; i++){
            if(data[this.fields[i].data.name]){
                obj_json['metadata_' + this.fields[i].data.pk] = data[this.fields[i].data.name]
//                console.log('this.fields[i].data.name ' + this.fields[i].data.name )
//                if (this.fields[i].data.name == 'Subject')
//                    
//                    this.keyword_submitted = true
            }
        }
        
    }
    
    
    obj_json.file_name = file.name;
    obj_json.file_size= file.blob.length;
    
//    for (i=0; i< inputs.length; i++){
//        console.log(inputs[i].name)
//        obj_json[inputs[i].name] = inputs[i].value
//        }
        obj = this;
        //console.log('send_file_to_worker');
        //console.log(obj_json);
        var conn = new Ext.data.Connection();
        conn.request({
            method:'POST', 
            url: '/get_upload_url/',
//            params: {json: Ext.encode(obj_json)},
            params: obj_json,
            success: function(data, textStatus){
                data = Ext.decode(data.responseText);
                //console.log(data.res_id);
                file.res_id = data.res_id;
                
                obj.on_get_upload_url(data, file_index, file);
            },
            failure: function (XMLHttpRequest, textStatus, errorThrown) {
                if(error_handler)
                    error_handler(file_index, XMLHttpRequest.responseText)
                
                obj.files[file_index].done = true;
                obj.try_to_upload_file();
                
                }
            
            }
        );
    }            

    this.abort_done = function(file_index){
        //console.log('abort_done')
        //console.log('upload_done ' + this.upload_done)
        
        
        if (! this.files[file_index].aborted){
//            var conn = new Ext.data.Connection();
//            conn.request({
//                method:'POST', 
//                url: '/abort_upload/',
//                params: {res_id: this.files[file_index].res_id}
//                }
//            );
            this.files[file_index].aborted = true
        }
        
        for(i=this.upload_done; i<this.files.length; i++){
                
                if(!this.files[i].done){
                    //console.log('aborting ' + i)
                    upload_grid = Ext.ComponentMgr.get('upload_grid');
                    this.files[i].aborted = true
                    if(upload_grid)
                        upload_grid.getStore().getAt(i).set('Progress', 'aborted')                    
                    
                    
                }
            }        
            //files = new Array();
            this.upload_queue = new Queue() ;    
            this.current_worker = null;
            //console.log('setting button after aborting')
          
    }

    this.openfile_callback = function(tmp_files, upload_grid) {
        if(this.files){
            files_length = this.files.length;
            this.files = this.files.concat(tmp_files);
        }
        else{
            this.files = tmp_files;
            files_length = 0;
            
        }
        //console.log('tmp_files.length ' + tmp_files.length)
        if (tmp_files.length > 0 && !this.current_worker){
            
            //console.log(this)
            
//            this.upload_button[0].disabled = false;
//            this.abort_button[0].disabled = true;
//            this.clear_button[0].disabled = false;
            
            }
        
        
                    
        for (i=files_length; i < this.files.length; i++){
    //         alert(files[i].name);
            this.upload_queue.push([i, this.files[i]]);
            //console.log('pushing element ' + i + ' in queue');
            //console.log(this.upload_queue);
    //        $j('#resources').append('<div>');
    //        $j('#files_table').append('<div class="filename" id="file_' + i + '">' + files[i].name + '</div>');
    //        $j('#files_table').append('<div class="status" id="file_' + i + '_progress">0</div>');
    //        $j('#resources').append('</div>');
//            if(added_file_callback)
//                added_file_callback(files, i)

            upload_grid = Ext.ComponentMgr.get('upload_grid');

            if (upload_grid) {
                var p = new this.UploadFile({
                    Filename: this.files[i].name,
                    Size: this.get_filesize(this.files, i),
                    Title: this.files[i].name,
                    Description: '',
                    Progress: 0.0
                });
                //console.log(upload_grid);
                upload_grid.getStore().add(p);
            }
            
            
        }
                
    }

    this.try_to_upload_file = function(){
        //console.log('try_to_upload_file')
        //console.log(this)
        if (this.upload_queue.size() > 0){
            this.aborted = false;
            var data = this.upload_queue.pop();
            var file = data[1];
            var file_index = data[0];
            //console.log('try upload of file ' + file.name);
            this.send_file_to_worker(file_index, file);
        }
        else{
            
            this.current_worker = null;
            if(this.done_upload_callback)
                this.done_upload_callback()
            up = this;
            tab = Ext.getCmp('media_tabs').getActiveTab();
            view = tab.getComponent(0);
            selecteds = view.getSelectedRecords();
            store = view.getStore();
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

		        Ext.MessageBox.alert('Upload',  (up.upload_done - up.last_upload_done) + ' object(s) uploaded successfully.');
            
        }
    }

    this.on_abort_click = function(){
        //console.log('aborting')
        aborted = true;

        if(this.current_worker){
            
            this.workerPool.sendMessage({'method' : 'STOP_UPLOAD'}, this.current_worker);
           
        }
       
    }

    this.on_uploadbutton_click = function(){
        //console.log('Upload queue contains ' + this.upload_queue.size() + ' elements');
        //console.log( this)
        grid = Ext.getCmp('upload_grid');
        grid.stopEditing();
        this.last_upload_done = this.upload_done;
        this.try_to_upload_file();
    }      

    this.on_loadbutton_click = function(){

        //console.log('on_loadbutton_click');
        //console.log(this)
        if (this.singleFile)
            this.reset();

        obj = this;

        this.desktop.openFiles(function(data){
            obj.openfile_callback(data)
            }, {singleFile: this.singleFile}
        );
        
    }

    this.get_filesize = function(files, i){
        
        size = this.files[i].blob.length;
            
        KB = 1024;
        MB = Math.pow(KB,2);
        GB = Math.pow(KB,3);
            
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
            
    }

    this.reset = function(){
        this.files = new Array();
        this.upload_queue = new Queue() ;
        this.upload_done = 0;
        this.last_upload_done = 0;
        this.current_worker = null;
        this.workerPool = google.gears.factory.create('beta.workerpool');
        this.aborted = false;

        //console.log(this.files)
        //console.log(this.upload_queue.size())    
        upload_grid = Ext.ComponentMgr.get('upload_grid');
        if (upload_grid)
            upload_grid.getStore().removeAll();
    }


    this.on_get_upload_url = function(data, file_index, file){

        //console.log('upload url: ' + data.unique_key);
        //console.log('num chunks: ' + data.chunks);
        //console.log('file: ' + file.name);
        //console.log('file_index: ' + file_index);
        //console.log('Load Worker from ' + 'http://' + data.ip + ':' + data.port + '/upload/script/gears/worker.js');
        var childWorkerId = this.workerPool.createWorkerFromUrl('http://' + data.ip + ':' + data.port + '/upload/script/gears/mng.js');
        //console.log(childWorkerId);
        var workers = new Array();
        this.current_worker = childWorkerId;
        obj = this;
        data.file_name = file.name
        this.files[file_index].data = data
        this.workerPool.onmessage = function(a, b, message) {
            if (message.body.method == 'DONE_UPLOAD_FILE'){
                obj.files[message.body.file_index].done = true
                //console.log('-------------------------------------done, message.body.file_index ' + message.body.file_index)
                Ext.getCmp('progress_' + message.body.file_index).updateProgress(1, '100%')
                
                obj_json = data;
//                obj_json.file_name = obj.files[message.body.file_index].file.name
                for (el in  obj.post_params)
                    obj_json[el] = obj.post_params[el]
                
                if(obj.fields){
                    grid = Ext.getCmp('upload_grid')
                    data = grid.getStore().getAt(file_index).data
                 
                    for (i=0; i<obj.fields.length; i++){
                        if(data[obj.fields[i].data.name]){
                            obj_json['metadata_' + obj.fields[i].data.pk] = data[obj.fields[i].data.name]
            //                console.log('this.fields[i].data.name ' + this.fields[i].data.name )
//                            if (obj.fields[i].data.name == 'Subject')
//                                
//                                obj.keyword_submitted = true
                        }
                    }
                    
                }
                
                //console.log('--------------- making request upload_finished  ')
                if(!obj.single_upload_finished_callback)
                    Ext.Ajax.request({
                        url:'/upload_finished/',
                        params:obj_json,
                        success: function(resp){
                            //resp_json =Ext.util.JSON.decode(resp.responseText)
                            
                                
                            }
                        
                        })
                else
                    obj.single_upload_finished_callback(obj_json)
                obj.upload_done += 1;
                obj.try_to_upload_file();
            }
            
            if (message.body.method == 'ERROR_UPLOAD_FILE'){}        
            
            if (message.body.method == 'PROGRESS_UPLOAD_FILE'){
                
                if(!obj.files[message.body.file_index].aborted){
                    progress = message.body.uploaded/message.body.totals;
//                    progress = Math.round(progress);
                    upload_grid = Ext.ComponentMgr.get('upload_grid');
                    if(upload_grid){
                        //console.log('progress updating index ' + message.body.file_index);
                        //console.log('progress updating value' + progress);
//                        upload_grid.getStore().getAt(message.body.file_index).set('Progress', '' + progress)
                        //console.log('obj.files[message.body.file_index].done ' +  obj.files[message.body.file_index].done)
                        progressBar = Ext.getCmp('progress_' + message.body.file_index)
                        if (!obj.files[message.body.file_index].done)
                            progressBar.updateProgress(progress, ''+ Math.round(progress*100) + '%')
                        else
                            progressBar.updateProgress(1, '100%')
                    }
                }
                else
                    console.log('file_index ' + file_index + 'aborted.. skipping update progress')
            }
            
            if (message.body.method == 'MAKE_WORKERS'){
            
                
                for(i=0; i < message.body.workers_number;i++){
                    workers[i] = obj.workerPool.createWorkerFromUrl('http://' + data.ip + ':' + data.port + '/upload/script/gears/upload.js');
                    obj.workerPool.sendMessage({'method' : 'START_UPLOAD', 'mng_id' : childWorkerId, 'data' : data},  workers[i]);
                }
            
            }
            
            if (message.body.method == 'INFO'){
                alert(message.body.text);
            }
            if (message.body.method == 'LOG'){
    //            console.log(message.body.text);
            }
            if (message.body.method == 'ERROR'){
                //console.error(message.body.text);
            }

            if (message.body.method == 'DONE_STOP_UPLOAD'){
                //console.log('ABORTED')
              
                //console.log('message.body.file_index  '+ message.body.file_index );
                //console.log('In progress Upload File #file_' + message.body.file_index + '_progress');
                obj.abort_done(message.body.file_index)
                
            }    
            
         };

    //                 
    //     alert('start to send ' + files[0].blob.length + ' bytes');
    //     console.log('start to send');
        this.workerPool.sendMessage({'method' : 'UPLOAD_FILE', 'file_index' : file_index, 'params' : data, 'blob' : file.blob}, childWorkerId);
    }   

    
    
    
    
        obj = this;

        var fm = Ext.form;

        var store = new Ext.data.SimpleStore({
            fields :this.record_entries
        });

        var progressbar_renderer = function(value, meta, rec, row, col, store){
            //console.log('progressbar_renderer')
            //console.log('value '+ value)
            //console.log('meta '+ meta)
            //console.log('rec '+ rec)
            //console.log('row '+ row)
            //console.log('col '+ col)
            
            var id = Ext.id();
            is_int = parseInt(value)
            
            if (isNaN(is_int)) {
                //console.log('aborted or error')
                text = value;
                value = 0;
            }
            else {
                
                //console.log('value ' + value)
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

        
        
        
        columns = [new Ext.grid.RowNumberer(), {
                   id:'filename',
                   header: "Filename",
                   dataIndex: 'Filename',
                sortable: false,
                menuDisabled: true
                }, 
                {
                   header: "Size",
                   dataIndex: 'Size',
                    sortable: false,
                    menuDisabled: true
                }
        ]
                
        //console.log('this.extra_record_entries')
        //console.log(this.extra_record_entries)
        for(i = 0; i<this.extra_record_entries.length; i++)
            columns.push( {
                   header: this.extra_record_entries[i].data.name,
                    sortable: false,
                    menuDisabled: true,
                   dataIndex: this.extra_record_entries[i].data.name,
                   editor: new fm.TextField({
                           allowBlank: true
                   })
                })
                
                
        columns.push( {
                   header: "Progress",
                   dataIndex: 'Progress',
                   renderer: progressbar_renderer,
                    width:220,
                    sortable: false,
                    menuDisabled: true
                })
                
                
        var cm = new Ext.grid.ColumnModel(columns);

        if(!tbar_grid)
            tbar_grid = [{
                    text: 'Add Files',
                    iconCls: 'add_icon',
                    handler : function(){
                        obj.on_loadbutton_click();
                     }},
                    {
                    text: 'Upload',
                    iconCls: 'upload',
                    handler : function(){
                        obj.on_uploadbutton_click();
                     }},
                    {
                    text: 'Clear',
                    iconCls: 'clear_icon',
                    handler : function(){
                        obj.reset();
                     }},
                    {
                    text: 'Abort',
                    iconCls: 'abort_icon',
                    handler : function(){
                        obj.on_abort_click();
                     }
               }]
            
                
        this.grid = new Ext.grid.EditorGridPanel({
                store: store,
                cm: cm,
                autoExpandColumn:'filename',
//                title:'File list',
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
                    
                    },
                
        });
        
        
        up = this
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
//                    console.log('this.keyword_submitted ' + up.keyword_submitted)
                    if(up.new_keywords){
                        keywords_tree = Ext.getCmp('keywords_tree')
                        root = keywords_tree.getRootNode()
                        new_keywords = root.findChild('text', 'New Keywords')
                        tree_loader.load(new_keywords, function(){new_keywords.expand()})
                        }
                }
                
                }
        });
    
    
    
    this.getGrid  = function(){
        return this.grid
        }
        
    
    this.openUpload = function(menu_item) {
        this.reset();
        this.win.show(menu_item);

    }

    this.reset();    
    
}
    

