"""AgriAgent-Bench 开题答辩 PPT 生成器。

以 slidep 生成的合法空白文稿为底版，直接写入 OOXML 页面，
规避本机 SWC 原生模块的安全校验问题。

坐标系统：1280x720 px（与设计稿一致），内部换算为 EMU。
字号：px -> pt 按 0.75 换算（1280px 宽 = 960pt）。
"""

import os
import shutil
import zipfile
from xml.sax.saxutils import escape

EMU = 9525          # 1 px = 9525 EMU (96 dpi)
W, H = 1280, 720
FONT_CN = "Microsoft YaHei"
FONT_EN = "Arial"

NS = ('xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"')


def e(v):
    return int(round(v * EMU))


class Slide:
    def __init__(self):
        self.items = []
        self._id = 2
        self.images = []        # [(rId, 文件名, 本地路径), ...]

    def _nid(self):
        self._id += 1
        return self._id

    def rect(self, x, y, w, h, fill=None, line=None, lw=1.0, radius=None):
        sid = self._nid()
        geom = f'<a:prstGeom prst="roundRect"><a:avLst><a:gd name="adj" fmla="val {radius}"/></a:avLst></a:prstGeom>' \
            if radius is not None else '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
        spPr = f'<a:xfrm><a:off x="{e(x)}" y="{e(y)}"/><a:ext cx="{e(w)}" cy="{e(h)}"/></a:xfrm>' + geom
        if fill:
            spPr += f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>'
        else:
            spPr += '<a:noFill/>'
        if line:
            spPr += f'<a:ln w="{int(lw*EMU)}"><a:solidFill><a:srgbClr val="{line}"/></a:solidFill></a:ln>'
        else:
            spPr += '<a:ln><a:noFill/></a:ln>'

        self.items.append(
            f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="S{sid}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr>{spPr}</p:spPr></p:sp>'
        )

    def text(self, x, y, w, h, runs, size=20, color="1A2230", bold=False,
             align="l", anchor="t", lnspc=1.35, spacing=0, wrap=True):
        """runs: 字符串，或 [(文本, {bold,color,size}), ...]"""
        sid = self._nid()
        if isinstance(runs, str):
            runs = [(runs, {})]

        body = ""
        for txt, style in runs:
            sz = style.get("size", size)
            b = style.get("bold", bold)
            c = style.get("color", color)
            body += (
                f'<a:r><a:rPr lang="zh-CN" altLang="en-US" sz="{int(sz*75)}" b="{1 if b else 0}" dirty="0"'
                f' spc="{int(spacing*75)}">'
                f'<a:solidFill><a:srgbClr val="{c}"/></a:solidFill>'
                f'<a:latin typeface="{FONT_EN}"/><a:ea typeface="{FONT_CN}"/></a:rPr>'
                f'<a:t>{escape(txt)}</a:t></a:r>'
            )

        algn = {"l": "l", "c": "ctr", "r": "r"}[align]
        self.items.append(
            f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="T{sid}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{e(x)}" y="{e(y)}"/><a:ext cx="{e(w)}" cy="{e(h)}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
            f'<p:txBody><a:bodyPr wrap="{"square" if wrap else "none"}" lIns="{e(2)}" tIns="{e(2)}" '
            f'rIns="{e(2)}" bIns="{e(2)}" anchor="{"ctr" if anchor=="c" else "b" if anchor=="b" else "t"}"/>'
            f'<a:lstStyle/><a:p><a:pPr algn="{algn}"><a:lnSpc><a:spcPct val="{int(lnspc*100000)}"/></a:lnSpc></a:pPr>'
            f'{body}</a:p></p:txBody></p:sp>'
        )

    def pic(self, x, y, w, h, path, name=None):
        """插入图片，按给定框等比铺满（不裁切）。"""
        sid = self._nid()
        rid = f"rId{10 + len(self.images)}"
        fname = os.path.basename(path)
        self.images.append((rid, fname, path))
        self.items.append(
            f'<p:pic><p:nvPicPr><p:cNvPr id="{sid}" name="{name or fname}"/>'
            f'<p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>'
            f'<p:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>'
            f'<p:spPr><a:xfrm><a:off x="{e(x)}" y="{e(y)}"/><a:ext cx="{e(w)}" cy="{e(h)}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>'
        )

    def to_xml(self):
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<p:sld {NS}><p:cSld><p:spTree>'
            '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
            '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>'
            '<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
            + "".join(self.items) +
            '</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>'
        )


def slide_rels(images=(), idx=1):
    extra = "".join(
        f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
        f'relationships/image" Target="../media/s{idx}_{fname}"/>'
        for rid, fname, _ in images
    )
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" '
            'Target="../slideLayouts/slideLayout1.xml"/>' + extra + '</Relationships>')


def build(template, out_path, slides):
    """在模板基础上写入 slides（Slide 对象列表）。"""
    tmp = out_path + ".tmp"

    with zipfile.ZipFile(template) as zin:
        names = zin.namelist()
        data = {n: zin.read(n) for n in names}

    n = len(slides)
    for i, s in enumerate(slides, start=1):
        data[f"ppt/slides/slide{i}.xml"] = s.to_xml().encode("utf-8")
        data[f"ppt/slides/_rels/slide{i}.xml.rels"] = slide_rels(s.images, i).encode("utf-8")
        for _, fname, path in s.images:
            with open(path, "rb") as f:
                data[f"ppt/media/s{i}_{fname}"] = f.read()

    # presentation.xml：插入 sldIdLst
    pres = data["ppt/presentation.xml"].decode("utf-8")
    sld_ids = "".join(
        f'<p:sldId id="{255+i}" r:id="rId{100+i}"/>' for i in range(1, n + 1)
    )
    if "<p:sldIdLst>" in pres:
        pres = pres.replace("<p:sldIdLst></p:sldIdLst>", f"<p:sldIdLst>{sld_ids}</p:sldIdLst>")
    else:
        pres = pres.replace("<p:sldSz", f"<p:sldIdLst>{sld_ids}</p:sldIdLst><p:sldSz")
    data["ppt/presentation.xml"] = pres.encode("utf-8")

    # presentation.xml.rels：追加 slide 关系
    rels = data["ppt/_rels/presentation.xml.rels"].decode("utf-8")
    add = "".join(
        f'<Relationship Id="rId{100+i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" '
        f'Target="slides/slide{i}.xml"/>' for i in range(1, n + 1)
    )
    rels = rels.replace("</Relationships>", add + "</Relationships>")
    data["ppt/_rels/presentation.xml.rels"] = rels.encode("utf-8")

    # [Content_Types].xml：追加 slide 覆盖项
    ct = data["[Content_Types].xml"].decode("utf-8")
    add = "".join(
        f'<Override PartName="/ppt/slides/slide{i}.xml" '
        f'ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
        for i in range(1, n + 1)
    )
    ct = ct.replace("</Types>", add + "</Types>")
    # 图片需要 png 的 Default 声明，模板默认只有 rels / xml
    if 'ContentType="image/png"' not in ct:
        ct = ct.replace("</Types>", '<Default Extension="png" ContentType="image/png"/></Types>')
    data["[Content_Types].xml"] = ct.encode("utf-8")

    order = [n for n in names if not n.endswith("/")]
    order += [k for k in data if k not in order]

    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for name in order:
            zout.writestr(name, data[name])

    shutil.move(tmp, out_path)
    return out_path
