# BabelDOC WebUI

基于 [NiceGUI](https://nicegui.io/) 构建的 [BabelDOC](https://github.com/funstory-ai/BabelDOC) Web 界面，让 PDF 文档翻译更简单。

## 功能特点

- 简洁直观的 Web 界面
- 支持多种 AI 服务商（OpenAI、DeepSeek、智谱 GLM、Claude、Ollama 等）
- 实时翻译进度显示
- 灵活的输出选项（双语对照 / 纯译文）
- 设置自动保存和持久化

## 界面预览

![BabelDOC WebUI](assets/screenshot.png)

## 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/ChenjieXu/BabelDOC-WebUI.git
cd BabelDOC-WebUI

# 安装依赖
uv sync

# 运行应用
uv run python main.py
```

访问 http://localhost:8080 即可使用。

### 配置模型

1. 点击右上角「设置」按钮
2. 选择服务商（如智谱 GLM）
3. 添加模型配置，填入 API Key（推荐免费的glm-4-flash-250414）
4. 保存并选择模型

## 推荐模型

### 智谱 GLM-4-Flash（推荐）

**配置方式：**

1. 前往 [智谱开放平台](https://open.bigmodel.cn/) 注册并获取 API Key
2. 在设置中选择「智谱 GLM」服务商
3. 添加模型，选择 `glm-4-flash-250414`
4. 填入 API Key 并保存

## 输出选项

- **双语对照 PDF**：原文和译文并排显示
- **纯译文 PDF**：仅显示翻译后的内容
- **水印模式**：可选择是否添加水印

## 高级设置

- **QPS 限制**：控制 API 调用频率
- **术语表**：支持自定义术语翻译
- **OCR 模式**：处理扫描版 PDF

## 配置文件

设置保存在 `~/.config/babeldoc-webui/settings.json`

## 许可证

AGPL-3.0 License

本项目基于 [BabelDOC](https://github.com/funstory-ai/BabelDOC)，遵循 AGPL-3.0 许可证。