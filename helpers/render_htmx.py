from typing import Any

from flask import make_response, render_template, Response
from jinja2 import Template


def render_htmx(template: str | Template | list[str | Template], url: str = None, **context: Any) -> Response:
    response = make_response(render_template(template, **context))
    if url is not None:
        response.headers['HX-Push-Url'] = url

    return response
