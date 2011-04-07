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

    Ext.QuickTips.init();

    Ext.form.Field.prototype.msgTarget = 'side';
    Ext.form.Field.prototype.invalidClass = 'invalid_field';

    var form = new Ext.form.FormPanel({
        title: 'New user',
        labelWidth: 100,
        defaultType: 'textfield',
        url: '/registration/',
        bodyStyle:'padding:5px 5px 0',
        frame: true,
        width: 300,
        id: 'registration_form',

        items: [{
            fieldLabel: gettext('Username'),
            name: 'username',
            allowBlank: false
        }, {
            fieldLabel: gettext('First name'),
            name: 'first_name'
        },{
            fieldLabel: gettext('Last name'),
            name: 'last_name'
        }, {
            fieldLabel: gettext('Email'),
            name: 'email',
            allowBlank: false,
            vtype:'email'
        }, {
            inputType: 'password',
            fieldLabel: gettext('Password'),
            name: 'password1',
            allowBlank: false
        }, {
            inputType: 'password',
            fieldLabel: gettext('Repeat Password'),
            name: 'password2',
            allowBlank: false
        } 
        ],

        buttons: [{
            text: gettext('Register'), 
            handler: function() {
                var f = Ext.getCmp('registration_form').form;
                if (f.isValid()) {
                    f.submit({waitMsg:gettext('Saving data...'), method: "POST", success: function(form, action) { document.location.href = '/'; }, failure: function(form, action) {var data = Ext.decode(action.response.responseText); Ext.MessageBox.alert(gettext('Error'), gettext('The following errors occured: ') + data.errors);}});
                }else{
                    Ext.MessageBox.alert(gettext('Error'), gettext('Please fill all the fields and try again.'));
                }
            }
        },{
            text: gettext('Reset'),
            handler: function() {
                var f = Ext.getCmp('registration_form').form;
                f.reset();
            }
        }]

    });

    form.render(document.body);

});
