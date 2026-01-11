"""简单的UI测试页面 - 验证新样式是否生效"""

from nicegui import ui

ui.add_head_html("""
<style>
    body {
        background: #f9fafb;
    }
</style>
""")

# Header - 应该是纯蓝色，不是渐变
with ui.header().classes("bg-blue-600 shadow-md"):
    with ui.row().classes("w-full items-center px-8 py-4"):
        ui.icon("translate", size="2rem").classes("text-white")
        ui.label("BabelDOC - 简约现代风格测试").classes("text-2xl font-bold text-white")

with ui.column().classes("w-full max-w-5xl mx-auto px-8 py-8 gap-8"):
    # 测试卡片 - 应该是白色背景，轻阴影
    with ui.card().classes("w-full rounded-xl shadow-sm border border-gray-200 bg-white"):
        with ui.row().classes("items-center gap-3 mb-5 pb-4 border-b border-gray-100"):
            ui.icon("cloud_upload", size="md").classes("text-blue-600")
            ui.label("测试卡片 - 应该是白色背景").classes("text-xl font-semibold text-gray-900")

        ui.label("如果你看到：").classes("mb-3")
        ui.label("✅ Header 是纯蓝色（不是渐变）").classes("text-green-600")
        ui.label("✅ 背景是浅灰色（不是彩虹渐变）").classes("text-green-600")
        ui.label("✅ 卡片是白色，阴影很轻").classes("text-green-600")
        ui.label("✅ 图标都是蓝色").classes("text-green-600")
        ui.label("✅ 按钮是纯蓝色（不是渐变）").classes("text-green-600 mb-4")
        ui.label("那么新样式已经生效！").classes("font-bold text-lg")

    # 测试按钮
    with ui.row().classes("gap-4 mt-4"):
        ui.button("主要按钮", icon="play_arrow").classes(
            "px-12 py-3 bg-blue-600 text-white hover:bg-blue-700 shadow-md"
        )
        ui.button("次要按钮", icon="close").props("outline").classes(
            "px-12 py-3 border-2 border-gray-300 text-gray-700 hover:bg-gray-50"
        )

ui.run(title="UI测试", port=8081)
