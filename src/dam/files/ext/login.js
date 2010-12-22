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
	
	function get_new_password(){
		
		
	};
	
    var submitClick = function() {
        var f = Ext.getCmp('login_form').form;
            if (f.isValid()) {
                f.getEl().dom.submit(); 
//               f.submit({waitMsg:'Trying to login...', method: "POST", failure: function() {Ext.MessageBox.alert('Error', 'Wrong login');}});
            }else{
                Ext.MessageBox.alert('Error', 'Please fill all the fields and try again.');
            }
        };

    Ext.form.Field.prototype.msgTarget = 'side';
    Ext.form.Field.prototype.invalidClass = 'invalid_field';

    var form = new Ext.form.FormPanel({
        title: 'Login required',
        labelWidth: 55,
        defaultType: 'textfield',
        url: '/login/',
        bodyStyle:'padding:5px 5px 0',
        frame: true,
        width: 300,
        id: 'login_form',
        keys: [{ key: Ext.EventObject.ENTER, fn: submitClick }],

        items: [{
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
//	    		+'<div><a href="javascript:get_new_password()">Have you forgotten your password?</a></div>'
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

    form.render(document.body);

});
