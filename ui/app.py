"""BabelDOC WebUI - Main Application."""

import asyncio
import logging
import tempfile
from pathlib import Path

from nicegui import ui, events

from ui.components.settings import settings_manager

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

# Model options
MODELS = [
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-4-turbo",
    "gpt-3.5-turbo",
    "deepseek-chat",
    "glm-4-flash",
    "claude-3-5-sonnet-20241022",
]


class TranslationState:
    """State management for translation process."""

    def __init__(self):
        self.is_running = False
        self.current_file: str | None = None
        self.progress: float = 0
        self.stage: str = ""
        self.stage_progress: str = ""
        self.result_files: list[dict] = []
        self.error: str | None = None
        self.cancel_event: asyncio.Event | None = None


state = TranslationState()


def create_header():
    """Create the application header with clean modern styling."""
    with ui.header().classes("bg-blue-600 shadow-md"):
        with ui.row().classes("w-full items-center justify-between px-8 py-4"):
            with ui.row().classes("items-center gap-5"):
                ui.icon("translate", size="2rem").classes("text-white float-animation")
                with ui.column().classes("gap-0"):
                    ui.label("BabelDOC").classes(
                        "text-2xl font-bold text-white tracking-tight"
                    )
                    ui.label("AI 驱动的 PDF 翻译工具").classes(
                        "text-xs text-white/90 font-medium"
                    )
                ui.label("v0.1.0").classes(
                    "text-xs text-white font-semibold bg-white/20 "
                    "px-3 py-1 rounded-full"
                )

            ui.button(
                icon="settings",
                on_click=lambda: settings_dialog.open(),
            ).props("flat round size=md").classes(
                "text-white hover:bg-white/20 transition-colors duration-200"
            )


def create_settings_dialog() -> ui.dialog:
    """Create the settings dialog with clean modern styling."""
    with (
        ui.dialog() as dialog,
        ui.card().classes(
            "w-full max-w-4xl rounded-xl shadow-lg border border-gray-200 p-8"
        ),
    ):
        with ui.row().classes("w-full items-center justify-between mb-6"):
            ui.label("设置").classes("text-2xl font-bold text-gray-900")
            ui.button(icon="close", on_click=dialog.close).props("flat round").classes(
                "hover:bg-gray-100 transition-colors duration-200"
            )

        with ui.tabs().classes("w-full") as tabs:
            openai_tab = ui.tab("OpenAI 配置", icon="key")
            translation_tab = ui.tab("翻译设置", icon="translate")
            pdf_tab = ui.tab("PDF 处理", icon="picture_as_pdf")
            advanced_tab = ui.tab("高级选项", icon="tune")

        with ui.tab_panels(tabs, value=openai_tab).classes("w-full"):
            with ui.tab_panel(openai_tab):
                create_openai_settings()

            with ui.tab_panel(translation_tab):
                create_translation_settings()

            with ui.tab_panel(pdf_tab):
                create_pdf_settings()

            with ui.tab_panel(advanced_tab):
                create_advanced_settings()

        with ui.row().classes("w-full justify-end mt-6 gap-3"):
            ui.button("取消", on_click=dialog.close).props("outline").classes(
                "px-8 text-gray-700 hover:bg-gray-50 transition-colors"
            )
            ui.button("保存", on_click=lambda: save_settings(dialog)).classes(
                "px-10 bg-blue-600 text-white hover:bg-blue-700 shadow-md hover:shadow-lg transition-all"
            )

    return dialog


def create_openai_settings():
    """Create OpenAI settings panel with enhanced styling."""
    s = settings_manager.settings

    with ui.row().classes("items-center gap-2 mb-3"):
        ui.icon("vpn_key", size="sm").classes("text-blue-600")
        ui.label("基础配置").classes("text-lg font-semibold text-gray-800")
    with ui.column().classes("w-full gap-3"):
        ui.input(
            "API Key",
            value=s.openai.api_key,
            password=True,
            password_toggle_button=True,
        ).classes("w-full").bind_value(s.openai, "api_key")

        ui.input("Base URL", value=s.openai.base_url).classes("w-full").bind_value(
            s.openai, "base_url"
        )

        with ui.row().classes("w-full gap-4"):
            ui.select(
                MODELS,
                label="模型",
                value=s.openai.model,
                with_input=True,
                new_value_mode="add-unique",
            ).classes("flex-1").bind_value(s.openai, "model")

    ui.separator().classes("my-5")
    with ui.row().classes("items-center gap-2 mb-3"):
        ui.icon("auto_awesome", size="sm").classes("text-blue-600")
        ui.label("术语提取配置 (可选)").classes("text-lg font-semibold text-gray-800")

    with ui.expansion("展开术语提取配置", icon="expand_more").classes(
        "w-full border border-gray-200 rounded-xl hover:border-purple-300 transition-all duration-200"
    ):
        with ui.column().classes("w-full gap-3 p-2"):
            ui.input(
                "术语提取 API Key (留空使用主 API Key)",
                value=s.openai.term_extraction_api_key,
                password=True,
            ).classes("w-full").bind_value(s.openai, "term_extraction_api_key")

            ui.input(
                "术语提取 Base URL (留空使用主 URL)",
                value=s.openai.term_extraction_base_url,
            ).classes("w-full").bind_value(s.openai, "term_extraction_base_url")

            ui.select(
                [""] + MODELS,
                label="术语提取模型 (留空使用主模型)",
                value=s.openai.term_extraction_model,
                with_input=True,
                new_value_mode="add-unique",
            ).classes("w-full").bind_value(s.openai, "term_extraction_model")

    ui.separator().classes("my-5")
    with ui.row().classes("items-center gap-2 mb-3"):
        ui.icon("tune", size="sm").classes("text-blue-600")
        ui.label("高级选项").classes("text-lg font-semibold text-gray-800")

    with ui.row().classes("w-full gap-4 flex-wrap"):
        ui.checkbox("启用 JSON 模式", value=s.openai.enable_json_mode).bind_value(
            s.openai, "enable_json_mode"
        )
        ui.checkbox(
            "发送 DashScope Header", value=s.openai.send_dashscope_header
        ).bind_value(s.openai, "send_dashscope_header")
        ui.checkbox(
            "不发送 Temperature", value=s.openai.no_send_temperature
        ).bind_value(s.openai, "no_send_temperature")


def create_translation_settings():
    """Create translation settings panel with enhanced styling."""
    s = settings_manager.settings

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

    ui.separator().classes("my-5")
    with ui.row().classes("items-center gap-2 mb-3"):
        ui.icon("settings_suggest", size="sm").classes("text-blue-600")
        ui.label("翻译选项").classes("text-lg font-semibold text-gray-800")

    with ui.column().classes("w-full gap-2"):
        ui.checkbox(
            "自动提取术语表", value=s.translation.auto_extract_glossary
        ).bind_value(s.translation, "auto_extract_glossary")
        ui.checkbox(
            "禁用相同文本回退翻译", value=s.translation.disable_same_text_fallback
        ).bind_value(s.translation, "disable_same_text_fallback")
        ui.checkbox(
            "添加公式占位符提示", value=s.translation.add_formula_placehold_hint
        ).bind_value(s.translation, "add_formula_placehold_hint")

    ui.textarea("自定义系统提示词", value=s.translation.custom_system_prompt).classes(
        "w-full mt-2"
    ).bind_value(s.translation, "custom_system_prompt")


def create_pdf_settings():
    """Create PDF settings panel with enhanced styling."""
    s = settings_manager.settings

    with ui.row().classes("items-center gap-2 mb-3"):
        ui.icon("output", size="sm").classes("text-blue-600")
        ui.label("输出设置").classes("text-lg font-semibold text-gray-800")

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

    ui.separator().classes("my-5")
    with ui.row().classes("items-center gap-2 mb-3"):
        ui.icon("build", size="sm").classes("text-blue-600")
        ui.label("兼容性设置").classes("text-lg font-semibold text-gray-800")

    with ui.column().classes("w-full gap-2"):
        ui.checkbox(
            "增强兼容性模式 (等于同时启用下面三个选项)",
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

    ui.separator().classes("my-5")
    with ui.row().classes("items-center gap-2 mb-3"):
        ui.icon("auto_stories", size="sm").classes("text-blue-600")
        ui.label("双语 PDF 布局").classes("text-lg font-semibold text-gray-800")

    ui.checkbox(
        "使用交替页面模式 (原文/译文交替排列)", value=s.pdf.use_alternating_pages_dual
    ).bind_value(s.pdf, "use_alternating_pages_dual")

    ui.separator().classes("my-5")
    with ui.row().classes("items-center gap-2 mb-3"):
        ui.icon("document_scanner", size="sm").classes("text-blue-600")
        ui.label("扫描文档处理").classes("text-lg font-semibold text-gray-800")

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


def create_advanced_settings():
    """Create advanced settings panel with enhanced styling."""
    s = settings_manager.settings

    with ui.row().classes("items-center gap-2 mb-3"):
        ui.icon("view_module", size="sm").classes("text-blue-600")
        ui.label("分段处理").classes("text-lg font-semibold text-gray-800")

    ui.number(
        "每部分最大页数 (留空不分段)", value=s.pdf.max_pages_per_part, min=1
    ).classes("w-full").bind_value(s.pdf, "max_pages_per_part")

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

    ui.separator().classes("my-5")
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


def create_main_content():
    """Create the main content area with sidebar layout."""
    with ui.row().classes("w-full max-w-7xl mx-auto px-8 py-8 gap-8 items-start"):
        # Left sidebar - Translation options only (fixed width)
        with ui.column().classes("w-80 gap-6 flex-shrink-0"):
            create_options_section()

        # Right content - File upload, buttons, progress, results (flexible width)
        with ui.column().classes("flex-1 gap-6 min-w-0"):
            create_upload_section()
            create_action_buttons()
            create_progress_section()
            create_results_section()


def create_upload_section():
    """Create file upload section with clean modern styling."""
    with ui.card().classes("w-full rounded-xl shadow-sm border border-gray-200 bg-white"):
        with ui.row().classes("items-center gap-3 mb-5 pb-4 border-b border-gray-100"):
            ui.icon("cloud_upload", size="md").classes("text-blue-600")
            ui.label("上传 PDF 文件").classes("text-xl font-semibold text-gray-900")

        upload_container = ui.column().classes("w-full")

        with upload_container:
            ui.upload(
                label="拖拽或点击上传 PDF 文件",
                multiple=True,
                on_upload=handle_file_upload,
                auto_upload=True,
            ).props('accept=".pdf"').classes(
                "w-full h-48 border-2 border-dashed border-gray-300 rounded-xl "
                "hover:border-blue-500 hover:bg-blue-50/30 transition-colors"
            )

        # File list display
        global file_list_container
        file_list_container = ui.column().classes("w-full mt-5 gap-3")


uploaded_files: list[dict] = []


async def handle_file_upload(e: events.UploadEventArguments):
    """Handle file upload event."""
    # Save uploaded file to temp directory
    temp_dir = Path(tempfile.gettempdir()) / "babeldoc-webui"
    temp_dir.mkdir(exist_ok=True)

    file_path = temp_dir / e.name
    with open(file_path, "wb") as f:
        f.write(e.content.read())

    uploaded_files.append({"name": e.name, "path": str(file_path)})
    update_file_list()
    ui.notify(f"已上传: {e.name}", type="positive")


def update_file_list():
    """Update the file list display with clean modern styling."""
    file_list_container.clear()
    with file_list_container:
        if uploaded_files:
            for i, file_info in enumerate(uploaded_files):
                with ui.row().classes(
                    "file-item w-full items-center gap-3 p-4 bg-gray-50 rounded-lg "
                    "border border-gray-200 hover:border-blue-300 hover:bg-white transition-all"
                ):
                    ui.icon("picture_as_pdf", size="md").classes("text-red-500")
                    ui.label(file_info["name"]).classes(
                        "flex-1 font-medium text-gray-700 truncate"
                    )
                    ui.button(
                        icon="delete",
                        on_click=lambda idx=i: remove_file(idx),
                    ).props("flat round dense").classes(
                        "text-red-500 hover:bg-red-50 transition-colors duration-200"
                    )


def remove_file(index: int):
    """Remove a file from the upload list."""
    if 0 <= index < len(uploaded_files):
        file_info = uploaded_files.pop(index)
        # Delete temp file
        try:
            Path(file_info["path"]).unlink(missing_ok=True)
        except Exception:
            pass
        update_file_list()


def create_options_section():
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

            # Model selection
            ui.select(
                MODELS,
                label="翻译模型",
                value=s.openai.model,
                with_input=True,
                new_value_mode="add-unique",
            ).classes("w-full").bind_value(s.openai, "model")

            # Page range input
            global pages_input
            pages_input = ui.input(
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


def create_action_buttons():
    """Create action buttons section below upload area."""
    with ui.row().classes("w-full gap-4 justify-center"):
        global start_button, cancel_button

        start_button = (
            ui.button(
                "开始翻译",
                icon="play_arrow",
                on_click=start_translation,
            )
            .props("size=lg")
            .classes(
                "px-16 py-3 bg-blue-600 text-white hover:bg-blue-700 shadow-md hover:shadow-lg "
                "font-semibold text-base transition-all duration-200"
            )
        )

        cancel_button = (
            ui.button(
                "取消翻译",
                icon="stop",
                on_click=cancel_translation,
            )
            .props("size=lg outline")
            .classes(
                "px-16 py-3 border-2 border-gray-300 text-gray-700 hover:bg-gray-50 "
                "font-semibold text-base transition-colors duration-200"
            )
        )
        cancel_button.set_visibility(False)


def create_progress_section():
    """Create progress display section with clean modern styling."""
    global progress_card, progress_bar, progress_label, stage_label

    progress_card = ui.card().classes(
        "w-full rounded-xl shadow-sm border border-blue-200 bg-blue-50/50"
    )
    progress_card.set_visibility(False)

    with progress_card:
        with ui.row().classes("items-center gap-3 mb-5 pb-4 border-b border-blue-100"):
            ui.icon("autorenew", size="md").classes("text-blue-600")
            ui.label("翻译进度").classes("text-xl font-semibold text-gray-900")

        with ui.column().classes("w-full gap-4"):
            progress_bar = ui.linear_progress(value=0, show_value=False).classes(
                "w-full h-2 rounded-full"
            )
            progress_label = ui.label("0%").classes(
                "text-center w-full text-3xl font-bold text-blue-600"
            )
            with ui.row().classes("items-center justify-center gap-2 w-full"):
                ui.icon("info", size="sm").classes("text-gray-500")
                stage_label = ui.label("准备中...").classes(
                    "text-base text-gray-600 font-medium"
                )


def create_results_section():
    """Create results display section with clean modern styling."""
    global results_card, results_container

    results_card = ui.card().classes(
        "w-full rounded-xl shadow-sm border border-green-200 bg-green-50/50"
    )
    results_card.set_visibility(False)

    with results_card:
        with ui.row().classes("items-center gap-3 mb-5 pb-4 border-b border-green-100"):
            ui.icon("check_circle", size="md").classes("text-green-600")
            ui.label("翻译完成").classes("text-xl font-semibold text-gray-900")
        results_container = ui.column().classes("w-full gap-3")


async def start_translation():
    """Start the translation process."""
    s = settings_manager.settings

    # Validate settings
    if not s.openai.api_key:
        ui.notify("请先在设置中配置 OpenAI API Key", type="negative")
        return

    if not uploaded_files:
        ui.notify("请先上传 PDF 文件", type="negative")
        return

    # Update UI state
    state.is_running = True
    state.progress = 0
    state.result_files = []
    state.error = None
    state.cancel_event = asyncio.Event()

    start_button.set_visibility(False)
    cancel_button.set_visibility(True)
    progress_card.set_visibility(True)
    results_card.set_visibility(False)

    try:
        await run_translation()
    except Exception as e:
        logger.exception("Translation error")
        state.error = str(e)
        ui.notify(f"翻译出错: {e}", type="negative")
    finally:
        state.is_running = False
        start_button.set_visibility(True)
        cancel_button.set_visibility(False)

        if state.result_files:
            show_results()


async def run_translation():
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

    # Initialize BabelDOC
    babeldoc.format.pdf.high_level.init()

    # Create translator
    translator_kwargs = {}
    if s.openai.reasoning:
        translator_kwargs["reasoning"] = s.openai.reasoning

    translator = OpenAITranslator(
        lang_in=s.translation.lang_in,
        lang_out=s.translation.lang_out,
        model=s.openai.model,
        base_url=s.openai.base_url or None,
        api_key=s.openai.api_key,
        ignore_cache=False,
        enable_json_mode_if_requested=s.openai.enable_json_mode,
        send_dashscope_header=s.openai.send_dashscope_header,
        send_temperature=not s.openai.no_send_temperature,
        **translator_kwargs,
    )

    # Create term extraction translator if configured
    term_extraction_translator = translator
    if (
        s.openai.term_extraction_model
        or s.openai.term_extraction_base_url
        or s.openai.term_extraction_api_key
    ):
        term_kwargs = {}
        if s.openai.term_extraction_reasoning:
            term_kwargs["reasoning"] = s.openai.term_extraction_reasoning

        term_extraction_translator = OpenAITranslator(
            lang_in=s.translation.lang_in,
            lang_out=s.translation.lang_out,
            model=s.openai.term_extraction_model or s.openai.model,
            base_url=s.openai.term_extraction_base_url or s.openai.base_url or None,
            api_key=s.openai.term_extraction_api_key or s.openai.api_key,
            ignore_cache=False,
            enable_json_mode_if_requested=s.openai.enable_json_mode,
            send_dashscope_header=s.openai.send_dashscope_header,
            send_temperature=not s.openai.no_send_temperature,
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
    for file_info in uploaded_files:
        if state.cancel_event and state.cancel_event.is_set():
            break

        state.current_file = file_info["name"]
        stage_label.set_text(f"正在处理: {file_info['name']}")

        pages = pages_input.value if pages_input.value else None

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
        )

        # Run translation
        async for event in babeldoc.format.pdf.high_level.async_translate(config):
            if state.cancel_event and state.cancel_event.is_set():
                break

            if event["type"] == "progress_update":
                state.progress = event["overall_progress"]
                progress_bar.set_value(state.progress / 100)
                progress_label.set_text(f"{state.progress:.0f}%")
                state.stage = event["stage"]
                stage_label.set_text(
                    f"{event['stage']} ({event['stage_current']}/{event['stage_total']})"
                )

            elif event["type"] == "error":
                state.error = event.get("error", "Unknown error")
                ui.notify(f"错误: {state.error}", type="negative")

            elif event["type"] == "finish":
                result = event["translate_result"]
                if result.mono_pdf_path:
                    state.result_files.append(
                        {
                            "name": result.mono_pdf_path.name,
                            "path": str(result.mono_pdf_path),
                            "type": "单语 PDF",
                        }
                    )
                if result.dual_pdf_path:
                    state.result_files.append(
                        {
                            "name": result.dual_pdf_path.name,
                            "path": str(result.dual_pdf_path),
                            "type": "双语 PDF",
                        }
                    )

            # Allow UI to update
            await asyncio.sleep(0)


def cancel_translation():
    """Cancel the ongoing translation."""
    if state.cancel_event:
        state.cancel_event.set()
    ui.notify("正在取消翻译...", type="warning")


def show_results():
    """Display translation results with clean modern styling."""
    results_card.set_visibility(True)
    results_container.clear()

    with results_container:
        for file_info in state.result_files:
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
                ui.button(
                    "下载",
                    icon="download",
                    on_click=lambda f=file_info: download_file(f),
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


# Global UI elements
settings_dialog: ui.dialog = None
file_list_container: ui.column = None
pages_input: ui.input = None
start_button: ui.button = None
cancel_button: ui.button = None
progress_card: ui.card = None
progress_bar: ui.linear_progress = None
progress_label: ui.label = None
stage_label: ui.label = None
results_card: ui.card = None
results_container: ui.column = None


def create_app():
    """Create and configure the NiceGUI application."""
    global settings_dialog

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
    settings_dialog = create_settings_dialog()

    with ui.column().classes("w-full min-h-screen"):
        create_main_content()

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
    create_app()
    ui.run(
        title="BabelDOC WebUI",
        favicon="🔤",
        port=8080,
        reload=False,
    )
