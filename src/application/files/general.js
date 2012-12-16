Ext.app.SearchField = Ext.extend(Ext.form.TriggerField, {
        id: 'search_field',
        triggerClass: 'x-form-search-trigger',
        initComponent : function(){
            Ext.app.SearchField.superclass.initComponent.call(this);
            this.on('specialkey', function(f, e){
                if(e.getKey() == e.ENTER){
                    this.onTriggerClick();
                }
            }, this);
        },

        onTriggerClick: function() {
            var v = this.getRawValue();
            
            var media_tabs = Ext.getCmp('media_tabs');
            var active_tab = media_tabs.getActiveTab();
            var store = active_tab.items.items[0].getStore()
            store.reload({params:{query:v}})    
            
            
            

        }

    });
 

function set_query(param, value){
    var tabs = Ext.getCmp('media_tabs');
    for (var i = 0; i < tabs.items.items.length; i++){
        var tab = tabs.items.items[i]
        var view = tab.items.items[0];
        view.getStore().baseParams[param]= value;
        
        if(tabs.getActiveTab() == tab)
            view.getStore().reload();
    }
    


};

function shortName(name){
    if(name.length > 15){
        return name.substr(0, 12) + '...';
    }
    return name;
};


function add_rating_stars(record){
    var rating_value = parseInt(record.data.xmp_rating) - 1;                    
    if (!rating_value)
        rating_value = 0;
        
    var rating_id = 'rating_' + parseInt(record.data.pk);
    var stars = new Ext.ux.StarRating(rating_id, {totalStars: 5, average: rating_value } );
    stars.on( 'rate', function( o, x ){
       
        Ext.Ajax.request({
            url: '/save_rating/',
            params:{
                rating:x,
                item_id: o.id                         
            }
        });
        
    });

};

function check_editability(uploader){
    if (uploader == user)
        return true;
    else
        return false;
       

};

var pageSize = 30;
var createStore = function(config) {

    
    return new Ext.data.JsonStore(Ext.apply({

        totalProperty: 'totalCount',
        root: 'items',
        method: 'post',
        idProperty: 'pk',
        baseParams: {start:0, limit: pageSize},
		fields:[
                'name', 'thumbnail', 'pk', 'size', 'media_type', 'xmp_rating', 'dc_title', 'notreDAM_UploadedBy',
                {name: 'shortName', mapping: 'dc_title', convert: shortName}, {name: 'editable', mapping:  'notreDAM_UploadedBy',  convert: check_editability}, 
            ],
	        listeners: {
	            load: function(store, records) {
    	            
                    for ( var i = 0 ; i < records.length ; i++ ){                    
                       add_rating_stars(records[i])                                               
                    }
	            }
	        }

    }, config));

};

function on_view(item_id, title, media_type){

	function open_fullscreen_window(height,width, html, callback){
    	
        var win = new Ext.Window({
            modal: true,
            width: width + 15 ,
            height: height + 15,
            resizable: true,                       
            title: title,
            html: html,

            listeners:{
                show: function(){                
                    
                    this.center()                            
                },
                afterrender: function(){
                	if(callback){
                		callback();                		
                	}
                	
                	
                }
            }                
        });    
        win.show();    
    };
    
    Ext.Ajax.request({
        url: '/on_view/',
        params:{item_id:item_id, media_type: media_type},
        success: function(resp){
            resp = Ext.decode(resp.responseText);
            
        	if (media_type == 'image' | media_type == 'doc'){
        		fullscreen = new Image();
	            fullscreen.src = resp.url;
        		
        		fullscreen.onload = function(){
        			html = '<div id="fullscreen"><img width="'+fullscreen.width +'" height="'+fullscreen.height+'" src="' + fullscreen.src+'"></img><div id="edit_item_form"></div></div>';
        			open_fullscreen_window(fullscreen.height,fullscreen.width,  html)};
            }
        	else {
        		html = '<a href="' + resp.url + '" style="display:block;width:300px;height:300px;" id="player"></a>';
        		callback = function(){
        			if(media_type == 'audio')
        				flowplayer("player", "/files/flowplayer/flowplayer-3.1.4.swf", { 
        	                clip: { autoPlay: false},
        	                plugins: { 
        	                    audio: { 
        	                        url: '/files/flowplayer/flowplayer.audio.swf' 
        	                    }, 
        	                    controls: { 
        	                        fullscreen: false, 
        	                        height: 30 
        	                    } 
        	                }
        	            });
        			else
		        		flowplayer("player", "/files/flowplayer/flowplayer-3.1.4.swf", { 
		                    clip: { initialScale: 'orig', autoPlay: false, scaling: 'orig' },             
		                    plugins: { 
		                        controls: { 
		                            fullscreen: false, 
		                            height: 30 
		                        } 
		                    }
		                }); 
        		};
        		
        		open_fullscreen_window(318, 300, html, callback);
        		
        	}
        	
             
        
        }
        
    });

};

function on_download(item_id){
    Ext.Ajax.request({
        url: '/download_item/',
        params:{item_id:item_id},
        success: function(resp){
            resp = Ext.decode(resp.responseText);
            window.open(resp.url + '?download=1');            
        }
        
    });
    
    
    

};

function delete_item(item_id){
	Ext.Msg.show({
		title:'Delete Item?',
		msg: 'Are you sure you want to delete the selected item?',
		buttons: Ext.Msg.YESNO,
		fn: function(btn){
			if(btn == 'yes')
				Ext.Ajax.request({
					url: '/delete_item/',
					params:{
						id: item_id,						
					},
					success: function(){
						var view = Ext.getCmp('media_tabs').getActiveTab().items.items[0];
						view.getStore().reload();
					}
					
				});
				
				
			
		},
		animEl: 'elId',
		icon: Ext.MessageBox.QUESTION
	});

}

var createView = function(config) {
    var tpl = new Ext.XTemplate(
       '<tpl for=".">',
       
            '<div class="thumb-wrap" id="{pk}">',
                '<div class="thumb">',
                    '<a href="javascript:void(0)" ondblclick="on_view(\'{pk}\', \'{dc_title}\', \'{media_type}\')">',
                        '<img src="{thumbnail}" class="thumb-img"/>',
                    '</a>',
                    
                 '</div>',            
            
                '<span>{shortName}</span>',
                '<div style="text-align:center">',
                    '<a href="javascript:void(0)" onclick="on_download(\'{pk}\')">download</a>',
                    '<tpl if="notreDAM_UploadedBy== \''  +user+ '\'">',
                        ' | ',
                        '<a href="javascript:void(0)" onclick="delete_item(\'{pk}\')">delete</a>',
                    '</tpl>',
                '</div>',
                '<div id="rating_{pk}"></div>',
                
            '</div>',
            
    
        '</tpl>'
    );
            
        
       
        
        
        return new Ext.DataView(Ext.apply({
            region:'center',
            itemSelector: 'div.thumb-wrap',
            style:'overflow:auto',
            singleSelect: true,
            
//            overClass: 'on_item',
//            plugins: new Ext.DataView.DragSelector({dragSafe:true}),
            layout: 'fit',
            //height: 300,
            tpl: tpl,
            listeners: {               
                selectionchange: function(view, selections){
                        metadata_editor = Ext.getCmp('metadata_editor');
                        item_tags = Ext.getCmp('item_tags');
                        
                        if (selections.length > 0){
                            item_selected = selections[0];                            
                            metadata_editor.show();
                            item_tags.show();
                            record = view.getSelectedRecords()[0];
                            
                            add_tag_button = Ext.getCmp('add_tag');
                            delete_tag_button = Ext.getCmp('delete_tag');
                            if (record.data.editable){
                                add_tag_button.enable();
                                delete_tag_button.enable();
                            
                            }
                            else{
                                add_tag_button.disable();
                                delete_tag_button.disable();
                            }
                            
                            metadata_editor.getStore().load({                            
                                params:{id:item_selected.id}
                            });
                            
                            item_tags.getStore().load({                            
                                params:{id:item_selected.id}
                            });
                        }
                        else{
                            metadata_editor.hide();
                            item_tags.hide();
                        }
                        
                    }                   
                  


            }
        }, config));
    };
        







Ext.onReady(function(){
    
    var header = new Ext.Panel({
       layout: 'border', 
       region:'north',
       height:60,
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
       ],
   });
    
   
   
    var tb = new Ext.Toolbar();
    
    var metadata_upload_store = new Ext.data.JsonStore({
        data:{'schemas': [{pk: 1, name: "Title"}, {pk: 2, name: "Description"}]},
        fields: ['name', 'pk'],
        root: 'schemas'
    });
   
    tb.add({
            text:'<span style="font-size: 12px; font-family: sans-serif">Upload</span>',
                handler:function(){
                fields = []
                metadata_upload_store.each(function(r){fields.push(r)})
                up = new Upload(fields);
                up.openUpload();
                }
        }, 
        '-',
        {
            text:'<span style="font-size: 12px; font-family: sans-serif">Help</span>',
        }
    );
    tb.render('toolbar');

   
    var store_tag = new Ext.data.JsonStore({
        url: '/get_tags/',
        fields: ['pk', 'text'],
        root: 'tags'
    });
        
    var store_image = createStore({
            id: 'store_image',
            url: '/load_items/image/',
            
//            autoLoad: true
        });
        
    var store_video = createStore({
            id: 'store_video',
            url: '/load_items/video/',
        });

        var store_audio = createStore({
            id:'store_audio',
            url: '/load_items/audio/',
        });

        var store_doc = createStore({
            id:'store_doc',
            url: '/load_items/doc/',
        });

    
    var view_image = createView({
        id: 'view_image',
        store: store_image
        
    });

    var view_video = createView({
        store: store_video,
    });

    var view_audio = createView({
        store: store_audio,
        
    });

    var view_doc = createView({
        store: store_doc,
    });
    
    
    var tab_images = new Ext.Panel({
        id:'images',
        title:'Image',
        items: [view_image],
        layout: 'fit',
        bbar: new Ext.PagingToolbar({
            id: 'paginator_image',
        	pageSize: pageSize,
            displayInfo: true,
            displayMsg: 'Displaying items {0} - {1} of {2}',
            emptyMsg: "No items to display",
            store: store_image            
        })
    });


    var tab_videos = new Ext.Panel({
        id:'videos',
        title:'Video',
        items: [view_video],
        layout: 'fit',
        
        bbar: new Ext.PagingToolbar({
            id: 'paginator_video',
        	pageSize: pageSize,
            displayInfo: true,
            displayMsg: 'Displaying items {0} - {1} of {2}',
            emptyMsg: "No items to display",
            store: store_video            
        })
        

    });

    var tab_audio = new Ext.Panel({
        id:'audio',
        title:'Audio',
        items: [view_audio],
        layout: 'fit',
        bbar: new Ext.PagingToolbar({
            id: 'paginator_audio',
        	pageSize: pageSize,
            displayInfo: true,
            displayMsg: 'Displaying items {0} - {1} of {2}',
            emptyMsg: "No items to display",
            store: store_audio            
        })

    });

    var tab_docs = new Ext.Panel({
        id:'docs',
        title:'Doc',
        items: [view_doc],
        
        layout: 'fit',
        bbar: new Ext.PagingToolbar({
            id: 'paginator_doc',
        	pageSize: pageSize,
            displayInfo: true,
            displayMsg: 'Displaying items {0} - {1} of {2}',
            emptyMsg: "No items to display",
            store: store_doc            
        })

        
    });


    var search = new Ext.app.SearchField({id:'search_field', width:250}); 
    
    
    
    var media_tabs  = new Ext.TabPanel({
            region:'center',
            deferredRender:false,
            activeTab:0,
            id: 'media_tabs',
            tbar: ['Quick Search: ', ' ',search, {tag: 'div', id: 'rating_search_div', style:'margin: 0px 0px 0px 22px'}],
            items:[tab_images, tab_videos, tab_audio, tab_docs],
            listeners:{
                tabchange:function(media_tabs, tab){
                    tab.items.items[0].getStore().load();
                    
                },
                afterrender: function(o, x){
                    var rating_search = new Ext.ux.StarRating('rating_search_div',{
                        id:'rating_search', 
                        totalStars: 5, 
                        average: 0, 
                        cancelRating: true,
                        listeners:{
                            rate: function(o,x){
                                set_query('rating', x);                                
                            },
                            cancel: function(){                                
                                set_query('rating', -1);
                            }
                        } 
                    });      
                              
                
                }
                
            }
        });






var details_tab = new Ext.Panel({
        id: 'details_tab ',        
        region:'east',
        title: 'Information',
        collapsible: true,
        collapsed: true,
        split:true,
        width: 330,

        minSize: 200,
        maxSize: 400,
        margins:'0 5 0 0',
        
        collapsable: true,
        collapsed: true,
        layout: 'accordion',
        forceLayout: true,
        items:[
        
        new Ext.grid.EditorGridPanel({
            id: 'item_tags',
            title: 'Tags',
            forceLayout: true,
            tbar:[{
                id: 'add_tag',
                text: 'Add',
                handler: function(){
                    var panel = Ext.getCmp('item_tags');
                    var store = panel.getStore();
                    var record = new Ext.data.Record({label: 'new tag'});
                    store.loadData({'keywords':[{label: 'new tag', id: null}]}, true);
                   
                    panel.startEditing(store.getTotalCount() - 1, 0);
                    
                }
            },
            {
                id: 'delete_tag',
                text:'Delete',
                handler: function(){
                    var panel = Ext.getCmp('item_tags');
                    if (panel.getSelectionModel().selection){
                        var record = panel.getSelectionModel().selection.record;                        
                        var view = Ext.getCmp('media_tabs').getActiveTab().items.items[0];
                        var item_id = view.getSelectedRecords()[0].data.pk;               
                        
                        Ext.Ajax.request({
                            url: '/delete_tag/',
                            params: {
                                id: item_id,
                                tag: record.data.id
                            },
                            success: function(){
                                panel.getStore().remove(record);
                            
                            }
                            
                        });
                    
                    }
                    
                }
            }
            ],
            hideHeaders: true,
            hidden: true,
            forceLayout: true,
            collapsed: true,
            listeners:{
                beforeedit: function(){
                    console.log('beforeedit');
                },
                afteredit: function(e){
                    
                    var view = Ext.getCmp('media_tabs').getActiveTab().items.items[0];
                    var item_id = view.getSelectedRecords()[0].data.pk;                     
                    
                    var label = e.record.data.label;
                    
                    if (!e.record.data.id)
                        var url =  '/add_tag/';
                        
                    else
                        var url = '/edit_tag/'; 
                        
                        Ext.Ajax.request({
                            url : url,
                            params: {
                                id: item_id,
                                label: label
                            },
                            success: function(resp){
                                console.log(resp);
                                json_resp = Ext.decode(resp.responseText);                            
                                
                                e.record.set('id', json_resp.id);
                                e.grid.getStore().commitChanges();
                                Ext.getCmp('tags_grid').getStore().reload();
                            
                            }
                        
                        });
                    
                }
  
            },
            
            view: new Ext.grid.GridView({
                forceFit: true,
            }),            
            //autoScroll: true,
            store: new Ext.data.JsonStore({
                url: '/get_item_tags/',
                root: 'keywords',
                fields: ['id', 'label']                
            
            }),
            columns:[{dataIndex: 'label', name: 'label', header: 'tag', editable: true,editor: new Ext.form.TextField({allowBlank: false})}],
                
        
        }),
        new Ext.grid.EditorGridPanel({
            id: 'metadata_editor',
            title: 'Metadata',
            hideHeaders: true,
            hidden: true,
            forceLayout: true,
            //autoScroll: true,
            collapsed: false,
            view: new Ext.grid.GridView({
                forceFit: true,
            }),            
            store: new Ext.data.JsonStore({
                url: '/get_metadata/',
                
                root: 'metadata',
                method: 'POST',                            
                fields:[
                        'metadata_schema',
                        'metadata', 
                        'value',
                        'editable'
                ],
                listeners:{
                    load: function(){
                        var view = Ext.getCmp('media_tabs').getActiveTab().items.items[0];
                        var item = view.getSelectedRecords()[0];                       
                        if (!item.data.editable){
                            Ext.getCmp('save_button').disable();
                        }
                        else
                            Ext.getCmp('save_button').enable();
                    
                    }
                    
                }
                
            }),
            listeners:{
            beforeedit: function(e){
                if (!e.record.data.editable)
                    e.cancel = true
            },
            
            },
            
            buttons:[{
                id:'save_button',
                text: 'save',
                handler: function(){
                    var store = Ext.getCmp('metadata_editor').getStore();
                    var metadata_to_save = []
                    var new_title = null;
                    store.each(function(r){
                        if(r.dirty){
                            metadata_to_save.push({metadata_schema: r.data.metadata_schema, value: r.data.value})        
                            if(r.data.metadata == 'title')
                                new_title = r.get('value');
                               
                        }
                    })  
                    if (metadata_to_save.length> 0)
                        
                        Ext.Ajax.request({
                            url: '/set_metadata/',
                            
                            
                            params: {
                                id: store.lastOptions.params.id,
                                metadata: Ext.encode(metadata_to_save)
                            },
                            success: function(resp, opts){
                                Ext.getCmp('metadata_editor').getStore().commitChanges();
                                if (new_title!= null){
                                    var view = Ext.getCmp('media_tabs').getActiveTab().items.items[0];
                                    var index = view.getSelectedIndexes()[0];
                                    var record = view.getSelectedRecords()[0];
                                                                        
                                    //saving title
                                    
                                    record.set('dc_title', new_title);
                                    record.set('shortName', new_title);                                    
                                    
                                    view.refreshNode(index);
                                    add_rating_stars(record);
                                }  
                            },
                            scope: new_title
                            
                        })                  
                }
                
            
            }],
            columns: [                
                {id: 'metadata', header: 'metadata', width: 60, sortable: false, dataIndex: 'metadata'},                
                {header: 'value',  dataIndex: 'value',sortable: false, editor: new Ext.form.TextField({autoScroll: true})},
            ]

        })
        
        ]
});


var tags_tab = new Ext.Panel({
        id: 'tags_tab ',        
        region:'west',
        title: 'Tags',
        collapsible: true,
        collapsed: false,
        split:true,
        width: 150,

        minSize: 100,
        maxSize: 200,
        margins:'0 5 0 0',
        
        layout: 'fit',         
        
        items:[
        new Ext.grid.GridPanel({
            id: 'tags_grid',
            hideHeaders: true,
            view: new Ext.grid.GridView({
                forceFit: true,
            }),       
            sm: new Ext.grid.RowSelectionModel({
            singleSelect: true,
            listeners:{
                selectionchange: {
                    fn:function(sm){
                        view = Ext.getCmp('media_tabs').getActiveTab().items.items[0];
                        console.log(sm.getCount());
                        
                        if (sm.getCount() > 0){
                            record = sm.getSelected();
                            tag = record.data.label;
                            
                            query = 'keyword:/Tags/' + tag+ '/';
                            
                            view.getStore().reload({params:{query: query}});
                            Ext.getCmp('search_field').setValue('');
                        }
                        else
                            view.getStore().reload({params:{query: ''}});
                    },
                buffer:100,
                }                
            }
        
        }),     
            store: new Ext.data.JsonStore({
                url: '/get_tags/',
//                data:{"tags": [{"label": "popo",  "id": 18}]},
                root: 'tags',
                method: 'POST',                            
                autoLoad: true,
                fields:[
                        'id',
                        'label', 
                        
                ],
            }),
            
            columns: [                
                {id: 'label', header: 'label', sortable: false, dataIndex: 'label'}
            ]
                
        })]
});

        
    var viewport = new Ext.Viewport({
           id:'viewport',
            layout:'border',
            items:[
                header,            
                media_tabs,
                details_tab,
                tags_tab
             ]
    });

});
