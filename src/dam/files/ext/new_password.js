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

var form;
Ext.onReady(function() {
	
    

    Ext.form.Field.prototype.msgTarget = 'side';
    Ext.form.Field.prototype.invalidClass = 'invalid_field';

    form = new Ext.form.FormPanel({
        title: 'Login required',
        labelWidth: 100,
        border: false,
        bodyBorder: false,
        region: 'center',
        buttonAlign: 'center',
        //region: 'center',
        defaultType: 'textfield',
        defaults:{
            //width: 300,
            style: 'margin-bottom: 3px;'
        },        
        bodyStyle:'padding:20px 5px 0; left:37%',
        
        url: '/get_new_password/',
        
        frame: true,
        //width: 300,
        id: 'new_password_form',
        //keys: [{ key: Ext.EventObject.ENTER, fn: submitClick }],

        items: [
             new Ext.Panel({
                 width: 400,
                 
                html: '<div style="padding-bottom: 30px;">Insert your username, a mail with a new password will be sent to you soon</div>'
               }),
            {
            fieldLabel: 'Username',
            name: 'username',
            width: 300,
            allowBlank: false,
            listeners: {render: function() {
                this.getEl().dom.focus();
                }
            }
        } 
        ],

        buttons: [{
            text: 'Ok', 
            handler: function() {
                var basic_form = form.getForm();
                if (basic_form.isValid()){
                    basic_form.submit();
                    Ext.Msg.alert('New Password', 'Check Your email for the new password', function(){document.location = '/'})
                }
                
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
