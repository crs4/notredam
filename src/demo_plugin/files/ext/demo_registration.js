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
        title: 'User registration',
        labelWidth: 100,
        defaultType: 'textfield',
        url: '/demo_registration/',
        bodyStyle:'padding:5px 5px 0',
        style: "margin: 5px auto 5px auto;",
        frame: true,
        width: 400,
        id: 'registration_form',

        items: [{
            fieldLabel: 'First name',
            name: 'first_name',
            allowBlank: false
        },{
            fieldLabel: 'Last name',
            name: 'last_name',
            allowBlank: false
        }, {
            fieldLabel: 'Email',
            name: 'email',
            allowBlank: false,
            vtype:'email'
        }, {
            fieldLabel: 'Username',
            name: 'username',
            allowBlank: false
        }, {
            inputType: 'password',
            fieldLabel: 'Password',
            name: 'password1',
            allowBlank: false
        }, {
            inputType: 'password',
            fieldLabel: 'Repeat Password',
            name: 'password2',
            allowBlank: false
        }, {
            xtype:'panel', bodyStyle: 'padding: 10px;', frame:false, border:false, 
            html:'By clicking "Register" you confirm that you have read and agree to the following Terms of Use:'
        },  {
            xtype: 'panel',
            items: [{
                xtype: 'textarea', 
                width: 370,
                height: 150,
                readOnly: true,
                value: 'These Terms of Use govern your access to and use of NotreDAM demo (the “Site”), any information, text, graphics, or other materials created and/or provided by NotreDAM and appearing on the Site (the “Content”). ' +
                        '\nThese Terms of Use limit NotreDAM\'s liability and obligations to you, grant NotreDAM certain rights and allow NotreDAM to change, suspend or terminate your access to and use of the Site and Content. ' + 
                        '\nYour access to and use of the Site and Content are expressly conditioned on your compliance with these Terms of Use. '+
                        '\nBy accessing or using the Site and/or Content you agree to be bound by these Terms of Use.' +
                        '\n\nYou can not: ' +
                        '\nPost, publish or transmit any text, graphics, or material that: (i) is false or misleading; (ii) is defamatory; (iii) invades anothers privacy; (iv) is obscene, pornographic, or offensive; (v) promotes bigotry, racism, hatred or harm against any individual or group; (vi) infringes anothers rights, including any intellectual property rights; or (vii) violates, or encourages any conduct that would violate, any applicable law or regulation or would give rise to civil liability;' + 
                        '\nAccess, tamper with, or use non-public areas of the Site (including but not limited to user folders not designated as public or that you have not been given permission to access);' +
                        '\nAttempt to probe, scan, or test the vulnerability of any system or network or breach any security or authentication measures;' + 
                        '\nAttempt to access or search the Site, Content, Files or Services with any engine, software, tool, agent, device or mechanism other than the available third-party web browsers (such as Microsoft Internet Explorer or Mozilla Firefox), including but not limited to browser automation tools;' +
                        '\nSend unsolicited email, junk mail, spam, or chain letters, or promotions or advertisements for products or services;' +
                        '\nForge any TCP/IP packet header or any part of the header information in any email or newsgroup posting, or in any way use the Site, Content, Files or Services to send altered, deceptive or false source-identifying information; ' +
                        '\nInterfere with, or attempt to interfere with, the access of any user, host or network, including, without limitation, sending a virus, overloading, flooding, spamming, or mail-bombing the Site;'
            }]
        }],

        buttons: [{
            text: 'Register', 
            handler: function() {
                var f = Ext.getCmp('registration_form').form;
                if (f.isValid()) {
                    f.submit({waitMsg:'Saving data...', method: "POST", success: function(form, action) { Ext.MessageBox.alert('OK', 'Your account request has been sent to the Administrator. You will receive an email when your account is active.'); }, failure: function(form, action) {var data = Ext.decode(action.response.responseText); Ext.MessageBox.alert('Error', data.errors);}});
                }else{
                    Ext.MessageBox.alert('Error', 'Please fill all the fields and try again.');
                }
            }
        },{
            text: 'Reset',
            handler: function() {
                var f = Ext.getCmp('registration_form').form;
                f.reset();
            }
        }]

    });

    form.render(document.body);

});
