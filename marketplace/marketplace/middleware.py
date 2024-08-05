from django.utils.deprecation import MiddlewareMixin


class CacheControlMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if request.path.startswith('/media/'):
            response['Cache-Control'] = 'public, max-age=2628000'
        return response
