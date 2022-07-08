from typing import Any

from jinja2 import Environment
from jinja2.loaders import PackageLoader


def id_sanitize(value: str) -> str:
    return "".join(filter(str.isalnum, value))


def template(data: dict[str, Any]) -> str:
    template_loader = PackageLoader(__package__, "templates")
    template_env = Environment(loader=template_loader, keep_trailing_newline=True)

    template_env.filters["id_sanitize"] = id_sanitize

    template = template_env.get_template("report.html.jinja2")
    return template.render(report=data)
