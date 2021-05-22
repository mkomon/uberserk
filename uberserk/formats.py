# -*- coding: utf-8 -*-

import ujson as json

from . import utils


class FormatHandler:
    """Provide request headers and parse responses for a particular format.

    Instances of this class should override the :meth:`parse_stream` and
    :meth:`parse` methods to support handling both streaming and non-streaming
    responses.

    :param str mime_type: the MIME type for the format
    """

    def __init__(self, mime_type):
        self.mime_type = mime_type
        self.headers = {'Accept': mime_type}

    def handle(self, response, is_stream, converter=utils.noop):
        """Handle the response by returning the data.

        :param response: raw response
        :type response: :class:`requests.Response`
        :param bool is_stream: ``True`` if the response is a stream
        :param func converter: function to handle field conversions
        :return: either all response data or an iterator of response data
        """
        if is_stream:
            return map(converter, iter(self.parse_stream(response)))
        else:
            return converter(self.parse(response))

    def parse(self, response):
        """Parse all data from a response.

        :param response: raw response
        :type response: :class:`requests.Response`
        :return: response data
        """
        return response

    def parse_stream(self, response):
        """Yield the parsed data from a stream response.

        :param response: raw response
        :type response: :class:`requests.Response`
        :return: iterator over the response data
        """
        yield response


class JsonHandler(FormatHandler):
    """Handle JSON data.

    :param str mime_type: the MIME type for the format
    :param decoder: the decoder to use for the JSON format
    """

    def __init__(self, mime_type, decoder=None):
        super().__init__(mime_type=mime_type)

    def parse(self, response):
        """Parse all JSON data from a response.

        :param response: raw response
        :type response: :class:`requests.Response`
        :return: response data
        :rtype: JSON
        """
        return json.loads(response.text)

    def parse_stream(self, response):
        """Yield the parsed data from a stream response.

        :param response: raw response
        :type response: :class:`requests.Response`
        :return: iterator over multiple JSON objects
        """
        for chunk in response:
            for line in chunk.splitlines():
                print('line: {}'.format(line))
                if line:
                    decoded_line = line.decode('utf-8')
                    yield json.loads(decoded_line)
                else:
                    yield {}


class TextHandler(FormatHandler):

    def __init__(self):
        super().__init__(mime_type='text/plain')

    def parse(self, response):
        return response.text

    def parse_stream(self, response):
        for chunk in response:
            for line in chunk.splitlines():
                decoded_line = line.decode('utf-8')
                print('decoded_line: {}'.format(decoded_line))
                yield decoded_line

#: Basic text
TEXT = TextHandler()

#: Handles vanilla JSON
JSON = JsonHandler(mime_type='application/json')
