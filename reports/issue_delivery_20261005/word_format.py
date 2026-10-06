"""純文書轉換函數，由 setup_run 入口呼叫；不包含研究計算。"""
import hashlib
import re
import zipfile
from pathlib import Path

def inline(value):
    value = value.replace(chr(96), "").replace("**", "")
    parts = []
    cursor = 0
    pattern = re.compile(r"\[([^\]]+)\]\((https?://)")
    while (match := pattern.search(value, cursor)):
        start = match.end(1)+2
        index = start
        depth = 0
        while index < len(value):
            token = value[index]
            if token == "(": depth += 1
            if token == ")":
                if depth == 0: break
                depth -= 1
            index += 1
        if index == len(value): break
        parts.append((value[cursor:match.start()], None))
        parts.append((match[1], value[start:index]))
        cursor = index+1
    parts.append((value[cursor:], None))
    return parts

def visible(value):
    return "".join(text for text, url in inline(value))

def make_word(markdown, destination):
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
    from docx.opc.constants import RELATIONSHIP_TYPE as RT
    document = Document()
    section = document.sections[0]
    section.page_width = Inches(8.27); section.page_height = Inches(11.69)
    section.top_margin = section.bottom_margin = Inches(.7)
    section.left_margin = section.right_margin = Inches(.6)
    for name in ["Normal","Title","Heading 1","Heading 2","Heading 3"]:
        style = document.styles[name]
        style.font.name = "Calibri"; style.font.color.rgb = RGBColor(0,0,0)
        style.font.size = Pt(11 if name == "Normal" else 21 if name == "Title" else 14 if name == "Heading 1" else 12)
        fonts = OxmlElement("w:rFonts"); fonts.set(qn("w:eastAsia"),"Microsoft JhengHei")
        style.element.get_or_add_rPr().append(fonts)
        style.paragraph_format.space_after = Pt(6)
        style.paragraph_format.line_spacing = 1.1
        style.paragraph_format.widow_control = True
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run("Lineage　")
    field = OxmlElement("w:fldSimple"); field.set(qn("w:instr"),"PAGE"); footer._p.append(field)
    def text(p, value):
        for label, url in inline(value):
            if not url: p.add_run(label); continue
            link = OxmlElement("w:hyperlink")
            link.set(qn("r:id"),p.part.relate_to(url,RT.HYPERLINK,is_external=True))
            run = OxmlElement("w:r"); content = OxmlElement("w:t")
            content.text = label; run.append(content); link.append(run); p._p.append(link)
    expected, equations = [], 0
    lines = markdown.splitlines(); index = 0
    while index < len(lines):
        line = lines[index]; index += 1
        if not line.strip(): continue
        if line in {"PAGE_BREAK", "<!-- PAGE_BREAK -->"}: document.add_page_break(); continue
        if line.startswith("|"):
            block = [line]
            while index < len(lines) and lines[index].startswith("|"):
                block.append(lines[index]); index += 1
            cells = [[part.strip() for part in row.strip("|").split("|")] for row in [block[0],*block[2:]]]
            if any(len(row) != len(cells[0]) for row in cells): raise ValueError("Markdown 表格欄數不符")
            expected.append([[visible(v) for v in row] for row in cells])
            table = document.add_table(rows=0, cols=len(cells[0])); table.autofit = False
            weights = [max(5,min(24, sum(len(visible(row[col])) for row in cells)/len(cells))) for col in range(len(cells[0]))]
            widths = [7.07*weight/sum(weights) for weight in weights]
            for col, width in zip(table.columns, widths): col.width = Inches(width)
            for row_index, row in enumerate(cells):
                new = table.add_row()
                if row_index == 0:
                    repeat = OxmlElement("w:tblHeader"); new._tr.get_or_add_trPr().append(repeat)
                for column, (cell, value) in enumerate(zip(new.cells,row)):
                    cell.width = Inches(widths[column]); cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                    properties = cell._tc.get_or_add_tcPr()
                    margins = OxmlElement("w:tcMar")
                    for side in ["top","bottom","left","right"]:
                        prop = OxmlElement("w:"+side); prop.set(qn("w:w"),"85"); prop.set(qn("w:type"),"dxa"); margins.append(prop)
                    properties.append(margins)
                    if row_index == 0:
                        shade = OxmlElement("w:shd"); shade.set(qn("w:fill"),"E8EEF5"); properties.append(shade)
                    p = cell.paragraphs[0]; text(p,value)
                    if len(visible(value)) < 18: p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p.paragraph_format.space_after = Pt(3)
                    p.paragraph_format.line_spacing = 1.05
                    for run in p.runs: run.font.size = Pt(10)
            borders = OxmlElement("w:tblBorders")
            for side in ["top","bottom","left","right","insideH","insideV"]:
                border = OxmlElement("w:"+side); border.set(qn("w:val"),"single")
                border.set(qn("w:sz"),"4"); border.set(qn("w:color"),"D9D9D9"); borders.append(border)
            table._tbl.tblPr.append(borders)
            document.add_paragraph()
        elif line.startswith("EQUATION:"):
            equations += 1
            p = document.add_paragraph(); math = OxmlElement("m:oMath"); run = OxmlElement("m:r"); value = OxmlElement("m:t")
            value.text = line.partition(":")[2].strip(); run.append(value); math.append(run); p._p.append(math)
        elif line.startswith("#"):
            level = len(line)-len(line.lstrip("#"))
            title = line[level:].strip()
            # 標題只保留文字、數字與空格；正文及引用維持原內容。
            title = re.sub(r"[^\w\s\u3400-\u9fff]", " ", title)
            text(document.add_paragraph(style="Title" if level == 1 else "Heading "+str(min(level-1,3))), title)
        else: text(document.add_paragraph(),line)
    document.core_properties.title = visible(lines[0].lstrip("# "))
    document.core_properties.author = "Lineage"
    destination = Path(destination); document.save(destination)
    opened = Document(destination)
    actual = [[[cell.text for cell in row.cells] for row in table.rows] for table in opened.tables]
    if actual != expected: raise ValueError("Word 表格逐格不符 Markdown")
    with zipfile.ZipFile(destination) as archive:
        if archive.testzip(): raise ValueError("DOCX CRC 不符")
        xml = archive.read("word/document.xml").decode("utf-8")
        if xml.count("<m:oMath>") != equations: raise ValueError("公式數不符")
        if "word/media/" in "\n".join(archive.namelist()): raise ValueError("文字不應轉成整頁圖片")
    return dict(path=str(destination),sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),
                editable_tables=len(expected),table_rows=sum(map(len,expected)),all_table_cells_exact=True,
                native_equations=equations,explicit_page_breaks=markdown.count("PAGE_BREAK"),
                structural_status="PASS",layout_status="NOT_RENDERED",page_count=None)
