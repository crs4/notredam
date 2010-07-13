package  
{
	import mx.containers.HBox;
	import mx.controls.ProgressBar;
	import mx.controls.dataGridClasses.*;
	
	public class myProgressBar extends HBox
	{
		private var pb:ProgressBar;
		
		public function myProgressBar():void {
			//Create new ProgressBar Instance
			pb = new ProgressBar();
			//Set some layout things
			pb.mode = "manual"; 
			pb.percentWidth = 100;   
			pb.labelPlacement = "center";
			pb.setStyle("barColor", "#FF0000");
			this.setStyle("verticalAlign","middle");
			//Add ProgressBar as child
			addChild(pb);
		}
		
		override public function set data(value:Object):void
		{
			super.data = value;
		}   
		
		override protected function updateDisplayList(unscaledWidth:Number, unscaledHeight:Number) : void{
			super.updateDisplayList(unscaledWidth, unscaledHeight);
			pb.setProgress(data.status, 100);
		}
	}
}