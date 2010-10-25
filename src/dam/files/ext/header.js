var header;
Ext.onReady(function(){
   Ext.QuickTips.init();
    header = new Ext.Panel({
       layout: 'border', 
       region:'north',
       height:HEADERHEIGHT,
       items: [
            new Ext.BoxComponent({ // raw
                region:'north',
                el: 'logo',
                height:35
            }),
            new Ext.BoxComponent({ // raw
                region:'center',
                el: 'north',
                height:20
            })
       ]
   });

});