"""把生成的 pptx 反向渲染成 HTML，用于视觉检查（不参与交付）。"""

import os
import zipfile
import xml.etree.ElementTree as ET

A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
P = '{http://schemas.openxmlformats.org/presentationml/2006/main}'
EMU = 9525.0

BASE = os.path.dirname(os.path.abspath(__file__))


def parse_slide(z, idx):
    root = ET.fromstring(z.read(f"ppt/slides/slide{idx}.xml"))
    boxes = []
    for sp in root.iter(P + 'sp'):
        off = sp.find('.//' + A + 'off')
        ext = sp.find('.//' + A + 'ext')
        if off is None:
            continue
        x = int(off.get('x')) / EMU
        y = int(off.get('y')) / EMU
        cx = int(ext.get('cx')) / EMU
        cy = int(ext.get('cy')) / EMU

        spPr = sp.find(P + 'spPr')
        fill = None
        for c in spPr.iter(A + 'srgbClr'):
            fill = '#' + c.get('val')
            break
        stroke = None
        ln = spPr.find(A + 'ln')
        if ln is not None:
            for c in ln.iter(A + 'srgbClr'):
                stroke = '#' + c.get('val')
                break

        body = sp.find(P + 'txBody')
        if body is None:
            boxes.append(dict(kind='rect', x=x, y=y, w=cx, h=cy, fill=fill, stroke=stroke, lw=1))
            continue

        # 收集段落
        paras = []
        for p in body.iter(A + 'p'):
            runs = []
            pPr = p.find(A + 'pPr')
            algn = pPr.get('algn', 'l') if pPr is not None else 'l'
            lnspc = 1.35
            sp_ = pPr.find(A + 'lnSpc') if pPr is not None else None
            if sp_ is not None:
                pct = sp_.find(A + 'spcPct')
                if pct is not None:
                    lnspc = int(pct.get('val')) / 100000
            for r in p.iter(A + 'r'):
                t = r.find(A + 't')
                rPr = r.find(A + 'rPr')
                sz = int(rPr.get('sz')) / 100 if rPr is not None and rPr.get('sz') else 12
                b = rPr is not None and rPr.get('b') == '1'
                col = '#1A2230'
                if rPr is not None:
                    for c in rPr.iter(A + 'srgbClr'):
                        col = '#' + c.get('val')
                        break
                runs.append(dict(t=t.text or '', sz=sz / 0.75, b=b, col=col))
            if runs:
                paras.append(dict(runs=runs, algn=algn, lnspc=lnspc))

        bodyPr = body.find(A + 'bodyPr')
        anchor = bodyPr.get('anchor', 't') if bodyPr is not None else 't'
        if paras:
            boxes.append(dict(kind='text', x=x, y=y, w=cx, h=cy,
                              paras=paras, anchor=anchor))
    return boxes


CSS_ALIGN = {'l': 'left', 'ctr': 'center', 'r': 'right'}
CSS_ANCHOR = {'t': 'flex-start', 'ctr': 'center', 'b': 'flex-end'}


def boxes_to_html(boxes):
    out = []
    for b in boxes:
        if b['kind'] == 'rect':
            style = (f"position:absolute;left:{b['x']:.1f}px;top:{b['y']:.1f}px;"
                     f"width:{b['w']:.1f}px;height:{b['h']:.1f}px;")
            if b['fill']:
                style += f"background:{b['fill']};"
            if b['stroke']:
                style += f"border:1px solid {b['stroke']};box-sizing:border-box;"
            out.append(f'<div style="{style}"></div>')
        else:
            first = b['paras'][0]['runs'][0]
            ana = CSS_ANCHOR.get(b['anchor'], 'flex-start')
            style = (f"position:absolute;left:{b['x']:.1f}px;top:{b['y']:.1f}px;"
                     f"width:{b['w']:.1f}px;height:{b['h']:.1f}px;"
                     f"display:flex;align-items:{ana};font-family:'Microsoft YaHei',sans-serif;"
                     f"overflow:hidden;")
            out.append(f'<div style="{style}">')
            out.append(f'<div style="width:100%;">')
            for para in b['paras']:
                al = CSS_ALIGN.get(para['algn'], 'left')
                out.append(f'<div style="text-align:{al};line-height:{para["lnspc"]};">')
                for r in para['runs']:
                    w = 'font-weight:700;' if r['b'] else ''
                    out.append(f'<span style="font-size:{r["sz"]:.1f}px;color:{r["col"]};{w}">'
                               f'{r["t"]}</span>')
                out.append('</div>')
            out.append('</div></div>')
    return ''.join(out)


def main():
    z = zipfile.ZipFile(os.path.join(BASE, "AgriAgent-Bench_开题答辩_终稿.pptx"))
    parts = []
    for i in range(1, 16):
        inner = boxes_to_html(parse_slide(z, i))
        parts.append(
            f'<div style="position:relative;width:1280px;height:720px;overflow:hidden;'
            f'background:#fff;margin:0 0 24px 0;outline:1px solid #bbb;">{inner}</div>'
        )
    html = ('<!DOCTYPE html><html><head><meta charset="utf-8">'
            '<style>body{margin:0;background:#e9edf2;padding:20px;'
            'font-family:"Microsoft YaHei",sans-serif;}</style></head><body>'
            + ''.join(parts) + '</body></html>')
    out = os.path.join(BASE, "preview.html")
    open(out, "w", encoding="utf-8").write(html)
    print("wrote", out)


if __name__ == "__main__":
    main()
