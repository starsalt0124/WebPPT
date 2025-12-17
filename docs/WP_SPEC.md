# WebPPT (.wp) File Specification (Draft)

[中文文档](WP_SPEC_zh.md)

## 1. Introduction
`.wp` (WebPPT) is a single-file component format designed specifically for PPT generation, inspired by Vue SFC (Single-File Component). It encapsulates the structure (HTML), style (CSS), and logic (JS) of a presentation in a single file, aiming to simplify the writing and maintenance of PPTs.

## 2. File Structure
A standard `.wp` file consists of three top-level code blocks:

```html
<ppt>
  <!-- Slide structure definition -->
</ppt>

<style>
  /* Style definition */
</style>

<script>
  /* Optional: Script logic */
</script>
```

### 2.1 `<ppt>` Block
*   **Purpose**: Defines the HTML structure of the slides.
*   **Content**: Contains one or more `<ppt-page>` tags.
*   **Features**: Supports custom syntactic sugar tags (see below), which the compiler converts into standard HTML with `data-ppt-render` attributes during the preprocessing stage.

### 2.2 `<style>` Block
*   **Purpose**: Defines global CSS styles.
*   **Features**: 
    *   Applies to the entire document by default.
    *   Supports standard CSS syntax.
    *   (Future Plan) Support for `lang="scss"` or `scoped`.

### 2.3 `<script>` Block (Optional)
*   **Purpose**: Defines runtime JavaScript logic for the page.
*   **Scenarios**: Used for dynamically generating charts (ECharts/Chart.js), populating data, or controlling complex DOM operations.
*   **Execution Timing**: Executed when the Playwright page loads.

## 3. Core Tags and Syntactic Sugar
To simplify writing, the `.wp` format introduces a set of semantic tags. The compiler is responsible for converting them into HTML recognized by the underlying rendering engine.

| Tag | Compiled HTML | Description |
| :--- | :--- | :--- |
| `<ppt-page>` | `<section class="slide">` | Defines a slide container. |
| `<ppt-text>` | `<div data-ppt-render="text">` | Defines an editable text block. |
| `<ppt-shape>` | `<div data-ppt-render="shape">` | Defines native shapes (rectangle/circle). |
| `<ppt-image>` | `<div data-ppt-render="image">` | Defines a complex component screenshot area (or directly wraps `<img>`). |
| `<ppt-table>` | `<table data-ppt-render="table">` | Defines a table. |

> **Note**: For elements with complex styles (such as gradients, shadows, filters) or **semi-transparent effects**, it is recommended to use the `<ppt-image>` tag. The compiler will take a screenshot of the entire area and insert it as an image into the PPT to ensure the visual effect is consistent with the web page.

> **Important**: The `<ppt-text>` tag currently only supports basic properties (color, font family, bold). If you need to render a **text card** (e.g., text with a background color, border, or shadow), do not apply these styles directly to `<ppt-text>`. Instead, use a separate `<ppt-shape>` for the background or wrap the entire card in `<ppt-image>` to export it as an image.

### 3.1 Attribute Passthrough
All standard HTML attributes defined on custom tags (such as `class`, `style`, `id`) are passed through to the compiled tags as is.

**Example**:
```html
<ppt-text class="title" style="color: red;">Hello</ppt-text>
```
**Compiled to**:
```html
<div data-ppt-render="text" class="title" style="color: red;">Hello</div>
```

## 4. Example File (`example.wp`)

```html
<ppt>
  <!-- Page 1 -->
  <ppt-page>
    <div class="layout-center">
      <ppt-text class="main-title">WebPPT 2.0</ppt-text>
      <ppt-text class="subtitle">Next-generation PPT generation tool based on .wp files</ppt-text>
      
      <!-- Shape Example -->
      <div class="shapes">
        <ppt-shape class="circle"></ppt-shape>
        <ppt-shape class="rect"></ppt-shape>
      </div>
    </div>
  </ppt-page>

  <!-- Page 2 -->
  <ppt-page>
    <ppt-text class="slide-title">Complex Component Screenshot</ppt-text>
    <!-- This card will be captured as a whole image -->
    <ppt-image class="card">
      <h2>Dynamic Card</h2>
      <p>The styles here are very complex...</p>
    </ppt-image>
  </ppt-page>
</ppt>

<style>
  /* Global Styles */
  body { font-family: 'Microsoft YaHei', sans-serif; }
  
  .layout-center {
    display: flex;
    flex-direction: column;
    /* ... */
  }
</style>
```

