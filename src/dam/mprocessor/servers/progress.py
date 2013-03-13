import re
from dam.mprocessor import log
from dam.mprocessor.utils import doHTTP

regular_expressions = {
    'gstreamer-progressreport': re.compile('report.*\(\s*([\d.]+) %\)$'),
}

def get_progress_cb(progress_url, regex):
    if not progress_url:
        return None 
    if regex in regular_expressions:
        regex = regular_expressions[regex]
    return ProgressReport(progress_url, regex).progress

class ProgressReport:
    def __init__(self, url, regex):
        "The parameter must be a regular expression to "
        self.re = re.compile(regex)
        self.url = url

    def progress(self, data):
        def log_ok(page):
            pass

        def log_err(failure):
            log.error('Error in sending update notifications: %s' % str(failure))

        print '****************** progress search on data:'
        print data
        print '******************'
        g = self.re.search(data)
        if not g:
            #log.debug('progress: no completion in %s' % data)
            return
        completion = g.group(1)
        log.debug('Progress report to %s: completion at %s%%' % (self.url, completion))
        url='%s/%s' % (self.url, completion)
        try:
            data = doHTTP(url)
            log_ok(data)
        except e:
            log_err(e)
            raise

