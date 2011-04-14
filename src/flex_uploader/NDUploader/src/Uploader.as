
package  {
	import flash.events.Event;
	import flash.events.ProgressEvent;
	import flash.filesystem.File;
	import flash.net.FileReference;
	import flash.net.URLRequest;
	import flash.net.URLVariables;
	import flash.net.URLRequestMethod;
	
	import mx.collections.ArrayCollection;

	public class Uploader {

		private var _files_to_upload:ArrayCollection;
		private var _current:int;
		
		public function Uploader(files:ArrayCollection):void {
			_files_to_upload = files;
			_current = 0;
		}

		public function doUpload():void {
			nextUpload();
		}
		
		private function complete(event:Event): void {
			var current:Object = _files_to_upload[_current-1];
			current.status = 100;
			_files_to_upload.itemUpdated(current);
			nextUpload();
		}
		
		public function updateProgress(event:ProgressEvent):void {
			var total:int = event.bytesTotal;
			var pct:Number = Math.ceil( ( event.bytesLoaded / total ) * 100 ); 
			trace('Uploaded ' + pct.toString() + '%');			
			var current:Object = _files_to_upload[_current-1];
			current.status = pct;
			_files_to_upload.itemUpdated(current);
		}
		
		public function nextUpload():void {
			while (_current < _files_to_upload.length) {
				if (_files_to_upload[_current].status == 0) {
					var params:URLVariables = new URLVariables();
					var request:URLRequest = new URLRequest("http://192.168.31.131:8000/flex_upload/");
					var current:Object = _files_to_upload[_current];
					var currentFile:File = new File(current.filepath);
					var file:FileReference = FileReference(currentFile);
					file.addEventListener(ProgressEvent.PROGRESS, this.updateProgress);
					file.addEventListener(Event.COMPLETE, this.complete);
					request.method = URLRequestMethod.POST;
					params.title = current.metadata.title;
					params.desc = current.metadata.desc;
					params.keywords = current.metadata.keywords;
					request.data = params;
					file.upload(request, 'upload_file');
					_current += 1;
					break;
				}
				else {
					_current += 1;
				}
			}
		}		
		
//		public function updateProgress(index:int, progress:String):void {
//			var current:Object = _files_to_upload[index];
//			current.status = progress;
//			_files_to_upload.itemUpdated(current);
//		}
		
//		public function nextUpload():void {
//			while (_current < _files_to_upload.length) {
//				if (_files_to_upload[_current].status == 0) {
//					var currentFile:File = new File(_files_to_upload[_current].filepath);
//					var upFile:UploadFile = new UploadFile(currentFile, this, _current);
//					_current += 1;
//					break;
//				}
//				else {
//					_current += 1;
//				}
//			}
//		}

	
	}
	
}
