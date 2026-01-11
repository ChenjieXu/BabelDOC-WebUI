# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BabelDOC WebUI is a NiceGUI-based web interface for BabelDOC, a PDF document translation tool that uses OpenAI-compatible APIs to translate scientific papers and generate bilingual PDFs.

## Commands

```bash
# Install dependencies
uv sync

# Run the application (starts on http://localhost:8080)
uv run python main.py

# Lint code
uv run ruff check ui/ main.py

# Format code
uv run ruff format ui/ main.py
```

## Architecture

```
babeldoc-webui/
├── main.py                    # Entry point, configures logging and multiprocessing
├── ui/
│   ├── app.py                 # Main NiceGUI application with all UI components
│   └── components/
│       └── settings.py        # Settings dataclasses and persistence manager
└── BabelDOC/                  # BabelDOC library (git submodule or local)
```

### Key Components

**Settings Management** (`ui/components/settings.py`):
- Dataclass-based settings: `OpenAISettings`, `TranslationSettings`, `PDFSettings`, `RPCSettings`, `PathSettings`
- `SettingsManager` handles JSON persistence to `~/.config/babeldoc-webui/settings.json`
- Settings bind directly to NiceGUI elements via `bind_value()`

**Main Application** (`ui/app.py`):
- `TranslationState` class manages translation process state
- Global UI elements (dialogs, buttons, progress indicators) declared at module level
- `run_translation()` is an async function that streams progress events from BabelDOC
- Settings dialog has 4 tabs: OpenAI配置, 翻译设置, PDF处理, 高级选项

### BabelDOC Integration

The WebUI creates a `TranslationConfig` object and calls `babeldoc.format.pdf.high_level.async_translate()` which yields progress events:
- `progress_update`: Contains `overall_progress`, `stage`, `stage_current`, `stage_total`
- `error`: Contains error message
- `finish`: Contains `translate_result` with output paths

Key BabelDOC classes used:
- `OpenAITranslator` from `babeldoc.translator.translator`
- `TranslationConfig`, `WatermarkOutputMode` from `babeldoc.format.pdf.translation_config`
- `DocLayoutModel` from `babeldoc.docvision.doclayout` (or RPC variants)

## UI Framework Notes

- Uses NiceGUI (Vue + Tailwind CSS under the hood)
- UI elements use method chaining: `ui.input(...).classes(...).bind_value(...)`
- Dialog/card context managers: `with ui.dialog() as dialog, ui.card():`
- Visibility controlled via `element.set_visibility(bool)`

## Configuration Reference

The UI exposes all major BabelDOC options. See `BabelDOC/README.md` for full documentation of:
- OpenAI API options (model, base_url, api_key, term extraction settings)
- PDF processing options (watermark mode, compatibility flags, OCR settings)
- Translation options (QPS, thread pools, glossary support)
