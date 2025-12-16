# WebPPT

WebPPT 是一个将 HTML 或自定义 `.wp` (WebPPT) 文件转换为 PowerPoint (`.pptx`) 演示文稿的工具。它利用 Playwright 进行渲染，并使用 `python-pptx` 生成 PPT 文件，旨在简化 PPT 的编写和维护过程。

[English](../README.md) | 中文

## 背景与初衷

大语言模型 (LLM) 在生成网页代码 (HTML/CSS) 方面表现出色，但直接创建 PowerPoint 文件却并非其强项。现有的 AI PPT 生成工具往往依赖于固定的模板，导致生成的演示文稿不够美观，或者难以契合特定的主题。

WebPPT 旨在利用大模型强大的网页生成能力来解决这一问题。它允许你使用 AI 生成美观、定制化的网页幻灯片，然后将其转换为可编辑的原生 PowerPoint 文件。

> **提示**: 想要让大模型生成符合要求的 `.wp` 文件，请将 [WP_SPEC_zh.md](WP_SPEC_zh.md) 规范文档提供给它作为上下文。

## 特性

- **.wp 单文件组件**: 类似于 Vue SFC，将结构、样式和逻辑封装在一个文件中。
- **HTML 支持**: 直接支持将 HTML 文件转换为 PPT。
- **智能渲染**: 支持多种渲染模式，能够提取文本、形状、图片和表格。
- **样式保留**: 尽可能保留 CSS 样式到 PPT 中。

## 安装

1. 克隆仓库：
   ```bash
   git clone <repository-url>
   cd webppt
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 安装 Playwright 浏览器：
   ```bash
   playwright install
   ```

## 使用方法

### 命令行工具

运行 `src/main.py` 来转换文件：

```bash
python src/main.py [input_file] [-o output_file] [-m render_mode]
```

- `input_file`: 输入文件路径，可以是 `.html` 或 `.wp` 文件。默认为 `input/slide.html`。
- `-o output_file`: 输出 `.pptx` 文件路径。默认为 `output/presentation.pptx`。
- `-m render_mode`: 渲染模式 (1: Minimal, 2: Smart [默认], 3: Maximal)。

### 示例

转换默认示例：
```bash
python src/main.py
```

转换指定的 `.wp` 文件：
```bash
python src/main.py input/test.wp -o output/test.pptx
```

## .wp 文件规范

`.wp` 文件由三个部分组成：

```html
<ppt>
  <!-- 幻灯片结构 -->
  <ppt-page>
     <ppt-text>Hello World</ppt-text>
  </ppt-page>
</ppt>

<style>
  /* CSS 样式 */
  .slide { background: white; }
</style>

<script>
  /* JS 逻辑 */
</script>
```

更多详情请参考 [WP_SPEC_zh.md](docs/WP_SPEC_zh.md)。

## 目录结构

- `src/`: 源代码目录
- `demo/`: 输入文件示例
- `docs/`: 文档目录

## 许可证

[MIT License](LICENSE)
