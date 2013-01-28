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

from dam.plugins.common.adapter import Adapter
from dam.repository.models import get_storage_file_name
from dam.core.dam_repository.models import Type
from dam.plugins.pdfcover_idl import inspect
from twisted.internet import defer, reactor
from mediadart import log

def run(workspace, 
        item_id, 
        source_variant_name,
        output_variant_name,
        output_extension,  # extension (with the '.') or "same_as_source"
        max_size = 0,          # largest dimension
        ):
    deferred = defer.Deferred()
    adapter = PdfCover(deferred, workspace, item_id, source_variant_name)
    reactor.callLater(0, adapter.execute, output_variant_name, output_extension,
        max_size=max_size)
    return deferred

class PdfCover(Adapter):
    remote_exe = 'convert'
    md_server = "LowLoad"

    def get_cmdline(self, output_variant_name, output_extension, max_size):
        global pipe1, pipe2
        if max_size:
            pipe = pipe1
        else:
            pipe = pipe2

        self.out_type = Type.objects.get_or_create_by_filename('foo%s' % output_extension)
        self.out_file = get_storage_file_name(self.item.ID, self.workspace.pk, 
                                              output_variant_name, output_extension)
        self.cmdline =  pipe % {'infile': self.source.uri, 'outfile':self.out_file,
                                'xsize':max_size, 'ysize':max_size, }


pipe1 = '-density 300 "file://%(infile)s[0]" -size %(xsize)sx%(ysize)s ' \
        '-geometry %(xsize)sx%(ysize)s +profile "*" "outfile://%(outfile)s"'

pipe2 = '-density 300 "file://%(infile)s[0]" "outfile://%(outfile)s"' 




#
# Stand alone test: need to provide a compatible database (item 2 must be an item with a audio comp.)
#
from twisted.internet import defer, reactor
from dam.repository.models import Item
from dam.workspace.models import DAMWorkspace

def test():
    print 'test'
    item = Item.objects.get(pk=6)
    workspace = DAMWorkspace.objects.get(pk = 1)
    d = run(workspace,
            item.pk,
            source_variant_name = 'original',
            output_variant_name =  'fullscreen',
            output_extension = '.jpg',
            max_size=400,
            )
    d.addBoth(print_result)
    
def print_result(result):
    print 'print_result', result
    reactor.stop()

if __name__ == "__main__":
    from twisted.internet import reactor
    
    reactor.callWhenRunning(test)
    reactor.run()

    
    
    

    
    
    
