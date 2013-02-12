
/*
# MediaDart, Copyright (C) 2006,2008 CRS4.
# All rights reserved.  Email: mediadart@crs4.it   Web: www.mediadart.org
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of:
#     The GNU Lesser General Public License as published by the Free
#     Software Foundation; either version 2.1 of the License, or (at
#     your option) any later version. The text of the GNU Lesser
#     General Public License is included with this library in the
#     file LICENSE.TXT.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the file
# LICENSE.TXT for more details.
#
*/


/**
 * SECTION:watermark-plugin
 *
 * <refsect2>
 * <title>Example launch line</title>
 * <para>
 * <programlisting>
 * gst-launch -v -m videotestsrc ! watermark filename=watermark.jpg ! fakesink silent=TRUE
 * </programlisting>
 * </para>
 * </refsect2>
 */

#ifdef HAVE_CONFIG_H
#  include <config.h>
#endif

#include <gst/gst.h>
#include <string.h>
#include "SDL.h"
#include "SDL_image.h"

#include "gstmediadartwatermarkfilter.h"

GST_DEBUG_CATEGORY_STATIC (gst_mediadartwatermarkfilter_debug);
#define GST_CAT_DEFAULT gst_mediadartwatermarkfilter_debug

#define WATERMARK_DEFAULT_NULL_FILENAME "__NONE__"

uint state, last_second, current_second;
SDL_Surface * image = NULL;
gint top, left;

/* Filter signals and args */
enum
{
  /* FILL ME */
  LAST_SIGNAL
};

enum
{
  ARG_0,
  ARG_SILENT,
  ARG_FILENAME,
  ARG_TOP,
  ARG_LEFT,
};

static GstStaticPadTemplate sink_factory = GST_STATIC_PAD_TEMPLATE ("sink",
    GST_PAD_SINK,
    GST_PAD_ALWAYS,
    GST_STATIC_CAPS ("ANY")
    );

static GstStaticPadTemplate src_factory = GST_STATIC_PAD_TEMPLATE ("src",
    GST_PAD_SRC,
    GST_PAD_ALWAYS,
    GST_STATIC_CAPS ("ANY")
    );

GST_BOILERPLATE (GstMediadartWatermarkFilter, gst_mediadartwatermarkfilter, GstElement,
    GST_TYPE_ELEMENT);

static void gst_mediadartwatermarkfilter_set_property (GObject * object, guint prop_id,
    const GValue * value, GParamSpec * pspec);
static void gst_mediadartwatermarkfilter_get_property (GObject * object, guint prop_id,
    GValue * value, GParamSpec * pspec);

static gboolean gst_mediadartwatermarkfilter_set_caps (GstPad * pad, GstCaps * caps);
static GstFlowReturn gst_mediadartwatermarkfilter_chain (GstPad * pad, GstBuffer * buf);

static void
gst_mediadartwatermarkfilter_base_init (gpointer gclass)
{
  static GstElementDetails element_details = {
    "Video Watermark Plugin",
    "Mediadart Filters",
    "Video Watermark Element",
    "Francesco Cabras <paneb@crs4.it>"
  };
  GstElementClass *element_class = GST_ELEMENT_CLASS (gclass);

  gst_element_class_add_pad_template (element_class,
      gst_static_pad_template_get (&src_factory));
  gst_element_class_add_pad_template (element_class,
      gst_static_pad_template_get (&sink_factory));
  gst_element_class_set_details (element_class, &element_details);
}

/* initialize the plugin's class */
static void
gst_mediadartwatermarkfilter_class_init (GstMediadartWatermarkFilterClass * klass)
{
  GObjectClass *gobject_class;
  GstElementClass *gstelement_class;

  gobject_class = (GObjectClass *) klass;
  gstelement_class = (GstElementClass *) klass;

  gobject_class->set_property = gst_mediadartwatermarkfilter_set_property;
  gobject_class->get_property = gst_mediadartwatermarkfilter_get_property;

  g_object_class_install_property (gobject_class, ARG_SILENT,
      g_param_spec_boolean ("silent", "Silent", "Produce verbose output ?",
          FALSE, G_PARAM_READWRITE));

  g_object_class_install_property (gobject_class, ARG_FILENAME,
      g_param_spec_string ("filename", "Filename", "Image Filename",
          WATERMARK_DEFAULT_NULL_FILENAME,
          G_PARAM_READWRITE | G_PARAM_STATIC_STRINGS));
	
  g_object_class_install_property (gobject_class, ARG_TOP,
	  g_param_spec_int ("top", "Top", "Watermark Top Position",
		  0, G_MAXINT, 0, G_PARAM_READWRITE));	
	
  g_object_class_install_property (gobject_class, ARG_LEFT,
      g_param_spec_int ("left", "Left", "Watermark Left Position",
		  0, G_MAXINT, 0, G_PARAM_READWRITE));	
}

/* initialize the new element
 * instantiate pads and add them to element
 * set functions
 * initialize structure
 */
static void
gst_mediadartwatermarkfilter_init (GstMediadartWatermarkFilter * filter,
    GstMediadartWatermarkFilterClass * gclass)
{
  GstElementClass *klass = GST_ELEMENT_GET_CLASS (filter);

  filter->sinkpad =
      gst_pad_new_from_template (gst_element_class_get_pad_template (klass,
          "sink"), "sink");
  gst_pad_set_setcaps_function (filter->sinkpad,
                                GST_DEBUG_FUNCPTR(gst_mediadartwatermarkfilter_set_caps));
  gst_pad_set_getcaps_function (filter->sinkpad,
                                GST_DEBUG_FUNCPTR(gst_pad_proxy_getcaps));

  filter->srcpad =
      gst_pad_new_from_template (gst_element_class_get_pad_template (klass,
          "src"), "src");
  gst_pad_set_getcaps_function (filter->srcpad,
                                GST_DEBUG_FUNCPTR(gst_pad_proxy_getcaps));

  gst_element_add_pad (GST_ELEMENT (filter), filter->sinkpad);
  gst_element_add_pad (GST_ELEMENT (filter), filter->srcpad);
  gst_pad_set_chain_function (filter->sinkpad,
                              GST_DEBUG_FUNCPTR(gst_mediadartwatermarkfilter_chain));
  filter->silent = FALSE;


  state = last_second = current_second = 0;

  //Init SDL
  if (SDL_Init(SDL_INIT_NOPARACHUTE) < 0){
    fprintf(stderr, "Error inizializing SDL:%s\n", SDL_GetError());
    exit(1);
  }else{
    //printf("Inizialized SDL\n");
    //g_print ("Filename: %s\n" , filter->filename);
//     image = IMG_Load("logo.gif");
//     SDL_SetAlpha(image, SDL_SRCALPHA, SDL_ALPHA_TRANSPARENT);
  }
}

static void
gst_mediadartwatermarkfilter_set_property (GObject * object, guint prop_id,
    const GValue * value, GParamSpec * pspec)
{
  GstMediadartWatermarkFilter *filter = GST_MEDIADARTWATERMARKFILTER (object);
  const gchar *filename = NULL;

  switch (prop_id) {
    case ARG_SILENT:
      filter->silent = g_value_get_boolean (value);
      break;
    case ARG_FILENAME:
			//g_print("Setting filename %s \n", g_value_get_string (value));
      filename = g_value_get_string(value);
      // FIXME: we are lenient, allowing prefixes to the NULL filename.  OK?
      if (g_str_has_suffix(filename, WATERMARK_DEFAULT_NULL_FILENAME)) {
          image = NULL;
      } else {
          image = IMG_Load(filename);
	  // filter->filename = g_value_get_string (value);
      }
      break;
	  case ARG_TOP:
			//g_print("In top");
			filter->top = g_value_get_int (value);	 
			//g_print("Top: %d\n", filter->top);	
			break;
		case ARG_LEFT:
			//g_print("In left");
			filter->left = g_value_get_int (value);
			//g_print("Left: %d\n", filter->left);
			break;	
    default:
      G_OBJECT_WARN_INVALID_PROPERTY_ID (object, prop_id, pspec);
      break;
  }
}

static void
gst_mediadartwatermarkfilter_get_property (GObject * object, guint prop_id,
    GValue * value, GParamSpec * pspec)
{
  GstMediadartWatermarkFilter *filter = GST_MEDIADARTWATERMARKFILTER (object);

  switch (prop_id) {
    case ARG_SILENT:
      g_value_set_boolean (value, filter->silent);
      break;
    case ARG_FILENAME:
      g_value_set_string  (value, filter->filename);
      break;
		case ARG_TOP:
			g_value_set_int  (value, filter->top);
			break;
		case ARG_LEFT:
			g_value_set_int  (value, filter->left);
			break;
		default:
      G_OBJECT_WARN_INVALID_PROPERTY_ID (object, prop_id, pspec);
      break;
  }
}

/* GstElement vmethod implementations */

/* this function handles the link with other elements */
static gboolean
gst_mediadartwatermarkfilter_set_caps (GstPad * pad, GstCaps * caps)
{
  GstMediadartWatermarkFilter *filter;
  GstPad *otherpad;

  filter = GST_MEDIADARTWATERMARKFILTER (gst_pad_get_parent (pad));
  otherpad = (pad == filter->srcpad) ? filter->sinkpad : filter->srcpad;

  return gst_pad_set_caps (pad, caps);
}

/* chain function
 * this function does the actual processing
 */

static GstFlowReturn
gst_mediadartwatermarkfilter_chain (GstPad * pad, GstBuffer * buf)
{



  GstMediadartWatermarkFilter *filter;
  filter = GST_MEDIADARTWATERMARKFILTER (GST_OBJECT_PARENT (pad));


  if (image != NULL){


  GstCaps *srcCaps = gst_pad_get_negotiated_caps(pad);

  const GstStructure *gstr;
  gstr = gst_caps_get_structure (srcCaps, 0);
  gint width, height;

  gst_structure_get_int (gstr, "width", &width);
  gst_structure_get_int (gstr, "height", &height);
  


  SDL_Surface * buffer = NULL;
  SDL_Rect dest;



//   GstBuffer  * gst_buffer_copy = NULL;
  /*Creo una surface x l'img da caricare*/
//   SDL_Surface * image = NULL;
  /*Loading Rect*/

  /* COPIO IL BUFFER DI GSTREAMER PER PASSARLO ALLE SDL */
//   gst_buffer_copy = gst_buffer_copy(buf);
//   g_print ("DONE COPYNG BUFFER: %d\n",gst_buffer_copy->size);
  /* COPIO I METADATA DENTRO IL NUOVO BUFFER */
//   gst_buffer_copy_metadata(gst_buffer_copy, buf, GST_BUFFER_COPY_ALL);

  /* Provo a creare una nuova surface SDL tramite questo buffer in ingresso */
//   buffer = SDL_CreateRGBSurfaceFrom(buf->data, 640, 480, 24, 1920, 0x0000ff, 0x00ff00, 0xff0000, 0x000000);
  buffer = SDL_CreateRGBSurfaceFrom(buf->data, width, height, 24, width*3, 0x0000ff, 0x00ff00, 0xff0000, 0x000000);

//   SDL_SetAlpha(buffer, SDL_SRCALPHA, SDL_ALPHA_TRANSPARENT);
  /*Inizializzo il buffer video*/
//   buffer = SDL_CreateRGBSurface(SDL_SWSURFACE, 640, 480, 32, 0xff000000, 0x00ff0000, 0x0000ff00, 0x000000ff);
  /*Carico l'img*/
  
//   g_print("Format:" ); //image->format
  /*Lock dell'image da cui ottere i dati */
//   SDL_LockSurface(image);

  /*Inizializzo il rect di destinazione */

  /*Lock del buffer */
//   SDL_LockSurface(buffer);
  
  /*Blit sul buffer */  
//   SDL_SetAlpha(buffer, SDL_SRCALPHA, 0);
//   g_print("Blitting surface: %d\n", SDL_BlitSurface(image, NULL, buffer, NULL));
//   SDL_BlitSurface(image, NULL, buffer, NULL);
//   g_print ("Image Dimensions: %d:%d\n", image->w, image->h);
//   SDL_UpdateRect(buffer, 0, 0, image->w, image->h);


	
		
  dest.y = filter->top;
  dest.x = filter->left;
  dest.w = image->w;
  dest.h = image->h;

  SDL_BlitSurface(image, NULL, buffer, &dest);

  


//   if (filter->silent == FALSE)
// 
//       current_second = (gint64)buf->timestamp / GST_SECOND;
//       if (current_second % 5 == 0 && current_second != last_second){
//         if (state == 0){
//           g_print("state == 0\n");
//           state=1;
//         }
//         else if (state == 1){
//           g_print("state == 1\n");
//           state=0;
//         }
//         last_second = current_second;
//         /*Salvo l'img blittata dalle SDL*/
//         SDL_SaveBMP  (buffer, "test.bmp");
//       }
//       
//       if (state == 0){    
// //         memset( buf->data, 255, sizeof(guint8) * buf->size);
//       }
//       if (state == 1){
// //         memset( buf->data, 0, sizeof(guint8) * buf->size);
// 
//       }
/*    for(x = 0;x < 640; ++x){
      for(y =0; y < 480; ++y){
        pos = (y * 640 + x) * 3;
//         g_print ("O merd: %d\n", pos);
        buf->data[pos] = 0;
        buf->data[pos+1] = 0;
        buf->data[pos+2] = 255;
      }
    }*/
//     g_print ("RGB: %d-%d-%d\n", buf->data[0], buf->data[1], buf->data[2]);
    

  /* just push out the incoming buffer without touching it */
//   SDL_UnlockSurface( buffer );
//   SDL_UnlockSurface( image );


  SDL_FreeSurface(buffer);
  }
//   SDL_FreeSurface(image);
  return gst_pad_push (filter->srcpad, buf);
}


/* entry point to initialize the plug-in
 * initialize the plug-in itself
 * register the element factories and pad templates
 * register the features
 *
 * exchange the string 'plugin' with your elemnt name
 */
static gboolean
plugin_init (GstPlugin * plugin)
{
  /* exchange the strings 'plugin' and 'Template plugin' with your
   * plugin name and description */
  GST_DEBUG_CATEGORY_INIT (gst_mediadartwatermarkfilter_debug, "plugin",
      0, "Template plugin");

  return gst_element_register (plugin, "watermark",
      GST_RANK_NONE, GST_TYPE_MEDIADARTWATERMARKFILTER);
}

/* this is the structure that gstreamer looks for to register plugins
 *
 * exchange the strings 'plugin' and 'Template plugin' with you plugin name and
 * description
 */
GST_PLUGIN_DEFINE (GST_VERSION_MAJOR,
    GST_VERSION_MINOR,
    "mediadartfilters",
    "Mediadart Watermark Filter",
    plugin_init, "0.3", "LGPL", "Mediadart", "http://www.mediadart.org/")

