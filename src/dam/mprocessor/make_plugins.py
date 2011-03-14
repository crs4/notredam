
simple_pipe = {
    'a1': {'params': {'l':22, 'm': 23}, 
           'script_name': 'pya1',
           'in':[],             
           'out':['v1'] },

    'a2': {'params': {'l':22, 'm': 23}, 
           'script_name': 'pya1',
           'in':['v1'],             
           'out':['v2'] },

    'a3': {'params': {'l':22, 'm': 23}, 
           'script_name': 'pya1',
           'in':['v1'],             
           'out':['v3',] },

    'a4': {'params': {'l':22, 'm': 23}, 
           'script_name': 'pya1',
           'in':['v2', 'v3'],             
           'out':[] },
}


pipeline = {
    'a1': {'params': {'l':22, 'm': 23}, 
           'script_name': 'pya1',
           'in':['vx'],             
           'out':['v1', 'v2',] },

    'a2': {'params': {'x':22, 'm': 23}, 
           'script_name': 'pya2',
           'in':['v1','v4',],    
           'out':['v3', ] },

    'a3': {'params': {'ubi':22, 'm': 23}, 
           'script_name': 'pya3',
           'in':['v0'],             
           'out':['v4','v5',] },

    'a4': {'params': {'cart':[1, 2, 3], 'm': 23}, 
           'script_name': 'pya4',
           'in':['v7',],            
           'out':[] },

    'a5': {'params': {'name':'a5', 'altro': {'a':1, 'b': 2},}, 
           'script_name': 'pya5',
           'in':['v4',], 
           'out':['v6'] },

    'a6': {'params': {'l':22, 'm': 23}, 
           'script_name': 'pya6',
           'in':['v3','v6','v9',],  
           'out':[] },

    'a7': {'params': {'l':22, 'm': 23}, 
           'script_name': 'pya7',
           'in':['v2', ],           
           'out':['v8'] },

    'a8': {'params': {'l':22, 'm': 23}, 
           'script_name': 'pya8',
           'in':['v8', ],           
           'out':['v9',] },

    'a9': {'params': {'l':22, 'm': 23}, 
           'script_name': 'pya9',
           'in':['v5',],            
           'out':['v7'] },
}

pipeline2 = {
    'a1': {'params': {'l':22, 'm': 23}, 
           'script_name': 'pya1',
           'in':[],             
           'out':[] },

    'a2': {'params': {'x':22, 'm': 23}, 
           'script_name': 'pya2',
           'in':[],             
           'out':[] },

    'a3': {'params': {'ubi':22, 'm': 23}, 
           'script_name': 'pya3',
           'in':[],             
           'out':[] },

    'a4': {'params': {'cart':[1, 2, 3], 'm': 23}, 
           'script_name': 'pya4',
           'in':[],             
           'out':[] },
}




if __name__=='__main__':
    import sys
    from random import random

    header = """
from random import random
from mediadart import log
from twisted.internet import defer, reactor
from twisted.python.failure import Failure

"""

    def main(failures):
        keys = pipeline.keys()
        keys.sort()

        if failures == 'all':
            failures = keys

        for p in keys:
            if p in failures:
                level = '0.9'
            else:
                level = '2.0'   # infinity
            script_name = pipeline[p]['script_name']
            f=open('plugins/%s.py' % script_name, 'w')
            f.write(header)
            f.write("def run(item, workspace, ")
            paramlist = tuple(pipeline[p]['params'].keys())
            for param in paramlist:
                f.write('%s, ' % param)
            f.write('):\n    log.debug("Executing %s.run(item=%%s, ' % p)
            for param in paramlist:
                f.write('%s=%%s, ' % param)
            f.write(')" % (item, ')
            for param in paramlist:
                f.write('%s, ' % param)
            f.write('))\n')
            f.write('    d = defer.Deferred()\n')
            f.write('    if random() > %s:\n' % level)
            if random() > 0.5:
                f.write('        d.errback(Failure(Exception("FAILURE error: %s" % __file__)))\n')
            else:
                f.write('        raise Exception("EXCEPTION error: %s" % __file__)\n')
            f.write('    else:\n')
            f.write('        reactor.callLater(3*random(), d.callback, "ok")\n')
            f.write('    return d\n')
            f.close()
    main(sys.argv[1:])
