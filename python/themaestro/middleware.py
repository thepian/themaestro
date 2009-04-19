import sys

from django.conf import settings
from django import http
from django.core.mail import mail_admins

class StandardExceptionMiddleware(object):
    """
    based on http://www.djangosnippets.org/snippets/638/
    """
    def process_exception(self, request, exception):
        # Get the exception info now, in case another exception is thrown later.
        if isinstance(exception, http.Http404):
            return self.handle_404(request, exception)
        else:
            return self.handle_500(request, exception)


    def handle_404(self, request, exception):
        if settings.DEBUG:
            import debug
            return debug.technical_404_response(request, exception)
        else:
            callback, param_dict = resolver(request).resolve404()
            return callback(request, **param_dict)


    def handle_500(self, request, exception):
        from django.core.cache import cache
        
        exc_info = sys.exc_info()
        if settings.DEBUG:
            k = '500:'+ request.affinity.encoded
            r = self.debug_500_response(request, exception, exc_info)
            cache.set(k,r,2000)
            return r
        else:
            self.log_exception(request, exception, exc_info)
            return self.production_500_response(request, exception, exc_info)


    def debug_500_response(self, request, exception, exc_info):
        from django.views import debug
        return debug.technical_500_response(request, *exc_info)


    def production_500_response(self, request, exception, exc_info):
        '''Return an HttpResponse that displays a friendly error message.'''
        callback, param_dict = resolver(request).resolve500()
        return callback(request, **param_dict)


    def exception_email(self, request, exc_info):
        subject = 'Error (%s IP): %s' % ((request.META.get('REMOTE_ADDR') in settings.INTERNAL_IPS and 'internal' or 'EXTERNAL'), request.path)
        try:
            request_repr = repr(request)
        except:
            request_repr = "Request repr() unavailable"
        message = "%s\n\n%s" % (_get_traceback(exc_info), request_repr)
        return subject, message


    def log_exception(self, request, exception, exc_info):
        subject, message = self.exception_email(request, exc_info)
        mail_admins(subject, message, fail_silently=True)



def _get_traceback(self, exc_info=None):
    """Helper function to return the traceback as a string"""
    import traceback
    return '\n'.join(traceback.format_exception(*(exc_info or sys.exc_info())))