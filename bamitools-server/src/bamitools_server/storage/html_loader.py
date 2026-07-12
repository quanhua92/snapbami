import pathlib

from jinja2 import Environment, FileSystemLoader, select_autoescape

_TEMPLATE_DIR = pathlib.Path(__file__).resolve().parent.parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=select_autoescape(["html"]),
)


def generate_page_loader(public_id: str, title: str = "BamiTools") -> str:
    return _env.get_template("page_loader.html").render(
        public_id=public_id,
        title=title,
    )
