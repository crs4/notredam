import os
from json import loads
from dam.mprocessor.models import Job
from django.http import Http404, HttpResponse, HttpResponseServerError
from settings import INSTALLATIONPATH
import logging
logger = logging.getLogger('batch_processor')
logger.addHandler(logging.FileHandler(os.path.join(INSTALLATIONPATH,  'log/mprocessor.log')))
logger.setLevel(logging.DEBUG)

#
# This is the view that receives responses and pushes on the chain of calls
#
def job_dispatch(request, job_id):
    """General dispatcher for incoming responses"""
    try:
        logger.debug("-------------------request.raw_post_data: %s" %request.raw_post_data)
        post_data = loads(request.raw_post_data)
        job = Job.objects.get(job_id=job_id)
    except Exception, e:
        logger.debug('-----------------------------------------------Invalid body in post: %s' % str(e))
        return HttpResponseServerError('invalid data');
    if 'result' in post_data:
        result = post_data['result']
    elif 'error' in post_data:
        logger.error('%s returned and error: %s:' % job.decoded_params[0], post_data['error'])
        result = {} 
    else:
        logger.error('Invalid jsonrpc response')
    if job.next():
        job.execute(result)
        logger.debug("-----job.next")
    return HttpResponse('ok')
