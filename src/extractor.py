import os
from config import PPT_WIDTH_PX

class ContentExtractor:
    def __init__(self, page):
        self.page = page

    async def extract_elements(self):
        """
        Injects JS to find all elements with 'data-ppt-render' attribute
        and returns their computed styles and coordinates.
        """
        return await self.page.evaluate("""() => {
            // Helper: Check if element text is single line
            function isSingleLine(el) {
                const range = document.createRange();
                range.selectNodeContents(el);
                const rects = range.getClientRects();
                if (rects.length === 0) return true;
                const firstTop = rects[0].top;
                for (let i = 1; i < rects.length; i++) {
                    if (Math.abs(rects[i].top - firstTop) > 5) {
                        return false;
                    }
                }
                return true;
            }

            // Helper: Auto-tag elements with text as 'text' if not already tagged
            function autoTagTextElements(root) {
                const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
                let node;
                while(node = walker.nextNode()) {
                    // Skip if already tagged or is the slide itself
                    if (node.hasAttribute('data-ppt-render') || node.classList.contains('slide')) continue;
                    
                    // Skip if inside table or image. Allow inside shape (container).
                    if (node.closest('[data-ppt-render="table"]') || node.closest('[data-ppt-render="image"]')) continue;

                    // Skip if it contains any already tagged elements (to avoid tagging containers as text)
                    if (node.querySelector('[data-ppt-render]')) continue;

                    // Check for direct text content
                    const hasDirectText = Array.from(node.childNodes).some(n => 
                        n.nodeType === Node.TEXT_NODE && n.textContent.trim().length > 0
                    );
                    
                    if (hasDirectText) {
                        // Check if visible
                        const style = window.getComputedStyle(node);
                        if (style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0') {
                            node.setAttribute('data-ppt-render', 'text');
                        }
                    }
                }
            }

            // Helper: Auto-tag container elements as 'shape'
            function autoTagContainerElements(root) {
                const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
                let node;
                while(node = walker.nextNode()) {
                    if (node.hasAttribute('data-ppt-render') || node.classList.contains('slide')) continue;
                    
                    // Skip if inside table
                    if (node.closest('[data-ppt-render="table"]')) continue;

                    const style = window.getComputedStyle(node);
                    if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') continue;

                    // Check for background or border
                    const hasBg = style.backgroundColor !== 'rgba(0, 0, 0, 0)' && style.backgroundColor !== 'transparent';
                    const hasBorder = (parseFloat(style.borderTopWidth) > 0 && style.borderTopStyle !== 'none') ||
                                      (parseFloat(style.borderBottomWidth) > 0 && style.borderBottomStyle !== 'none') ||
                                      (parseFloat(style.borderLeftWidth) > 0 && style.borderLeftStyle !== 'none') ||
                                      (parseFloat(style.borderRightWidth) > 0 && style.borderRightStyle !== 'none');
                    
                    // Also check for specific classes like 'card' as a heuristic
                    const isCard = node.classList.contains('card');
                                      
                    if (hasBg || hasBorder || isCard) {
                        node.setAttribute('data-ppt-render', 'shape');
                    }
                }
            }

            // Find all slide sections
            const slides = document.querySelectorAll('section.slide');
            const allSlidesData = [];

            function getComputedStyles(el) {
                const s = window.getComputedStyle(el);
                return {
                    color: s.color,
                    fontSize: s.fontSize,
                    fontFamily: s.fontFamily,
                    fontWeight: s.fontWeight,
                    textAlign: s.textAlign,
                    opacity: s.opacity,
                    boxShadow: s.boxShadow,
                    backgroundColor: s.backgroundColor,
                    backgroundImage: s.backgroundImage,
                    borderRadius: s.borderRadius,
                    borderTopWidth: s.borderTopWidth,
                    borderTopColor: s.borderTopColor,
                    borderTopStyle: s.borderTopStyle,
                    borderBottomWidth: s.borderBottomWidth,
                    borderBottomColor: s.borderBottomColor,
                    borderBottomStyle: s.borderBottomStyle,
                    borderLeftWidth: s.borderLeftWidth,
                    borderLeftColor: s.borderLeftColor,
                    borderLeftStyle: s.borderLeftStyle,
                    borderRightWidth: s.borderRightWidth,
                    borderRightColor: s.borderRightColor,
                    borderRightStyle: s.borderRightStyle,
                    lineHeight: s.lineHeight,
                    letterSpacing: s.letterSpacing,
                    display: s.display,
                    alignItems: s.alignItems,
                    justifyContent: s.justifyContent,
                    flexDirection: s.flexDirection,
                    mixBlendMode: s.mixBlendMode,
                    backdropFilter: s.backdropFilter,
                    webkitBackdropFilter: s.webkitBackdropFilter
                };
            }

            // If no sections found, treat body as one slide (backward compatibility)
            let slideContainers = slides.length > 0 ? Array.from(slides) : [document.body];

            slideContainers.forEach((slideContainer, slideIndex) => {
                slideContainer.setAttribute('data-ppt-slide-id', `slide_${slideIndex}`);
                
                // Run auto-tagging for this slide
                autoTagContainerElements(slideContainer);
                autoTagTextElements(slideContainer);

                // Filter elements to avoid duplication
                const rawElements = Array.from(slideContainer.querySelectorAll('[data-ppt-render]'));
                const elements = rawElements.filter(el => {
                    const parent = el.parentElement.closest('[data-ppt-render]');
                    if (!parent) return true;
                    
                    const parentType = parent.getAttribute('data-ppt-render');
                    // Only allow children if parent is a shape (container)
                    if (parentType === 'shape') return true;
                    
                    return false;
                });
                const slideResults = [];
                
                // Get slide offset to normalize coordinates relative to the slide
                const slideRect = slideContainer.getBoundingClientRect();
                
                // Determine Slide Background Color
                // Logic: Start with the section's background. 
                // If the first child covers the entire section and has a background, use that instead.
                let slideStyles = getComputedStyles(slideContainer);
                let finalBgColor = slideStyles.backgroundColor;
                let finalBgImage = slideStyles.backgroundImage;

                const firstChild = slideContainer.firstElementChild;
                if (firstChild) {
                     const childStyles = getComputedStyles(firstChild);
                     const childRect = firstChild.getBoundingClientRect();
                     
                     // Check if child covers the slide (approximate check for float precision)
                     const covers = Math.abs(childRect.width - slideRect.width) < 2 && 
                                    Math.abs(childRect.height - slideRect.height) < 2;
                     
                     const hasBgColor = childStyles.backgroundColor !== 'rgba(0, 0, 0, 0)' && childStyles.backgroundColor !== 'transparent';
                     const hasBgImage = childStyles.backgroundImage !== 'none' && childStyles.backgroundImage !== '';

                     if (covers && (hasBgColor || hasBgImage)) {
                         finalBgColor = childStyles.backgroundColor;
                         finalBgImage = childStyles.backgroundImage;
                     }
                }
                slideStyles.backgroundColor = finalBgColor;
                slideStyles.backgroundImage = finalBgImage;

                elements.forEach((el, index) => {
                    const rect = el.getBoundingClientRect();
                    const styles = getComputedStyles(el);
                    
                    // Unique ID including slide index
                    const uniqueId = `slide_${slideIndex}_el_${index}`;
                    el.setAttribute('data-ppt-id', uniqueId);

                    // Determine text content
                    // If it's a shape and has rendered children, suppress text to avoid duplication
                    let textContent = el.innerText;
                    if (el.getAttribute('data-ppt-render') === 'shape') {
                         if (el.querySelector('[data-ppt-render]')) {
                             textContent = "";
                         }
                    }

                    const item = {
                        id: uniqueId,
                        type: el.getAttribute('data-ppt-render'),
                        text: textContent,
                        isSingleLine: isSingleLine(el),
                        href: el.tagName === 'A' ? el.href : (el.closest('a') ? el.closest('a').href : null),
                        // Coordinates relative to the slide container
                        x: rect.x - slideRect.x,
                        y: rect.y - slideRect.y,
                        width: rect.width,
                        height: rect.height,
                        styles: styles,
                        children: [],
                        rows: [] // For tables
                    };

                    // Table Handling
                    if (item.type === 'table') {
                        const rows = el.querySelectorAll('tr');
                        rows.forEach(row => {
                            const rowData = [];
                            const rowStyles = getComputedStyles(row);
                            const cells = row.querySelectorAll('td, th');
                            cells.forEach(cell => {
                                const cellRect = cell.getBoundingClientRect();
                                const cellStyles = getComputedStyles(cell);
                                
                                // Inherit background from row if transparent
                                if ((cellStyles.backgroundColor === 'rgba(0, 0, 0, 0)' || cellStyles.backgroundColor === 'transparent') &&
                                    (rowStyles.backgroundColor !== 'rgba(0, 0, 0, 0)' && rowStyles.backgroundColor !== 'transparent')) {
                                    cellStyles.backgroundColor = rowStyles.backgroundColor;
                                }

                                rowData.push({
                                    text: cell.innerText,
                                    width: cellRect.width,
                                    height: cellRect.height,
                                    styles: cellStyles
                                });
                            });
                            item.rows.push(rowData);
                        });
                    }

                    // If it's an image container, look for text children to make editable
                    if (item.type === 'image') {
                        const textNodes = [];
                        const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, null, false);
                        let node;
                        while(node = walker.nextNode()) {
                            if (node.textContent.trim().length > 0) {
                                let parent = node.parentElement;
                                // Check if parent is suitable for extraction
                                // We only want to extract text that doesn't have its own "box" styling (bg, border)
                                // because if we hide it, we lose that styling in the screenshot.
                                const pStyle = window.getComputedStyle(parent);
                                const hasBg = pStyle.backgroundColor !== 'rgba(0, 0, 0, 0)' && pStyle.backgroundColor !== 'transparent';
                                const hasBorder = (parseFloat(pStyle.borderTopWidth) > 0 && pStyle.borderTopStyle !== 'none');
                                
                                if (!hasBg && !hasBorder) {
                                    if (!textNodes.includes(parent)) {
                                        textNodes.push(parent);
                                    }
                                }
                            }
                        }

                        textNodes.forEach((childEl, childIndex) => {
                            const childRect = childEl.getBoundingClientRect();
                            const childStyles = getComputedStyles(childEl);
                            const childId = `${uniqueId}_child_${childIndex}`;
                            childEl.setAttribute('data-ppt-child-id', childId);
                            
                            item.children.push({
                                id: childId,
                                text: childEl.innerText,
                                isSingleLine: isSingleLine(childEl),
                                // Relative coordinates
                                x: childRect.x - slideRect.x,
                                y: childRect.y - slideRect.y,
                                width: childRect.width,
                                height: childRect.height,
                                styles: childStyles
                            });
                        });
                    }

                    slideResults.push(item);
                });
                allSlidesData.push({
                    id: `slide_${slideIndex}`,
                    elements: slideResults,
                    backgroundColor: slideStyles.backgroundColor,
                    backgroundImage: slideStyles.backgroundImage
                });
            });
            
            return allSlidesData;
        }""")

    async def capture_slide_background(self, slide_id, slide_elements):
        # 1. Hide all elements on this slide
        for el in slide_elements:
            await self.page.evaluate(f"document.querySelector('[data-ppt-id=\"{el['id']}\"]').style.visibility = 'hidden'")
        
        # 2. Screenshot the slide container
        slide_handle = await self.page.query_selector(f'[data-ppt-slide-id="{slide_id}"]')
        bg_screenshot_path = f"output/temp_bg_{slide_id}.png"
        await slide_handle.screenshot(path=bg_screenshot_path)
        
        # 3. Restore elements
        for el in slide_elements:
            await self.page.evaluate(f"document.querySelector('[data-ppt-id=\"{el['id']}\"]').style.visibility = 'visible'")
            
        return bg_screenshot_path

    async def capture_element_image(self, slide_id, el):
        # 1. Isolate element: Hide siblings and set transparent bg
        js = """() => {{
            const slide = document.querySelector('[data-ppt-slide-id="{slide_id}"]');
            const targetEl = document.querySelector('[data-ppt-id="{el_id}"]');
            
            // Check for backdrop-filter
            const style = window.getComputedStyle(targetEl);
            const hasBackdropFilter = style.backdropFilter !== 'none' && style.backdropFilter !== undefined || 
                                      style.webkitBackdropFilter !== 'none' && style.webkitBackdropFilter !== undefined;

            window._ppt_snapshot_state = {{
                slideBg: slide.style.background,
                bodyBg: document.body.style.background,
                siblingsVisibility: []
            }};
            
            // Only hide background if no backdrop-filter is present
            if (!hasBackdropFilter) {{
                slide.style.background = 'transparent';
                document.body.style.background = 'transparent';
            }}
            
            const allEls = slide.querySelectorAll('[data-ppt-render]');
            allEls.forEach(e => {{
                if (e !== targetEl && !targetEl.contains(e) && !e.contains(targetEl)) {{
                    window._ppt_snapshot_state.siblingsVisibility.push({{el: e, val: e.style.visibility}});
                    e.style.visibility = 'hidden';
                }}
            }});
        }}""".format(slide_id=slide_id, el_id=el['id'])

        await self.page.evaluate(js)

        # 2. Hide text children
        if el['children']:
            for child in el['children']:
                await self.page.evaluate(f"document.querySelector('[data-ppt-child-id=\"{child['id']}\"]').style.opacity = '0'")

        # 3. Take screenshot with omit_background=True
        element_handle = await self.page.query_selector(f'[data-ppt-id="{el["id"]}"]')
        screenshot_path = f"output/temp_{el['id']}.png"
        
        # Use page.screenshot with clip to capture shadows (add padding)
        box = await element_handle.bounding_box()
        padding = 30 # px
        
        crop_info = None

        if box:
            raw_x = box['x'] - padding
            raw_y = box['y'] - padding
            raw_w = box['width'] + (padding * 2)
            raw_h = box['height'] + (padding * 2)
            
            final_x = max(0, raw_x)
            final_y = max(0, raw_y)
            
            final_w = min(PPT_WIDTH_PX - final_x, raw_w - (final_x - raw_x))
            final_h = raw_h - (final_y - raw_y)

            if final_w > 0 and final_h > 0:
                clip_rect = {
                    'x': final_x,
                    'y': final_y,
                    'width': final_w,
                    'height': final_h
                }
                await self.page.screenshot(path=screenshot_path, clip=clip_rect, omit_background=True)
                
                crop_left = final_x - raw_x
                crop_top = final_y - raw_y
                
                crop_info = {
                    'crop_left': crop_left,
                    'crop_top': crop_top,
                    'width': final_w,
                    'height': final_h,
                    'padding': padding
                }
            else:
                # Fallback
                await element_handle.screenshot(path=screenshot_path, omit_background=True)
        else:
            # Fallback
            await element_handle.screenshot(path=screenshot_path, omit_background=True)
            
        # 4. Restore text children
        if el['children']:
            for child in el['children']:
                await self.page.evaluate(f"document.querySelector('[data-ppt-child-id=\"{child['id']}\"]').style.opacity = '1'")

        # 5. Restore isolation state
        await self.page.evaluate(f"""() => {{
            const slide = document.querySelector('[data-ppt-slide-id="{slide_id}"]');
            const state = window._ppt_snapshot_state;
            if (state) {{
                slide.style.background = state.slideBg;
                document.body.style.background = state.bodyBg;
                state.siblingsVisibility.forEach(item => {{
                    item.el.style.visibility = item.val;
                }});
                delete window._ppt_snapshot_state;
            }}
        }}""")
        
        return screenshot_path, crop_info
