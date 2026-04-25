from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape


class XmlTemplateRenderer:
    def __init__(self, template_directory: Path) -> None:
        self.environment = Environment(
            loader=FileSystemLoader(str(template_directory)),
            autoescape=select_autoescape(
                enabled_extensions=("xml",),
                default_for_string=False,
                default=False,
            ),
            keep_trailing_newline=True,
            lstrip_blocks=True,
            trim_blocks=True,
            undefined=StrictUndefined,
        )

    def render(self, template_name: str, context: object) -> str:
        template = self.environment.get_template(template_name)
        return template.render(context=context)
