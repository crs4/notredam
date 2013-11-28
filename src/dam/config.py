import os
# MediaDART path containing security certs (default to /home/user/node00/crypto)
MD_CERT_PATH = os.path.join(os.getenv('HOME'), 'node00', 'crypto')

# MediaDART configuration (to be changed if you installed MediaDART on a remote node, default to local install configuration)
#MEDIADART_CONF = {
#        "node_ip" : "192.168.100.3",
#        "node_port" :"7000",
#        "client_key" : os.path.join(MD_CERT_PATH, "client.key"),
#        "client_certificate" : os.path.join(MD_CERT_PATH, "client.crt"),
#        "client_key_cert" : os.path.join(MD_CERT_PATH, "client-key-cert.pem"),
#        "ca_certificate" : os.path.join(MD_CERT_PATH, "myca.crt"), 
#}

#OLD GOOGLE_KEY="ABQIAAAASa-q3XL_xChhiMK0ZCLQDhTpH3CbXHjuCVmaTc5MkkU4wO1RRhSAW5M-xy41b6agXuGI_c_kjlFOKg"
GOOGLE_KEY="ABQIAAAAo28WphcXpYaxZbMn79s0VRRETiP29whtXF2gCnIqeoPY9fJFzxSVzP1SJSa_NlficQA0MT5QgWobQw"

SAFE_MODE = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'dam',                      # Or path to database file if using sqlite3.
        'USER': 'dam',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    },
    #'default': {
        #'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        #'NAME': 'dam_db',                      # Or path to database file if using sqlite3.
        #'USER': 'dam',                      # Not used with sqlite3.
        #'PASSWORD': 'dam',                  # Not used with sqlite3.
        #'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        #'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    #}
    
}

SERVER_PUBLIC_ADDRESS = '127.0.0.1:10000'
