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


header = """
import random
from mediadart import log
from twisted.internet import defer, reactor

"""

def main():
    keys = pipeline.keys()
    keys.sort()

    for p in keys[0:]:
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
        f.write('    reactor.callLater(0*random.random(), d.callback, "ok")\n')
        f.write('    return d\n')
        f.close()

if __name__=="__main__":
    main()
