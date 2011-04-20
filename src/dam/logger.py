#########################################################################
#
# NotreDAM, Copyright (C) 2009, Sardegna Ricerche.
# Email: labcontdigit@sardegnaricerche.it
# Web: www.notre-dam.org
#
# This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#########################################################################


import logging
#from web_application.config import dir_log, logging_level
from dam.settings import DEBUG,  dir_log
import sys, os.path
from django.utils.encoding import smart_unicode


#logging_level = logging.DEBUG
logging_level = logging.DEBUG
logging.basicConfig(level=logging_level,
                    format='[%(asctime)s] %(levelname)-8s %(pathname)s %(lineno)s %(message)s',
                    datefmt = '%d/%b/%Y %H:%M:%S',
#                    format='[%(asctime)s] %(levelname)-8s %(module)s %(lineno)d  %(message)s',
#                    datefmt='%d/%b/%Y %H:%M:%S',
#                    filename=dir_log + '/dam.log',
                    filemode='a'
                    )
                    
logger = logging.getLogger('dam')
logger.addHandler(logging.FileHandler(os.path.join(dir_log,  'dam.log')))

#console = logging.StreamHandler()
## define a Handler which writes INFO messages or higher to the sys.stderr
#console.setLevel(logging_level)
## set a format which is simpler for console use
#formatter = logging.Formatter('[%(asctime)s] %(levelname)-8s %(message)s')
#formatter.datefmt = '%d/%b/%Y %H:%M:%S'
#
#
#console.setFormatter(formatter)
## add the handler to the root logger
#
##logging.getLogger('').addHandler(console)
#default_logger.addHandler(console)


#def set_fileoutput(filename):
    #file_handler = logging.FileHandler(filename)
    #logging.getLogger('').addHandler(file_handler )
#
#def critical(message):
    #"""
    #Logs in a critical level 
    #"""
    #if DEBUG: default_logger.critical(  "["+ sys._getframe(1).f_code.co_filename +" " + sys._getframe(1).f_code.co_name + ":"+smart_unicode(sys._getframe(1).f_lineno)+"] " + smart_unicode( message )  )
#
#def error(message):
    #"""
    #Logs in a error level 
    #"""
    #default_logger.error(  "["+ sys._getframe(1).f_code.co_filename +" " + sys._getframe(1).f_code.co_name + ":"+smart_unicode(sys._getframe(1).f_lineno)+"] " + smart_unicode( message )  )
#
#def warning(message):
    #"""
    #Logs in a warning level 
    #"""
    #if DEBUG: default_logger.warning( "["+ sys._getframe(1).f_code.co_filename +" " + sys._getframe(1).f_code.co_name + ":"+smart_unicode(sys._getframe(1).f_lineno)+"] " + smart_unicode( message ) )
#
#def debug(message):
    #"""
    #Logs in a debug level 
    #"""
    #if DEBUG: default_logger.debug( "[" + sys._getframe(1).f_code.co_name + ":"+smart_unicode(sys._getframe(1).f_lineno)+"] " + smart_unicode( message )  )
#
#def info(message):
    #"""
    #Logs in a info level 
    #"""
    #default_logger.info(   "["+ sys._getframe(1).f_code.co_filename +" " + sys._getframe(1).f_code.co_name + ":"+smart_unicode(sys._getframe(1).f_lineno)+"] " + smart_unicode( message )  )
#
#def exception(message):
    #"""
    #Logs an exception 
    #"""
    #default_logger.exception(  "["+ sys._getframe(1).f_code.co_filename +" " + sys._getframe(1).f_code.co_name + ":"+smart_unicode(sys._getframe(1).f_lineno)+"] " + smart_unicode( message )  )
    #
