from flask import request


def htmx() -> bool:
    """Return a boolean indicating whether the request arrived from HTMX"""
    return request.headers.get('HX-Request') is not None
