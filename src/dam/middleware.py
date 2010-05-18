from django.conf import settings
from django.http import HttpResponseRedirect, get_host

class QueryStringSessionMiddleware:
    def process_request(self, request):
        if request.GET.has_key(settings.SESSION_COOKIE_NAME):
            request.COOKIES[settings.SESSION_COOKIE_NAME] = request.GET[settings.SESSION_COOKIE_NAME]

from django.conf import settings
from django.http import HttpResponseRedirect, get_host
import re

SSL = 'SSL'

class SSLRedirect:
    urls = tuple([re.compile(url) for url in settings.SSL_URLS])
    
    def process_request(self, request):
        secure = False
        for url in self.urls:
            if url.match(request.path):
                secure = True
                break
        if not secure == self._is_secure(request):
            return self._redirect(request, secure)

    def _is_secure(self, request):
        if request.is_secure():
            return True

        #Handle the Webfaction case until this gets resolved in the request.is_secure()
        if 'HTTP_X_FORWARDED_SSL' in request.META:
            return request.META['HTTP_X_FORWARDED_SSL'] == 'on'

        return False

    def _redirect(self, request, secure):
        protocol = secure and "https" or "http"
        if secure:
            host = getattr(settings, 'SSL_HOST', get_host(request))
        else:
            host = getattr(settings, 'HTTP_HOST', get_host(request))
        newurl = "%s://%s%s" % (protocol,host,request.get_full_path())
        if settings.DEBUG and request.method == 'POST':
            raise RuntimeError, \
        """Django can't perform a SSL redirect while maintaining POST data.
           Please structure your views so that redirects only occur during GETs."""

        return HttpResponseRedirect(newurl)
