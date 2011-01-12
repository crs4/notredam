/** Basic upload manager for single or multiple files (Safari 4 Compatible)
 * @author  Andrea Giammarchi
 * @blog    WebReflection [webreflection.blogspot.com]
 * @license Mit Style License
 */

var sendFile = 1024000; // maximum allowed file size
                        // should be smaller or equal to the size accepted in the server for each file

// function to upload a single file via handler
sendFile = (function(toString, maxSize){
    var isFunction = function(Function){return  toString.call(Function) === "[object Function]";},
        split = "onabort.onerror.onloadstart.onprogress".split("."),
        length = split.length;
    return  function(handler){
        if(maxSize && maxSize < handler.file.fileSize){
            if(isFunction(handler.onerror))
                handler.onerror();
            return;
        };
        var xhr = new XMLHttpRequest,
            upload = xhr.upload;
        for(var
            xhr = new XMLHttpRequest,
            upload = xhr.upload,
            i = 0;
            i < length;
            i++
        )
            upload[split[i]] = (function(event){
                return  function(rpe){
                    if(isFunction(handler[event]))
                        handler[event].call(handler, rpe, xhr);
                };
            })(split[i]);
        upload.onload = function(rpe){
            if(handler.onreadystatechange === false){
                if(isFunction(handler.onload))
                    handler.onload(rpe, xhr);
            } else {
                setTimeout(function(){
                    if(xhr.readyState === 4){
                        if(isFunction(handler.onload))
                            handler.onload(rpe, xhr);
                    } else
                        setTimeout(arguments.callee, 15);
                }, 15);
            }
        };
        xhr.open("post", handler.url + "?variant=original&session=fuuu" , true);
        xhr.setRequestHeader("If-Modified-Since", "Mon, 26 Jul 1997 05:00:00 GMT");
        xhr.setRequestHeader("Cache-Control", "no-cache");
        xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");
        xhr.setRequestHeader("X-File-Name", handler.file.fileName);
        xhr.setRequestHeader("X-File-Size", handler.file.fileSize);
        var boundary = "AJAX--------------" + (new Date).getTime();
        
        xhr.setRequestHeader("Content-Type", "multipart/form-data; boundary=" + boundary);      
        
        xhr.send(handler.file);
        return  handler;
    };
})(Object.prototype.toString, sendFile);

// function to upload multiple files via handler
function sendMultipleFiles(handler){
    var length = handler.files.length,
        i = 0,
        onload = handler.onload;
    handler.current = 0;
    handler.total = 0;
    handler.sent = 0;
    while(handler.current < length)
        handler.total += handler.files[handler.current++].fileSize;
    handler.current = 0;
    if(length){
        handler.file = handler.files[handler.current];
        sendFile(handler).onload = function(rpe, xhr){
            if(++handler.current < length){
                handler.sent += handler.files[handler.current - 1].fileSize;
                handler.file = handler.files[handler.current];
                sendFile(handler).onload = arguments.callee;
            } else if(onload) {
                handler.onload = onload;
                handler.onload(rpe, xhr);
            }
        };
    };
    return  handler;
};

/** basic server side example
 * @language    PHP
<?php
// e.g. url:"page.php?upload=true" as handler property
if(isset($_GET['upload']) && $_GET['upload'] === 'true'){
    $headers = getallheaders();
    if(
        // basic checks
        isset(
            $headers['Content-Type'],
            $headers['Content-Length'],
            $headers['X-File-Size'],
            $headers['X-File-Name']
        ) &&
        $headers['Content-Type'] === 'multipart/form-data' &&
        $headers['Content-Length'] === $headers['X-File-Size']
    ){
        // create the object and assign property
        $file = new stdClass;
        $file->name = basename($headers['X-File-Name']);
        $file->size = $headers['X-File-Size'];
        $file->content = file_get_contents("php://input");
        
        // if everything is ok, save the file somewhere
        if(file_put_contents('files/'.$file->name, $file->content))
            exit('OK');
    }
    
    // if there is an error this will be the output instead of "OK"
    exit('Error');
}
?>
 */

//from http://igstan.ro/posts/2009-01-11-ajax-file-upload-with-pure-javascript.html

var Uploader = function(form) {
    this.form = form;
};

Uploader.prototype = {
    /**
     * @param Object HTTP headers to send to the server, the key is the
     * header name, the value is the header value
     */
    headers : {},

    /**
     * @return Array of DOMNode elements
     */
    get elements() {
	    var fields = [];
	
	    // gather INPUT elements
	    var inputs = this.form.getElementsByTagName("INPUT");
	    for (var l=inputs.length, i=0; i< l; i++)
	        fields.push(inputs[i]);
	   
	  
	
	    return fields;
	},

    /**
     * @return String A random string
     */
    generateBoundary: function() {
		return "AJAX-----------------------" + (new Date).getTime();
	},

    /**
     * Constructs the message as discussed in the section about form
     * data transmission over HTTP
     *
     * @param Array elements
     * @param String boundary
     * @return String
     */
    buildMessage : function(elements, boundary) {
    	var CRLF = "\r\n";
	    var parts = [];
	
	    elements.forEach(function(element, index, all) {
	        var part = "";
	        var type = "TEXT";
	
	        if (element.nodeName.toUpperCase() === "INPUT") {
	            type = element.getAttribute("type").toUpperCase();
	        }
	
	        if (type === "FILE" && element.files.length > 0) {
	            var fieldName = element.name;
	            var fileName = element.files[0].fileName;
	
	            /*
	             * Content-Disposition header contains name of the field
	             * used to upload the file and also the name of the file as
	             * it was on the user's computer.
	             */
	            part += 'Content-Disposition: form-data; ';
	            part += 'name="' + fieldName + '"; ';
	            part += 'filename="'+ fileName + '"' + CRLF;
				
	            /*
	             * Content-Type header contains the mime-type of the file
	             * to send. Although we could build a map of mime-types
	             * that match certain file extensions, we'll take the easy
	             * approach and send a general binary header:
	             * application/octet-stream
	             */
	            part += "Content-Type: application/octet-stream";
	            part += CRLF + CRLF; // marks end of the headers part
	
	            /*
	             * File contents read as binary data, obviously
	             */
	            part += element.files[0].getAsBinary() + CRLF;
	       } else {
	            /*
	             * In case of non-files fields, Content-Disposition
	             * contains only the name of the field holding the data.
	             */
//	            part += 'Content-Disposition: form-data; ';
//	            part += 'name="' + element.name + '"' + CRLF + CRLF;
//	
//	            /*
//	             * Field value
//	             */
//	            part += element.value + CRLF;
	       }
	
	       parts.push(part);
	    });
	
	    var request = "--" + boundary + CRLF;
	        request+= parts.join("--" + boundary + CRLF);
	        request+= "--" + boundary + "--" + CRLF;
		
	    return request;
    
    
    },

    /**
     * @return null
     */
    send : function() {
    	var boundary = this.generateBoundary();
    	var files = Ext.get('file_upload-file').dom.files
    	Ext.each(files, function(file){
    	
    	});
	    var xhr = new XMLHttpRequest;
	
	    xhr.open("POST", '/upload_resource/?variant=original&session=fuuuu', true);	  
	    var contentType = "multipart/form-data; boundary=" + boundary;
	    xhr.setRequestHeader("Content-Type", contentType);
	    
//	    xhr.setRequestHeader("Content-Disposition", 'form-data; name="Filedata"');
	
	    for (var header in this.headers) {
	        xhr.setRequestHeader(header, headers[header]);
	    }
	
	    // here's our data variable that we talked about earlier
	    var data = this.buildMessage(this.elements, boundary);
		
	    // finally send the request as binary data
	    xhr.send(data);
    
    
    
    }
};






