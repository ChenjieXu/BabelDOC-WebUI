"""Settings management for BabelDOC WebUI."""

import json
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Literal


# ============ 内置服务商预设 ============

BUILTIN_PROVIDERS: list[dict] = [
    {
        "id": "openai",
        "name": "OpenAI",
        "default_base_url": "https://api.openai.com/v1",
        "icon": "auto_awesome",
        "suggested_models": ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
    },
    {
        "id": "deepseek",
        "name": "DeepSeek",
        "default_base_url": "https://api.deepseek.com",
        "icon": "explore",
        "suggested_models": ["deepseek-chat", "deepseek-reasoner"],
    },
    {
        "id": "zhipu",
        "name": "智谱 GLM",
        "default_base_url": "https://open.bigmodel.cn/api/paas/v4",
        "icon": "psychology",
        "suggested_models": ["glm-4-flash", "glm-4-flash-250414", "glm-4", "glm-4-plus"],
    },
    {
        "id": "ollama",
        "name": "Ollama (本地)",
        "default_base_url": "http://localhost:11434/v1",
        "icon": "computer",
        "suggested_models": ["llama3.1", "qwen2.5", "deepseek-r1"],
    },
    {
        "id": "claude",
        "name": "Claude (Anthropic)",
        "default_base_url": "https://api.anthropic.com/v1",
        "icon": "chat",
        "suggested_models": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229"],
    },
]


def get_builtin_provider_by_id(provider_id: str) -> dict | None:
    """获取内置服务商预设"""
    for p in BUILTIN_PROVIDERS:
        if p["id"] == provider_id:
            return p
    return None


# ============ 模型配置数据类 ============


@dataclass
class ModelConfig:
    """单个模型配置"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    display_name: str = ""
    model_name: str = ""
    api_key: str = ""
    base_url: str | None = None  # None 表示使用服务商默认
    enable_json_mode: bool = False
    send_dashscope_header: bool = False
    no_send_temperature: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ModelConfig":
        return cls(**data)


@dataclass
class Provider:
    """服务商"""

    id: str = ""
    name: str = ""
    default_base_url: str = ""
    is_builtin: bool = True
    icon: str = "smart_toy"
    models: list[ModelConfig] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "default_base_url": self.default_base_url,
            "is_builtin": self.is_builtin,
            "icon": self.icon,
            "models": [m.to_dict() for m in self.models],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Provider":
        models_data = data.get("models", [])
        models = [ModelConfig.from_dict(m) for m in models_data]
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            default_base_url=data.get("default_base_url", ""),
            is_builtin=data.get("is_builtin", True),
            icon=data.get("icon", "smart_toy"),
            models=models,
        )


@dataclass
class ProviderSettings:
    """服务商设置"""

    providers: list[Provider] = field(default_factory=list)
    selected_model_id: str = ""

    def to_dict(self) -> dict:
        return {
            "providers": [p.to_dict() for p in self.providers],
            "selected_model_id": self.selected_model_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProviderSettings":
        providers_data = data.get("providers", [])
        providers = [Provider.from_dict(p) for p in providers_data]
        return cls(
            providers=providers,
            selected_model_id=data.get("selected_model_id", ""),
        )


@dataclass
class TermExtractionSettings:
    """术语提取设置"""

    use_separate_config: bool = False
    model_config_id: str = ""  # 使用已配置的模型 ID
    custom_api_key: str = ""
    custom_base_url: str = ""
    custom_model: str = ""
    reasoning: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "TermExtractionSettings":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ============ 旧版 OpenAI 设置（保留用于迁移） ============


@dataclass
class OpenAISettings:
    """OpenAI API configuration. (保留用于旧配置迁移)"""

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
    ignore_cache: bool = False
    save_auto_extracted_glossary: bool = False


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
    translate_table_text: bool = False
    only_include_translated_page: bool = False
    merge_alternating_line_numbers: bool = False


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

    providers: ProviderSettings = field(default_factory=ProviderSettings)
    term_extraction: TermExtractionSettings = field(default_factory=TermExtractionSettings)
    translation: TranslationSettings = field(default_factory=TranslationSettings)
    pdf: PDFSettings = field(default_factory=PDFSettings)
    rpc: RPCSettings = field(default_factory=RPCSettings)
    paths: PathSettings = field(default_factory=PathSettings)

    def to_dict(self) -> dict:
        """Convert settings to dictionary."""
        return {
            "providers": self.providers.to_dict(),
            "term_extraction": self.term_extraction.to_dict(),
            "translation": asdict(self.translation),
            "pdf": asdict(self.pdf),
            "rpc": asdict(self.rpc),
            "paths": asdict(self.paths),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Settings":
        """Create settings from dictionary."""
        return cls(
            providers=ProviderSettings.from_dict(data.get("providers", {})),
            term_extraction=TermExtractionSettings.from_dict(data.get("term_extraction", {})),
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
        """Load settings from file with migration support."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # 检查是否需要从旧版本迁移
                if "openai" in data and "providers" not in data:
                    data = self._migrate_from_v1(data)
                    # 保存迁移后的配置
                    self._settings = Settings.from_dict(data)
                    self.save()
                    return self._settings

                return Settings.from_dict(data)
            except (json.JSONDecodeError, KeyError, TypeError):
                pass
        return self._create_default_settings()

    def _migrate_from_v1(self, old_data: dict) -> dict:
        """从旧版本迁移配置"""
        old_openai = old_data.get("openai", {})

        # 找到匹配的内置服务商
        old_base_url = old_openai.get("base_url", "https://api.openai.com/v1")
        matched_provider_id = "openai"  # 默认

        for preset in BUILTIN_PROVIDERS:
            if preset["default_base_url"] == old_base_url:
                matched_provider_id = preset["id"]
                break

        preset = get_builtin_provider_by_id(matched_provider_id)

        # 创建服务商和模型配置
        migrated_model_id = str(uuid.uuid4())
        migrated_model = {
            "id": migrated_model_id,
            "display_name": old_openai.get("model", "gpt-4o-mini"),
            "model_name": old_openai.get("model", "gpt-4o-mini"),
            "api_key": old_openai.get("api_key", ""),
            "base_url": None if old_base_url == preset["default_base_url"] else old_base_url,
            "enable_json_mode": old_openai.get("enable_json_mode", False),
            "send_dashscope_header": old_openai.get("send_dashscope_header", False),
            "no_send_temperature": old_openai.get("no_send_temperature", False),
        }

        provider = {
            "id": preset["id"],
            "name": preset["name"],
            "default_base_url": preset["default_base_url"],
            "is_builtin": True,
            "icon": preset.get("icon", "smart_toy"),
            "models": [migrated_model] if old_openai.get("api_key") else [],
        }

        # 术语提取设置
        term_extraction = {
            "use_separate_config": bool(
                old_openai.get("term_extraction_model")
                or old_openai.get("term_extraction_base_url")
                or old_openai.get("term_extraction_api_key")
            ),
            "model_config_id": "",
            "custom_api_key": old_openai.get("term_extraction_api_key", ""),
            "custom_base_url": old_openai.get("term_extraction_base_url", ""),
            "custom_model": old_openai.get("term_extraction_model", ""),
            "reasoning": old_openai.get("term_extraction_reasoning", ""),
        }

        # 构建新数据结构
        new_data = {
            "providers": {
                "providers": [provider],
                "selected_model_id": migrated_model_id if old_openai.get("api_key") else "",
            },
            "term_extraction": term_extraction,
            "translation": old_data.get("translation", {}),
            "pdf": old_data.get("pdf", {}),
            "rpc": old_data.get("rpc", {}),
            "paths": old_data.get("paths", {}),
        }

        return new_data

    def _create_default_settings(self) -> Settings:
        """创建包含所有内置服务商的默认设置"""
        providers = []
        for preset in BUILTIN_PROVIDERS:
            providers.append(
                Provider(
                    id=preset["id"],
                    name=preset["name"],
                    default_base_url=preset["default_base_url"],
                    is_builtin=True,
                    icon=preset.get("icon", "smart_toy"),
                    models=[],
                )
            )
        return Settings(providers=ProviderSettings(providers=providers, selected_model_id=""))

    def save(self, settings: Settings | None = None) -> None:
        """Save settings to file."""
        if settings is not None:
            self._settings = settings
        if self._settings is None:
            return

        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self._settings.to_dict(), f, indent=2, ensure_ascii=False)

    # ============ 辅助方法 ============

    def get_selected_model_config(self) -> ModelConfig | None:
        """获取当前选中的模型配置"""
        model_id = self.settings.providers.selected_model_id
        if not model_id:
            return None
        for provider in self.settings.providers.providers:
            for model in provider.models:
                if model.id == model_id:
                    return model
        return None

    def get_provider_for_model(self, model_id: str) -> Provider | None:
        """获取模型所属的服务商"""
        for provider in self.settings.providers.providers:
            for model in provider.models:
                if model.id == model_id:
                    return provider
        return None

    def get_model_config_by_id(self, model_id: str) -> ModelConfig | None:
        """根据 ID 获取模型配置"""
        for provider in self.settings.providers.providers:
            for model in provider.models:
                if model.id == model_id:
                    return model
        return None

    def get_effective_base_url(self, model_config: ModelConfig) -> str:
        """获取模型的有效 Base URL"""
        if model_config.base_url:
            return model_config.base_url
        provider = self.get_provider_for_model(model_config.id)
        if provider:
            return provider.default_base_url
        return "https://api.openai.com/v1"

    def get_all_model_options(self) -> list[dict]:
        """获取所有可选的模型配置，供首页选择框使用"""
        options = []
        for provider in self.settings.providers.providers:
            for model in provider.models:
                options.append(
                    {
                        "id": model.id,
                        "label": f"{provider.name} / {model.display_name}",
                        "provider_name": provider.name,
                        "model_name": model.model_name,
                        "icon": provider.icon,
                    }
                )
        return options

    def get_provider_by_id(self, provider_id: str) -> Provider | None:
        """根据 ID 获取服务商"""
        for provider in self.settings.providers.providers:
            if provider.id == provider_id:
                return provider
        return None

    def add_provider(self, provider: Provider) -> None:
        """添加服务商"""
        self.settings.providers.providers.append(provider)
        self.save()

    def remove_provider(self, provider_id: str) -> bool:
        """删除服务商"""
        providers = self.settings.providers.providers
        for i, p in enumerate(providers):
            if p.id == provider_id:
                # 检查是否有选中的模型属于这个服务商
                selected_id = self.settings.providers.selected_model_id
                for model in p.models:
                    if model.id == selected_id:
                        self.settings.providers.selected_model_id = ""
                        break
                providers.pop(i)
                self.save()
                return True
        return False

    def add_model_to_provider(self, provider_id: str, model: ModelConfig) -> bool:
        """向服务商添加模型配置"""
        provider = self.get_provider_by_id(provider_id)
        if provider:
            provider.models.append(model)
            self.save()
            return True
        return False

    def remove_model(self, model_id: str) -> bool:
        """删除模型配置"""
        for provider in self.settings.providers.providers:
            for i, model in enumerate(provider.models):
                if model.id == model_id:
                    provider.models.pop(i)
                    # 如果删除的是选中的模型，清空选择
                    if self.settings.providers.selected_model_id == model_id:
                        self.settings.providers.selected_model_id = ""
                    self.save()
                    return True
        return False

    def update_model(self, model_id: str, **kwargs) -> bool:
        """更新模型配置"""
        model = self.get_model_config_by_id(model_id)
        if model:
            for key, value in kwargs.items():
                if hasattr(model, key):
                    setattr(model, key, value)
            self.save()
            return True
        return False

    def select_model(self, model_id: str) -> None:
        """选择模型"""
        self.settings.providers.selected_model_id = model_id
        self.save()

    # ============ 旧版兼容方法（保留向后兼容） ============

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

    def update_term_extraction(self, **kwargs) -> None:
        """Update term extraction settings."""
        for key, value in kwargs.items():
            if hasattr(self.settings.term_extraction, key):
                setattr(self.settings.term_extraction, key, value)
        self.save()


# Global settings manager instance
settings_manager = SettingsManager()
