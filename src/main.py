import asyncio
import os
import sys
from playwright.async_api import async_playwright
from wp_compiler import WPCompiler
from config import PPT_WIDTH_PX, PPT_HEIGHT_PX
from extractor import ContentExtractor
from ppt_renderer import PPTRenderer
from utils import parse_color

async def main():
    # Default paths
    input_file = "input/slide.html"
    output_path = "output/presentation.pptx"
    render_mode = 2 # 1: Minimal, 2: Smart (Default), 3: Maximal

    # Parse arguments
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == '-o':
            if i + 1 < len(args):
                output_path = args[i+1]
                i += 1
        elif arg == '-m':
            if i + 1 < len(args):
                render_mode = int(args[i+1])
                i += 1
        elif not arg.startswith('-'):
            input_file = arg
        i += 1

    input_path = os.path.abspath(input_file)
    print(f"Processing {input_path} with Render Mode {render_mode}...")

    # Handle .wp files
    if input_file.endswith('.wp'):
        print("Detected .wp file. Compiling...")
        with open(input_path, 'r', encoding='utf-8') as f:
            wp_content = f.read()
        
        compiler = WPCompiler()
        html_content = compiler.compile(wp_content)
        
        # Save to temp html
        temp_html_path = input_path.replace('.wp', '.temp.html')
        with open(temp_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        input_path = temp_html_path
        print(f"Compiled to temporary file: {input_path}")

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        # Use device_scale_factor=3 for high DPI screenshots (Retina quality)
        page = await browser.new_page(viewport={'width': PPT_WIDTH_PX, 'height': PPT_HEIGHT_PX}, device_scale_factor=3)
        await page.goto(f"file://{input_path}")
        
        extractor = ContentExtractor(page)
        slides_data = await extractor.extract_elements()
        print(f"Found {len(slides_data)} slides to render.")
        
        # Resize viewport to fit all content to ensure screenshots work for elements outside initial viewport
        doc_height = await page.evaluate("document.body.scrollHeight")
        # Add some buffer just in case
        await page.set_viewport_size({'width': PPT_WIDTH_PX, 'height': int(doc_height) + 100})
        
        # Take a full page screenshot for reference
        await page.screenshot(path="output/reference_render.png", full_page=True)
        print("Saved reference screenshot to output/reference_render.png")

        # Create PPT
        renderer = PPTRenderer(output_path)

        for i, slide_data in enumerate(slides_data):
            slide_elements = slide_data['elements']
            slide_bg_image = slide_data.get('backgroundImage')
            slide_id = slide_data.get('id')
            
            # Check for gradient/image background
            is_complex_bg = slide_bg_image and slide_bg_image != 'none'
            bg_image_path = None
            
            if is_complex_bg:
                bg_image_path = await extractor.capture_slide_background(slide_id, slide_elements)
            
            slide = renderer.add_slide(slide_data, bg_image_path)
            
            if bg_image_path:
                os.remove(bg_image_path)

            for el in slide_elements:
                # Overflow Check
                if el['x'] + el['width'] > PPT_WIDTH_PX + 1 or el['y'] + el['height'] > PPT_HEIGHT_PX + 1:
                    print(f"WARNING: Element '{el['text'][:20]}...' on slide {i+1} is out of bounds!")

            for el in slide_elements:
                # Check if shape has gradient or complex styles that require image rendering
                styles = el['styles']
                bg_image = styles.get('backgroundImage', '')
                is_gradient = 'gradient' in bg_image
                
                # Check for glassmorphism (backdrop-filter)
                bd_filter = styles.get('backdropFilter', 'none')
                wk_bd_filter = styles.get('webkitBackdropFilter', 'none')
                is_glass = (bd_filter and bd_filter != 'none') or (wk_bd_filter and wk_bd_filter != 'none')
                
                # Check for mix-blend-mode
                mix_blend = styles.get('mixBlendMode', 'normal')
                is_blend = mix_blend != 'normal'

                # Check for transparency
                opacity = float(styles.get('opacity', '1'))
                is_transparent = opacity < 1
                
                bg_color = styles.get('backgroundColor', '')
                is_semi_transparent_bg = False
                if bg_color and 'rgba' in bg_color:
                     try:
                         _, alpha = parse_color(bg_color)
                         if 0 < alpha < 1:
                             is_semi_transparent_bg = True
                     except:
                         pass

                # Check for semi-transparent text color
                text_color = styles.get('color', '')
                is_semi_transparent_text = False
                if text_color and 'rgba' in text_color:
                     try:
                         _, alpha = parse_color(text_color)
                         if 0 < alpha < 1:
                             is_semi_transparent_text = True
                     except:
                         pass

                # Force image rendering for complex effects
                # Applies to shapes and text (if text has complex transparency/effects)
                should_fallback = False
                
                if render_mode == 1:
                    # Mode 1: Minimal - Only if explicitly 'image' (handled by el['type'] check later)
                    should_fallback = False
                    
                elif render_mode == 2:
                    # Mode 2: Smart (Default)
                    if el['type'] == 'shape':
                        if is_gradient or is_glass or is_blend or is_transparent or is_semi_transparent_bg:
                            should_fallback = True
                    elif el['type'] == 'text':
                        # For text, we fallback if there's opacity, blend mode, or semi-transparent color
                        if is_transparent or is_blend or is_semi_transparent_text:
                            should_fallback = True

                elif render_mode == 3:
                    # Mode 3: Maximal
                    if el['type'] == 'shape':
                        should_fallback = True # Always render shapes as images
                    elif el['type'] == 'text':
                        # Still check for complex effects for text to preserve editability for simple text
                        if is_transparent or is_blend or is_semi_transparent_text:
                            should_fallback = True

                if should_fallback:
                    reason = []
                    if render_mode == 3 and el['type'] == 'shape':
                        reason.append('maximal mode')
                    else:
                        if is_gradient: reason.append('gradient')
                        if is_glass: reason.append('glass effect')
                        if is_blend: reason.append('blend mode')
                        if is_transparent: reason.append('opacity')
                        if is_semi_transparent_bg: reason.append('rgba background')
                        if is_semi_transparent_text: reason.append('rgba text')
                    
                    print(f"Element '{el['id']}' ({el['type']}) has {', '.join(reason)}, switching to image rendering.")
                    el['type'] = 'image'

                if el['type'] == 'text':
                    renderer.create_text_box(slide, el)
                    
                elif el['type'] == 'shape':
                    renderer.create_shape(slide, el)
                    # If shape has text, add it on top
                    if el['text'].strip():
                        renderer.create_text_box(slide, el)
                
                elif el['type'] == 'table':
                    renderer.create_table(slide, el)

                elif el['type'] == 'image':
                    image_path, crop_info = await extractor.capture_element_image(slide_id, el)
                    
                    renderer.add_image_element(slide, el, image_path, crop_info)
                    
                    os.remove(image_path)

                    # Insert Text Boxes on top
                    if el['children']:
                        for child in el['children']:
                            renderer.create_text_box(slide, child)

        renderer.save()
        print(f"Saved presentation to {output_path}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
