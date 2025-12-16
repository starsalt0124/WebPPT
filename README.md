# WebPPT

WebPPT is a tool that converts HTML or custom `.wp` (WebPPT) files into PowerPoint (`.pptx`) presentations. It leverages Playwright for rendering and uses `python-pptx` to generate PPT files, aiming to simplify the process of writing and maintaining presentations.

English | [中文](docs/README_zh.md)

## Motivation

Large Language Models (LLMs) excel at generating code for web pages (HTML/CSS) but often struggle with creating PowerPoint files directly. Existing AI PPT generators typically rely on rigid templates, resulting in presentations that may lack aesthetic appeal or fail to align with specific themes.

WebPPT bridges this gap by leveraging the LLM's strong web generation capabilities. It allows you to use AI to generate beautiful, custom web-based slides and then converts them into editable native PowerPoint files.

> **Tip**: To get the best results from an LLM, provide it with the [WP_SPEC.md](docs/WP_SPEC.md) file so it understands the `.wp` format requirements.

## Features

- **.wp Single-File Component**: Similar to Vue SFC, it encapsulates structure, style, and logic in a single file.
- **HTML Support**: Directly supports converting HTML files to PPT.
- **Smart Rendering**: Supports multiple rendering modes, capable of extracting text, shapes, images, and tables.
- **Style Preservation**: Preserves CSS styles in the PPT as much as possible.

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd webppt
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install Playwright browsers:
   ```bash
   playwright install
   ```

## Usage

### Command Line Tool

Run `src/main.py` to convert files:

```bash
python src/main.py [input_file] [-o output_file] [-m render_mode]
```

- `input_file`: Input file path, can be a `.html` or `.wp` file. Defaults to `input/slide.html`.
- `-o output_file`: Output `.pptx` file path. Defaults to `output/presentation.pptx`.
- `-m render_mode`: Render mode (1: Minimal, 2: Smart [Default], 3: Maximal).

### Examples

Convert the default example:
```bash
python src/main.py
```

Convert a specific `.wp` file:
```bash
python src/main.py input/test.wp -o output/test.pptx
```

## .wp File Specification

A `.wp` file consists of three parts:

```html
<ppt>
  <!-- Slide Structure -->
  <ppt-page>
     <ppt-text>Hello World</ppt-text>
  </ppt-page>
</ppt>

<style>
  /* CSS Styles */
  .slide { background: white; }
</style>

<script>
  /* JS Logic */
</script>
```

For more details, please refer to [WP_SPEC.md](docs/WP_SPEC.md).

## Directory Structure

- `src/`: Source code directory
- `demo/`: Input file examples
- `docs/`: Documentation files

## License

[MIT License](LICENSE)
