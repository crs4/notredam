import os
from json import loads
from dam.mprocessor.models import Task
from django.http import Http404, HttpResponse, HttpResponseServerError
from dam.logger import logger

#import logging
#logger = logging.getLogger('mprocessor')
#logger.addHandler(logging.FileHandler(os.path.join(INSTALLATIONPATH,  'log/mprocessor.log')))
#logger.setLevel(LOG_LEVEL)

#
# This is the view that receives responses and pushes on the chain of calls
#
def task_dispatch(request, task_id):
    """General dispatcher for incoming responses"""
    try:
        logger.debug("-------------------request.raw_post_data: %s" %request.raw_post_data)
        post_data = loads(request.raw_post_data)
        task = Task.objects.get(task_id=task_id)
        logger.debug('task_dispatch: executing %s' % task.params)
    except Exception, e:
        task.failed()
        logger.debug('-----------------------------------------------Invalid body in post: %s' % str(e))
        return HttpResponseServerError('invalid data');

    try:
        logger.debug('----------type: %s' % type(post_data))
        logger.debug('----------post_data: %s' % post_data['result'])
    except Exception, ex:
        logger.debug('----------error: %s' % ex)

        
    if 'result' in post_data:
        result = post_data['result']
    elif 'error' in post_data:
        logger.error('%s returned and error: %s:' % task.decoded_params[0], post_data['error'])
        task.failed()
        result = {} 
    else:
        logger.error('Invalid jsonrpc response')
    task.execute(result)
    return HttpResponse('ok')
