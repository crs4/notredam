from . import log

class Schedule:
    """
        Manages action states across execution. An action can be in 5 states:
            <ready>: if it can be run
            <wait>:  if it depends on an running action
            <done>:  if it has finished running
            <fail>:  if it produced an error
            <cancelled>: if it depends on a failed action.

        When an action is <ready> its index is in the set self.ready

        When an action is in <wait> the list self.actions[action]['wait'] holds the
        name of the actions to be waited upon.

        An action is in <done>, <fail> or <cancelled> when it is not present in
        self.actions.
    """
    def __init__(self, dag, target, sorted=True):
        self.target = target   # used only for logging
        self.dag = dag
        a = self.action_list = self.dag.sort(sorted)
        self.ready = set(range(len(a)))
        self.actions = dict([(x, {'index':y, 'wlist':[]}) for (x,y) in zip(a, xrange(len(a)))])

    def _cb_set_to_wait(self, node, root):
        "set all actions dependent on root to wait"
        if node.name != root and node.name in self.actions:
            if root not in self.actions[node.name]['wlist']:
                self.actions[node.name]['wlist'].append(root)
            r = self.actions[node.name]['index']
            if r in self.ready:
                self.ready.remove(r)

    def _cb_set_to_ready(self, node, root):
        "mark all actions dependent on root (which just completed) as ready to run"
        action = self.actions.get(node.name, None)
        if action and root in action['wlist']:
            action['wlist'].remove(root)
            if not action['wlist']:
                self.ready.add(action['index'])

    def _cb_remove(self, node, user_data):
        "lo stato non e' ready di sicuro del nodo"
        log.info('target %s: cancelling %s on failed %s' % (self.target, node.name, user_data['failed_action']))
        if node.name in self.actions:
            del self.actions[node.name]
            if node.name != user_data['failed_action']:
                user_data['deleted'].append(node.name)

    def action_to_run(self):
        """Return the first action ready to run.
           If all actions are done, failed, or cancelled, returns None
           If no action is ready to run returns ''
        """
        #log.debug("action_to_run item=%s, actions=%s ready=%s" % (self.target, len(self.actions), len(self.ready))) #d 
        if not self.actions:
            #log.debug('action_to_run: no actions') #d
            return None
        if not self.ready:
            #log.debug('action_to_run: nothing ready') #d
            return ''
        else:
            r = min(self.ready)
            action = self.action_list[r]
            log.info('### target %s: run %s' % (self.target, action))
            self.ready.remove(r)
            self.dag.visit(action, self._cb_set_to_wait, action)
            #self.show() #d
            return action

    def done(self, action):
        log.debug('#### target %s: done %s' % (self.target, action))
        del self.actions[action]
        self.dag.visit(action, self._cb_set_to_ready, action)
        #self.show() #d

    def fail(self, action):
        "delete action and all actions dependent on it. Returns the number of actions deleted"
        log.debug('#### %s: FAIL %s' % (self.target, action))
        user_data = {'failed_action':action, 'deleted':[]}
        self.dag.visit(action, self._cb_remove, user_data)
        #self.show()
        return user_data['deleted']

    def show(self):
        ret = "sched %s: " % self.target
        for action in self.action_list:
            if action not in self.actions:
                ret += "%s:k, " % action    # done, failed or cancelled
            elif self.actions[action]['index'] in self.ready:
                ret += "%s:=, " % action    # ready
            elif not self.actions[action]['wlist']:
                ret += "%s:@, " % action    # running
            else:
                ret += ("%s:<%s>, " % (action, '-'.join(self.actions[action]['wlist'])))     # waiting
        log.debug(ret)

    def __str__(self):
        return "schedule(%s)" % self.target


# Test
if __name__=='__main__':
    from dam.mprocessor.pipeline import DAG
    from dam.mprocessor.make_plugins import pipeline
    def main():
        p = DAG(pipeline)
        p.show()
        s = Schedule(p, 'dddd')
        x1 = s.action_to_run()
        x2 = s.action_to_run()
        s.done(x2)
        x3 = s.action_to_run()
        x4 = s.action_to_run()
        s.fail(x1)
        x5 = s.action_to_run()
    main()
