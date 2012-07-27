import mimetypes

try:
    import simplejson as json
except ImportError:
    import json

import mimeparse

from django.db.models.query import QuerySet
from django.http import HttpResponse as DjangoHttpResponse
from django.core import serializers
from django.conf import settings


SUPPORTED_MIMETYPES = {
    'text/html': 'to_html',
    'text/plain': 'to_txt',
    'application/json': 'to_json'
}

# If the user has added more mimetypes, update the list
if hasattr(settings, 'SUPPORTED_MIMETYPES'):
    SUPPORTED_MIMETYPES.update(settings.SUPPORTED_MIMETYPES)

def to_json(content):
    if isinstance(content, QuerySet):
        json_serializer = serializers.get_serializer('json')()
        serialized_content = json_serializer.serialize(content, ensure_ascii=False)
    else:
        json_encoder = serializers.json.DjangoJSONEncoder
        serialized_content = json.dumps(content, cls=json_encoder, ensure_ascii=False)
    return serialized_content


class RESTFulResponse(object):
    status_code = 200

    def __init__(self, content=None, status=None):
        self.content = content
        if status:
            self.status_code = status

    def to_json(self):
        if isinstance(self.content, QuerySet):
            json_serializer = serializers.get_serializer('json')()
            serialized_content = json_serializer.serialize(self.content, ensure_ascii=False)
        else:
            json_encoder = serializers.json.DjangoJSONEncoder
            serialized_content = json.dumps(self.content, cls=json_encoder, ensure_ascii=False)
        return serialized_content


class ContentNegotiationMiddleware(object):
    def process_view(self, request, view_func, view_args, view_kwargs):

        import sys
        import inspect
        import rest.views

        module = sys.modules[view_func.__module__]
        klass = getattr(module, view_func.__name__)

        if inspect.isclass(klass) and issubclass(klass, rest.views.View):
            response = view_func(request, *view_args, **view_kwargs)

            # Try to get the mimetype from the URL override if one was provided
            mimetype = mimetypes.guess_type(request.path_info)[0]
            serializer_name = SUPPORTED_MIMETYPES.get(mimetype)
            serializer = serializer_name and getattr(response, serializer_name, None)
            if serializer:
                response.content = to_xml(response._container)
                response['Content-Type'] = mimetype
                return response

            # Otherwise, get the mimetype from the HTTP Accepts header
            accepts = request.META.get('HTTP_ACCEPT', 'application/json')
            mimetype = mimeparse.best_match(SUPPORTED_MIMETYPES.keys(), accepts)
            serializer_name = SUPPORTED_MIMETYPES.get(mimetype)
            serializer = serializer_name and getattr(response, serializer_name, None)
            if serializer:
                response.content = to_xml(response._container)
                response['Content-Type'] = mimetype
                return response

        return None

    # def process_response(self, request, response):
    #     # if the response is a typical Django HttpResponse class,
    #     # let it go through
    #     if not isinstance(response, RESTFulResponse):
    #         return response

    #     # Try to get the mimetype from the URL override if one was provided
    #     import ipdb; ipdb.set_trace()
    #     mimetype = mimetypes.guess_type(request.path_info)[0]
    #     serializer_name = SUPPORTED_MIMETYPES.get(mimetype)
    #     serializer = serializer_name and getattr(response, serializer_name, None)
    #     if serializer:
    #          return DjangoHttpResponse(serializer(), content_type=mimetype, status=response.status_code)

    #     # Otherwise, get the mimetype from the HTTP Accepts header
    #     accepts = request.META.get('HTTP_ACCEPT', 'application/json')
    #     mimetype = mimeparse.best_match(SUPPORTED_MIMETYPES.keys(), accepts)
    #     serializer_name = SUPPORTED_MIMETYPES.get(mimetype)
    #     serializer = serializer_name and getattr(response, serializer_name, None)
    #     if serializer:
    #         return DjangoHttpResponse(serializer(), content_type=mimetype, status=response.status_code)

    #     # TODO: Should we call a default format method here, such as to_json,
    #     #       or should we return an HttpError for bad accepts header, or
    #     #       should we simply return None and let the response return
    #     #       whatever was passed into it?
    #     return DjangoHttpResponse(response.content, content_type='application/json', status=response.status_code)

