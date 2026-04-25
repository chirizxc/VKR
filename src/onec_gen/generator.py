import logging
import shutil
from collections.abc import Callable
from pathlib import Path

from onec_gen.models import (
    AccumulationRegisterSpec,
    CatalogSpec,
    ConfigSpec,
    DocumentSpec,
    SubsystemSpec,
)
from onec_gen.naming import default_generated_dir_name
from onec_gen.renderer import XmlTemplateRenderer
from onec_gen.template_context import TemplateContextBuilder

logger = logging.getLogger(__name__)
DEFAULT_GENERATED_DIR = "output"
TEMPLATES_ROOT = Path(__file__).resolve().parent / "templates"
TEMPLATE_CONFIG_DUMP = TEMPLATES_ROOT / "base"
TEMPLATE_RENDER_DIR = TEMPLATES_ROOT / "jinja"


def default_generated_path(project_root: Path, config: ConfigSpec) -> Path:
    return project_root / DEFAULT_GENERATED_DIR / default_generated_dir_name(config)


def generate_config(
    config: ConfigSpec,
    output_path: Path,
    *,
    onec_binary: Path | None,
) -> Path:
    generator = ConfigDumpGenerator(
        base_template_directory=TEMPLATE_CONFIG_DUMP,
        renderer=XmlTemplateRenderer(TEMPLATE_RENDER_DIR),
        context_builder=TemplateContextBuilder(),
    )
    return generator.generate(
        config=config,
        output_path=output_path,
        onec_binary=onec_binary,
    )


class ConfigDumpGenerator:
    def __init__(
        self,
        *,
        base_template_directory: Path,
        renderer: XmlTemplateRenderer,
        context_builder: TemplateContextBuilder,
    ) -> None:
        self.base_template_directory = base_template_directory
        self.renderer = renderer
        self.context_builder = context_builder

    def generate(
        self,
        *,
        config: ConfigSpec,
        output_path: Path,
        onec_binary: Path | None,
    ) -> Path:
        resolved_output_path = output_path.expanduser().resolve()
        logger.info(
            "Генерирую каталог выгрузки конфигурации 1С: %s",
            resolved_output_path,
        )
        self._create_empty_dump(
            output_path=resolved_output_path,
            onec_binary=onec_binary,
        )
        self._write_configuration(config=config, output_path=resolved_output_path)
        self._write_catalogs(config=config, output_path=resolved_output_path)
        self._write_documents(config=config, output_path=resolved_output_path)
        self._write_accumulation_registers(
            config=config,
            output_path=resolved_output_path,
        )
        self._write_roles(config=config, output_path=resolved_output_path)
        self._write_subsystems(config=config, output_path=resolved_output_path)
        return resolved_output_path

    def _create_empty_dump(
        self,
        *,
        output_path: Path,
        onec_binary: Path | None,
    ) -> None:
        if output_path.exists():
            shutil.rmtree(output_path)
        if onec_binary is None:
            logger.info(
                "1С не указана, использую встроенный шаблон пустой файловой выгрузки.",
            )
        else:
            logger.info(
                "Для стартовой файловой выгрузки использую встроенный шаблон вместо "
                "выгрузки пустой конфигурации через 1С.",
            )
        shutil.copytree(self.base_template_directory, output_path)

    def _write_configuration(self, *, config: ConfigSpec, output_path: Path) -> None:
        config_path = output_path / "Configuration.xml"
        config_path.write_text(
            self.renderer.render(
                "configuration.xml.j2",
                self.context_builder.build_configuration_context(config),
            ),
            encoding="utf-8",
        )

    def _write_catalogs(self, *, config: ConfigSpec, output_path: Path) -> None:
        self._write_object_files(
            output_path=output_path,
            dir_name="Catalogs",
            items=config.catalogs,
            file_name_getter=lambda catalog: catalog.name,
            content_getter=self._render_catalog,
        )

    def _write_documents(self, *, config: ConfigSpec, output_path: Path) -> None:
        self._write_object_files(
            output_path=output_path,
            dir_name="Documents",
            items=config.documents,
            file_name_getter=lambda document: document.name,
            content_getter=self._render_document,
        )

    def _write_subsystems(self, *, config: ConfigSpec, output_path: Path) -> None:
        self._write_object_files(
            output_path=output_path,
            dir_name="Subsystems",
            items=config.subsystems,
            file_name_getter=lambda subsystem: subsystem.name,
            content_getter=lambda subsystem: self._render_subsystem(
                subsystem=subsystem,
                config=config,
            ),
        )

    def _write_accumulation_registers(
        self,
        *,
        config: ConfigSpec,
        output_path: Path,
    ) -> None:
        self._write_object_files(
            output_path=output_path,
            dir_name="AccumulationRegisters",
            items=config.accumulation_registers,
            file_name_getter=lambda register: register.name,
            content_getter=self._render_accumulation_register,
        )

    def _write_roles(self, *, config: ConfigSpec, output_path: Path) -> None:
        roles_path = output_path / "Roles"
        roles_path.mkdir(parents=True, exist_ok=True)
        for role in config.roles:
            role_context = self.context_builder.build_role_context(role, config)
            role_path = roles_path / f"{role.name}.xml"
            role_path.write_text(self._render_role(role_context), encoding="utf-8")
            rights_path = roles_path / role.name / "Ext"
            rights_path.mkdir(parents=True, exist_ok=True)
            (rights_path / "Rights.xml").write_text(
                self._render_role_rights(role_context),
                encoding="utf-8",
            )

    def _write_object_files[T](
        self,
        *,
        output_path: Path,
        dir_name: str,
        items: tuple[T, ...],
        file_name_getter: Callable[[T], str],
        content_getter: Callable[[T], str],
    ) -> None:
        objects_path = output_path / dir_name
        objects_path.mkdir(parents=True, exist_ok=True)
        for item in items:
            item_path = objects_path / f"{file_name_getter(item)}.xml"
            item_path.write_text(content_getter(item), encoding="utf-8")

    def _render_catalog(self, catalog: CatalogSpec) -> str:
        return self.renderer.render(
            "catalog.xml.j2",
            self.context_builder.build_catalog_context(catalog),
        )

    def _render_document(self, document: DocumentSpec) -> str:
        return self.renderer.render(
            "document.xml.j2",
            self.context_builder.build_document_context(document),
        )

    def _render_subsystem(
        self,
        *,
        subsystem: SubsystemSpec,
        config: ConfigSpec,
    ) -> str:
        return self.renderer.render(
            "subsystem.xml.j2",
            self.context_builder.build_subsystem_context(subsystem, config),
        )

    def _render_accumulation_register(
        self,
        accumulation_register: AccumulationRegisterSpec,
    ) -> str:
        return self.renderer.render(
            "accumulation_register.xml.j2",
            self.context_builder.build_accumulation_register_context(
                accumulation_register,
            ),
        )

    def _render_role(self, role_context: object) -> str:
        return self.renderer.render(
            "role.xml.j2",
            role_context,
        )

    def _render_role_rights(self, role_context: object) -> str:
        return self.renderer.render(
            "role_rights.xml.j2",
            role_context,
        )
