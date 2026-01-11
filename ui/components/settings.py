"""Settings management for BabelDOC WebUI."""

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Literal


@dataclass
class OpenAISettings:
    """OpenAI API configuration."""

    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"
    term_extraction_model: str = ""
    term_extraction_base_url: str = ""
    term_extraction_api_key: str = ""
    reasoning: str = ""
    term_extraction_reasoning: str = ""
    enable_json_mode: bool = False
    send_dashscope_header: bool = False
    no_send_temperature: bool = False


@dataclass
class TranslationSettings:
    """Translation configuration."""

    lang_in: str = "en"
    lang_out: str = "zh"
    qps: int = 4
    min_text_length: int = 5
    pool_max_workers: int | None = None
    term_pool_max_workers: int | None = None
    custom_system_prompt: str = ""
    auto_extract_glossary: bool = True
    disable_same_text_fallback: bool = False
    add_formula_placehold_hint: bool = False


@dataclass
class PDFSettings:
    """PDF processing configuration."""

    output_dual: bool = True
    output_mono: bool = True
    watermark_mode: Literal["watermarked", "no_watermark", "both"] = "watermarked"
    skip_clean: bool = False
    dual_translate_first: bool = False
    disable_rich_text_translate: bool = False
    enhance_compatibility: bool = False
    use_alternating_pages_dual: bool = False
    max_pages_per_part: int | None = None
    skip_scanned_detection: bool = False
    ocr_workaround: bool = False
    auto_enable_ocr_workaround: bool = False
    split_short_lines: bool = False
    short_line_split_factor: float = 0.8
    primary_font_family: Literal["serif", "sans-serif", "script"] | None = None
    formular_font_pattern: str = ""
    formular_char_pattern: str = ""
    skip_form_render: bool = False
    skip_curve_render: bool = False
    only_parse_generate_pdf: bool = False
    remove_non_formula_lines: bool = False
    non_formula_line_iou_threshold: float = 0.9
    figure_table_protection_threshold: float = 0.9


@dataclass
class RPCSettings:
    """RPC service configuration."""

    doclayout_host: str = ""


@dataclass
class PathSettings:
    """Path configuration."""

    output_dir: str = ""
    working_dir: str = ""
    glossary_files: str = ""


@dataclass
class Settings:
    """Complete settings configuration."""

    openai: OpenAISettings = field(default_factory=OpenAISettings)
    translation: TranslationSettings = field(default_factory=TranslationSettings)
    pdf: PDFSettings = field(default_factory=PDFSettings)
    rpc: RPCSettings = field(default_factory=RPCSettings)
    paths: PathSettings = field(default_factory=PathSettings)

    def to_dict(self) -> dict:
        """Convert settings to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Settings":
        """Create settings from dictionary."""
        return cls(
            openai=OpenAISettings(**data.get("openai", {})),
            translation=TranslationSettings(**data.get("translation", {})),
            pdf=PDFSettings(**data.get("pdf", {})),
            rpc=RPCSettings(**data.get("rpc", {})),
            paths=PathSettings(**data.get("paths", {})),
        )


class SettingsManager:
    """Manages settings persistence."""

    def __init__(self, config_path: Path | None = None):
        if config_path is None:
            config_path = Path.home() / ".config" / "babeldoc-webui" / "settings.json"
        self.config_path = config_path
        self._settings: Settings | None = None

    @property
    def settings(self) -> Settings:
        """Get current settings, loading from file if needed."""
        if self._settings is None:
            self._settings = self.load()
        return self._settings

    def load(self) -> Settings:
        """Load settings from file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return Settings.from_dict(data)
            except (json.JSONDecodeError, KeyError, TypeError):
                pass
        return Settings()

    def save(self, settings: Settings | None = None) -> None:
        """Save settings to file."""
        if settings is not None:
            self._settings = settings
        if self._settings is None:
            return

        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self._settings.to_dict(), f, indent=2, ensure_ascii=False)

    def update_openai(self, **kwargs) -> None:
        """Update OpenAI settings."""
        for key, value in kwargs.items():
            if hasattr(self.settings.openai, key):
                setattr(self.settings.openai, key, value)
        self.save()

    def update_translation(self, **kwargs) -> None:
        """Update translation settings."""
        for key, value in kwargs.items():
            if hasattr(self.settings.translation, key):
                setattr(self.settings.translation, key, value)
        self.save()

    def update_pdf(self, **kwargs) -> None:
        """Update PDF settings."""
        for key, value in kwargs.items():
            if hasattr(self.settings.pdf, key):
                setattr(self.settings.pdf, key, value)
        self.save()

    def update_rpc(self, **kwargs) -> None:
        """Update RPC settings."""
        for key, value in kwargs.items():
            if hasattr(self.settings.rpc, key):
                setattr(self.settings.rpc, key, value)
        self.save()

    def update_paths(self, **kwargs) -> None:
        """Update path settings."""
        for key, value in kwargs.items():
            if hasattr(self.settings.paths, key):
                setattr(self.settings.paths, key, value)
        self.save()


# Global settings manager instance
settings_manager = SettingsManager()
