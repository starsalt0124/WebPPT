# WebPPT (.wp) 文件规范 (Draft)

[English](WP_SPEC.md)

## 1. 简介
`.wp` (WebPPT) 是一种专为 PPT 生成设计的单文件组件格式，灵感来源于 Vue SFC (Single-File Component)。它将 PPT 的结构 (HTML)、样式 (CSS) 和 逻辑 (JS) 封装在一个文件中，旨在简化 PPT 的编写和维护过程。

## 2. 文件结构
一个标准的 `.wp` 文件由三个顶级代码块组成：

```html
<ppt>
  <!-- 幻灯片结构定义 -->
</ppt>

<style>
  /* 样式定义 */
</style>

<script>
  /* 可选：脚本逻辑 */
</script>
```

### 2.1 `<ppt>` 块
*   **作用**: 定义幻灯片的 HTML 结构。
*   **内容**: 包含一个或多个 `<ppt-page>` 标签。
*   **特性**: 支持自定义语法糖标签（见下文），编译器会在预处理阶段将其转换为带有 `data-ppt-render` 属性的标准 HTML。

### 2.2 `<style>` 块
*   **作用**: 定义全局 CSS 样式。
*   **特性**: 
    *   默认作用于整个文档。
    *   支持标准 CSS 语法。
    *   (未来规划) 可支持 `lang="scss"` 或 `scoped`。

### 2.3 `<script>` 块 (可选)
*   **作用**: 定义页面运行时的 JavaScript 逻辑。
*   **场景**: 用于动态生成图表 (ECharts/Chart.js)、动态填充数据或控制复杂的 DOM 操作。
*   **执行时机**: 在 Playwright 页面加载时执行。

## 3. 核心标签与语法糖
为了简化编写，`.wp` 格式引入了一组语义化标签，编译器负责将其转换为底层渲染引擎识别的 HTML。

| 标签 | 编译后 HTML | 描述 |
| :--- | :--- | :--- |
| `<ppt-page>` | `<section class="slide">` | 定义一页幻灯片容器。 |
| `<ppt-text>` | `<div data-ppt-render="text">` | 定义可编辑文本块。 |
| `<ppt-shape>` | `<div data-ppt-render="shape">` | 定义原生形状 (矩形/圆形)。 |
| `<ppt-image>` | `<div data-ppt-render="image">` | 定义复杂组件截图区域 (或直接包裹 `<img>`)。 |
| `<ppt-table>` | `<table data-ppt-render="table">` | 定义表格。 |

> **注意**: 对于带有复杂样式（如渐变、阴影、滤镜）或**半透明效果**的元素，建议使用 `<ppt-image>` 标签。编译器会将该区域整体截图作为图片插入 PPT，以确保视觉效果与网页完全一致。

> **重要提示**: `<ppt-text>` 标签目前仅支持基础属性（颜色、字体、加粗）。如果您需要渲染**文字卡片**（例如带有背景色、边框或阴影的文本块），请勿直接将这些内容放入 `<ppt-text>` 中。相反，您应该使用 `<ppt-image>` 标签将其作为图片处理。

### 3.1 属性透传
所有在自定义标签上定义的标准 HTML 属性 (如 `class`, `style`, `id`) 都会原样透传给编译后的标签。

**示例**:
```html
<ppt-text class="title" style="color: red;">Hello</ppt-text>
```
**编译为**:
```html
<div data-ppt-render="text" class="title" style="color: red;">Hello</div>
```

## 4. 示例文件 (`example.wp`)

```html
<ppt>
  <!-- 第一页 -->
  <ppt-page>
    <div class="layout-center">
      <ppt-text class="main-title">WebPPT 2.0</ppt-text>
      <ppt-text class="subtitle">基于 .wp 文件的下一代 PPT 生成工具</ppt-text>
      
      <!-- 形状示例 -->
      <div class="shapes">
        <ppt-shape class="circle"></ppt-shape>
        <ppt-shape class="rect"></ppt-shape>
      </div>
    </div>
  </ppt-page>

  <!-- 第二页 -->
  <ppt-page>
    <ppt-text class="slide-title">复杂组件截图</ppt-text>
    <!-- 这个卡片会被整体截图 -->
    <ppt-image class="card">
      <h2>动态卡片</h2>
      <p>这里的样式非常复杂...</p>
    </ppt-image>
  </ppt-page>
</ppt>

<style>
  /* 全局样式 */
  body { font-family: 'Microsoft YaHei', sans-serif; }
  
  .layout-center {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
  }

  .main-title { font-size: 60px; font-weight: bold; color: #333; }
  .subtitle { font-size: 32px; color: #666; margin-top: 20px; }

  .shapes { display: flex; gap: 20px; margin-top: 40px; }
  .circle { width: 50px; height: 50px; background: red; border-radius: 50%; }
  .rect { width: 50px; height: 50px; background: blue; }

  .card {
    background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
    padding: 40px;
    border-radius: 20px;
    box-shadow: 0 10px 20px rgba(0,0,0,0.2);
  }
</style>
```

## 5. 编译流程
1.  **读取**: 读取 `.wp` 文件内容。
2.  **解析**: 使用正则或 HTML 解析器分离 `<ppt>`, `<style>`, `<script>` 块。
3.  **转换**: 
    *   将 `<ppt>` 中的自定义标签 (`<ppt-*>`) 替换为对应的标准 HTML 标签。
    *   将 `<style>` 内容注入到 HTML `<head><style>...</style></head>` 中。
    *   将 `<script>` 内容注入到 HTML `<body><script>...</script></body>` 中。
4.  **包装**: 添加标准的 HTML5 Boilerplate (`<html>`, `<head>`, `<body>`)。
5.  **输出**: 生成临时 `.html` 文件，供 Playwright 渲染。

## 6. 布局约束与最佳实践
### 6.1 尺寸限制
*   **画布尺寸**: 默认 PPT 画布尺寸固定为 **1280px x 720px** (16:9)。
*   **溢出警告**: 任何超出此范围的元素（x + width > 1280 或 y + height > 720）在生成 PPT 时可能会被裁剪或导致布局错乱。控制台会输出 `WARNING: Element ... is out of bounds!` 警告。
*   **建议**: 
    *   在 CSS 中显式设置 `.slide` 的尺寸为 `1280px` x `720px` 并使用 `overflow: hidden` 进行预览。
    *   避免使用绝对定位将元素放置在画布外。

### 6.2 文本排版
*   **文本框宽度**: 为了防止 PPT 中的字体渲染差异导致意外换行，生成器会自动将文本框宽度增加 **20%**。
*   **对齐**: 建议显式设置 `text-align` (left/center/right)，生成器会根据对齐方式自动调整文本框的锚点位置，确保视觉位置不变。

