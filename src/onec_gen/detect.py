import logging
import os
import shutil
from pathlib import Path, PureWindowsPath

from questionary.prompts.common import Choice

from onec_gen.consts import IS_WINDOWS, KBI_MESSAGE
from onec_gen.exceptions import OneCBatchModeNotSupportedError, OneCNotFoundError
from onec_gen.select import select_with_compact_answer

logger = logging.getLogger(__name__)

IBCMD = "ibcmd.exe"
EDUCATIONAL_ONEC = "1cv8t.exe"
BATCH_ONEC = "1cv8.exe"
SUPPORTED_BATCH_ONEC = (EDUCATIONAL_ONEC, BATCH_ONEC)
SUPPORTED_MANUAL_ONEC = (*SUPPORTED_BATCH_ONEC, "1cv8c.exe")

if IS_WINDOWS:
    from prompt_toolkit.output.win32 import NoConsoleScreenBufferError
else:

    class NoConsoleScreenBufferError(Exception):
        pass


class OneCDetector:
    def __init__(self) -> None:
        self.program_files = Path(os.environ.get("PROGRAMFILES", r"C:\Program Files"))
        self.program_files_x86 = Path(
            os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"),
        )
        self.local_app_data = Path(
            os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"),
        )
        self.roaming_app_data = Path(
            os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"),
        )
        self.search_roots = self._build_search_roots()

    def resolve_onec_binary(self, onec_path: str | Path | None) -> Path:
        if onec_path is not None:
            logger.info("Проверяю путь указанный к 1С: %s", onec_path)
            resolved_path = self._normalize_onec_path(Path(onec_path).expanduser())
            if resolved_path is not None:
                self._ensure_batch_mode_supported(resolved_path)
                logger.info("Указанный путь к 1С подтвержден: %s", resolved_path)
                return resolved_path
            raise OneCNotFoundError(onec_path)

        detected_path = self.detect_onec_binary()
        if detected_path is not None:
            logger.info("1С найдена автоматически: %s", detected_path)
            return detected_path

        raise OneCNotFoundError

    def detect_onec_binary(self) -> Path | None:
        candidates = self._collect_onec_candidates()
        if not candidates:
            return None
        if len(candidates) == 1:
            return candidates[0]
        return self._ask_user_to_choose_path(candidates)

    def detect_ibcmd_binary(self, onec_binary: Path | None = None) -> Path | None:
        if onec_binary is not None:
            candidate_path = onec_binary.with_name(IBCMD)
            if candidate_path.is_file():
                logger.debug("Найден ibcmd рядом с бинарем 1С: %s", candidate_path)
                return candidate_path.resolve()

        path_from_system = shutil.which(IBCMD)
        if path_from_system is not None:
            logger.debug("Найден ibcmd в PATH: %s", path_from_system)
            return Path(path_from_system).resolve()

        for pattern in self._ibcmd_glob_patterns():
            for candidate_root in self.search_roots:
                bin_candidates = sorted(candidate_root.glob(pattern), reverse=True)
                if not bin_candidates:
                    continue
                logger.debug("Найден ibcmd в типовом каталоге: %s", bin_candidates[0])
                return bin_candidates[0].resolve()

        return None

    def _build_search_roots(self) -> tuple[Path, ...]:
        configured_roots = self._read_configured_install_roots()
        local_roots = (
            self.program_files / "1cv8",
            self.program_files_x86 / "1cv8",
            self.local_app_data / "Programs" / "1cv8",
            self.local_app_data / "Programs" / "1cv8_x86",
            self.local_app_data / "Programs" / "1cv8_x64",
            *configured_roots,
            self.program_files / "1cv8t",
            self.program_files_x86 / "1cv8t",
        )
        existing_roots: list[Path] = []
        seen_roots: set[Path] = set()
        for root in local_roots:
            resolved_root = root.expanduser().resolve()
            if not resolved_root.exists() or resolved_root in seen_roots:
                continue
            seen_roots.add(resolved_root)
            existing_roots.append(resolved_root)
        return tuple(existing_roots)

    def _collect_onec_candidates(self) -> tuple[Path, ...]:
        logger.debug("Пробую найти batch-пригодную 1С через PATH и каталоги установки")
        unique_candidates: list[Path] = []
        seen_candidates: set[Path] = set()

        for executable_name in SUPPORTED_BATCH_ONEC:
            path_candidate = self._detect_batch_onec_from_system_path(executable_name)
            if path_candidate is not None:
                self._append_unique_candidate(
                    unique_candidates,
                    seen_candidates,
                    path_candidate,
                )

        for candidate_root in self.search_roots:
            logger.debug(
                "Проверяю каталог установки batch-пригодной 1С: %s",
                candidate_root,
            )
            for pattern in self._batch_onec_glob_patterns():
                for candidate in sorted(candidate_root.glob(pattern), reverse=True):
                    self._append_unique_candidate(
                        unique_candidates,
                        seen_candidates,
                        candidate.resolve(),
                    )

        return tuple(unique_candidates)

    def _read_configured_install_roots(self) -> tuple[Path, ...]:
        configured_roots: list[Path] = []
        for config_path in self._onec_start_config_paths():
            installed_location = self._read_installed_location(config_path)
            if installed_location is None:
                continue
            configured_roots.append(installed_location)
        return tuple(configured_roots)

    def _onec_start_config_paths(self) -> tuple[Path, ...]:
        all_users_profile = Path(
            os.environ.get("ALLUSERSPROFILE", r"C:\ProgramData"),
        )
        return (
            self.roaming_app_data / "1C" / "1CEStart" / "1cestart.cfg",
            all_users_profile / "1C" / "1CEStart" / "1cestart.cfg",
        )

    def _read_installed_location(self, config_path: Path) -> Path | None:
        if not config_path.is_file():
            return None

        try:
            config_text = config_path.read_text(encoding="utf-16le")
        except UnicodeError:
            config_text = config_path.read_text(encoding="utf-8", errors="replace")

        for line in config_text.splitlines():
            normalized_line = line.lstrip("\ufeff")
            if not normalized_line.startswith("InstalledLocation="):
                continue
            raw_path = normalized_line.removeprefix("InstalledLocation=").strip()
            if not raw_path:
                return None
            return Path(raw_path).expanduser()

        return None

    def _append_unique_candidate(
        self,
        unique_candidates: list[Path],
        seen_candidates: set[Path],
        candidate: Path,
    ) -> None:
        if candidate in seen_candidates:
            return
        self._ensure_batch_mode_supported(candidate)
        seen_candidates.add(candidate)
        unique_candidates.append(candidate)

    def _detect_batch_onec_from_system_path(self, executable_name: str) -> Path | None:
        path_from_system = shutil.which(executable_name)
        if path_from_system is None:
            return None

        logger.debug(
            "Проверяю batch-пригодный исполняемый файл из PATH: %s",
            executable_name,
        )
        normalized_path = self._normalize_onec_path(Path(path_from_system))
        if normalized_path is None:
            return None
        self._ensure_batch_mode_supported(normalized_path)
        return normalized_path

    def _ask_user_to_choose_path(self, candidates: tuple[Path, ...]) -> Path:
        max_title_length = max(
            len(self._candidate_kind(candidate)) for candidate in candidates
        )

        def answer_formatter(candidate: Path) -> str:
            return self._format_selected_candidate_answer(candidate)

        try:
            choice = select_with_compact_answer(
                "Найдено несколько установленных 1С. Какой путь использовать?",
                choices=[
                    Choice(
                        self._format_candidate_title(
                            candidate,
                            max_title_length=max_title_length,
                        ),
                        value=candidate,
                    )
                    for candidate in candidates
                ],
                answer_formatter=answer_formatter,
            ).ask(kbi_msg=KBI_MESSAGE)
        except NoConsoleScreenBufferError:
            preferred_candidate = self._preferred_candidate(candidates)
            logger.warning(
                "Не удалось открыть диалог выбора пути 1С, "
                "использую приоритетный путь: %s",
                preferred_candidate,
            )
            return preferred_candidate
        if choice is None:
            raise KeyboardInterrupt
        return choice

    def _candidate_kind(self, candidate: Path) -> str:
        if self._candidate_name(candidate) == EDUCATIONAL_ONEC:
            return "Учебная версия"
        return "Платформа"

    def _preferred_candidate(self, candidates: tuple[Path, ...]) -> Path:
        for candidate in candidates:
            if self._candidate_name(candidate) == EDUCATIONAL_ONEC:
                return candidate
        return candidates[0]

    def _candidate_name(self, candidate: Path) -> str:
        candidate_name = candidate.name
        if "\\" in candidate_name:
            candidate_name = PureWindowsPath(candidate_name).name
        return candidate_name.lower()

    def _format_candidate_title(
        self,
        candidate: Path,
        *,
        max_title_length: int,
    ) -> str:
        platform_kind = self._candidate_kind(candidate).ljust(max_title_length)
        return f"{platform_kind} | {candidate}"

    def _format_selected_candidate_answer(self, candidate: Path) -> str:
        return f"{self._candidate_kind(candidate)} | {candidate}"

    def _batch_onec_glob_patterns(self) -> tuple[str, ...]:
        return (
            f"*/bin/{EDUCATIONAL_ONEC}",
            f"*/bin/{BATCH_ONEC}",
            f"common/{EDUCATIONAL_ONEC}",
            f"common/{BATCH_ONEC}",
        )

    def _ibcmd_glob_patterns(self) -> tuple[str, ...]:
        return (f"*/bin/{IBCMD}",)

    def _normalize_onec_path(self, candidate_path: Path) -> Path | None:
        logger.debug("Нормализую кандидат пути к 1С: %s", candidate_path)
        if candidate_path.is_dir():
            for executable_name in SUPPORTED_MANUAL_ONEC:
                nested_candidate = candidate_path / executable_name
                if nested_candidate.is_file():
                    return nested_candidate.resolve()

        if candidate_path.is_file():
            return candidate_path.resolve()

        return None

    def _ensure_batch_mode_supported(self, candidate_path: Path) -> None:
        if candidate_path.name.lower() not in SUPPORTED_BATCH_ONEC:
            raise OneCBatchModeNotSupportedError(candidate_path)


def resolve_onec_binary(onec_path: str | Path | None) -> Path:
    detector = OneCDetector()
    return detector.resolve_onec_binary(onec_path)


def detect_ibcmd_binary(onec_binary: Path | None = None) -> Path | None:
    detector = OneCDetector()
    return detector.detect_ibcmd_binary(onec_binary)
