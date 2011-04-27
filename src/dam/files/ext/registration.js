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
        title: 'Registration',
        labelWidth: 100,
        region: 'center',
        defaultType: 'textfield',
        defaults:{
            width: 300,
            style: 'margin-bottom: 3px;'
        },
        url: '/registration/',
        bodyStyle:'padding:20px 5px 0; left:37%',
        frame: true,
        width: 400,
        height: 400,
        
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
        },
        new Ext.BoxComponent({autoEl: {
        tag: 'div',
        style: 'height:100; width: 100; padding-top: 10px;',
        id: 'captcha'
        },
        listeners: {
            afterrender: function(){
               
                Recaptcha.create("6LeIrcMSAAAAADFPURWv4VAh5H8V3HjNZgHB4GYA",
                    "captcha",
                    {
                      theme: "clean",
                      callback: Recaptcha.focus_response_field
                    }
                  );
            }
        }
        })        
        ],

        buttons: [{
            text: gettext('Register'), 
            handler: function() {                
                
                var f = Ext.getCmp('registration_form').form;
                if (f.isValid()) {                
                    //captcha stuff
                    var challenge = Recaptcha.get_challenge();
                    var response = Recaptcha.get_response();
                    Ext.Ajax.request({
                        url:'/captcha_check/',
                        method: 'POST',
                        params:{
                            challenge: challenge,
                            response: response
                        },
                        success: function(resp){
                            console.log('captcha ok');
                            f.submit({waitMsg:gettext('Saving data...'), method: "POST", 
                            success: function(form, action) { 
                                console.log('user registered');
                                document.location.href = '/'; 
                            }, 
                            failure: function(form, action) {var data = Ext.decode(action.response.responseText); Ext.MessageBox.alert(gettext('Error'), gettext('The following errors occured: ') + data.errors);}});
                        },
                        failure: function(){
                            Ext.MessageBox.alert(gettext('Error'), gettext('Uncorrect Captcha.'));
                        }
                    });
                    
                    
                    
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

    //form.render(document.body);
    new Ext.Viewport({
        layout: 'border',
        items: [header,form]
    })

});
