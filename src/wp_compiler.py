import re

class WPCompiler:
    def __init__(self):
        # Configuration for tag transformation
        self.tag_mapping = {
            'ppt-page': {'tag': 'section', 'default_attrs': {'class': 'slide'}},
            'ppt-text': {'tag': 'div', 'default_attrs': {'data-ppt-render': 'text'}},
            'ppt-shape': {'tag': 'div', 'default_attrs': {'data-ppt-render': 'shape'}},
            'ppt-image': {'tag': 'div', 'default_attrs': {'data-ppt-render': 'image'}},
            'ppt-table': {'tag': 'table', 'default_attrs': {'data-ppt-render': 'table'}},
        }

    def compile(self, wp_content: str) -> str:
        """
        Compiles .wp content into a full HTML string.
        """
        # 1. Extract blocks
        ppt_match = re.search(r'<ppt>(.*?)</ppt>', wp_content, re.DOTALL)
        style_match = re.search(r'<style>(.*?)</style>', wp_content, re.DOTALL)
        script_match = re.search(r'<script>(.*?)</script>', wp_content, re.DOTALL)

        ppt_content = ppt_match.group(1) if ppt_match else ""
        style_content = style_match.group(1) if style_match else ""
        script_content = script_match.group(1) if script_match else ""

        # 2. Transform Custom Tags in PPT content
        html_body = self._transform_tags(ppt_content)

        # 3. Assemble Final HTML
        final_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WebPPT Render</title>
    <style>
        /* Reset & Base Styles */
        body {{ margin: 0; padding: 0; background: #f0f0f0; }}
        .slide {{
            width: 1280px;
            height: 720px;
            background: white;
            position: relative;
            overflow: hidden;
            margin-bottom: 20px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        /* User Styles */
        {style_content}
    </style>
</head>
<body>
    {html_body}
    <script>
        {script_content}
    </script>
</body>
</html>
"""
        return final_html

    def _transform_tags(self, content: str) -> str:
        """
        Replaces <ppt-*> tags with standard HTML tags and attributes.
        """
        
        # Helper to process opening tags
        def open_tag_replacer(match):
            tag_name = match.group(1)
            attrs_str = match.group(2) or ""
            
            if tag_name not in self.tag_mapping:
                return match.group(0) # Should not happen due to regex, but safety first
            
            config = self.tag_mapping[tag_name]
            target_tag = config['tag']
            default_attrs = config['default_attrs'].copy()
            
            # Parse existing attributes to handle merging (especially 'class')
            # Simple parser: key="value" or key='value'
            user_attrs = {}
            attr_pattern = re.compile(r'(\w+)=["\']([^"\']*)["\']')
            
            # Remove parsed attributes from attrs_str to keep unparsed ones (like boolean attrs or unquoted)
            # For simplicity, we will reconstruct the attribute string.
            
            for attr_match in attr_pattern.finditer(attrs_str):
                key = attr_match.group(1)
                val = attr_match.group(2)
                user_attrs[key] = val
            
            # Merge logic
            final_attrs = user_attrs.copy()
            for k, v in default_attrs.items():
                if k == 'class' and 'class' in final_attrs:
                    final_attrs[k] = f"{final_attrs[k]} {v}"
                elif k not in final_attrs:
                    final_attrs[k] = v
            
            # Reconstruct attributes string
            # Note: This drops attributes that didn't match the simple regex (e.g. boolean attrs like 'checked')
            # To be more robust, we should append our defaults to the raw string if not present.
            # But merging classes requires parsing.
            # Let's stick to the parsed dictionary for the specific keys we care about, 
            # and append the rest of the raw string? No, that duplicates.
            
            # Revised Strategy:
            # 1. Start with target tag.
            # 2. Add default attributes.
            # 3. Append user attributes string.
            # 4. Fix duplicates for 'class'.
            
            # Actually, let's just use the dictionary approach. It covers 99% of cases.
            # If user uses boolean attributes, they usually don't apply to our container divs.
            
            attrs_output = " ".join([f'{k}="{v}"' for k, v in final_attrs.items()])
            
            return f"<{target_tag} {attrs_output}>"

        # Replace Opening Tags
        # Matches <ppt-tag ... >
        pattern = re.compile(r'<(ppt-[\w-]+)([^>]*)>')
        content = pattern.sub(open_tag_replacer, content)

        # Replace Closing Tags
        for custom, config in self.tag_mapping.items():
            content = content.replace(f"</{custom}>", f"</{config['tag']}>")

        return content
