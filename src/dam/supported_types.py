import os
import dam
import mimetypes
# This dictionary lists all the types supported by Notredam

supported_types  = {
   'audio/flac': ['.flac'],
   'audio/midi': ['.mid', '.midi', '.midi', '.kar', '.mid'],
   'audio/mpeg': ['.mp3', '.mpega', '.mp2', '.mpga'],       # no aac here
   'audio/ogg': ['.spx', '.ogg', '.oga'],
   'audio/x-m4a': ['.m4a', '.aac'],
   'audio/x-ms-wma': ['.wma'],
   'audio/x-wav': ['.wav'],
   'image/gif': ['.gif'],
   'image/jpeg': ['.jpg', '.jpe', '.jpeg'],
   'image/png': ['.png'],
   'image/tiff': ['.tiff', '.tif'],
   'image/x-adobe-dng': ['.dng'],
   'image/x-canon-cr2': ['.cr2'],
   'image/x-ms-bmp': ['.bmp'],
   'image/x-nikon-nef': ['.nef'],
   'image/x-portable-graymap': ['.pgm'],
   'image/x-portable-pixmap': ['.ppm'],
   'application/pdf': ['.pdf'],
   'video/flv': ['.flv'],
   'video/mp4': ['.mp4'],
   'video/mpeg': ['.m1v', '.mpa', '.mpg', '.mpe', '.mpeg'],
   'video/ogg': ['.ogg'],
   'video/ts': ['.ts'],
   'video/x-m4v': ['.m4v'],
   'video/x-matroska': ['.mpv', '.mkv'],
   'video/x-msvideo': ['.avi'],
}


def get_types_by_ext(dict):
    "return the mapping extension: mime-type"
    ret = {}
    for k, v in dict.items():
        for ext in v:
            if ext in dict:
                raise ('Duplicated extension in supported types')
            ret[ext] = k
    return ret

def get_types_by_type(dict):
    "return the mapping  type:subtype:extensions"
    ret = {}
    for k, v in dict.items():
        t, subt = k.split('/')
        if t not in ret:
            ret[t] = {}
        ret[t][subt] = v
    return ret


mime_types_by_ext = get_types_by_ext(supported_types)
mime_types_by_type = get_types_by_type(supported_types)

def supported_extensions(mime_type):
    return supported_types.get(mime_type, None)


def guess_file_type(filename):
    ext = os.path.splitext(os.path.normpath(filename))[1]
    return mime_types_by_ext.get(ext, None)


if __name__=='__main__':
    import mimetypes
    mimetypes.knownfiles.append('mime.types')
    def make_list(strict):
        global types
        for (ext, t) in mimetypes._db.types_map[strict].items():
            a, b = t.split('/')
            if a in types:
                if b in types[a]:
                    types[a][b].append(ext)
                else:
                    types[a][b] = [ext]

    mimetypes.init()
    make_list(0)
    make_list(1)

    from pprint import pprint
    pprint(types)
