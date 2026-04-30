from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from gojek_receipt.core.models import Receipt, Transaction


# ─── Style constants ──────────────────────────────────────────────────────────

_THIN = Side(style="thin", color="CCCCCC")
_BORDER = Border(left=_THIN, right=_THIN, top=_THIN, bottom=_THIN)

_HEADER_FONT = Font(bold=True, color="FFFFFF")
_HEADER_FILL = PatternFill(fill_type="solid", fgColor="16A34A")

_FILL_GORIDE = PatternFill(fill_type="solid", fgColor="DCFCE7")
_FILL_GOFOOD = PatternFill(fill_type="solid", fgColor="FEF3C7")
_FILL_GOTRANSIT = PatternFill(fill_type="solid", fgColor="DBEAFE")
_FILL_DEFAULT = PatternFill(fill_type="solid", fgColor="FFFFFF")

_FOOTER_FONT = Font(bold=True)
_FOOTER_FILL = PatternFill(fill_type="solid", fgColor="F3F4F6")

_HEADERS = [
    "Tanggal",
    "Waktu",
    "No. Transaksi",
    "Layanan",
    "Dari",
    "Tujuan",
    "Metode Bayar",
    "Total Dibayar",
]

_COL_WIDTHS = [12, 12, 22, 18, 28, 28, 20, 16]

_DATE_FMT = "DD/MM/YYYY"
_TIME_FMT = "HH:MM:SS"
_AMOUNT_FMT = "#,##0"


def _row_fill(layanan: str) -> PatternFill:
    """Determine row color based on service type."""
    s = layanan.lower()
    if "goride" in s or "gride" in s:
        return _FILL_GORIDE
    if "gofood" in s or "food" in s:
        return _FILL_GOFOOD
    if "gotransit" in s or "transit" in s:
        return _FILL_GOTRANSIT
    return _FILL_DEFAULT


def _ensure_parent(path: Path) -> None:
    """Ensure parent directory exists."""
    path.parent.mkdir(parents=True, exist_ok=True)


def render(receipt: Receipt, path: Path) -> Path:
    """Write receipt data to an XLSX workbook."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Transaksi"

    # ─── Header row ───────────────────────────────────────────────────────────
    for col, label in enumerate(_HEADERS, start=1):
        cell = ws.cell(1, col, label)
        cell.font = _HEADER_FONT
        cell.fill = _HEADER_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = _BORDER

    # ─── Data rows ────────────────────────────────────────────────────────────
    for r_idx, tx in enumerate(receipt.transactions, start=2):
        fill = _row_fill(tx.layanan)
        _write_row(ws, r_idx, tx, fill)

    # ─── Footer SUM row ───────────────────────────────────────────────────────
    footer_row = len(receipt.transactions) + 2
    last_data_row = footer_row - 1

    ws.cell(footer_row, 1, "TOTAL").font = _FOOTER_FONT
    ws.cell(footer_row, 1).fill = _FOOTER_FILL
    ws.cell(footer_row, 1).border = _BORDER

    # SUM formula for Total Dibayar (column H = 8)
    sum_cell = ws.cell(footer_row, 8, f"=SUM(H2:H{last_data_row})")
    sum_cell.number_format = _AMOUNT_FMT
    sum_cell.font = _FOOTER_FONT
    sum_cell.fill = _FOOTER_FILL
    sum_cell.border = _BORDER

    # Fill remaining footer cells
    for col in range(2, 8):
        c = ws.cell(footer_row, col)
        c.fill = _FOOTER_FILL
        c.border = _BORDER

    # ─── Column widths ────────────────────────────────────────────────────────
    col_letters = "ABCDEFGH"
    for i, width in enumerate(_COL_WIDTHS):
        ws.column_dimensions[col_letters[i]].width = width

    # Freeze header row
    ws.freeze_panes = "A2"

    _ensure_parent(path)
    wb.save(path)
    return path


def _write_row(ws, row: int, tx: Transaction, fill: PatternFill) -> None:
    """Write a single transaction row to the worksheet."""
    cells_data = [
        (1, tx.tanggal, _DATE_FMT),
        (2, tx.waktu, _TIME_FMT),
        (3, tx.no_transaksi, None),
        (4, tx.layanan, None),
        (5, tx.dari, None),
        (6, tx.tujuan, None),
        (7, tx.metode_bayar, None),
        (8, tx.total_dibayar, _AMOUNT_FMT),
    ]
    for col, value, fmt in cells_data:
        cell = ws.cell(row, col, value)
        cell.fill = fill
        cell.border = _BORDER
        cell.alignment = Alignment(vertical="top", wrap_text=False)
        if fmt:
            cell.number_format = fmt
