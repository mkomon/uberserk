

def get_message(e):
    return e.args[0] if e.args else ''


def set_message(e, value):
    args = list(e.args)
    if args:
        args[0] = value
    else:
        args.append(value)
    e.args = args


class BerserkError(Exception):
    message = property(get_message, set_message)


class ApiError(BerserkError):
    def __init__(self, error):
        super().__init__(get_message(error))
        self.__cause__ = self.error = error


class ResponseError(ApiError):
    """Response that indicates an error."""

    # sentinal object for when None is a valid result
    __UNDEFINED = object()

    def __init__(self, response):
        error = ResponseError._catch_exception(response)
        super().__init__(error)
        self._cause = ResponseError.__UNDEFINED
        self.response = response
        base_message = 'HTTP {}: {}'.format(self.status_code, self.reason)
        if self.cause:
            self.message = '{}: {}'.format(base_message, self.cause)

    @property
    def status_code(self):
        """HTTP status code of the response."""
        return self.response.status_code

    @property
    def reason(self):
        """HTTP status text of the response."""
        return self.response.reason

    @property
    def cause(self):
        if self._cause is ResponseError.__UNDEFINED:
            try:
                self._cause = self.response.json()
            except Exception:
                self._cause = None
        return self._cause

    @staticmethod
    def _catch_exception(response):
        try:
            http_error_msg = ''
            if isinstance(response.reason, bytes):
                # We attempt to decode utf-8 first because some servers
                # choose to localize their reason strings. If the string
                # isn't utf-8, we fall back to iso-8859-1 for all other
                # encodings. (See PR #3538)
                try:
                    reason = response.reason.decode('utf-8')
                except UnicodeDecodeError:
                    reason = response.reason.decode('iso-8859-1')
            else:
                reason = response.reason

            if 400 <= response.status_code < 500:
               http_error_msg = u'%s Client Error: %s' % (response.status_code, reason)

            elif 500 <= response.status_code < 600:
                http_error_msg = u'%s Server Error: %s' % (response.status_code, reason)

            if http_error_msg:
                raise Exception(http_error_msg)

        except Exception as e:
            return e