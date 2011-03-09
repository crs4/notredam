package
{
	import com.adobe.crypto.MD5;
	
	import flash.events.Event;
	import flash.events.TimerEvent;
	import flash.filesystem.File;
	import flash.filesystem.FileMode;
	import flash.filesystem.FileStream;
	import flash.net.URLLoader;
	import flash.net.URLLoaderDataFormat;
	import flash.net.URLRequest;
	import flash.net.URLRequestHeader;
	import flash.net.URLRequestMethod;
	import flash.utils.ByteArray;
	import flash.utils.Timer;

	public class UploadFile {
		
		private var _uploader:Uploader;
		private var _currentChunk:int;
		private var _chunkSize:int = 1024 * 512;
		private var _fileStream:FileStream = new FileStream();
		private var _resID:String;
		private var _totalChunks:int;
		private var _my_timer:Timer = new Timer(100);
		private var _uploading:Array = new Array();
		private var _file:File;
		private var _fileIndex:int;
		
		public function UploadFile(file:File, up:Uploader, index:int):void {
			_fileIndex = index;
			_file = file;
			_uploader = up;
			_currentChunk = 0;
//			_fileStream.addEventListener(Event.COMPLETE, startUpload);
//			_fileStream.openAsync(_file, FileMode.READ);
			_resID = randomString() + '.' + file.extension;
			_totalChunks = Math.ceil(file.size / _chunkSize);		
						
			_my_timer.addEventListener(TimerEvent.TIMER, checkChunks);

			startUpload();
			
		}
		
		private function randomString():String {
			var chars:String = "0123456789";
			var string_length:int = 8;
			var randomstring:String = '';
			for (var i:int=0; i<string_length; i++) {
				var rnum:Number = Math.floor(Math.random() * chars.length);
				randomstring += chars.substring(rnum,rnum+1);
			}
			return randomstring;
		}		
		
		private function showProgress(loaded:int):void {
			var total:int = _file.size;
			var pct:Number = Math.ceil( ( loaded / total ) * 100 ); 
			trace('Uploaded ' + pct.toString() + '%');
			_uploader.updateProgress(_fileIndex, pct.toString());
		}		
		
		private function uploadChunk(byteArray:ByteArray, chunkNumber:int):void {
//			var md5_chunk:String = MD5.hashBinary(byteArray);
//			trace(md5_chunk);
			var urlLoader:URLLoader = new URLLoader();
			var url:String = "http://192.168.31.131:8081/uploader/";
			var urlRequest:URLRequest = new URLRequest();
			urlRequest.url = url; 
			urlRequest.method = URLRequestMethod.POST;
			urlRequest.data = byteArray;
			urlLoader.dataFormat = URLLoaderDataFormat.BINARY;
			urlRequest.useCache = false;
			urlRequest.requestHeaders.push(new URLRequestHeader('Cache-Control', 'no-cache'));
//			urlRequest.requestHeaders.push(new URLRequestHeader('md5', md5_chunk));
			urlRequest.requestHeaders.push(new URLRequestHeader('total_chunks', _totalChunks.toString()));
			urlRequest.requestHeaders.push(new URLRequestHeader('res_id', _resID));
			urlRequest.requestHeaders.push(new URLRequestHeader('chunk_number', chunkNumber.toString()));
			urlRequest.requestHeaders.push(new URLRequestHeader('content-type', 'application/octet-stream'));
			urlLoader.addEventListener(Event.COMPLETE, chunkSentCallback);
			urlLoader.load(urlRequest);
			
		}		
		
		private function chunkSentCallback(evt:Event):void {
			_uploading.pop();
		}
		
		private function checkChunks(evt:Event):void {
			if (_uploading.length == 0) {
				_my_timer.stop();
				startUpload();
			}
		};			
		
		private function startUpload():void {     
			var chunkData:ByteArray;
			var max_chunks:int = 5;
			var index:int = 0;
			if (_currentChunk === _totalChunks) {
				_uploader.nextUpload();
				return;
			}
			_fileStream.open(_file, FileMode.READ);
			while (_currentChunk < _totalChunks && index < max_chunks) {
				index = index + 1;
				var requiredPosition:int = _currentChunk * _chunkSize;
				var requiredBytes:int = _file.size - requiredPosition >= _chunkSize ? _chunkSize : _file.size - requiredPosition;
//				var requiredBytes:int = _fileStream.bytesAvailable >= _chunkSize ? _chunkSize : _fileStream.bytesAvailable ;            
				_fileStream.position = requiredPosition;
				chunkData = new ByteArray();
				_fileStream.readBytes(chunkData, 0, requiredBytes);
				_currentChunk = _currentChunk + 1;
				_uploading.push(_currentChunk);
				uploadChunk(chunkData, _currentChunk);
				showProgress(requiredPosition + requiredBytes);
			}
			_fileStream.close();			
			_my_timer.start();
			
		}		
		
	}
}