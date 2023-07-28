from typing import Union, Optional
import websockets.exceptions
import urllib.error
import aiohttp
import uuid


class DeepgramError:
    pass


class DeepgramSetupError(DeepgramError, ValueError):
    pass


class DeepgramApiError(DeepgramError):
    """An error returned by the Deepgram API.

    If the error was raised by an http client, the client's error message
    is accessible via the `http_library_error` field. This may be useful
    for handling different error codes, such as 429s or 503s.

    The `error` field is set to the API's error message (dict), if avilable.
    Otherwise the `error` field is set to the parent exception's message (str).
    
    The `warning` field is set to the API's warning messages (list[str]), if available.

    The `request_id` field is set to the API's request ID, if available.
    """
    def __init__(
        self,
        *args: object,
        http_library_error: Optional[
            Union[
                urllib.error.HTTPError,
                urllib.error.URLError,
                websockets.exceptions.InvalidHandshake,
                aiohttp.ClientResponseError,
                aiohttp.ClientError,
            ]
        ] = None,
    ):
        super().__init__(*args)
        self.http_library_error = http_library_error
        self.error: Union[str, dict]  # If you change the type, change it in the docstring as well!
        self.warnings: Optional[list[str]] = None  # If you change the type, change it in the docstring as well!
        self.request_id: Optional[uuid.UUID] = None
        self.http_error_status: Optional[int] = None

        # Set the `error`, `warning`, and `request_id` fields
        if isinstance(args[0], dict) and "err_msg" in args[0]:
            self.error = args[0]["err_msg"]
            if "metadata" in args[0] and "warnings" in args[0]["metadata"]:
                self.warnings = args[0]["metadata"]["warnings"]
            elif "warnings" in args[0]:  # Occurs when `raise_warnings_as_errors` is enabled
                self.warnings = args[0]["warnings"]
            if "metadata" in args[0] and "request_id" in args[0]["metadata"]:
                self.request_id = uuid.UUID(args[0]["request_id"])
        elif isinstance(args[0], str):
            self.error = args[0]
        else:
            self.error = str(args[0])

        # Set the error code from the underlying exception, if possible
        if http_library_error is not None:
            # Note: The following Exceptions do not have HTTP error codes:
            #   - urllib.error.URLError
            #   - websockets.exceptions.InvalidHandshake
            #   - aiohttp.ClientError
            if isinstance(http_library_error, urllib.error.HTTPError):
                self.http_error_status = http_library_error.code
            elif isinstance(http_library_error, aiohttp.ClientResponseError):
                self.http_error_status = http_library_error.status

    def __str__(self) -> str:
        if self.request_id:
            if self.warnings:
                warning_string = f"\n\n{self.warnings}"
            else:
                warning_string = ""
            if self.http_error_status:
                return f"Request `{self.request_id}` returned {self.http_error_status}: {self.error}" + warning_string
            else:
                return f"Request `{self.request_id}` returned {self.error}" + warning_string
        return super().__str__()
