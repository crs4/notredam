/*
*
* NotreDAM, Copyright (C) 2009, Sardegna Ricerche.
* Email: labcontdigit@sardegnaricerche.it
* Web: www.notre-dam.org
*
* This program is free software: you can redistribute it and/or modify
*    it under the terms of the GNU General Public License as published by
*    the Free Software Foundation, either version 3 of the License, or
*    (at your option) any later version.
*
*    This program is distributed in the hope that it will be useful,
*    but WITHOUT ANY WARRANTY; without even the implied warranty of
*    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
*    GNU General Public License for more details.
*
*/

Ext.grid.ProgressBarSelectionModel = Ext.extend(Ext.grid.RowSelectionModel, {
    /**
     * @cfg {String} header Any valid text or HTML fragment to display in the header cell for the row
     * number column (defaults to '').
     */
    header: "",
    sortable: true,
    fixed:true,
    dataIndex: '',
    id: 'progress-grid',
	text: '%',
	baseCls: 'x-progress',
	colored: true,
	initEvents : function(){
        Ext.grid.ProgressBarSelectionModel.superclass.initEvents.call(this);
	},
  
    // private
    renderer : function(v, p, record, w){
		var text_post = '%';
		
		if(this.text){
            text_post = this.text;
        }
		var text_front;
		var text_back;
		
		text_front = (v <55)?'':v+text_post;
		text_back = (v >=55)?'':v+text_post;		
		
		var style ='';
		this.colored = true;
		if (this.colored == true)
		{
			if (v <= 100 && v >66) style='-green';
			if (v < 67  && v >33) style='-orange';
			if (v < 34 ) style='-red';
		}
		
		return String.format('<div class="x-progress-wrap"><div class="x-progress-inner"><div class="x-progress-bar{0}" style="width:{1}%;"><div class="x-progress-text" style="width:100%;">{2}</div></div><div class="x-progress-text x-progress-text-back" style="width:100%;">{3}</div></div></div>',style,v,text_front,text_back);		

    }
});
Ext.reg('progress-grid', Ext.grid.ProgressBarSelectionModel);
