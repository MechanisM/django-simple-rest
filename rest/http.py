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


class RESTFulResponse(DjangoHttpResponse):

    def __init__(self, content='', mimetype=None, status=None, content_type=None, request=None):
        if request and mimetype is None and content_type is None:
            # Try to get the mimetype from the URL override if one was provided
            mimetype = mimetypes.guess_type(request.path_info)[0]
            if mimetype in SUPPORTED_MIMETYPES.keys():
                content_type = mimetype
            else:
                # Otherwise, get the mimetype from the HTTP Accepts header
                accepts = request.META.get('HTTP_ACCEPT', 'application/json')
                mimetype = mimeparse.best_match(SUPPORTED_MIMETYPES.keys(), accepts)
                if mimetype in SUPPORTED_MIMETYPES.keys():
                    content_type = mimetype

            if content_type:
                serializer_name = SUPPORTED_MIMETYPES.get(content_type)
                serializer = serializer_name and getattr(self, serializer_name, None)
                content = serializer(content)

        super(RESTFulResponse, self).__init__(content=content, status=status, content_type=content_type)


    def to_json(self, content):
        if isinstance(content, QuerySet):
            json_serializer = serializers.get_serializer('json')()
            serialized_content = json_serializer.serialize(content, ensure_ascii=False)
        else:
            json_encoder = serializers.json.DjangoJSONEncoder
            serialized_content = json.dumps(content, cls=json_encoder, ensure_ascii=False)
        return serialized_content

    # def __getattribute__(self, name):
    #     if name == '_container':
    #         _container = self.__dict__.get('_container', [''])
    #         serializer_name = SUPPORTED_MIMETYPES.get(self['Content-Type'])
    #         serializer = serializer_name and getattr(self, serializer_name, None)
    #         return serializer(_container) #[serializer(val) for val in _container]
    #     else:
    #         return object.__getattribute__(self, name)
