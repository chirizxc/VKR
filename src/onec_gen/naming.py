from onec_gen.consts import RE_PATTERN
from onec_gen.models import ConfigSpec


def default_template_stem(config: ConfigSpec) -> str:
    base_name = (
        config.project.name.strip() or
        config.project.namespace.strip()
    )  # fmt: off
    normalized_name = _compact_name(base_name)
    if normalized_name.startswith("Шаблон"):
        return normalized_name
    return f"Шаблон{normalized_name}"


def default_cf_file_name(config: ConfigSpec) -> str:
    return f"{default_template_stem(config)}.cf"


def default_generated_dir_name(config: ConfigSpec) -> str:
    return default_template_stem(config)


def _compact_name(value: str) -> str:
    pattern = RE_PATTERN
    parts = pattern.findall(value)
    if not parts:
        return "Конфигурации"
    return "".join(_capitalize_part(part) for part in parts)


def _capitalize_part(value: str) -> str:
    if not value:
        return value
    return value[:1].upper() + value[1:]
