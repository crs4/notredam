import ldap
import sys
from django.contrib.auth.models import User
from dam.settings import AUTH_LDAP_SERVER, AUTH_LDAP_BASE_USER, AUTH_LDAP_BASE_PASS

class LDAPBackend:
    def authenticate(self, username=None, password=None):
        base = "dc=crs4"
        scope = ldap.SCOPE_SUBTREE
        filter = "(&(objectclass=posixAccount) (uid=%s))" % username
        ret = ['dn','sn','cn','givenName']
        # Authenticate the base user so we can search
        try:
            l = ldap.initialize(AUTH_LDAP_SERVER)
            l.protocol_version = ldap.VERSION3
            l.simple_bind_s(AUTH_LDAP_BASE_USER,AUTH_LDAP_BASE_PASS)
        except Exception, e : #ldap.LDAPError:
            print >> sys.stderr, "error %s " % (str(e))
            return None

        try:
            result_id = l.search(base, scope, filter, ret)
            result_type, result_data = l.result(result_id, 0)

            # If the user does not exist in LDAP, Fail.
            if (len(result_data) != 1):
                return None

            # Attempt to bind to the user's DN
            l.simple_bind_s(result_data[0][0],password)

            # The user existed and authenticated. Get the user
            # record or create one with no privileges.
            try:
                user = User.objects.get(username__exact=username)
            except:
                # Theoretical backdoor could be input right here. We don't
                # want that, so input an unused random password here.
                # The reason this is a backdoor is because we create a
                # User object for LDAP users so we can get permissions,
                # however we -don't- want them able to login without
                # going through LDAP with this user. So we effectively
                # disable their non-LDAP login ability by setting it to a
                # random password that is not given to them. In this way,
                # static users that don't go through ldap can still login
                # properly, and LDAP users still have a User object.
                from random import choice
                import string
                temp_pass = ""
                for i in range(8):
                    temp_pass = temp_pass + choice(string.letters)
                user = User.objects.create_user(username,
                         username + '@crs4.it',temp_pass)
                user.is_staff = False
		user.first_name=result_data[0][1]['givenName'][0]
		user.last_name=result_data[0][1]['sn'][0]
                user.save()
            # Success.
            return user
           
        except ldap.INVALID_CREDENTIALS:
            # Name or password were bad. Fail.
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

