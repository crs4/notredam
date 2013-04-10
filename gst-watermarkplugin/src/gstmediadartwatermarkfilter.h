/* MediaDart, Copyright (C) 2006,2009 CRS4.
 * All rights reserved.  Email: mediadart@crs4.it   Web: www.mediadart.org
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of:
 *     The GNU Lesser General Public License as published by the Free
 *     Software Foundation; either version 2.1 of the License, or (at
 *     your option) any later version. The text of the GNU Lesser
 *     General Public License is included with this library in the
 *     file LICENSE.TXT.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the file
 * LICENSE.TXT for more details.
 */


#ifndef __GST_MEDIADARTWATERMARKFILTER_H__
#define __GST_MEDIADARTWATERMARKFILTER_H__

#include <gst/gst.h>

G_BEGIN_DECLS

/* #defines don't like whitespacey bits */
#define GST_TYPE_MEDIADARTWATERMARKFILTER \
  (gst_mediadartwatermarkfilter_get_type())
#define GST_MEDIADARTWATERMARKFILTER(obj) \
  (G_TYPE_CHECK_INSTANCE_CAST((obj),GST_TYPE_MEDIADARTWATERMARKFILTER,GstMediadartWatermarkFilter))
#define GST_MEDIADARTWATERMARKFILTER_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_CAST((klass),GST_TYPE_MEDIADARTWATERMARKFILTER,GstMediadartWatermarkFilterClass))
#define GST_IS_MEDIADARTWATERMARKFILTER(obj) \
  (G_TYPE_CHECK_INSTANCE_TYPE((obj),GST_TYPE_MEDIADARTWATERMARKFILTER))
#define GST_IS_MEDIADARTWATERMARKFILTER_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_TYPE((klass),GST_TYPE_MEDIADARTWATERMARKFILTER))

typedef struct _GstMediadartWatermarkFilter      GstMediadartWatermarkFilter;
typedef struct _GstMediadartWatermarkFilterClass GstMediadartWatermarkFilterClass;

struct _GstMediadartWatermarkFilter
{
  GstElement element;

  GstPad *sinkpad, *srcpad;

  gboolean silent;
  const gchar* filename;
  gint top, left;
};

struct _GstMediadartWatermarkFilterClass 
{
  GstElementClass parent_class;
};

GType gst_mediadartwatermarkfilter_get_type (void);

G_END_DECLS

#endif /* __GST_MEDIADARTWATERMARKFILTER_H__ */
