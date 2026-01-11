"""BabelDOC WebUI - Main Application."""

import asyncio
import logging
import tempfile
import uuid
from pathlib import Path

from nicegui import ui, events

from ui.components.settings import (
    settings_manager,
    ModelConfig,
    Provider,
    get_builtin_provider_by_id,
)

logger = logging.getLogger(__name__)

# Language options
LANGUAGES = {
    "en": "English",
    "zh": "中文",
    "zh-TW": "繁體中文",
    "ja": "日本語",
    "ko": "한국어",
    "fr": "Français",
    "de": "Deutsch",
    "es": "Español",
    "pt": "Português",
    "ru": "Русский",
    "ar": "العربية",
    "it": "Italiano",
}


class PageState:
    """每个页面/客户端的 UI 状态"""

    def __init__(self):
        # 翻译状态
        self.is_running = False
        self.current_file: str | None = None
        self.progress: float = 0
        self.stage: str = ""
        self.result_files: list[dict] = []
        self.error: str | None = None
        self.cancel_event: asyncio.Event | None = None

        # 上传的文件
        self.uploaded_files: list[dict] = []

        # UI 元素引用
        self.file_list_container: ui.column | None = None
        self.upload_element: ui.upload | None = None
        self.pages_input: ui.input | None = None
        self.start_button: ui.button | None = None
        self.cancel_button: ui.button | None = None
        self.progress_card: ui.card | None = None
        self.progress_bar: ui.linear_progress | None = None
        self.progress_label: ui.label | None = None
        self.stage_label: ui.label | None = None
        self.results_card: ui.card | None = None
        self.results_container: ui.column | None = None


def create_header():
    """Create the application header with clean modern styling."""
    # 在 header 上下文中创建设置对话框
    dialog = create_settings_dialog()

    with ui.header().classes("bg-blue-600"):
        with ui.row().classes("w-full items-center justify-between px-4 py-1"):
            with ui.row().classes("items-center gap-2"):
                ui.icon("translate", size="1.2rem").classes("text-white")
                ui.label("BabelDOC").classes("text-base font-bold text-white")
                ui.label("v0.1.0").classes(
                    "text-[10px] text-white/70 font-medium"
                )

            ui.button(
                icon="settings",
                on_click=dialog.open,
            ).props("flat round dense").classes(
                "text-white hover:bg-white/20"
            )


def create_settings_dialog() -> ui.dialog:
    """Create the settings dialog with clean modern styling."""
    dialog = ui.dialog()
    with dialog:
        with ui.card().classes(
            "max-w-4xl max-h-[90vh] rounded-xl shadow-lg border border-gray-200 p-8"
        ):
            with ui.row().classes("w-full items-center justify-between mb-6"):
                ui.label("设置").classes("text-2xl font-bold text-gray-900")
                ui.button(icon="close", on_click=dialog.close).props("flat round").classes(
                    "hover:bg-gray-100 transition-colors duration-200"
                )

            # 用 column 包裹 tabs 和 panels 确保垂直布局
            with ui.column().classes("w-full flex-1 gap-0"):
                with ui.tabs().classes("w-full") as tabs:
                    provider_tab = ui.tab("服务商管理", icon="hub")
                    translation_tab = ui.tab("翻译选项", icon="settings_suggest")
                    output_tab = ui.tab("PDF 输出", icon="picture_as_pdf")
                    processing_tab = ui.tab("文档处理", icon="build")
                    expert_tab = ui.tab("专家选项", icon="tune")

                with ui.tab_panels(tabs, value=provider_tab).classes("w-full flex-1 overflow-y-auto"):
                    with ui.tab_panel(provider_tab):
                        create_provider_settings()

                    with ui.tab_panel(translation_tab):
                        create_translation_options_tab()

                    with ui.tab_panel(output_tab):
                        create_pdf_output_tab()

                    with ui.tab_panel(processing_tab):
                        create_document_processing_tab()

                    with ui.tab_panel(expert_tab):
                        create_expert_options_tab()

            with ui.row().classes("w-full justify-end mt-4 gap-3 pt-4 border-t border-gray-200"):
                ui.button("取消", on_click=dialog.close).props("outline").classes(
                    "px-8 text-gray-700 hover:bg-gray-50 transition-colors"
                )
                ui.button("保存", on_click=lambda: save_settings(dialog)).classes(
                    "px-10 bg-blue-600 text-white hover:bg-blue-700 shadow-md hover:shadow-lg transition-all"
                )

    return dialog


def create_provider_settings():
    """Create provider management panel."""
    # 用于刷新 UI 的容器引用
    provider_list_container = ui.column().classes("w-full gap-4")

    def refresh_provider_list():
        """刷新服务商列表"""
        provider_list_container.clear()
        with provider_list_container:
            render_provider_list()

    def render_provider_list():
        """渲染服务商列表"""
        providers = settings_manager.settings.providers.providers

        if not providers:
            with ui.row().classes("w-full items-center justify-center p-8 text-gray-500"):
                ui.icon("inbox", size="lg")
                ui.label("暂无服务商配置")
            return

        for provider in providers:
            render_provider_card(provider)

    def render_provider_card(provider: Provider):
        """渲染单个服务商卡片"""
        preset = get_builtin_provider_by_id(provider.id)
        suggested_models = preset.get("suggested_models", []) if preset else []

        with ui.expansion(
            value=len(provider.models) > 0
        ).classes(
            "w-full border border-gray-200 rounded-xl hover:border-blue-300 transition-all duration-200"
        ) as expansion:
            # 自定义标题
            with expansion.add_slot("header"):
                with ui.row().classes("w-full items-center gap-3 py-2"):
                    ui.icon(provider.icon, size="md").classes("text-blue-600")
                    ui.label(provider.name).classes("text-lg font-semibold text-gray-800 flex-1")
                    ui.label(f"{len(provider.models)} 个模型").classes(
                        "text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full"
                    )
                    if not provider.is_builtin:
                        ui.button(
                            icon="edit",
                            on_click=lambda p=provider: open_edit_provider_dialog(p, refresh_provider_list),
                        ).props("flat round dense").classes("text-gray-500 hover:text-blue-600")
                        ui.button(
                            icon="delete",
                            on_click=lambda p=provider: confirm_delete_provider(p, refresh_provider_list),
                        ).props("flat round dense").classes("text-red-500 hover:text-red-700")

            # 展开内容
            with ui.column().classes("w-full gap-3 p-2"):
                # 显示默认 Base URL
                ui.label(f"默认 Base URL: {provider.default_base_url}").classes(
                    "text-xs text-gray-500 mb-2"
                )

                # 模型列表
                if provider.models:
                    for model in provider.models:
                        render_model_item(model, provider, refresh_provider_list)
                else:
                    ui.label("暂无模型配置").classes("text-gray-400 text-sm py-2")

                # 添加模型按钮
                ui.button(
                    "+ 添加模型配置",
                    on_click=lambda p=provider, sm=suggested_models: open_add_model_dialog(
                        p, sm, refresh_provider_list
                    ),
                ).props("flat dense").classes(
                    "text-blue-600 hover:bg-blue-50 mt-2"
                )

    def render_model_item(model: ModelConfig, provider: Provider, on_refresh):
        """渲染单个模型配置项"""
        selected_id = settings_manager.settings.providers.selected_model_id
        is_selected = model.id == selected_id

        with ui.row().classes(
            f"w-full items-center gap-3 p-3 rounded-lg border transition-all "
            f"{'border-blue-400 bg-blue-50' if is_selected else 'border-gray-200 bg-gray-50 hover:border-gray-300'}"
        ):
            # 选中指示器
            if is_selected:
                ui.icon("check_circle", size="sm").classes("text-blue-600")
            else:
                ui.icon("radio_button_unchecked", size="sm").classes("text-gray-400")

            # 模型信息
            with ui.column().classes("flex-1 gap-1"):
                ui.label(model.display_name).classes("font-medium text-gray-800")
                with ui.row().classes("gap-2 text-xs text-gray-500"):
                    ui.label(f"模型: {model.model_name}")
                    ui.label("•")
                    if model.api_key:
                        ui.label("API Key: 已配置").classes("text-green-600")
                    else:
                        ui.label("API Key: 未配置").classes("text-red-500")

            # 操作按钮
            ui.button(
                icon="edit",
                on_click=lambda m=model, p=provider: open_edit_model_dialog(m, p, on_refresh),
            ).props("flat round dense").classes("text-gray-500 hover:text-blue-600")
            ui.button(
                icon="delete",
                on_click=lambda m=model: confirm_delete_model(m, on_refresh),
            ).props("flat round dense").classes("text-red-500 hover:text-red-700")

    # 渲染页面
    with ui.row().classes("w-full items-center justify-between mb-4"):
        with ui.row().classes("items-center gap-2"):
            ui.icon("hub", size="sm").classes("text-blue-600")
            ui.label("服务商管理").classes("text-lg font-semibold text-gray-800")
        ui.button(
            "+ 添加自定义服务商",
            icon="add",
            on_click=lambda: open_add_provider_dialog(refresh_provider_list),
        ).props("flat dense").classes("text-blue-600 hover:bg-blue-50")

    render_provider_list()


def open_add_model_dialog(provider: Provider, suggested_models: list[str], on_refresh):
    """打开添加模型对话框"""
    with ui.dialog() as dialog, ui.card().classes("w-96 p-6"):
        ui.label("添加模型配置").classes("text-xl font-bold text-gray-900 mb-4")

        display_name_input = ui.input("显示名称 *", placeholder="例如: GPT-4o Mini").classes("w-full")

        model_options = suggested_models if suggested_models else []
        model_select = ui.select(
            model_options,
            label="模型名称 *",
            with_input=True,
            new_value_mode="add-unique",
        ).classes("w-full")

        api_key_input = ui.input(
            "API Key *",
            password=True,
            password_toggle_button=True,
        ).classes("w-full")

        # 高级选项
        with ui.expansion("高级选项", icon="settings").classes("w-full mt-2"):
            with ui.column().classes("w-full gap-2 p-2"):
                base_url_input = ui.input(
                    "自定义 Base URL (留空使用服务商默认)",
                    placeholder=provider.default_base_url,
                ).classes("w-full")

                json_mode_checkbox = ui.checkbox("启用 JSON 模式")
                dashscope_checkbox = ui.checkbox("发送 DashScope Header")
                no_temp_checkbox = ui.checkbox("不发送 Temperature")

        def save_model():
            if not display_name_input.value or not model_select.value or not api_key_input.value:
                ui.notify("请填写必填项", type="negative")
                return

            new_model = ModelConfig(
                id=str(uuid.uuid4()),
                display_name=display_name_input.value,
                model_name=model_select.value,
                api_key=api_key_input.value,
                base_url=base_url_input.value or None,
                enable_json_mode=json_mode_checkbox.value,
                send_dashscope_header=dashscope_checkbox.value,
                no_send_temperature=no_temp_checkbox.value,
            )

            settings_manager.add_model_to_provider(provider.id, new_model)
            ui.notify(f"已添加模型: {new_model.display_name}", type="positive")
            dialog.close()
            on_refresh()

        with ui.row().classes("w-full justify-end gap-2 mt-4"):
            ui.button("取消", on_click=dialog.close).props("flat")
            ui.button("保存", on_click=save_model).classes("bg-blue-600 text-white")

    dialog.open()


def open_edit_model_dialog(model: ModelConfig, provider: Provider, on_refresh):
    """打开编辑模型对话框"""
    preset = get_builtin_provider_by_id(provider.id)
    suggested_models = preset.get("suggested_models", []) if preset else []

    with ui.dialog() as dialog, ui.card().classes("w-96 p-6"):
        ui.label("编辑模型配置").classes("text-xl font-bold text-gray-900 mb-4")

        display_name_input = ui.input("显示名称 *", value=model.display_name).classes("w-full")

        model_options = suggested_models if suggested_models else []
        if model.model_name and model.model_name not in model_options:
            model_options = [model.model_name] + model_options

        model_select = ui.select(
            model_options,
            label="模型名称 *",
            value=model.model_name,
            with_input=True,
            new_value_mode="add-unique",
        ).classes("w-full")

        api_key_input = ui.input(
            "API Key *",
            value=model.api_key,
            password=True,
            password_toggle_button=True,
        ).classes("w-full")

        # 高级选项
        with ui.expansion("高级选项", icon="settings").classes("w-full mt-2"):
            with ui.column().classes("w-full gap-2 p-2"):
                base_url_input = ui.input(
                    "自定义 Base URL (留空使用服务商默认)",
                    value=model.base_url or "",
                    placeholder=provider.default_base_url,
                ).classes("w-full")

                json_mode_checkbox = ui.checkbox("启用 JSON 模式", value=model.enable_json_mode)
                dashscope_checkbox = ui.checkbox("发送 DashScope Header", value=model.send_dashscope_header)
                no_temp_checkbox = ui.checkbox("不发送 Temperature", value=model.no_send_temperature)

        def save_model():
            if not display_name_input.value or not model_select.value or not api_key_input.value:
                ui.notify("请填写必填项", type="negative")
                return

            settings_manager.update_model(
                model.id,
                display_name=display_name_input.value,
                model_name=model_select.value,
                api_key=api_key_input.value,
                base_url=base_url_input.value or None,
                enable_json_mode=json_mode_checkbox.value,
                send_dashscope_header=dashscope_checkbox.value,
                no_send_temperature=no_temp_checkbox.value,
            )
            ui.notify(f"已更新模型: {display_name_input.value}", type="positive")
            dialog.close()
            on_refresh()

        with ui.row().classes("w-full justify-end gap-2 mt-4"):
            ui.button("取消", on_click=dialog.close).props("flat")
            ui.button("保存", on_click=save_model).classes("bg-blue-600 text-white")

    dialog.open()


def confirm_delete_model(model: ModelConfig, on_refresh):
    """确认删除模型"""
    with ui.dialog() as dialog, ui.card().classes("p-6"):
        ui.label("确认删除").classes("text-xl font-bold text-gray-900 mb-2")
        ui.label(f"确定要删除模型配置 \"{model.display_name}\" 吗？").classes("text-gray-600 mb-4")

        def do_delete():
            settings_manager.remove_model(model.id)
            ui.notify(f"已删除模型: {model.display_name}", type="positive")
            dialog.close()
            on_refresh()

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("取消", on_click=dialog.close).props("flat")
            ui.button("删除", on_click=do_delete).classes("bg-red-600 text-white")

    dialog.open()


def open_add_provider_dialog(on_refresh):
    """打开添加自定义服务商对话框"""
    with ui.dialog() as dialog, ui.card().classes("w-96 p-6"):
        ui.label("添加自定义服务商").classes("text-xl font-bold text-gray-900 mb-4")

        name_input = ui.input("服务商名称 *", placeholder="例如: 我的私有服务").classes("w-full")
        base_url_input = ui.input(
            "默认 Base URL *",
            placeholder="https://api.example.com/v1",
        ).classes("w-full")

        icon_options = {
            "smart_toy": "机器人",
            "cloud": "云",
            "computer": "电脑",
            "dns": "服务器",
            "settings": "设置",
            "auto_awesome": "星星",
            "psychology": "大脑",
        }
        icon_select = ui.select(icon_options, label="图标", value="smart_toy").classes("w-full")

        def save_provider():
            if not name_input.value or not base_url_input.value:
                ui.notify("请填写必填项", type="negative")
                return

            new_provider = Provider(
                id=f"custom_{uuid.uuid4().hex[:8]}",
                name=name_input.value,
                default_base_url=base_url_input.value,
                is_builtin=False,
                icon=icon_select.value,
                models=[],
            )

            settings_manager.add_provider(new_provider)
            ui.notify(f"已添加服务商: {new_provider.name}", type="positive")
            dialog.close()
            on_refresh()

        with ui.row().classes("w-full justify-end gap-2 mt-4"):
            ui.button("取消", on_click=dialog.close).props("flat")
            ui.button("保存", on_click=save_provider).classes("bg-blue-600 text-white")

    dialog.open()


def open_edit_provider_dialog(provider: Provider, on_refresh):
    """打开编辑服务商对话框"""
    with ui.dialog() as dialog, ui.card().classes("w-96 p-6"):
        ui.label("编辑服务商").classes("text-xl font-bold text-gray-900 mb-4")

        name_input = ui.input("服务商名称 *", value=provider.name).classes("w-full")
        base_url_input = ui.input("默认 Base URL *", value=provider.default_base_url).classes("w-full")

        icon_options = {
            "smart_toy": "机器人",
            "cloud": "云",
            "computer": "电脑",
            "dns": "服务器",
            "settings": "设置",
            "auto_awesome": "星星",
            "psychology": "大脑",
        }
        icon_select = ui.select(icon_options, label="图标", value=provider.icon).classes("w-full")

        def save_provider():
            if not name_input.value or not base_url_input.value:
                ui.notify("请填写必填项", type="negative")
                return

            provider.name = name_input.value
            provider.default_base_url = base_url_input.value
            provider.icon = icon_select.value
            settings_manager.save()

            ui.notify(f"已更新服务商: {provider.name}", type="positive")
            dialog.close()
            on_refresh()

        with ui.row().classes("w-full justify-end gap-2 mt-4"):
            ui.button("取消", on_click=dialog.close).props("flat")
            ui.button("保存", on_click=save_provider).classes("bg-blue-600 text-white")

    dialog.open()


def confirm_delete_provider(provider: Provider, on_refresh):
    """确认删除服务商"""
    with ui.dialog() as dialog, ui.card().classes("p-6"):
        ui.label("确认删除").classes("text-xl font-bold text-gray-900 mb-2")
        ui.label(f"确定要删除服务商 \"{provider.name}\" 吗？").classes("text-gray-600")
        if provider.models:
            ui.label(f"该服务商下有 {len(provider.models)} 个模型配置也将被删除。").classes(
                "text-red-500 text-sm mt-1"
            )

        def do_delete():
            settings_manager.remove_provider(provider.id)
            ui.notify(f"已删除服务商: {provider.name}", type="positive")
            dialog.close()
            on_refresh()

        with ui.row().classes("w-full justify-end gap-2 mt-4"):
            ui.button("取消", on_click=dialog.close).props("flat")
            ui.button("删除", on_click=do_delete).classes("bg-red-600 text-white")

    dialog.open()


def create_translation_options_tab():
    """Create translation options tab with performance and behavior settings."""
    s = settings_manager.settings

    # Language Settings
    with ui.row().classes("items-center gap-2 mb-3"):
        ui.icon("language", size="sm").classes("text-blue-600")
        ui.label("语言设置").classes("text-lg font-semibold text-gray-800")
    with ui.row().classes("w-full gap-4"):
        ui.select(LANGUAGES, label="源语言", value=s.translation.lang_in).classes(
            "flex-1"
        ).bind_value(s.translation, "lang_in")

        ui.select(LANGUAGES, label="目标语言", value=s.translation.lang_out).classes(
            "flex-1"
        ).bind_value(s.translation, "lang_out")

    # Performance Settings
    ui.separator().classes("my-5")
    with ui.row().classes("items-center gap-2 mb-3"):
        ui.icon("speed", size="sm").classes("text-blue-600")
        ui.label("性能设置").classes("text-lg font-semibold text-gray-800")

    with ui.row().classes("w-full gap-4"):
        ui.number("QPS 限制", value=s.translation.qps, min=1, max=100, step=1).classes(
            "flex-1"
        ).bind_value(s.translation, "qps")

        ui.number(
            "最小文本长度", value=s.translation.min_text_length, min=1, max=100, step=1
        ).classes("flex-1").bind_value(s.translation, "min_text_length")

    with ui.row().classes("w-full gap-4"):
        ui.number(
            "工作线程数 (留空自动)", value=s.translation.pool_max_workers, min=1, max=32
        ).classes("flex-1").bind_value(s.translation, "pool_max_workers")

        ui.number(
            "术语提取线程数 (留空自动)",
            value=s.translation.term_pool_max_workers,
            min=1,
            max=32,
        ).classes("flex-1").bind_value(s.translation, "term_pool_max_workers")

    # Translation Behavior
    ui.separator().classes("my-5")
    with ui.row().classes("items-center gap-2 mb-3"):
        ui.icon("settings_suggest", size="sm").classes("text-blue-600")
        ui.label("翻译行为").classes("text-lg font-semibold text-gray-800")

    with ui.column().classes("w-full gap-2"):
        ui.checkbox(
            "自动提取术语表", value=s.translation.auto_extract_glossary
        ).bind_value(s.translation, "auto_extract_glossary")
        ui.checkbox(
            "保存自动提取的术语表", value=s.translation.save_auto_extracted_glossary
        ).bind_value(s.translation, "save_auto_extracted_glossary")
        ui.checkbox(
            "禁用相同文本回退翻译", value=s.translation.disable_same_text_fallback
        ).bind_value(s.translation, "disable_same_text_fallback")
        ui.checkbox(
            "添加公式占位符提示", value=s.translation.add_formula_placehold_hint
        ).bind_value(s.translation, "add_formula_placehold_hint")
        ui.checkbox(
            "忽略翻译缓存", value=s.translation.ignore_cache
        ).bind_value(s.translation, "ignore_cache")

    # Custom System Prompt
    ui.separator().classes("my-5")
    with ui.row().classes("items-center gap-2 mb-3"):
        ui.icon("tune", size="sm").classes("text-blue-600")
        ui.label("高级选项").classes("text-lg font-semibold text-gray-800")

    with ui.expansion("展开高级选项", icon="expand_more").classes(
        "w-full border border-gray-200 rounded-xl hover:border-purple-300 transition-all duration-200"
    ):
        with ui.column().classes("w-full gap-3 p-2"):
            ui.textarea("自定义系统提示词", value=s.translation.custom_system_prompt).classes(
                "w-full"
            ).bind_value(s.translation, "custom_system_prompt")

    # 术语提取设置
    ui.separator().classes("my-5")
    with ui.row().classes("items-center gap-2 mb-3"):
        ui.icon("auto_awesome", size="sm").classes("text-blue-600")
        ui.label("术语提取配置 (可选)").classes("text-lg font-semibold text-gray-800")

    with ui.expansion("展开术语提取配置", icon="expand_more").classes(
        "w-full border border-gray-200 rounded-xl hover:border-purple-300 transition-all duration-200"
    ):
        with ui.column().classes("w-full gap-3 p-2"):
            ui.checkbox(
                "使用独立的术语提取配置",
                value=s.term_extraction.use_separate_config,
            ).bind_value(s.term_extraction, "use_separate_config")

            # 选择已配置的模型
            model_options = settings_manager.get_all_model_options()
            if model_options:
                model_dict = {"": "使用当前翻译模型"}
                model_dict.update({opt["id"]: opt["label"] for opt in model_options})

                ui.select(
                    model_dict,
                    label="选择术语提取模型",
                    value=s.term_extraction.model_config_id,
                ).classes("w-full").bind_value(s.term_extraction, "model_config_id")

            ui.label("或手动配置:").classes("text-sm text-gray-500 mt-2")

            ui.input(
                "术语提取 API Key (留空使用主模型)",
                value=s.term_extraction.custom_api_key,
                password=True,
            ).classes("w-full").bind_value(s.term_extraction, "custom_api_key")

            ui.input(
                "术语提取 Base URL (留空使用主模型)",
                value=s.term_extraction.custom_base_url,
            ).classes("w-full").bind_value(s.term_extraction, "custom_base_url")

            ui.input(
                "术语提取模型名称 (留空使用主模型)",
                value=s.term_extraction.custom_model,
            ).classes("w-full").bind_value(s.term_extraction, "custom_model")

            ui.input(
                "术语提取 Reasoning 模式",
                value=s.term_extraction.reasoning,
            ).classes("w-full").bind_value(s.term_extraction, "reasoning")


def create_pdf_output_tab():
    """Create PDF output tab with format and appearance settings."""
    s = settings_manager.settings

    # Output Format
    with ui.row().classes("items-center gap-2 mb-3"):
        ui.icon("output", size="sm").classes("text-blue-600")
        ui.label("输出格式").classes("text-lg font-semibold text-gray-800")

    with ui.row().classes("w-full gap-4 flex-wrap"):
        ui.checkbox("输出双语 PDF", value=s.pdf.output_dual).bind_value(
            s.pdf, "output_dual"
        )
        ui.checkbox("输出单语 PDF", value=s.pdf.output_mono).bind_value(
            s.pdf, "output_mono"
        )

    ui.select(
        {"watermarked": "有水印", "no_watermark": "无水印", "both": "两者都输出"},
        label="水印模式",
        value=s.pdf.watermark_mode,
    ).classes("w-full mt-2").bind_value(s.pdf, "watermark_mode")

    # Dual PDF Layout
    ui.separator().classes("my-5")
    with ui.row().classes("items-center gap-2 mb-3"):
        ui.icon("auto_stories", size="sm").classes("text-blue-600")
        ui.label("双语 PDF 布局").classes("text-lg font-semibold text-gray-800")

    with ui.column().classes("w-full gap-2"):
        ui.checkbox(
            "使用交替页面模式 (原文/译文交替排列)", value=s.pdf.use_alternating_pages_dual
        ).bind_value(s.pdf, "use_alternating_pages_dual")
        ui.checkbox("翻译页在前", value=s.pdf.dual_translate_first).bind_value(
            s.pdf, "dual_translate_first"
        )
        ui.checkbox(
            "仅包含翻译页", value=s.pdf.only_include_translated_page
        ).bind_value(s.pdf, "only_include_translated_page")

    # Font Settings
    ui.separator().classes("my-5")
    with ui.row().classes("items-center gap-2 mb-3"):
        ui.icon("text_fields", size="sm").classes("text-blue-600")
        ui.label("字体设置").classes("text-lg font-semibold text-gray-800")

    ui.select(
        {None: "自动", "serif": "衬线体", "sans-serif": "无衬线体", "script": "手写体"},
        label="主字体族",
        value=s.pdf.primary_font_family,
    ).classes("w-full").bind_value(s.pdf, "primary_font_family")

    ui.input("公式字体匹配模式", value=s.pdf.formular_font_pattern).classes(
        "w-full"
    ).bind_value(s.pdf, "formular_font_pattern")

    ui.input("公式字符匹配模式", value=s.pdf.formular_char_pattern).classes(
        "w-full"
    ).bind_value(s.pdf, "formular_char_pattern")


def create_document_processing_tab():
    """Create document processing tab with compatibility and OCR settings."""
    s = settings_manager.settings

    # Compatibility Settings
    with ui.row().classes("items-center gap-2 mb-3"):
        ui.icon("build", size="sm").classes("text-blue-600")
        ui.label("兼容性设置").classes("text-lg font-semibold text-gray-800")

    with ui.column().classes("w-full gap-2"):
        ui.checkbox(
            "增强兼容性模式 (启用下面三个选项)",
            value=s.pdf.enhance_compatibility,
        ).bind_value(s.pdf, "enhance_compatibility")

        with ui.row().classes("w-full gap-4 pl-4 flex-wrap"):
            ui.checkbox("跳过 PDF 清理", value=s.pdf.skip_clean).bind_value(
                s.pdf, "skip_clean"
            )
            ui.checkbox("翻译页在前", value=s.pdf.dual_translate_first).bind_value(
                s.pdf, "dual_translate_first"
            )
            ui.checkbox(
                "禁用富文本翻译", value=s.pdf.disable_rich_text_translate
            ).bind_value(s.pdf, "disable_rich_text_translate")

    # Scanning & OCR
    ui.separator().classes("my-5")
    with ui.row().classes("items-center gap-2 mb-3"):
        ui.icon("document_scanner", size="sm").classes("text-blue-600")
        ui.label("扫描文档与 OCR").classes("text-lg font-semibold text-gray-800")

    with ui.column().classes("w-full gap-2"):
        ui.checkbox("跳过扫描文档检测", value=s.pdf.skip_scanned_detection).bind_value(
            s.pdf, "skip_scanned_detection"
        )
        ui.checkbox(
            "OCR 处理 (适用于白底黑字扫描件)", value=s.pdf.ocr_workaround
        ).bind_value(s.pdf, "ocr_workaround")
        ui.checkbox(
            "自动启用 OCR 处理", value=s.pdf.auto_enable_ocr_workaround
        ).bind_value(s.pdf, "auto_enable_ocr_workaround")

    # Text Processing
    ui.separator().classes("my-5")
    with ui.row().classes("items-center gap-2 mb-3"):
        ui.icon("text_format", size="sm").classes("text-blue-600")
        ui.label("文本处理").classes("text-lg font-semibold text-gray-800")

    with ui.column().classes("w-full gap-2"):
        ui.checkbox("强制分割短行", value=s.pdf.split_short_lines).bind_value(
            s.pdf, "split_short_lines"
        )

        ui.number(
            "短行分割因子",
            value=s.pdf.short_line_split_factor,
            min=0.1,
            max=1.0,
            step=0.1,
        ).classes("w-full").bind_value(s.pdf, "short_line_split_factor")

        ui.checkbox(
            "合并交替行号", value=s.pdf.merge_alternating_line_numbers
        ).bind_value(s.pdf, "merge_alternating_line_numbers")

    # Pagination
    ui.separator().classes("my-5")
    with ui.row().classes("items-center gap-2 mb-3"):
        ui.icon("view_module", size="sm").classes("text-blue-600")
        ui.label("分段处理").classes("text-lg font-semibold text-gray-800")

    ui.number(
        "每部分最大页数 (留空不分段)", value=s.pdf.max_pages_per_part, min=1
    ).classes("w-full").bind_value(s.pdf, "max_pages_per_part")

    # Experimental Features
    ui.separator().classes("my-5")
    with ui.row().classes("items-center gap-2 mb-3"):
        ui.icon("science", size="sm").classes("text-orange-600")
        ui.label("实验性功能").classes("text-lg font-semibold text-orange-700")

    with ui.expansion("展开实验性功能", icon="expand_more").classes(
        "w-full border border-orange-200 rounded-xl hover:border-orange-300 transition-all duration-200"
    ):
        with ui.column().classes("w-full gap-2 p-2"):
            ui.label("以下功能处于实验阶段，可能不稳定").classes("text-sm text-orange-600 mb-2")
            ui.checkbox(
                "翻译表格文本", value=s.pdf.translate_table_text
            ).bind_value(s.pdf, "translate_table_text")
            ui.checkbox(
                "仅解析生成 PDF (不翻译)", value=s.pdf.only_parse_generate_pdf
            ).bind_value(s.pdf, "only_parse_generate_pdf")


def create_expert_options_tab():
    """Create expert options tab with rendering, paths, and RPC settings."""
    s = settings_manager.settings

    # Rendering Options
    with ui.row().classes("items-center gap-2 mb-3"):
        ui.icon("brush", size="sm").classes("text-blue-600")
        ui.label("渲染选项").classes("text-lg font-semibold text-gray-800")

    with ui.row().classes("w-full gap-4 flex-wrap"):
        ui.checkbox("跳过表单渲染", value=s.pdf.skip_form_render).bind_value(
            s.pdf, "skip_form_render"
        )
        ui.checkbox("跳过曲线渲染", value=s.pdf.skip_curve_render).bind_value(
            s.pdf, "skip_curve_render"
        )
        ui.checkbox("移除非公式线条", value=s.pdf.remove_non_formula_lines).bind_value(
            s.pdf, "remove_non_formula_lines"
        )

    with ui.row().classes("w-full gap-4"):
        ui.number(
            "非公式线条 IoU 阈值",
            value=s.pdf.non_formula_line_iou_threshold,
            min=0.0,
            max=1.0,
            step=0.05,
        ).classes("flex-1").bind_value(s.pdf, "non_formula_line_iou_threshold")

        ui.number(
            "图表保护阈值",
            value=s.pdf.figure_table_protection_threshold,
            min=0.0,
            max=1.0,
            step=0.05,
        ).classes("flex-1").bind_value(s.pdf, "figure_table_protection_threshold")

    # Path Settings
    ui.separator().classes("my-5")
    with ui.row().classes("items-center gap-2 mb-3"):
        ui.icon("folder", size="sm").classes("text-blue-600")
        ui.label("路径设置").classes("text-lg font-semibold text-gray-800")

    ui.input("输出目录 (留空使用当前目录)", value=s.paths.output_dir).classes(
        "w-full"
    ).bind_value(s.paths, "output_dir")

    ui.input("工作目录 (留空使用临时目录)", value=s.paths.working_dir).classes(
        "w-full"
    ).bind_value(s.paths, "working_dir")

    ui.input("术语表文件 (多个用逗号分隔)", value=s.paths.glossary_files).classes(
        "w-full"
    ).bind_value(s.paths, "glossary_files")

    # RPC Service
    ui.separator().classes("my-5")
    with ui.row().classes("items-center gap-2 mb-3"):
        ui.icon("dns", size="sm").classes("text-blue-600")
        ui.label("RPC 服务").classes("text-lg font-semibold text-gray-800")

    ui.input("DocLayout RPC 地址", value=s.rpc.doclayout_host).classes(
        "w-full"
    ).bind_value(s.rpc, "doclayout_host")


def save_settings(dialog: ui.dialog):
    """Save settings and close dialog."""
    settings_manager.save()
    ui.notify("设置已保存", type="positive")
    dialog.close()


def create_main_content(ps: PageState):
    """Create the main content area with sidebar layout."""
    with ui.row().classes("w-full max-w-7xl mx-auto px-8 py-8 gap-8 items-start"):
        # Left sidebar - Translation options only (fixed width)
        with ui.column().classes("w-64 gap-6 flex-shrink-0"):
            create_options_section(ps)

        # Right content - File upload, buttons, progress, results (flexible width)
        with ui.column().classes("flex-1 gap-6 min-w-0"):
            create_upload_section(ps)
            create_action_buttons(ps)
            create_progress_section(ps)
            create_results_section(ps)


def create_upload_section(ps: PageState):
    """Create file upload section with clean modern styling."""

    async def handle_file_upload(e: events.UploadEventArguments):
        """Handle file upload event."""
        temp_dir = Path(tempfile.gettempdir()) / "babeldoc-webui"
        temp_dir.mkdir(exist_ok=True)

        # NiceGUI 新版本: e.file 包含文件信息
        filename = e.file.name
        file_path = temp_dir / filename

        # 使用 await e.file.read() 读取内容（异步方法）
        content = await e.file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        ps.uploaded_files.append({"name": filename, "path": str(file_path)})
        update_file_list()
        ps.upload_element.reset()
        ui.notify(f"已上传: {filename}", type="positive")

    def update_file_list():
        """Update the file list display."""
        ps.file_list_container.clear()
        with ps.file_list_container:
            if ps.uploaded_files:
                for i, file_info in enumerate(ps.uploaded_files):
                    with ui.row().classes(
                        "file-item w-full items-center gap-3 p-4 bg-gray-50 rounded-lg "
                        "border border-gray-200 hover:border-blue-300 hover:bg-white transition-all"
                    ):
                        ui.icon("picture_as_pdf", size="md").classes("text-red-500")
                        ui.label(file_info["name"]).classes(
                            "flex-1 font-medium text-gray-700 truncate"
                        )

                        def make_remove_handler(idx):
                            def handler():
                                if 0 <= idx < len(ps.uploaded_files):
                                    removed = ps.uploaded_files.pop(idx)
                                    try:
                                        Path(removed["path"]).unlink(missing_ok=True)
                                    except Exception:
                                        pass
                                    update_file_list()
                            return handler

                        ui.button(
                            icon="delete",
                            on_click=make_remove_handler(i),
                        ).props("flat round dense").classes(
                            "text-red-500 hover:bg-red-50 transition-colors duration-200"
                        )

    with ui.card().classes("w-full rounded-xl shadow-sm border border-gray-200 bg-white"):
        with ui.row().classes("items-center gap-3 mb-5 pb-4 border-b border-gray-100"):
            ui.icon("cloud_upload", size="md").classes("text-blue-600")
            ui.label("上传 PDF 文件").classes("text-xl font-semibold text-gray-900")

        ps.upload_element = ui.upload(
            label="拖拽或点击上传 PDF 文件",
            multiple=True,
            on_upload=handle_file_upload,
            auto_upload=True,
        ).props('accept=".pdf" flat bordered').classes(
            "w-full upload-area"
        )

        ps.file_list_container = ui.column().classes("w-full mt-4 gap-3")


def create_options_section(ps: PageState):
    """Create translation options section for sidebar."""
    s = settings_manager.settings

    with ui.card().classes("w-full rounded-xl shadow-sm border border-gray-200 bg-white"):
        with ui.row().classes("items-center gap-3 mb-5 pb-4 border-b border-gray-100"):
            ui.icon("tune", size="md").classes("text-blue-600")
            ui.label("翻译选项").classes("text-lg font-semibold text-gray-900")

        with ui.column().classes("w-full gap-4"):
            # Language selection
            ui.select(
                LANGUAGES,
                label="源语言",
                value=s.translation.lang_in,
            ).classes("w-full").bind_value(s.translation, "lang_in")

            ui.select(
                LANGUAGES,
                label="目标语言",
                value=s.translation.lang_out,
            ).classes("w-full").bind_value(s.translation, "lang_out")

            # Model selection - 使用新的服务商模型选择
            model_options = settings_manager.get_all_model_options()

            if model_options:
                # 构建选项字典
                options_dict = {opt["id"]: opt["label"] for opt in model_options}

                # 当前选中值
                current_value = s.providers.selected_model_id
                if current_value not in options_dict and options_dict:
                    current_value = list(options_dict.keys())[0]
                    settings_manager.select_model(current_value)

                model_select = ui.select(
                    options_dict,
                    label="翻译模型",
                    value=current_value,
                ).classes("w-full")

                def on_model_change(e):
                    settings_manager.select_model(e.value)

                model_select.on("update:model-value", on_model_change)

                # 显示当前选中模型信息
                model_config = settings_manager.get_selected_model_config()
                if model_config:
                    provider = settings_manager.get_provider_for_model(model_config.id)
                    with ui.row().classes("w-full items-center gap-2 text-xs text-gray-500"):
                        if provider:
                            ui.icon(provider.icon, size="xs")
                        ui.label(f"模型: {model_config.model_name}")
            else:
                # 没有配置模型时显示提示
                with ui.column().classes("w-full gap-2 p-3 bg-yellow-50 rounded-lg border border-yellow-200"):
                    with ui.row().classes("items-center gap-2"):
                        ui.icon("warning", size="sm").classes("text-yellow-600")
                        ui.label("请先配置翻译模型").classes("text-yellow-700 font-medium")

            # Page range input
            ps.pages_input = ui.input(
                "页码范围 (留空翻译全部)",
                placeholder="例如: 1,2,1-,-3,3-5",
            ).classes("w-full")

        # Quick options
        with ui.expansion("更多选项", icon="tune").classes(
            "w-full mt-4 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors"
        ):
            with ui.column().classes("w-full gap-3 p-3"):
                ui.checkbox("输出双语 PDF", value=s.pdf.output_dual).bind_value(
                    s.pdf, "output_dual"
                )
                ui.checkbox("输出单语 PDF", value=s.pdf.output_mono).bind_value(
                    s.pdf, "output_mono"
                )
                ui.checkbox(
                    "增强兼容性", value=s.pdf.enhance_compatibility
                ).bind_value(s.pdf, "enhance_compatibility")
                ui.checkbox(
                    "自动提取术语", value=s.translation.auto_extract_glossary
                ).bind_value(s.translation, "auto_extract_glossary")


def create_action_buttons(ps: PageState):
    """Create action buttons section below upload area."""

    async def on_start_click():
        await start_translation(ps)

    def on_cancel_click():
        cancel_translation(ps)

    with ui.row().classes("w-full gap-4 justify-center"):
        ps.start_button = (
            ui.button(
                "开始翻译",
                icon="play_arrow",
                on_click=on_start_click,
            )
            .props("size=lg")
            .classes(
                "px-16 py-3 bg-blue-600 text-white hover:bg-blue-700 shadow-md hover:shadow-lg "
                "font-semibold text-base transition-all duration-200"
            )
        )

        ps.cancel_button = (
            ui.button(
                "取消翻译",
                icon="stop",
                on_click=on_cancel_click,
            )
            .props("size=lg outline")
            .classes(
                "px-16 py-3 border-2 border-gray-300 text-gray-700 hover:bg-gray-50 "
                "font-semibold text-base transition-colors duration-200"
            )
        )
        ps.cancel_button.visible = False


def create_progress_section(ps: PageState):
    """Create progress display section with clean modern styling."""
    ps.progress_card = ui.card().classes(
        "w-full rounded-xl shadow-sm border border-blue-200 bg-blue-50/50"
    )

    with ps.progress_card:
        with ui.row().classes("items-center gap-3 mb-5 pb-4 border-b border-blue-100"):
            ui.icon("autorenew", size="md").classes("text-blue-600")
            ui.label("翻译进度").classes("text-xl font-semibold text-gray-900")

        with ui.column().classes("w-full gap-4"):
            ps.progress_bar = ui.linear_progress(value=0, show_value=False).classes(
                "w-full h-2 rounded-full"
            )
            ps.progress_label = ui.label("0%").classes(
                "text-center w-full text-3xl font-bold text-blue-600"
            )
            with ui.row().classes("items-center justify-center gap-2 w-full"):
                ui.icon("info", size="sm").classes("text-gray-500")
                ps.stage_label = ui.label("准备中...").classes(
                    "text-base text-gray-600 font-medium"
                )

    # 在所有子元素添加完毕后再隐藏
    ps.progress_card.visible = False


def create_results_section(ps: PageState):
    """Create results display section with clean modern styling."""
    ps.results_card = ui.card().classes(
        "w-full rounded-xl shadow-sm border border-green-200 bg-green-50/50"
    )

    with ps.results_card:
        with ui.row().classes("items-center gap-3 mb-5 pb-4 border-b border-green-100"):
            ui.icon("check_circle", size="md").classes("text-green-600")
            ui.label("翻译完成").classes("text-xl font-semibold text-gray-900")
        ps.results_container = ui.column().classes("w-full gap-3")

    # 在所有子元素添加完毕后再隐藏
    ps.results_card.visible = False


async def start_translation(ps: PageState):
    """Start the translation process."""
    # Validate settings - 使用新的模型配置
    model_config = settings_manager.get_selected_model_config()

    if not model_config:
        ui.notify("请先在设置中配置翻译模型", type="negative")
        return

    if not model_config.api_key:
        ui.notify("所选模型未配置 API Key", type="negative")
        return

    if not ps.uploaded_files:
        ui.notify("请先上传 PDF 文件", type="negative")
        return

    # Update UI state
    ps.is_running = True
    ps.progress = 0
    ps.result_files = []
    ps.error = None
    ps.cancel_event = asyncio.Event()

    ps.start_button.visible = False
    ps.cancel_button.visible = True
    ps.progress_card.visible = True
    ps.results_card.visible = False

    try:
        await run_translation(ps)
    except Exception as e:
        logger.exception("Translation error")
        ps.error = str(e)
        ui.notify(f"翻译出错: {e}", type="negative")
    finally:
        ps.is_running = False
        ps.start_button.visible = True
        ps.cancel_button.visible = False

        if ps.result_files:
            show_results(ps)


async def run_translation(ps: PageState):
    """Run the actual translation."""
    import babeldoc.assets.assets
    import babeldoc.format.pdf.high_level
    from babeldoc.format.pdf.translation_config import (
        TranslationConfig,
        WatermarkOutputMode,
    )
    from babeldoc.translator.translator import (
        OpenAITranslator,
        set_translate_rate_limiter,
    )

    s = settings_manager.settings

    # 获取当前选中的模型配置
    model_config = settings_manager.get_selected_model_config()
    if not model_config:
        raise ValueError("请先选择翻译模型")

    # 获取有效的 Base URL
    effective_base_url = settings_manager.get_effective_base_url(model_config)

    # Initialize BabelDOC
    babeldoc.format.pdf.high_level.init()

    # Create translator - 使用新的配置结构
    translator = OpenAITranslator(
        lang_in=s.translation.lang_in,
        lang_out=s.translation.lang_out,
        model=model_config.model_name,
        base_url=effective_base_url or None,
        api_key=model_config.api_key,
        ignore_cache=s.translation.ignore_cache,
        enable_json_mode_if_requested=model_config.enable_json_mode,
        send_dashscope_header=model_config.send_dashscope_header,
        send_temperature=not model_config.no_send_temperature,
    )

    # Create term extraction translator - 使用新的术语提取设置
    term_extraction_translator = translator
    term_settings = s.term_extraction

    if term_settings.use_separate_config:
        # 检查是否使用已配置的模型
        if term_settings.model_config_id:
            term_model_config = settings_manager.get_model_config_by_id(term_settings.model_config_id)
            if term_model_config:
                term_base_url = settings_manager.get_effective_base_url(term_model_config)
                term_kwargs = {}
                if term_settings.reasoning:
                    term_kwargs["reasoning"] = term_settings.reasoning

                term_extraction_translator = OpenAITranslator(
                    lang_in=s.translation.lang_in,
                    lang_out=s.translation.lang_out,
                    model=term_model_config.model_name,
                    base_url=term_base_url or None,
                    api_key=term_model_config.api_key,
                    ignore_cache=s.translation.ignore_cache,
                    enable_json_mode_if_requested=term_model_config.enable_json_mode,
                    send_dashscope_header=term_model_config.send_dashscope_header,
                    send_temperature=not term_model_config.no_send_temperature,
                    **term_kwargs,
                )
        elif term_settings.custom_api_key or term_settings.custom_base_url or term_settings.custom_model:
            # 使用自定义配置
            term_kwargs = {}
            if term_settings.reasoning:
                term_kwargs["reasoning"] = term_settings.reasoning

            term_extraction_translator = OpenAITranslator(
                lang_in=s.translation.lang_in,
                lang_out=s.translation.lang_out,
                model=term_settings.custom_model or model_config.model_name,
                base_url=term_settings.custom_base_url or effective_base_url or None,
                api_key=term_settings.custom_api_key or model_config.api_key,
                ignore_cache=s.translation.ignore_cache,
                **term_kwargs,
            )

    # Set rate limiter
    set_translate_rate_limiter(s.translation.qps)

    # Initialize document layout model
    if s.rpc.doclayout_host:
        from babeldoc.docvision.rpc_doclayout import RpcDocLayoutModel

        doc_layout_model = RpcDocLayoutModel(host=s.rpc.doclayout_host)
    else:
        from babeldoc.docvision.doclayout import DocLayoutModel

        doc_layout_model = DocLayoutModel.load_onnx()

    # Load glossaries
    loaded_glossaries = []
    if s.paths.glossary_files:
        from babeldoc.glossary import Glossary

        for path_str in s.paths.glossary_files.split(","):
            path = Path(path_str.strip())
            if path.exists() and path.is_file():
                try:
                    glossary = Glossary.from_csv(path, s.translation.lang_out)
                    if glossary.entries:
                        loaded_glossaries.append(glossary)
                except Exception as e:
                    logger.warning(f"Failed to load glossary {path}: {e}")

    # Watermark mode
    watermark_mode_map = {
        "watermarked": WatermarkOutputMode.Watermarked,
        "no_watermark": WatermarkOutputMode.NoWatermark,
        "both": WatermarkOutputMode.Both,
    }
    watermark_mode = watermark_mode_map.get(
        s.pdf.watermark_mode, WatermarkOutputMode.Watermarked
    )

    # Split strategy
    split_strategy = None
    if s.pdf.max_pages_per_part:
        split_strategy = TranslationConfig.create_max_pages_per_part_split_strategy(
            s.pdf.max_pages_per_part
        )

    # Output directory
    output_dir = s.paths.output_dir or None
    working_dir = s.paths.working_dir or None

    # Process each file
    for file_info in ps.uploaded_files:
        if ps.cancel_event and ps.cancel_event.is_set():
            break

        ps.current_file = file_info["name"]
        ps.stage_label.set_text(f"正在处理: {file_info['name']}")

        pages = ps.pages_input.value if ps.pages_input.value else None

        config = TranslationConfig(
            input_file=file_info["path"],
            font=None,
            pages=pages,
            output_dir=output_dir,
            translator=translator,
            term_extraction_translator=term_extraction_translator,
            debug=False,
            lang_in=s.translation.lang_in,
            lang_out=s.translation.lang_out,
            no_dual=not s.pdf.output_dual,
            no_mono=not s.pdf.output_mono,
            qps=s.translation.qps,
            min_text_length=s.translation.min_text_length,
            formular_font_pattern=s.pdf.formular_font_pattern or None,
            formular_char_pattern=s.pdf.formular_char_pattern or None,
            split_short_lines=s.pdf.split_short_lines,
            short_line_split_factor=s.pdf.short_line_split_factor,
            doc_layout_model=doc_layout_model,
            skip_clean=s.pdf.skip_clean,
            dual_translate_first=s.pdf.dual_translate_first,
            disable_rich_text_translate=s.pdf.disable_rich_text_translate,
            enhance_compatibility=s.pdf.enhance_compatibility,
            use_alternating_pages_dual=s.pdf.use_alternating_pages_dual,
            watermark_output_mode=watermark_mode,
            split_strategy=split_strategy,
            skip_scanned_detection=s.pdf.skip_scanned_detection,
            ocr_workaround=s.pdf.ocr_workaround,
            custom_system_prompt=s.translation.custom_system_prompt or None,
            working_dir=working_dir,
            add_formula_placehold_hint=s.translation.add_formula_placehold_hint,
            disable_same_text_fallback=s.translation.disable_same_text_fallback,
            glossaries=loaded_glossaries,
            pool_max_workers=s.translation.pool_max_workers,
            auto_extract_glossary=s.translation.auto_extract_glossary,
            auto_enable_ocr_workaround=s.pdf.auto_enable_ocr_workaround,
            primary_font_family=s.pdf.primary_font_family,
            skip_form_render=s.pdf.skip_form_render,
            skip_curve_render=s.pdf.skip_curve_render,
            remove_non_formula_lines=s.pdf.remove_non_formula_lines,
            non_formula_line_iou_threshold=s.pdf.non_formula_line_iou_threshold,
            figure_table_protection_threshold=s.pdf.figure_table_protection_threshold,
            term_pool_max_workers=s.translation.term_pool_max_workers,
            save_auto_extracted_glossary=s.translation.save_auto_extracted_glossary,
            only_include_translated_page=s.pdf.only_include_translated_page,
            merge_alternating_line_numbers=s.pdf.merge_alternating_line_numbers,
            only_parse_generate_pdf=s.pdf.only_parse_generate_pdf,
        )

        # Run translation
        async for event in babeldoc.format.pdf.high_level.async_translate(config):
            if ps.cancel_event and ps.cancel_event.is_set():
                break

            if event["type"] == "progress_update":
                ps.progress = event["overall_progress"]
                ps.progress_bar.set_value(ps.progress / 100)
                ps.progress_label.set_text(f"{ps.progress:.0f}%")
                ps.stage = event["stage"]
                ps.stage_label.set_text(
                    f"{event['stage']} ({event['stage_current']}/{event['stage_total']})"
                )

            elif event["type"] == "error":
                ps.error = event.get("error", "Unknown error")
                ui.notify(f"错误: {ps.error}", type="negative")

            elif event["type"] == "finish":
                result = event["translate_result"]

                if result.mono_pdf_path:
                    ps.result_files.append(
                        {
                            "name": result.mono_pdf_path.name,
                            "path": str(result.mono_pdf_path),
                            "type": "单语 PDF",
                        }
                    )
                if result.dual_pdf_path:
                    ps.result_files.append(
                        {
                            "name": result.dual_pdf_path.name,
                            "path": str(result.dual_pdf_path),
                            "type": "双语 PDF",
                        }
                    )

                # 立即显示结果
                show_results(ps)
                ui.notify("翻译完成！", type="positive")

            # Allow UI to update
            await asyncio.sleep(0)


def cancel_translation(ps: PageState):
    """Cancel the ongoing translation."""
    if ps.cancel_event:
        ps.cancel_event.set()
    ui.notify("正在取消翻译...", type="warning")


def show_results(ps: PageState):
    """Display translation results with clean modern styling."""
    if not ps.result_files:
        return

    # 重置按钮状态
    ps.is_running = False
    ps.start_button.visible = True
    ps.cancel_button.visible = False

    # 显示结果卡片
    ps.results_card.visible = True
    ps.results_container.clear()

    with ps.results_container:
        for file_info in ps.result_files:
            with ui.row().classes(
                "result-item w-full items-center gap-3 p-4 bg-white rounded-lg "
                "border border-green-200 hover:border-green-400 hover:shadow-sm transition-all"
            ):
                ui.icon("check_circle", size="md").classes("text-green-600")
                ui.label(file_info["type"]).classes(
                    "bg-green-100 text-green-700 px-3 py-1 rounded-full text-xs font-semibold"
                )
                ui.label(file_info["name"]).classes(
                    "flex-1 font-medium text-gray-700 truncate"
                )

                # 使用闭包正确捕获 file_path
                file_path = file_info["path"]
                ui.button(
                    "下载",
                    icon="download",
                    on_click=lambda p=file_path: ui.download(p),
                ).props("flat").classes(
                    "text-green-600 hover:bg-green-100 font-semibold transition-colors duration-200"
                )


async def download_file(file_info: dict):
    """Download a result file."""
    path = Path(file_info["path"])
    if path.exists():
        ui.download(str(path))
    else:
        ui.notify("文件不存在", type="negative")


def create_app_for_client(ps: PageState):
    """Create and configure the NiceGUI application for a specific client."""
    # Add custom CSS with clean modern styling
    ui.add_head_html("""
    <style>
        /* Clean background */
        body {
            background: #f9fafb;
            min-height: 100vh;
        }
        .nicegui-content {
            padding-bottom: 2rem;
        }

        /* Smooth transitions for interactive elements */
        .q-btn {
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }

        /* Card styles */
        .q-card {
            transition: all 0.2s ease;
        }

        /* Input focus states */
        .q-field--focused .q-field__control {
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        }

        /* Upload area */
        .q-uploader {
            transition: border-color 0.2s ease, background-color 0.2s ease;
        }

        /* 美化上传区域 */
        .upload-area .q-uploader {
            border: 2px dashed #d1d5db;
            border-radius: 12px;
            background: #fafafa;
            min-height: 120px;
        }
        .upload-area .q-uploader:hover {
            border-color: #3b82f6;
            background: #eff6ff;
        }
        .upload-area .q-uploader__header {
            background: transparent;
            color: #6b7280;
        }
        /* 隐藏上传组件内部的文件列表 */
        .upload-area .q-uploader__list {
            display: none;
        }

        /* Simple scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #f3f4f6;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb {
            background: #d1d5db;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #9ca3af;
        }

        .q-tab-panel {
            min-height: 100%;
            padding-bottom: 1rem;
        }

        /* Active tab styling */
        .q-tab--active {
            font-weight: 600;
            background: rgba(37, 99, 235, 0.08);
            border-radius: 6px;
        }

        /* Dialog backdrop */
        .q-dialog__backdrop {
            backdrop-filter: blur(2px);
        }

        /* Checkbox and radio */
        .q-checkbox__inner, .q-radio__inner {
            transition: all 0.15s ease;
        }

        /* Expansion panel */
        .q-expansion-item {
            border-radius: 10px;
            overflow: hidden;
            transition: background-color 0.2s ease;
        }
        .q-expansion-item:hover {
            background: rgba(37, 99, 235, 0.02);
        }

        /* File item hover effect */
        .file-item {
            transition: all 0.2s ease;
            position: relative;
        }
        .file-item:hover {
            transform: translateX(2px);
        }
        .file-item::before {
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 3px;
            background: #2563eb;
            transform: scaleY(0);
            transition: transform 0.2s ease;
            border-radius: 0 2px 2px 0;
        }
        .file-item:hover::before {
            transform: scaleY(1);
        }

        /* Result item hover effect */
        .result-item {
            transition: all 0.2s ease;
            position: relative;
        }
        .result-item:hover {
            transform: translateX(2px);
        }
        .result-item::before {
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 3px;
            background: #059669;
            transform: scaleY(0);
            transition: transform 0.2s ease;
            border-radius: 0 2px 2px 0;
        }
        .result-item:hover::before {
            transform: scaleY(1);
        }

        /* Gentle float animation for header icon */
        @keyframes float {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-2px); }
        }
        .float-animation {
            animation: float 3s ease-in-out infinite;
        }
    </style>
    """)

    create_header()

    with ui.column().classes("w-full min-h-screen"):
        create_main_content(ps)

        # Footer
        with ui.row().classes(
            "w-full justify-center items-center mt-10 mb-6 text-gray-500 text-sm gap-2"
        ):
            ui.label("Powered by").classes("font-medium")
            ui.link("BabelDOC", "https://github.com/funstory-ai/BabelDOC").classes(
                "text-blue-600 hover:text-blue-700 font-semibold transition-colors duration-200"
            )
            ui.label("&").classes("font-medium")
            ui.link("NiceGUI", "https://nicegui.io").classes(
                "text-blue-600 hover:text-blue-700 font-semibold transition-colors duration-200"
            )


def run():
    """Run the application."""

    @ui.page("/")
    def index():
        # 每个页面实例创建自己的状态
        ps = PageState()
        create_app_for_client(ps)

    ui.run(
        title="BabelDOC WebUI",
        favicon="🔤",
        port=8080,
        reload=False,
    )
