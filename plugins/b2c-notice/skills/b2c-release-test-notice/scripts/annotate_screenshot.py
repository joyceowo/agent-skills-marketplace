"""Plan 2x tile captures, stitch them, and draw anti-aliased screenshot callouts.

`plan` prints the page transform and tile offsets for browsers whose screenshot tool
downscales the viewport. `render` stitches tiles (or loads one image) and draws callouts.
All callout geometry is given in page CSS px; the script multiplies it by `scale`.
"""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

DEFAULT_COLOR = '#E53935'
MAX_DOT = 28        # CSS px
DOT_RATIO = 0.8
PAD = 4             # CSS px between target and box line
STROKE = 2.5
TIGHT_STROKE = 2    # for boxes whose targets sit closer than 2 * PAD
RADIUS = 6
DOT_GAP = 7         # box edge -> dot
TEXT_GAP = 6        # dot -> text
TEXT_SIZE = 17
LINE_SPACING = 4
SUPERSAMPLE = 3
MAX_COLORS = 3


def size_pair(text):
    try:
        width, height = (int(part) for part in text.lower().split('x'))
    except ValueError as error:
        raise argparse.ArgumentTypeError('use WIDTHxHEIGHT, e.g. 1060x934') from error
    if width <= 0 or height <= 0:
        raise argparse.ArgumentTypeError('sizes must be positive')
    return width, height


def plan(viewport, output, region, scale):
    """Tile plan: each tile is one screenshot of the scaled page."""
    vw, vh = viewport
    ow, oh = output
    rw, rh = region
    per_css = ow / vw                      # screenshot px per CSS px before scaling
    transform = scale / per_css            # CSS transform so 1 CSS px -> `scale` image px
    step_x, step_y = math.floor(ow / scale), math.floor(oh / scale)  # CSS px covered per tile
    tiles = []
    for row in range(math.ceil(rh / step_y)):
        for col in range(math.ceil(rw / step_x)):
            tx, ty = -col * step_x * transform, -row * step_y * transform
            tiles.append({
                'file': f'tile-r{row}-c{col}.png',
                'x': round(col * step_x * scale), 'y': round(row * step_y * scale),
                'js': (f"document.documentElement.style.transform="
                       f"'translate({tx:.2f}px,{ty:.2f}px) scale({transform:.4f})'"),
            })
    setup = ("(()=>{const h=document.documentElement;window.__b2cCapture={t:h.style.transform,"
             "o:h.style.transformOrigin,v:h.style.overflow};h.style.transformOrigin='0 0';"
             "h.style.overflow='hidden';return 'ready'})()")
    restore = ("(()=>{const h=document.documentElement,s=window.__b2cCapture||{t:'',o:'',v:''};"
               "h.style.transform=s.t;h.style.transformOrigin=s.o;h.style.overflow=s.v;"
               "delete window.__b2cCapture;return 'restored'})()")
    return {
        'scale': scale, 'transform': round(transform, 4),
        'tile_size': [ow, oh], 'size': [round(rw * scale), round(rh * scale)],
        'setup_js': setup, 'tiles': tiles, 'restore_js': restore,
        'notes': ['Run setup_js once, then each tile js; wait >= 1.5 s before every capture.',
                  'Save every capture losslessly at full output size (no reduced preview).',
                  'Check each tile shows its own area before rendering; always run restore_js.'],
    }


def load_base(spec, root):
    scale = spec['scale']
    if 'image' in spec:
        base = Image.open(root / spec['image']).convert('RGB')
    else:
        tiles = spec['tiles']
        if not tiles:
            raise ValueError('tiles must not be empty')
        width, height = spec['size']
        base = Image.new('RGB', (width, height), 'white')
        digests = {}
        for tile in tiles:
            image = Image.open(root / tile['file']).convert('RGB')
            digest = hashlib.sha1(image.tobytes()).hexdigest()
            if digest in digests:
                print(f"warning: {tile['file']} is identical to {digests[digest]}; "
                      'recapture it unless both areas are truly blank')
            digests[digest] = tile['file']
            base.paste(image, (tile['x'], tile['y']))
    if 'crop' in spec:
        left, top, right, bottom = (round(value * scale) for value in spec['crop'])
        base = base.crop((left, top, right, bottom))
    return base


def dot_size(target_height):
    return min(MAX_DOT, math.floor(target_height * DOT_RATIO))


def render(spec, root, output, font_path):
    scale = spec['scale']
    offset_x, offset_y = (spec.get('crop') or [0, 0])[:2]
    base = load_base(spec, root)
    marks = spec['marks']
    colors = {mark.get('color', spec.get('color', DEFAULT_COLOR)).upper() for mark in marks}
    if len(colors) > MAX_COLORS:
        raise ValueError(f'use at most {MAX_COLORS} callout colors, got {len(colors)}')
    k = scale * SUPERSAMPLE
    overlay = Image.new('RGBA', (base.width * SUPERSAMPLE, base.height * SUPERSAMPLE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    text_font = ImageFont.truetype(str(font_path), round(TEXT_SIZE * k))
    boxes = []
    for mark in marks:
        color = mark.get('color', spec.get('color', DEFAULT_COLOR))
        x0, y0, x1, y1 = mark['target']
        x0, x1, y0, y1 = x0 - offset_x, x1 - offset_x, y0 - offset_y, y1 - offset_y
        pad_x, pad_y = mark.get('pad', [PAD, PAD])
        stroke = mark.get('stroke', STROKE)
        box = (x0 - pad_x, y0 - pad_y, x1 + pad_x, y1 + pad_y)
        for other_index, other in boxes:
            if box[0] < other[2] + stroke and other[0] < box[2] + stroke \
                    and box[1] < other[3] + stroke and other[1] < box[3] + stroke:
                raise ValueError(f"callout {mark['n']} box touches callout {other_index}; "
                                 'reduce pad or use stroke 2')
        boxes.append((mark['n'], box))
        draw.rounded_rectangle([value * k for value in box], radius=RADIUS * k,
                               outline=color, width=round(stroke * k))
        dot = dot_size(y1 - y0)
        side = mark.get('side', 'right')
        cy = (y0 + y1) / 2
        if side == 'right':
            cx = box[2] + DOT_GAP + dot / 2
            text_x, anchor, align = cx + dot / 2 + TEXT_GAP, 'lm', 'left'
        elif side == 'left':
            cx = box[0] - DOT_GAP - dot / 2
            text_x, anchor, align = cx - dot / 2 - TEXT_GAP, 'rm', 'right'
        elif side in ('above', 'below'):
            # Dot and text share one line over/under the box, aligned with its left edge.
            default_y = box[1] - DOT_GAP - dot / 2 if side == 'above' else box[3] + DOT_GAP + dot / 2
            cx, cy = box[0] + dot / 2, mark.get('line_y', default_y + offset_y) - offset_y
            text_x, anchor, align = cx + dot / 2 + TEXT_GAP, 'lm', 'left'
        else:
            raise ValueError(f"callout {mark['n']}: side must be right, left, above or below")
        r = dot / 2
        draw.ellipse([(cx - r) * k, (cy - r) * k, (cx + r) * k, (cy + r) * k], fill=color)
        number_font = ImageFont.truetype(str(font_path), round(math.floor(dot * 2 / 3) * k))
        draw.text((cx * k, cy * k), str(mark['n']), fill='white', font=number_font, anchor='mm')
        draw.multiline_text((text_x * k, cy * k), mark['text'], fill=color, font=text_font,
                            anchor=anchor, align=align, spacing=round(LINE_SPACING * k))
        left, top, right, bottom = draw.multiline_textbbox(
            (text_x * k, cy * k), mark['text'], font=text_font, anchor=anchor,
            align=align, spacing=round(LINE_SPACING * k))
        if left < 0 or top < 0 or right > overlay.width or bottom > overlay.height:
            raise ValueError(f"callout {mark['n']} text leaves the image; change side or line_y")
    overlay = overlay.resize(base.size, Image.LANCZOS)
    result = Image.alpha_composite(base.convert('RGBA'), overlay).convert('RGB')
    output.parent.mkdir(parents=True, exist_ok=True)
    result.save(output, optimize=True)
    print(f'Saved {output} ({result.width}x{result.height}, {len(marks)} callouts)')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest='command', required=True)
    plan_parser = commands.add_parser('plan', help='print a 2x tile capture plan as JSON')
    plan_parser.add_argument('--viewport', required=True, type=size_pair, help='page viewport in CSS px')
    plan_parser.add_argument('--output', required=True, type=size_pair, help='screenshot tool output in px')
    plan_parser.add_argument('--region', required=True, type=size_pair,
                             help='page area to capture from the top-left, in CSS px')
    plan_parser.add_argument('--scale', type=float, default=2, help='image px per CSS px (default 2)')
    render_parser = commands.add_parser('render', help='stitch tiles and draw callouts')
    render_parser.add_argument('--input', required=True, type=Path, help='callout spec JSON')
    render_parser.add_argument('--output', required=True, type=Path, help='annotated PNG')
    windows_fonts = Path(os.environ.get('WINDIR', r'C:\Windows')) / 'Fonts'
    render_parser.add_argument('--font', type=Path, default=windows_fonts / 'msjhbd.ttc',
                               help='bold Traditional Chinese font')
    args = parser.parse_args()
    if args.command == 'plan':
        print(json.dumps(plan(args.viewport, args.output, args.region, args.scale),
                         ensure_ascii=False, indent=2))
        return
    if not args.font.is_file():
        parser.error('Specify an installed bold Traditional Chinese font with --font')
    try:
        spec = json.loads(args.input.read_text(encoding='utf-8-sig'))
        render(spec, args.input.parent, args.output, args.font)
    except (OSError, KeyError, ValueError) as error:
        parser.exit(1, f'Cannot render screenshot: {error}\n')


if __name__ == '__main__':
    main()
