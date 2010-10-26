var header;
Ext.onReady(function(){
   Ext.QuickTips.init();
   
    var items = [
            new Ext.BoxComponent({ // raw
                region:'center',
                el: 'logo',
                height:35
            })
            
       ];
       
   if (Ext.get('toolbar_container'))
   
   		items.push(new Ext.BoxComponent({ // raw
                region:'south',
                el: 'toolbar_container',
                height:25
            }));
   
    header = new Ext.Panel({
       layout: 'border', 
       region:'north',
       height:HEADERHEIGHT,
       items: items
   });

});