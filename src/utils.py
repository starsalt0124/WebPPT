import re
from pptx.dml.color import RGBColor
from config import PX_TO_EMU

def px_to_emu(px):
    return int(px * PX_TO_EMU)

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join([c*2 for c in hex_color])
    return RGBColor(int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16))

def parse_color(color_string):
    """Parses 'rgb(r, g, b)' or 'rgba(r, g, b, a)' into (RGBColor, alpha)"""
    # Match rgba(r, g, b, a) or rgb(r, g, b)
    match = re.match(r'rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)', color_string)
    if match:
        r, g, b = int(match.group(1)), int(match.group(2)), int(match.group(3))
        a_str = match.group(4)
        alpha = float(a_str) if a_str else 1.0
        return RGBColor(r, g, b), alpha
    return RGBColor(0, 0, 0), 1.0

def parse_rgb_string(rgb_string):
    """Parses 'rgb(0, 120, 212)' into RGBColor object (Backward compatibility)"""
    rgb, _ = parse_color(rgb_string)
    return rgb
