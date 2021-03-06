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

Ext.onReady(function() {
	
    var submitClick = function() {
        var f = Ext.getCmp('login_form').form;
            if (f.isValid()) {
                f.getEl().dom.submit(); 
                //f.submit(); 
               //f.submit({waitMsg:'Trying to login...', method: "POST", failure: function() {Ext.MessageBox.alert('Error', 'Wrong login');}});
               
               //Ext.Ajax.request({
                   //url: f.url,
                   //params: f.getValues()
               //});
            }else{
                Ext.MessageBox.alert('Error', 'Please fill all the fields and try again.');
            }
        };

    Ext.form.Field.prototype.msgTarget = 'side';
    Ext.form.Field.prototype.invalidClass = 'invalid_field';

    var form = new Ext.form.FormPanel({
        title: 'Login required',
        labelWidth: 100,
        border: false,
        bodyBorder: false,
        //standardSubmit: true,
        region: 'center',
        buttonAlign: 'center',
        //region: 'center',
        defaultType: 'textfield',
        defaults:{
            width: 300,
            style: 'margin-bottom: 3px;'
        },        
        bodyStyle:'padding:20px 5px 0; left:37%',
        
        url: '/login/',
        
        frame: true,
        //width: 300,
        id: 'login_form',
        keys: [{ key: Ext.EventObject.ENTER, fn: submitClick }],

        items: [
            {
                xtype: 'textfield',
		name: 'csrfmiddlewaretoken',
		hidden: true,
		listeners:{
		    	afterrender: function(){
				this.setValue(Ext.util.Cookies.get('csrftoken'));
			}
		}
               
            },
        
            {
            fieldLabel: 'Username',
            name: 'username',
            allowBlank: false,
            listeners: {render: function() {
                this.getEl().dom.focus();
                }
            }
        }, {
            inputType: 'password',
            fieldLabel: 'Password',
            name: 'password',
            allowBlank: false
        }, new Ext.Panel({
	    html: '<div><a href="/registration/">New user? register now!</a></div>' 
	    		+'<div><a href="/new_password/">Have you forgotten your password?</a></div>'
	   }) 
        ],

        buttons: [{
            text: 'Login', 
            handler: function() {
                submitClick();
            }
        },{
            text: 'Reset',
            handler: function() {
                var f = Ext.getCmp('login_form').form;
                f.reset();
            }
        }]

    });

    new Ext.Viewport({
        layout: 'border',
        items: [
            header,
            //form
            new Ext.Panel({
                region: 'center',
                layout: 'absolute',
                frame: true,
                border: false,                 
                bodyBorder: false,               
                bodyStyle: 'margin-top:-7px',
                items: form})
        ]
    })

});
