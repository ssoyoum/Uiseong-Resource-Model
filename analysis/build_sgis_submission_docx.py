"""Create the five-page SGIS excellent-use-case submission form document."""

from __future__ import annotations

import json
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Mm, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "submission" / "sgis-uiseong-excellent-use-case-submission.docx"
ANALYSIS_DIR = ROOT / "data" / "analysis"
FIGURE_DIR = ROOT / "analysis" / "figures"

FONT_BODY = "휴먼명조"
FONT_HEADING = "HY헤드라인M"
INK = RGBColor(31, 41, 55)
MUTED = RGBColor(75, 85, 99)
ACCENT = "1F4E79"
LIGHT_FILL = "EAF2F8"
SOFT_FILL = "F5F7FA"
TABLE_WIDTH_DXA = 9638  # A4 210 mm - 20 mm left/right margins.


def set_east_asia_font(run, name: str, size: float, bold: bool | None = None, color: RGBColor | None = None):
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), name)
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), name)
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if color is not None:
        run.font.color.rgb = color


def set_style_font(style, name: str, size: float, bold: bool | None = None, color: RGBColor | None = None):
    style.font.name = name
    style._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), name)
    style._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), name)
    style._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), name)
    style.font.size = Pt(size)
    if bold is not None:
        style.font.bold = bold
    if color is not None:
        style.font.color.rgb = color


def set_cell_shading(cell, fill: str):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=80, start=120, bottom=80, end=120):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for margin, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{margin}"))
        if node is None:
            node = OxmlElement(f"w:{margin}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_table_geometry(table, widths: list[int], header=True):
    if sum(widths) != TABLE_WIDTH_DXA:
        raise ValueError(f"Table widths must sum to {TABLE_WIDTH_DXA}: {widths}")
    table.autofit = False
    tbl = table._tbl
    tbl_pr = tbl.tblPr
    tbl_w = tbl_pr.find(qn("w:tblW"))
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tbl_pr.append(tbl_w)
    tbl_w.set(qn("w:w"), str(TABLE_WIDTH_DXA))
    tbl_w.set(qn("w:type"), "dxa")
    tbl_ind = tbl_pr.find(qn("w:tblInd"))
    if tbl_ind is None:
        tbl_ind = OxmlElement("w:tblInd")
        tbl_pr.append(tbl_ind)
    tbl_ind.set(qn("w:w"), "120")
    tbl_ind.set(qn("w:type"), "dxa")
    layout = tbl_pr.find(qn("w:tblLayout"))
    if layout is None:
        layout = OxmlElement("w:tblLayout")
        tbl_pr.append(layout)
    layout.set(qn("w:type"), "fixed")
    grid = tbl.tblGrid
    for child in list(grid):
        grid.remove(child)
    for width in widths:
        col = OxmlElement("w:gridCol")
        col.set(qn("w:w"), str(width))
        grid.append(col)
    for row_index, row in enumerate(table.rows):
        if header and row_index == 0:
            tr_pr = row._tr.get_or_add_trPr()
            tbl_header = tr_pr.find(qn("w:tblHeader"))
            if tbl_header is None:
                tbl_header = OxmlElement("w:tblHeader")
                tr_pr.append(tbl_header)
            tbl_header.set(qn("w:val"), "true")
        for index, cell in enumerate(row.cells):
            cell.width = Inches(widths[index] / 1440)
            tc_pr = cell._tc.get_or_add_tcPr()
            tc_w = tc_pr.find(qn("w:tcW"))
            if tc_w is None:
                tc_w = OxmlElement("w:tcW")
                tc_pr.append(tc_w)
            tc_w.set(qn("w:w"), str(widths[index]))
            tc_w.set(qn("w:type"), "dxa")
            set_cell_margins(cell)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            if header and row_index == 0:
                set_cell_shading(cell, LIGHT_FILL)
                for paragraph in cell.paragraphs:
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    for run in paragraph.runs:
                        set_east_asia_font(run, FONT_BODY, 11.5, bold=True, color=INK)


def add_table(doc: Document, headers: list[str], rows: list[list[str]], widths: list[int]):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    for index, value in enumerate(headers):
        cell = table.rows[0].cells[index]
        cell.text = value
    for row_values in rows:
        cells = table.add_row().cells
        for index, value in enumerate(row_values):
            cells[index].text = value
            for paragraph in cells[index].paragraphs:
                paragraph.paragraph_format.line_spacing = 1.15
                paragraph.paragraph_format.space_after = Pt(0)
                for run in paragraph.runs:
                    set_east_asia_font(run, FONT_BODY, 11.2, color=INK)
    set_table_geometry(table, widths)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    return table


def add_paragraph(doc: Document, text: str, *, bold_prefix: str | None = None, size=15, after=5, align=None):
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.line_spacing = 1.6
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(after)
    if align is not None:
        paragraph.alignment = align
    if bold_prefix and text.startswith(bold_prefix):
        first = paragraph.add_run(bold_prefix)
        set_east_asia_font(first, FONT_BODY, size, bold=True, color=INK)
        rest = paragraph.add_run(text[len(bold_prefix):])
        set_east_asia_font(rest, FONT_BODY, size, color=INK)
    else:
        run = paragraph.add_run(text)
        set_east_asia_font(run, FONT_BODY, size, color=INK)
    return paragraph


def add_heading(doc: Document, text: str, level=1):
    paragraph = doc.add_paragraph(style=f"Heading {level}")
    paragraph.paragraph_format.keep_with_next = True
    run = paragraph.add_run(text)
    set_east_asia_font(run, FONT_HEADING, 16, bold=True, color=INK)
    return paragraph


def add_caption(doc: Document, text: str):
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.line_spacing = 1.15
    paragraph.paragraph_format.space_before = Pt(1)
    paragraph.paragraph_format.space_after = Pt(5)
    run = paragraph.add_run(text)
    set_east_asia_font(run, FONT_BODY, 10.5, color=MUTED)
    return paragraph


def add_figure(doc: Document, filename: str, caption: str, width_inches: float):
    path = FIGURE_DIR / filename
    if not path.is_file() or path.stat().st_size == 0:
        raise FileNotFoundError(path)
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(2)
    paragraph.paragraph_format.space_after = Pt(0)
    run = paragraph.add_run()
    inline = run.add_picture(str(path), width=Inches(width_inches))
    inline._inline.docPr.set("descr", caption)
    add_caption(doc, caption)


def add_page_number(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run("- ")
    set_east_asia_font(run, FONT_BODY, 9, color=MUTED)
    fld_char1 = OxmlElement("w:fldChar")
    fld_char1.set(qn("w:fldCharType"), "begin")
    instr_text = OxmlElement("w:instrText")
    instr_text.set(qn("xml:space"), "preserve")
    instr_text.text = " PAGE "
    fld_char2 = OxmlElement("w:fldChar")
    fld_char2.set(qn("w:fldCharType"), "end")
    run._r.append(fld_char1)
    run._r.append(instr_text)
    run._r.append(fld_char2)
    run2 = paragraph.add_run(" -")
    set_east_asia_font(run2, FONT_BODY, 9, color=MUTED)


def configure_document(doc: Document):
    section = doc.sections[0]
    section.page_width = Mm(210)
    section.page_height = Mm(297)
    section.top_margin = Mm(10)
    section.bottom_margin = Mm(10)
    section.left_margin = Mm(20)
    section.right_margin = Mm(20)
    section.header_distance = Mm(10)
    section.footer_distance = Mm(10)

    normal = doc.styles["Normal"]
    set_style_font(normal, FONT_BODY, 15, color=INK)
    normal.paragraph_format.line_spacing = 1.6
    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.space_after = Pt(5)
    for level, before, after in ((1, 8, 4), (2, 5, 2)):
        style = doc.styles[f"Heading {level}"]
        set_style_font(style, FONT_HEADING, 16, bold=True, color=INK)
        style.paragraph_format.line_spacing = 1.6
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)
    footer = section.footer
    add_page_number(footer.paragraphs[0])


def build():
    sgis = json.loads((ANALYSIS_DIR / "sgis_catchment_analysis.json").read_text(encoding="utf-8"))
    comparison = json.loads((ANALYSIS_DIR / "sgis_policy_comparison.json").read_text(encoding="utf-8"))
    validation = json.loads((ANALYSIS_DIR / "validation_report.json").read_text(encoding="utf-8"))
    claims = json.loads((ANALYSIS_DIR / "submission_claims_report.json").read_text(encoding="utf-8"))

    doc = Document()
    configure_document(doc)

    # Page 1: form opening sections.
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_before = Pt(0)
    title.paragraph_format.space_after = Pt(10)
    title_run = title.add_run("SGIS 지역통계를 활용한 인구감소지역 유휴자원 활용정책 제안 — 의성군 전통 못 사례를 중심으로")
    set_east_asia_font(title_run, FONT_HEADING, 16, bold=True, color=INK)

    add_heading(doc, "□ 추진배경 및 필요성")
    add_paragraph(doc, "인구감소지역에서는 지역자원이 존재하더라도 인구구조와 생활권 수요, 접근성, 주변 인프라가 연결되지 않으면 실제 활용으로 이어지기 어렵다. 의성군은 기존 연구를 통해 427개 전통 못의 위치와 기초 특성을 구축했지만, 개별 자원이 어떤 지역 수요와 연결될 수 있는지 설명하는 근거가 추가로 필요했다.")
    add_paragraph(doc, "본 사례는 SGIS 생활권역 주행인구와 행정안전부 읍면 인구, VWorld 도로·공공·문화·관광시설 자료를 결합해 의성군 전통 못의 활용 가능성을 검토한다. 목표는 자동 추천점수나 전국 전수모델을 제시하는 것이 아니라, 지역통계와 공간자원을 연결하는 재현 가능한 정책 접근방향을 제시하는 데 있다.")

    add_heading(doc, "□ 추진과정")
    add_paragraph(doc, "첫째, 의성군 경계 내 전통 못 427개를 분석대상으로 확정하고 시설·주소·좌표 품질을 점검했다. 둘째, SGIS 인증과 생활권역 API를 이용해 시설별 5분·10분 주행생활권 인구를 반복 수집했다. 셋째, 도로 접근성, 주변 시설·농업지역, 읍면 인구구조, 활용유형 분류를 연결하고 정책 검토 맥락을 도출했다. 넷째, 결측·좌표·기준연도·통계 정의 차이를 별도 관리한 뒤 보고서와 시각화 산출물을 검증했다.")

    add_heading(doc, "□ 활용분야 및 주요내용")
    add_paragraph(doc, "활용분야는 공공정책 및 연구·교육이다. 주요내용은 SGIS 5분·10분 생활권 인구를 이용한 도달 규모 분석, 427개 전통 못과 도로·주변시설의 공간분석, 청년·고령 지역특성과 활용 가능성의 연결, 그리고 좌표·결측·출처를 포함한 재현 가능한 정책 검토 절차다.")

    doc.add_page_break()

    # Page 2: methods and verified data.
    add_heading(doc, "□ 추진내용")
    add_heading(doc, "1. 자료 구축 및 분석 설계", level=2)
    add_paragraph(doc, "분석은 원자료를 우선 사용하고, 확보되지 않은 지표는 임의값으로 대체하지 않는 원칙으로 수행했다. 행정안전부 자료는 2024년 12월·2025년 12월 읍면 집계로 관리하고, SGIS 생활권역 주행인구는 주민등록 인구격자나 Buffer 인구와 구분했다. VWorld 자료는 의성군 범위로 Clip하고 거리·면적 계산은 EPSG:5174, 웹 지도 출력은 EPSG:4326으로 통일했다.")
    add_table(
        doc,
        ["검토 항목", "확인 결과", "해석 기준"],
        [
            ["분석 시설", "427개 / 고유 ID 427개", "전체 대상 누락 없이 연결"],
            ["VWorld 공간자료", "시설 68개 / 도로 483개", "의성군 범위·geometry 검증"],
            ["SGIS 생활권역", "5분 175개 / 10분 190개 / 양쪽 175개", "응답이 있는 검증좌표만 비교"],
            ["행정 인구", "18개 읍면, 2024·2025년", "청년 19~39세·고령 65세 이상"],
            ["분류 결과", "보존·기록 329 / 문화·관광 55 / 생태·교육 43", "규칙기반 1개 라벨, ML 정확도 아님"],
        ],
        [2100, 2600, 4938],
    )
    add_heading(doc, "2. 추진 흐름", level=2)
    add_paragraph(doc, "분석 흐름은 지역 특성·수요 확인에서 시작해 427개 못의 공간 특성, 도로 접근성, 주변 인프라, SGIS 생활권역 도달 규모를 순차적으로 결합하는 방식이다. 정책 방향은 분석 이후 검토 가설로 제시하며, 관리상태·보존가치·현장 수요가 확인되기 전에는 확정하지 않았다.")
    add_paragraph(doc, "SGIS는 427개 시설에 대해 총 854개 시간대 조합을 요청했다. 결과가 제공되지 않은 399개는 위치 인식 실패 384개와 생활권역은 생성됐으나 인구 필드가 없는 15개로 분리했으며, 모두 0명으로 바꾸지 않았다.", bold_prefix="SGIS는")

    doc.add_page_break()

    # Page 3: policy interpretation and quality limitations.
    add_heading(doc, "□ 추진내용")
    add_heading(doc, "3. SGIS 기반 정책 해석", level=2)
    add_paragraph(doc, "SGIS 연결 전후의 차이는 정책을 자동 결정하는 데 있지 않고, 기존 읍면 인구·도로·주변시설 맥락에 시설별 도달 규모와 5분에서 10분으로 확장되는 수요 신호를 추가하는 데 있다. 최종 정책 검토 맥락은 시설별 하나만 부여해 합계를 427개로 검증했다.")
    add_table(
        doc,
        ["정책 검토 맥락", "시설 수", "근거와 다음 확인"],
        [
            ["청년 참여 검토", "43", "청년비율 상위 + SGIS 응답; 실제 청년 수요·관리상태 확인"],
            ["공동체 지원 검토", "53", "고령비율 상위 + 매핑시설 없음; 시설 누락·운영상태 확인"],
            ["접근·도달 검토", "20", "10분 도달·확장 상위; 관광·도로 연결성과 현장수요 확인"],
            ["CONTEXT_ONLY", "74", "기존 지역·공간 맥락만 확인; 직접 SGIS 정책 신호 없음"],
            ["FIELD_REVIEW_REQUIRED", "47", "좌표 품질 문제; 좌표 보정 후 재검토"],
            ["INSUFFICIENT_SGIS_10MIN", "190", "10분 인구 미확보; 0명·낮은 수요로 해석하지 않음"],
        ],
        [2500, 1100, 6038],
    )
    add_paragraph(doc, "정책 검토 그룹의 합계는 43 + 53 + 20 + 74 + 47 + 190 = 427개다. 이 그룹은 상호배타적이지만, 별도 SGIS 증거 flag인 10분 상위 25%와 5→10분 증가폭 상위 25%는 중복될 수 있으며 실제 중복은 42개다.")

    add_heading(doc, "4. 결측·좌표 이슈 및 처리", level=2)
    add_paragraph(doc, "대표점·인근좌표·중복좌표가 포함되어 좌표 품질 검증 후 380개 고유 좌표만 추론 요약에 사용했고, 47개는 현장·공식 원자료 확인 대상으로 남겼다. 좌표 보정 전에는 SGIS 순위나 정책 결론을 확정하지 않는다.")
    add_paragraph(doc, "공식 인구격자 원자료가 확보되지 않아 500m·1km Buffer 주민인구는 산출하지 않았다. SGIS 주행생활권 인구, 행정 읍면 인구, 공식 격자 인구는 공간단위와 정의가 다르므로 각각 별도 지표로 기록했다. 상세 품질 이슈와 잔여 한계는 `docs/data-quality.md`에 보존했다.")

    doc.add_page_break()

    # Page 4: visual evidence.
    add_heading(doc, "□ 추진내용")
    add_heading(doc, "5. 시각화자료", level=2)
    add_paragraph(doc, "시각화는 위치 분포, 도로 접근성, 분류 결과, SGIS 생활권역 인구를 단계별로 확인할 수 있도록 구성했다. 아래 그림은 제출용 대표 시각화이며, 전체 그림의 출처·상태·해석 주의점은 `data/analysis/submission_visualization_manifest.json`에 기록했다.")
    add_figure(doc, "06_pond_distribution.png", "그림 1. 의성군 전통 못 427개 공간 분포", 4.45)
    add_figure(doc, "07_pond_road_accessibility.png", "그림 2. UQ151 도로 기준 못-도로 최근접거리 접근성", 4.45)
    add_paragraph(doc, "그림 2의 거리는 EPSG:5174 미터 단위 유클리드 최근접거리이며 주행 네트워크 거리나 5분·10분 이동시간을 의미하지 않는다.", size=11.5, after=0)

    doc.add_page_break()

    # Page 5: outcomes, two additional figures, and evidence.
    add_heading(doc, "□ 추진성과")
    add_paragraph(doc, "첫째, 427개 전통 못을 기준으로 SGIS 생활권역 주행인구를 반복 처리하고, 5분·10분 도달 규모를 기존 공간분석에 연결했다. 둘째, SGIS 미확보 399건을 위치 인식 실패 384건과 인구 필드 미제공 15건으로 분리해 결측 원인을 설명할 수 있게 했다. 셋째, 정책 검토 그룹과 규칙기반 활용유형을 별도 체계로 관리해 합계·중복·미확보 범위를 검증했다.")
    add_figure(doc, "09_pond_classification.png", "그림 3. 규칙기반 전통 못 활용유형 분류", 3.2)
    add_figure(doc, "11_sgis_5_vs_10_population.png", "그림 4. SGIS 5분·10분 생활권 인구 비교", 3.2)
    add_paragraph(doc, "최종 분석 파이프라인은 `PASS`, 공간·필수값 검증은 16 PASS / 0 FAIL(좌표 중복 WARN 1건), 제출근거 검증은 17 PASS / 0 WARN / 0 FAIL이다. 결과물은 보고서, 정책 해석표, CSV·JSON·GeoJSON·GPKG·PNG로 재현 가능하게 보관했다.")
    add_paragraph(doc, "다만 좌표 보정, 현장관리상태·보존가치·실제 서비스 수요 대조, 공식 인구격자 확보, VWorld 라이선스·snapshot 확인은 후속 검증 대상이다. 따라서 본 성과는 정책 확정이 아니라 SGIS와 지역자원을 연결한 검토 근거 및 의성 Case Study 성과로 제시한다.")
    source = doc.add_paragraph()
    source.paragraph_format.line_spacing = 1.15
    source.paragraph_format.space_before = Pt(3)
    source.paragraph_format.space_after = Pt(0)
    run = source.add_run("근거자료: data/analysis/validation_report.json, data/analysis/submission_claims_report.json, data/analysis/sgis_policy_comparison.json, data/analysis/submission_visualization_manifest.json")
    set_east_asia_font(run, FONT_BODY, 10, color=MUTED)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)
    print(json.dumps({"output": str(OUTPUT), "status": "CREATED"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    from build_sgis_final_document import build as build_final
    build_final()
