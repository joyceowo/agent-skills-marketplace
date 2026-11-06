"""Render one offline B2C notice with a PDF download from the same content."""

import argparse
import base64
from html import escape
from html.parser import HTMLParser
from io import BytesIO
import json
import os
from pathlib import Path
import re

from PIL import Image, ImageDraw, ImageFont, ImageOps
from pypdf import PdfReader
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image as PdfImage
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer


ASSETS = Path(__file__).resolve().parents[1] / 'assets'
MAIL_WIDTH = 860
BLUE = '#00ACCA'
RED = '#E53935'
GRAY = '#66747B'
INK = '#333333'
MAIL_FONT = 'Microsoft JhengHei'
FONT_STYLE = (
    f"font-family:'{MAIL_FONT}','微軟正黑體',Arial,sans-serif;"
    f"mso-ascii-font-family:'{MAIL_FONT}';mso-hansi-font-family:'{MAIL_FONT}';"
    f"mso-fareast-font-family:'{MAIL_FONT}';"
)
LABELS = {'release': '上線通知', 'test': '測試通知'}
TEXT_KINDS = {'heading', 'paragraph', 'bullet', 'emphasis'}


def required_text(obj, key):
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{key} must be non-empty text')
    return value.strip()


def read_notice(path):
    data = json.loads(path.read_text(encoding='utf-8-sig'))
    if not isinstance(data, dict) or data.get('type') not in ('release', 'test'):
        raise ValueError('type must be release or test')
    label = LABELS[data['type']]
    title = required_text(data, 'title')
    if not title.endswith(label):
        title = f'{title} {label}'
    highlight = data.get('highlight', '')
    if not isinstance(highlight, str):
        raise ValueError('highlight must be text')
    entries = data.get('blocks')
    if not isinstance(entries, list) or not entries:
        raise ValueError('blocks must be a non-empty array')
    blocks = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError('Each block must be an object')
        kind = entry.get('kind')
        if isinstance(kind, str) and kind in TEXT_KINDS:
            blocks.append({'kind': kind, 'text': required_text(entry, 'text')})
        elif kind == 'image':
            source = path.parent / required_text(entry, 'path')
            with Image.open(source) as original:
                if original.format not in {'PNG', 'JPEG'}:
                    raise ValueError(f'Expected a PNG or JPEG screenshot: {source}')
                screenshot = ImageOps.exif_transpose(original).convert('RGB')
                png = BytesIO()
                screenshot.save(png, format='PNG')
            blocks.append({'kind': kind, 'png': png.getvalue(), 'alt': required_text(entry, 'alt')})
            if entry.get('caption'):
                blocks.append({'kind': 'caption', 'text': required_text(entry, 'caption')})
        else:
            raise ValueError(f'Unknown block kind: {kind}')
    return title, highlight.strip(), blocks


def title_image(title, font_path, bell):
    font = ImageFont.truetype(str(font_path), 54)
    lines = []
    current = ''
    for char in title:
        if char == '\n' or (current and font.getlength(current + char) > (MAIL_WIDTH - 65) * 2):
            lines.append(current)
            current = ''
        if char != '\n':
            current += char
    if current:
        lines.append(current)
    artwork = Image.new('RGB', (MAIL_WIDTH * 2, (25 + 33 * len(lines)) * 2), 'white')
    with Image.open(BytesIO(bell)) as original:
        icon = original.convert('RGBA').resize((48, 48), Image.Resampling.LANCZOS)
    artwork.paste(icon, (0, 34), icon)
    draw = ImageDraw.Draw(artwork)
    for index, line in enumerate(lines):
        draw.text((62, 58 + 66 * index), line, fill=BLUE, font=font, anchor='lm')
    end = 78 + round(font.getlength(lines[-1]))
    artwork.paste(icon, (end, 34 + 66 * (len(lines) - 1)), icon)
    output = BytesIO()
    artwork.save(output, format='PNG')
    return output.getvalue()


def image_size(data):
    with Image.open(BytesIO(data)) as image:
        return image.size


def marked_text(text, highlight, render):
    if not highlight:
        return render(text)
    segments = text.split(highlight)
    return render(highlight, RED).join(render(segment) for segment in segments)


def block_text(block):
    return ('• ' if block['kind'] == 'bullet' else '') + block['text']


def html_rows(title, highlight, blocks, brand, title_png):
    def image(data, alt):
        width, height = image_size(data)
        scaled = round(MAIL_WIDTH * height / width)
        encoded = base64.b64encode(data).decode('ascii')
        return (f'<img src="data:image/png;base64,{encoded}" width="{MAIL_WIDTH}" height="{scaled}" '
                f'alt="{escape(alt)}" style="display:block;width:{MAIL_WIDTH}px;max-width:100%;height:auto;'
                'margin:0;border:0;vertical-align:top;">')

    def row(content, top=0, bottom=0):
        padding = f'{top}pt 0 {bottom}pt 0'
        return ('<tr><td align="left" valign="top" bgcolor="#FFFFFF" '
                f'style="padding:{padding};mso-padding-alt:{padding};text-align:left;vertical-align:top;'
                f'background-color:#FFFFFF;">{content}</td></tr>')

    rows = [row(image(brand['header'], 'GIGABYTE 數位平台')),
            row('<h1 align="left" style="margin:0;text-align:left;">'+image(title_png, title)+'</h1>'),
            row(image(brand['divider'], '藍綠漸層分隔色帶'), bottom=13)]
    for block in blocks:
        kind = block['kind']
        if kind == 'image':
            rows.append(row(image(block['png'], block['alt']), top=4))
            continue
        size, line, color, top, bottom = {
            'heading': (15.75, 22, BLUE, 12, 4),
            'caption': (9.75, 14, GRAY, 4, 5),
            'bullet': (12, 18, INK, 2, 2),
        }.get(kind, (12, 18, INK, 6, 0))

        def run(text, ink=color):
            value = escape(text).replace('\n', '<br>')
            return (f'<font face="{MAIL_FONT}" color="{ink}" lang="zh-TW" '
                    f'style="{FONT_STYLE}font-size:{size}pt;color:{ink};">{value}</font>')

        value = marked_text(block_text(block), highlight, run)
        if kind in {'heading', 'emphasis'}:
            value = f'<strong>{value}</strong>'
        heading = ' role="heading" aria-level="2"' if kind == 'heading' else ''
        rows.append(row(f'<p align="left"{heading} style="{FONT_STYLE}font-size:{size}pt;color:{color};'
                        f'margin:0;text-align:left;line-height:{line}pt;mso-line-height-rule:at-least;">'
                        f'{value}</p>', top, bottom))
    rows.append(row(image(brand['footer'], 'GIGABYTE 數位平台頁尾'), top=13))
    return '\n'.join(rows)


def render_pdf(title, highlight, blocks, brand, font_path, bold_path):
    pdfmetrics.registerFont(TTFont('NoticeRegular', str(font_path)))
    pdfmetrics.registerFont(TTFont('NoticeBold', str(bold_path)))
    width, height = A4
    margin = 36
    available = width - 2 * margin

    def dimensions(data, max_height):
        w, h = image_size(data)
        ratio = min(available / w, max_height / h)
        return w * ratio, h * ratio

    header_width, header_height = dimensions(brand['header'], 42)
    footer_width, footer_height = dimensions(brand['footer'], 120)

    def draw_brand(canvas, doc):
        canvas.setTitle(title)
        canvas.setAuthor('數位平台')
        canvas.drawImage(ImageReader(BytesIO(brand['header'])), margin, height - 28 - header_height,
                         header_width, header_height, mask='auto')
        canvas.drawImage(ImageReader(BytesIO(brand['footer'])), margin, 26,
                         footer_width, footer_height, mask='auto')

    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, leftMargin=margin-6, rightMargin=margin-6,
                            topMargin=28+header_height+12, bottomMargin=26+footer_height+16)
    body = ParagraphStyle('body', fontName='NoticeRegular', fontSize=11, leading=17,
                          textColor=HexColor(INK), wordWrap='CJK', spaceAfter=5)
    styles = {
        'heading': ParagraphStyle('heading', parent=body, fontName='NoticeBold', fontSize=13,
                                  leading=20, textColor=HexColor('#0099BA'), spaceBefore=9, keepWithNext=True),
        'emphasis': ParagraphStyle('emphasis', parent=body, fontName='NoticeBold'),
        'caption': ParagraphStyle('caption', parent=body, fontSize=8.5, leading=13,
                                  textColor=HexColor(GRAY), spaceBefore=4),
    }
    title_style = ParagraphStyle('title', parent=body, fontName='NoticeBold', fontSize=18, leading=25,
                                 textColor=HexColor(BLUE), keepWithNext=True)

    def picture(data, max_height):
        w, h = dimensions(data, max_height)
        return PdfImage(BytesIO(data), width=w, height=h, hAlign='LEFT')

    def run(text, color=None):
        value = escape(text).replace('\n', '<br/>')
        return f'<font color="{color}">{value}</font>' if color else value

    story = [Paragraph(run(title), title_style), picture(brand['divider'], 8), Spacer(1, 9)]
    index = 0
    while index < len(blocks):
        block = blocks[index]
        kind = block['kind']
        figure_heading = None
        if kind == 'heading' and index + 1 < len(blocks) and blocks[index+1]['kind'] == 'image':
            figure_heading = Paragraph(marked_text(block_text(block), highlight, run), styles['heading'])
            index += 1
            block = blocks[index]
            kind = 'image'
        if kind == 'image':
            figure = [Spacer(1, 5), picture(block['png'], 330)]
            if figure_heading is not None:
                figure.insert(0, figure_heading)
            if index + 1 < len(blocks) and blocks[index+1]['kind'] == 'caption':
                index += 1
                figure.append(Paragraph(run(blocks[index]['text']), styles['caption']))
            story.append(KeepTogether(figure))
        else:
            story.append(Paragraph(marked_text(block_text(block), highlight, run), styles.get(kind, body)))
        index += 1
    doc.build(story, onFirstPage=draw_brand, onLaterPages=draw_brand)
    return output.getvalue()


class NoticeText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_notice = False
        self.in_title = False
        self.parts = []

    def handle_starttag(self, tag, attributes):
        if tag == 'main':
            self.in_notice = True
        if self.in_notice and tag == 'h1':
            self.in_title = True
        if self.in_title and tag == 'img':
            self.parts.append(dict(attributes)['alt'])

    def handle_endtag(self, tag):
        if tag == 'main':
            self.in_notice = False
        if tag == 'h1':
            self.in_title = False

    def handle_data(self, data):
        if self.in_notice:
            self.parts.append(data)


def verify(document, title, blocks):
    parser = NoticeText()
    parser.feed(document)
    encoded = re.search(r'<script type="application/octet-stream" id="notice-pdf">([^<]+)</script>', document)
    if not encoded:
        raise ValueError('Missing embedded PDF')
    pdf = PdfReader(BytesIO(base64.b64decode(encoded.group(1), validate=True)))

    def normalized(text):
        return re.sub(r'\s+', '', text)

    expected = normalized(title+''.join(block_text(block) for block in blocks if block['kind'] != 'image'))
    if normalized(''.join(parser.parts)) != expected:
        raise ValueError('HTML text differs from the notice')
    if normalized(''.join(page.extract_text() for page in pdf.pages)) != expected:
        raise ValueError('PDF text differs from the notice; verify the input and selected fonts')
    return len(pdf.pages)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    windows_fonts = Path(os.environ.get('WINDIR', r'C:\Windows')) / 'Fonts'
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--font', type=Path, default=windows_fonts/'msjh.ttc')
    parser.add_argument('--bold-font', type=Path, default=windows_fonts/'msjhbd.ttc')
    args = parser.parse_args()
    if args.output.suffix.lower() != '.html':
        parser.error('--output must be an .html file')
    if not args.font.is_file() or not args.bold_font.is_file():
        parser.error('Specify installed Traditional Chinese TrueType fonts with --font and --bold-font')
    try:
        title, highlight, blocks = read_notice(args.input)
        brand = {name: (ASSETS/f'brand-{name}.png').read_bytes() for name in ('header', 'divider', 'footer')}
        title_png = title_image(title, args.bold_font, (ASSETS/'bell.png').read_bytes())
        pdf = render_pdf(title, highlight, blocks, brand, args.font, args.bold_font)
        tokens = {'TITLE': escape(title), 'ROWS': html_rows(title, highlight, blocks, brand, title_png),
                  'PDF': base64.b64encode(pdf).decode('ascii')}
        template = (ASSETS/'notice-template.html').read_text(encoding='utf-8')
        document = re.sub(r'@@(TITLE|ROWS|PDF)@@', lambda match: tokens[match[1]], template)
        pages = verify(document, title, blocks)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(document, encoding='utf-8')
        print(f'Generated one HTML with a {pages}-page Document.pdf download. Text parity verified.')
    except (OSError, ValueError) as error:
        parser.exit(1, f'Cannot generate notice: {error}\n')


if __name__ == '__main__':
    main()
