# plugindir is set in configure
COMPOSER_CFLAGS = -Wall `sdl-config --cflags`
COMPOSER_LIBS = -lSDL_image
COMPOSER_LDFLAGS = `sdl-config --libs`
# ##############################################################################
# # change libgstplugin.la to something more suitable, e.g. libmysomething.la  #
# ##############################################################################
plugin_LTLIBRARIES = libgstmediadart.la
#
# ##############################################################################
# # for the next set of variables, rename the prefix if you renamed the .la,   #
# #  e.g. libgstplugin_la_SOURCES => libmysomething_la_SOURCES                 #
# #       libgstplugin_la_CFLAGS  => libmysomething_la_CFLAGS                  #
# #       libgstplugin_la_LIBADD  => libmysomething_la_LIBADD                  #
# #       libgstplugin_la_LDFLAGS => libmysomething_la_LDFLAGS                 #
# ##############################################################################
#
# # sources used to compile this plug-in
libgstmediadart_la_SOURCES = gstmediadartwatermarkfilter.c

# # flags used to compile this plugin
# # add other _CFLAGS and _LIBS as needed
#
libgstmediadart_la_CFLAGS = $(GST_CFLAGS)  $(COMPOSER_CFLAGS) $(GST_CONTROLLER_CFLAGS)
libgstmediadart_la_LIBADD = $(GST_LIBS) $(GST_BASE_LIBS) $(COMPOSER_LIBS)
libgstmediadart_la_LDFLAGS = $(GST_PLUGIN_LDFLAGS) $(GST_CONTROLLER_LDFLAGS) $(COMPOSER_LDFLAGS)
#
# # headers we need but don't want installed
#
#
noinst_HEADERS = gstmediadartwatermarkfilter.h
