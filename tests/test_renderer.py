from datetime import date, time
from pathlib import Path

import pytest
from openpyxl import load_workbook

from gojek_receipt.core.models import Receipt, Transaction
from gojek_receipt.core.renderer import render


def _sample_receipt() -> Receipt:
    return Receipt(
        nama="Budi Santoso",
        periode="01/04/2026 - 29/04/2026",
        total_transaksi=2,
        transactions=[
            Transaction(
                tanggal=date(2026, 4, 29),
                waktu=time(10, 2, 32),
                no_transaksi="RB-123456-789",
                layanan="GoRide",
                dari="Sudirman",
                tujuan="Kuningan",
                metode_bayar="GoPay",
                total_dibayar=15000,
            ),
            Transaction(
                tanggal=date(2026, 4, 28),
                waktu=time(14, 0, 0),
                no_transaksi="F-987654",
                layanan="GoFood",
                dari="Warung Nasi ABC",
                tujuan="Kuningan Barat",
                metode_bayar="Kartu kredit/debit",
                total_dibayar=75000,
            ),
        ],
    )


class TestRenderer:
    def test_renderer_creates_xlsx(self, tmp_path: Path) -> None:
        path = tmp_path / "out.xlsx"
        render(_sample_receipt(), path)
        assert path.exists()

    def test_renderer_headers(self, tmp_path: Path) -> None:
        path = tmp_path / "out.xlsx"
        render(_sample_receipt(), path)
        wb = load_workbook(path)
        ws = wb.active
        assert ws.title == "Transaksi"
        assert ws.cell(1, 1).value == "Tanggal"
        assert ws.cell(1, 8).value == "Total Dibayar"
        assert ws.cell(1, 3).value == "No. Transaksi"

    def test_renderer_sum_formula(self, tmp_path: Path) -> None:
        path = tmp_path / "out.xlsx"
        render(_sample_receipt(), path)
        wb = load_workbook(path, data_only=False)
        ws = wb.active
        # Footer is row 4 (1 header + 2 data + 1 footer)
        footer_cell = ws.cell(4, 8).value or ""
        assert "SUM" in footer_cell

    def test_renderer_data_values(self, tmp_path: Path) -> None:
        path = tmp_path / "out.xlsx"
        render(_sample_receipt(), path)
        wb = load_workbook(path, data_only=True)
        ws = wb.active
        assert ws.cell(2, 3).value == "RB-123456-789"
        assert ws.cell(2, 8).value == 15000
        assert ws.cell(3, 4).value == "GoFood"

    def test_renderer_number_format(self, tmp_path: Path) -> None:
        path = tmp_path / "out.xlsx"
        render(_sample_receipt(), path)
        wb = load_workbook(path)
        ws = wb.active
        # Check that Total Dibayar has number format
        cell_h2 = ws.cell(2, 8)
        assert cell_h2.number_format == "#,##0"

    def test_renderer_empty_receipt(self, tmp_path: Path) -> None:
        path = tmp_path / "out.xlsx"
        empty = Receipt(
            nama="Test User", periode="01-29/04/2026", total_transaksi=0, transactions=[]
        )
        render(empty, path)
        wb = load_workbook(path)
        ws = wb.active
        # Header row + footer row
        assert ws.cell(1, 1).value == "Tanggal"
        assert ws.cell(2, 1).value == "TOTAL"
