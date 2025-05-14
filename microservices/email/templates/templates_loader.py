import os
from jinja2 import Environment, FileSystemLoader, select_autoescape

env = Environment(
	loader=FileSystemLoader(os.path.dirname(__file__)),
	autoescape=select_autoescape(['html', 'xml'])
)


def render_template(template_name: str, context: dict) -> str:
    template = env.get_template(template_name)
    return template.render(context)