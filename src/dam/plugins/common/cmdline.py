#
# Functions to manage the command line
#

class Pushlist(list):
    "A List where we can push back values when iterating"
    def __init__(self, *args):
        list.__init__(self, *args)
        self.stack = []
        self.iterator = None

    def __iter__(self):
        self.iterator = list.__iter__(self)
        return self

    def next(self):
        if self.stack:
            return self.stack.pop()
        else:
            return self.iterator.next()

    def push(self, a):
        self.stack.append(a)
        

def splitstring(s):
    """Tokenizes a string containing command line arguments:

    See test_splitsstring() for examples.
    """
    s = s.replace('\n', ' ')
    sep = ' '
    l = Pushlist(s.split(sep))
    quotes = ['"', "'"]
    inside = False
    ret = []
    for w in l:
        if inside:
            if not w:
                word += sep
            elif w[-1] == quote:
                word += sep + w[:-1]
                inside = False
                quote=None
                ret.append(word)
            else:
                word += sep + w
        else:
            if not w:
                continue
            elif w[0] in quotes:
                if len(w) > 1 and w[-1] in quotes:   # a single word in quotes
                    ret.append(w[1:-1])
                    #if len(w) > 2:
                    #else:
                    #    ret.append('""')
                else:
                    quote = w[0]
                    inside = True
                    word = w[1:]
            elif w.find('=') >= 0:    # further split arguments of the type key=value so that
                i = w.find('=')       # value is a entry in the list
                if i:
                    ret.append(w[:i])
                ret.append('=')
                l.push(w[i+1:])
            else:
                ret.append(w)
    if inside:
        raise Exception("Error: unmatched quote in string")
    return ret

def test_splitstring():
    cases = [
      ( 'a b c', ['a', 'b', 'c'],),
      ( 'a   c', ['a', 'c'],),
      ( 'a ""  c', ['a', '', 'c'],),
      ( 'a "  "\n  c', ['a','  ', 'c'],),
      ( "a 'a b'  c", ['a', 'a b', 'c'],),
      ( 'a "a b" c', ['a', 'a b', 'c'],),
      ( 'a "a=b" c', ['a', 'a=b', 'c'],),
      ( 'a "a=" c', ['a', 'a=', 'c'],),
      ( 'a  a=  c', ['a', 'a', '=', 'c'],),
      ( 'a  =a  c', ['a', '=', 'a', 'c'],),
      ( 'a a="" c', ['a', 'a', '=', '', 'c'],),
      ( 'a z="b" c', ['a', 'z', '=', 'b', 'c'],),
      ( 'a z="b=c" d', ['a', 'z', '=', 'b=c', 'd'],),
      ( 'a z="x y z" c', ['a', 'z', '=', 'x y z', 'c'],),
    ]
    msg = ""
    for c in cases:
        r = splitstring(c[0])
        if r != c[1]:
            msg += "ERROR: <%s> split in %s (expecting %s)" % (c[0], r, c[1])
    print (not msg and 'OK') or msg


def import_cmd(modulename, name):
    module = __import__(modulename, fromlist = modulename)
    cmd = getattr(module, name)
    return cmd

## Test
#d = import_cmd('video_gst', 'FFF')
#print 'd', d
