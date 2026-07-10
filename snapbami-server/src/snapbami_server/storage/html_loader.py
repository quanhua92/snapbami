import pathlib

from jinja2 import Environment, FileSystemLoader, select_autoescape

_TEMPLATE_DIR = pathlib.Path(__file__).resolve().parent.parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=select_autoescape(["html"]),
)


def generate_html_loader(public_id: str, title: str = "Dashboard") -> str:
    return _env.get_template("dashboard_loader.html").render(
        public_id=public_id,
        title=title,
    )
