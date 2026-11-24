"""Word COM layout helper (shared styling with Sandvik EngD portfolio)."""
from __future__ import annotations

from pathlib import Path

import win32com.client

CM = 28.3465
PAGE_W, PAGE_H = 595.28, 841.89
MARGIN = 2.0 * CM
TEXT_W_CM = 17.0
NAVY = (31, 56, 100)
TEAL = (0, 120, 130)
GREY = (89, 89, 89)
RULE = (191, 191, 191)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
FONT = "Calibri"
BODY_PT = 11
S_NORMAL, S_H1, S_H2 = -1, -2, -3
S_TITLE, S_SUBTITLE, S_CAPTION, S_BULLET = -63, -75, -35, -49
ALIGN_L, ALIGN_C = 0, 1
B_TOP, B_LEFT, B_BOTTOM, B_RIGHT, B_HORIZ, B_VERT = -1, -2, -3, -4, -5, -6


def rgb(t: tuple[int, int, int]) -> int:
    return t[0] | (t[1] << 8) | (t[2] << 16)


def n3(x: float) -> str:
    return f"{x:.1f}".replace("-", "\u2212")


class Doc:
    def __init__(self) -> None:
        self.word = win32com.client.Dispatch("Word.Application")
        self.word.Visible = False
        self.word.DisplayAlerts = 0
        self.word.Documents.Add()
        self.doc = self.word.ActiveDocument
        self.fig_n = 0
        self.tab_n = 0
        self._page_setup()
        self._styles()

    def _page_setup(self) -> None:
        for sec in self.doc.Sections:
            ps = sec.PageSetup
            ps.PageWidth, ps.PageHeight = PAGE_W, PAGE_H
            ps.TopMargin = ps.BottomMargin = MARGIN
            ps.LeftMargin = ps.RightMargin = MARGIN
            ps.FooterDistance = 28
            sec.Footers(1).PageNumbers.Add(ALIGN_C, True)
            try:
                hf = sec.Headers(1)
                hf.LinkToPrevious = False
                hf.Range.Text = "Nikhil Hase | Research evidence portfolio | "
                hf.Range.Font.Name = FONT
                hf.Range.Font.Size = 8
                hf.Range.Font.Color = rgb(GREY)
                hf.Range.ParagraphFormat.Alignment = ALIGN_C
            except Exception:
                pass

    def _font(self, st, size, bold=False, italic=False, color=BLACK) -> None:
        st.Font.Name = FONT
        st.Font.Size = size
        st.Font.Bold = bold
        st.Font.Italic = italic
        st.Font.Color = rgb(color)

    def _styles(self) -> None:
        d = self.doc
        n = d.Styles(S_NORMAL)
        self._font(n, BODY_PT)
        pf = n.ParagraphFormat
        pf.LineSpacingRule = 5
        pf.LineSpacing = 13.8
        pf.SpaceBefore, pf.SpaceAfter = 0, 6
        pf.Alignment = ALIGN_L
        for sid, size, before, after in ((S_H1, 15, 16, 6), (S_H2, 12, 10, 3)):
            st = d.Styles(sid)
            self._font(st, size, bold=True, color=NAVY)
            st.ParagraphFormat.SpaceBefore = before
            st.ParagraphFormat.SpaceAfter = after
            st.ParagraphFormat.KeepWithNext = True
        h1b = d.Styles(S_H1).ParagraphFormat.Borders(B_BOTTOM)
        h1b.LineStyle = 1
        h1b.LineWidth = 6
        h1b.Color = rgb(TEAL)
        t = d.Styles(S_TITLE)
        self._font(t, 22, bold=True, color=NAVY)
        s = d.Styles(S_SUBTITLE)
        self._font(s, 13, color=TEAL)
        c = d.Styles(S_CAPTION)
        self._font(c, 9.5, color=GREY)
        b = d.Styles(S_BULLET)
        self._font(b, BODY_PT)

    def _last(self):
        return self.doc.Paragraphs.Last.Range

    def _new_para(self) -> None:
        self.doc.Content.InsertParagraphAfter()

    def add(self, text, style=S_NORMAL, align=None, lead=None, italic=False, color=None, size=None,
            space_after=None, space_before=None, page_break=False, links=None) -> None:
        rng = self._last()
        full = (lead + " " if lead else "") + text
        rng.InsertBefore(full)
        rng = self._last()
        rng.Style = self.doc.Styles(style)
        rng.Font.Reset()
        rng.ParagraphFormat.Reset()
        start = rng.Start
        if align is not None:
            rng.ParagraphFormat.Alignment = align
        if page_break:
            rng.ParagraphFormat.PageBreakBefore = True
        if space_after is not None:
            rng.ParagraphFormat.SpaceAfter = space_after
        if space_before is not None:
            rng.ParagraphFormat.SpaceBefore = space_before
        if italic:
            rng.Font.Italic = True
        if color is not None:
            rng.Font.Color = rgb(color)
        if size is not None:
            rng.Font.Size = size
        if lead:
            self.doc.Range(start, start + len(lead)).Font.Bold = True
        if links:
            for idx, lbl, url in sorted(((full.find(l), l, u) for l, u in links), reverse=True):
                if idx >= 0:
                    self.doc.Hyperlinks.Add(
                        Anchor=self.doc.Range(start + idx, start + idx + len(lbl)), Address=url
                    )
        self._new_para()

    def h1(self, t, page_break=False):
        self.add(t, S_H1, page_break=page_break)

    def h2(self, t):
        self.add(t, S_H2)

    def para(self, t, **kw):
        self.add(t, S_NORMAL, **kw)

    def bullet(self, t, lead=None):
        self.add(t, S_BULLET, lead=lead)

    def table(self, caption, headers, rows, widths_cm, aligns, note=None, font_pt=9.5):
        assert abs(sum(widths_cm) - TEXT_W_CM) < 0.15
        self.tab_n += 1
        self.add(f"Table {self.tab_n}. {caption}", S_CAPTION, space_before=6, space_after=3)
        rng = self._last()
        rng.Collapse(1)
        tbl = self.doc.Tables.Add(rng, len(rows) + 1, len(headers))
        tbl.AllowAutoFit = False
        tbl.Range.Font.Name = FONT
        tbl.Range.Font.Size = font_pt
        for i, w in enumerate(widths_cm, start=1):
            tbl.Columns(i).Width = w * CM
        for c, h in enumerate(headers, start=1):
            tbl.Cell(1, c).Range.Text = h
        for r, row in enumerate(rows, start=2):
            for c, val in enumerate(row, start=1):
                tbl.Cell(r, c).Range.Text = str(val)
        for b in (B_LEFT, B_RIGHT, B_VERT):
            tbl.Borders(b).LineStyle = 0
        hdr = tbl.Rows(1)
        hdr.Shading.BackgroundPatternColor = rgb(NAVY)
        hdr.Range.Font.Bold = True
        hdr.Range.Font.Color = rgb(WHITE)
        for r in range(1, len(rows) + 2):
            for c, a in enumerate(aligns, start=1):
                tbl.Cell(r, c).Range.ParagraphFormat.Alignment = a
        if note:
            self.para(note, size=9, color=GREY, space_after=6)

    def figure(self, path: Path, caption: str, width_cm: float = 15.0) -> None:
        if not path.is_file():
            raise FileNotFoundError(path)
        self.fig_n += 1
        rng = self._last()
        rng.Collapse(1)
        pic = self.doc.InlineShapes.AddPicture(str(path), False, True, rng)
        pic.LockAspectRatio = True
        pic.Width = width_cm * CM
        self._last().ParagraphFormat.Alignment = ALIGN_C
        self.add(f"Figure {self.fig_n}. {caption}", S_CAPTION, align=ALIGN_C)

    def finish(self, title: str, out_docx: Path, out_pdf: Path) -> int:
        out_docx.parent.mkdir(parents=True, exist_ok=True)
        self.doc.Content.LanguageID = 2057
        pages = self.doc.ComputeStatistics(2)
        self.doc.SaveAs2(str(out_docx), FileFormat=16)
        try:
            self.doc.ExportAsFixedFormat(str(out_pdf), ExportFormat=17, OpenAfterExport=False)
        except Exception:
            self.doc.SaveAs2(str(out_pdf), FileFormat=17)
        self.doc.Close(False)
        self.word.Quit()
        return pages