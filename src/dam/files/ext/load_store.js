Ext.onReady(function(){

	ws_store.load({callback:function(wss){
		var data_tabs = []
		
		for(var i = 0; i < wss.length; i ++){
		   	var ws_id = wss[i].data.pk;
		   	data_tabs.push(create_tabs(ws_id, wss[i].data.media_type));
		   		
		   	}
		store_tabs.loadData({'tabs':data_tabs})
		switch_ws(null, ws.id);
		}
	    
	});	
	ws_state_store.load();	

});