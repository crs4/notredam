import random
import os
#from mediadart import log

class DAGError(Exception):
    pass

class Node:
    def __init__(self, name):
        self.name = name
        self.childs = []
        self.index = None
        self.lowlink = None
        self.depth = None   #
        self.visited = 0

    def add_child(self, node):
        self.childs.append(node)

    def __repr__(self):
        return "<Node %s>" % self.name


class DAG:
    def __init__(self, pipeline):
        self.root = Node('__start__')
        self.pipeline = pipeline
        self._build_dag()
        self._check_cycles()

    def _build_dag(self):
        outputs = {}  # dizionario 'output': nodo produttore
        if len(self.pipeline) == 0:
            raise DAGError('Empty pipeline')
        for name, data in self.pipeline.items():
            #print 'processing node', name
            node = Node(name)
            data['__node__'] = node
            for v in data['out']:
                #print 'adding %s<-%s to outputs' % (v, node.name) 
                if v in outputs:
                    raise DAGError('duplicated output %s for %s and %s' % (v, outputs[v].name, node.name))
                else:
                    outputs[v] = node

        #print outputs
        for data in self.pipeline.values():
            node = data['__node__']
            attached = 0
            for v in data['in']:
                if v in outputs:  
                    #print 'found dependency %s -> %s' % (outputs[v].name, node.name)
                    attached = 1
                    outputs[v].add_child(node)
            if not attached:
                #print 'attaching %s to root' % node.name
                self.root.add_child(node)
        if not self.root.childs:
            raise DAGError('Cycles detected')


    def _check_cycles(self):
        nodes = []
        msg = self._tarjan(self.root, 0, 0, nodes, '')
        if msg:
            raise DAGError("cyclic dependencies: %s" % msg)

    def _tarjan(self, node, index, lowlink, stack, msg):
        """ detect if there are cycles """
        node.index = node.depth = index
        node.lowlink = index 
        index += 1
        stack.append(node)
        #print "_tarjan: appending %s(index=%s, lowlink=%s, childs=%s)" % (node.name, node.index, node.lowlink, '-'.join([x.name for x in node.childs]))
        for n in node.childs:
            if n.index is None:
                msg = self._tarjan(n, index, lowlink, stack, msg)
                node.lowlink = min(node.lowlink, n.lowlink)
            elif n in stack:
                node.lowlink = min(node.lowlink, n.index)
            n.depth = max(n.depth, index)
        if node.lowlink == node.index:
            top = stack.pop()
            if top != node:
                n = top
                while n != node:
                    msg += '%s <- ' % n.name
                    n = stack.pop()
                msg += '%s <- %s;' % (node.name, top.name)
        return msg

    def _new_tag(self):
        self.root.visited += 1
        return self.root.visited

    def _visit(self, node, shuffled, tag, user_callback, user_data):
        """ visit the DAG depth first, call the callback at each node """
        node.visited = tag
        childs = node.childs
        if shuffled and childs:
            childs = random.sample(node.childs, len(node.childs))
        for n in childs:
            if n.visited != tag:
                self._visit(n, shuffled, tag, user_callback, user_data)
        if user_callback:
            user_callback(node, user_data)

    def sort(self, shuffled=False):
        """returns a topological sorting of the DAG. If shuffled is True, return
           a (possibly) different ordering each time it is called
        """
        tag = self._new_tag()
        sorted = []
        def cb(node, user_data):
            user_data.insert(0, node.name)
        self._visit(self.root, shuffled, tag, cb, sorted)
        return sorted[1:]

    def visit(self, name, user_callback, user_data):
        """ visit all the nodes applying callback to user_data """
        tag = self._new_tag()
        self._visit(self.pipeline[name]['__node__'], 0, tag, user_callback, user_data)

    def show(self):
        """Print node: childs ordering nodes per depth in DAG (distance from root)"""
        depths = {}
        for name in self.sort():
            node = self.pipeline[name]['__node__']
            childs = node.childs[:]
            childs.sort()
            s = '%s: %s\n' % (node.name, ' '.join(['%s' % (x.name) for x in childs]))
            if node.depth in depths:
                depths[node.depth].append(s)
            else:
                depths[node.depth] = [s]
        keys = depths.keys()
        keys.sort()
        for k in keys:
            nodes = depths[k][:]
            nodes.sort()
            print 'depth %s:\n %s' % (k, ' '.join(nodes))

def test():
    pipeline = {
        'a1': {'in':['v13'],                 'out':['v1', 'v2',] },
        'a2': {'in':['v1','v4', 'v9'],       'out':['v3', ] },
        'a3': {'in':['v0'],                 'out':['v4','v5',] },
        'a4': {'in':['v7',],            'out':[] },
        'a5': {'in':['v4',],            'out':['v6', 'vx'] },
        'a6': {'in':['v3','v6','v9',],  'out':[] },
        'a7': {'in':['v2', ],           'out':['v8'] },
        'a8': {'in':['v8', ],            'out':['v9',] },
        'a9': {'in':['v5',],            'out':['v7'] },
    }
    try:
        dg = DAG(pipeline)
    except DAGError, e:
        print 'ERROR: %s' % str(e)
    else:
        d1 = dg.sort(0)
        print id(d1), d1
        
if __name__=='__main__':
    test()


            
