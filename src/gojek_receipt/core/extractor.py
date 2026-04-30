from __future__ import annotations

import re
from datetime import date, datetime, time
from pathlib import Path

from gojek_receipt.core.models import Receipt, Transaction


def extract(pdf_path: Path) -> Receipt:
    """Open PDF, extract all transaction rows, parse into Receipt."""
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError(
            "PyMuPDF is required for PDF extraction.\n"
            "Install it: pip install pymupdf"
        ) from exc

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    doc = fitz.open(str(pdf_path))
    raw_rows: list[list[str]] = []

    for page_num, page in enumerate(doc, start=1):
        try:
            rows = _extract_page_rows(page)
            raw_rows.extend(rows)
        except Exception as e:
            raise ValueError(f"Error parsing page {page_num}: {e}") from e

    if not raw_rows:
        raise ValueError(f"No transaction table found in {pdf_path.name}")

    transactions = []
    for row_num, row in enumerate(raw_rows, start=1):
        try:
            tx = _parse_row(row)
            transactions.append(tx)
        except Exception as e:
            raise ValueError(f"Error parsing row {row_num}: {e}") from e

    meta = _extract_meta(doc[0])

    return Receipt(
        nama=meta.get("nama", ""),
        periode=meta.get("periode", ""),
        total_transaksi=len(transactions),
        transactions=transactions,
    )


def _extract_page_rows(page) -> list[list[str]]:
    """Extract data rows from a single PDF page using find_tables()."""
    finder = page.find_tables()

    if not finder.tables:
        return []

    for table in finder.tables:
        rows = table.extract()
        if not rows:
            continue
        if len(rows[0]) != 7:
            continue

        data_rows = []
        for row in rows:
            if _is_header_row(row):
                continue
            if _is_empty_row(row):
                continue
            normalized = _normalize_row(row)
            data_rows.append(normalized)

        return data_rows

    return []


def _is_header_row(row: list) -> bool:
    """Check if a row is a header row (contains 'Tanggal' in first cell)."""
    if not row or not row[0]:
        return False
    cell_0 = str(row[0]).strip()
    return "Tanggal" in cell_0 or "Periode" in cell_0


def _is_empty_row(row: list) -> bool:
    """Check if a row is completely empty."""
    return all(cell is None or str(cell).strip() == "" for cell in row)


def _normalize_row(row: list) -> list[str]:
    """Normalize a row: replace None with '', strip whitespace."""
    return [str(cell).strip() if cell is not None else "" for cell in row]


def _parse_row(row: list[str]) -> Transaction:
    """Parse a 7-element raw row into a Transaction.

    Column order: Tanggal | No. transaksi | Layanan | Dari | Tujuan |
                  Metode bayar | Total dibayar
    """
    if len(row) != 7:
        raise ValueError(f"Expected 7 columns, got {len(row)}")

    tanggal_raw, no_transaksi, layanan, dari_raw, tujuan_raw, metode_raw, total_raw = row

    tanggal, waktu = _parse_tanggal(tanggal_raw)
    dari = _extract_short_location(dari_raw)
    tujuan = _extract_short_location(tujuan_raw)
    metode_bayar = _normalize_metode(metode_raw)
    total_dibayar = _parse_total(total_raw)

    return Transaction(
        tanggal=tanggal,
        waktu=waktu,
        no_transaksi=no_transaksi.strip(),
        layanan=layanan.strip(),
        dari=dari,
        tujuan=tujuan,
        metode_bayar=metode_bayar,
        total_dibayar=total_dibayar,
    )


# ─── Cell parsing functions ────────────────────────────────────────────────────

_DATE_RE = re.compile(r"(\d{2}/\d{2}/\d{4})")
_TIME_RE = re.compile(r"(\d{1,2}:\d{2}:\d{2}\s*(?:AM|PM)?)", re.IGNORECASE)


def _parse_tanggal(raw: str) -> tuple[date, time]:
    """Extract date and time from a possibly multi-line Tanggal cell.

    Expected formats:
      "29/04/2026\n10:02:32 AM"
      "29/04/2026 10:02:32 AM"   (if joined by space)
    """
    if not raw:
        raise ValueError("Empty date field")

    date_match = _DATE_RE.search(raw)
    if not date_match:
        raise ValueError(f"Cannot parse date from: {raw!r}")

    d = datetime.strptime(date_match.group(1), "%d/%m/%Y").date()

    time_match = _TIME_RE.search(raw)
    if time_match:
        time_str = time_match.group(1).strip()
        if re.search(r"[AP]M", time_str, re.IGNORECASE):
            t = datetime.strptime(time_str, "%I:%M:%S %p").time()
        else:
            t = datetime.strptime(time_str, "%H:%M:%S").time()
    else:
        t = time(0, 0, 0)

    return d, t


def _extract_short_location(raw: str) -> str:
    """Return the first meaningful line of a location cell.

    For multi-line addresses, the first line is the actionable short name.
    Subsequent lines are full street addresses (dropped).
    """
    if not raw:
        return ""
    lines = [line.strip() for line in raw.split("\n") if line.strip()]
    return lines[0] if lines else raw.strip()


def _normalize_metode(raw: str) -> str:
    """Normalize payment method, joining multi-line split like 'Kartu\nkredit/debit'."""
    if not raw:
        return ""
    joined = " ".join(part.strip() for part in raw.split("\n") if part.strip())
    return joined


_AMOUNT_RE = re.compile(r"[\d.,]+")


def _parse_total(raw: str) -> int:
    """Parse IDR amount from strings like 'Rp12.000' or 'Rp 12.000' or '12.000'.

    Indonesian number format: period as thousands separator, no decimals.
    """
    if not raw:
        raise ValueError("Empty amount field")

    cleaned = raw.replace("Rp", "").replace(" ", "").strip()
    cleaned = cleaned.replace(".", "").replace(",", "")
    match = _AMOUNT_RE.search(cleaned)
    if not match:
        raise ValueError(f"Cannot parse amount from: {raw!r}")
    return int(match.group())


def _extract_meta(page) -> dict[str, str]:
    """Extract header block: name, period from first page plain text."""
    text = page.get_text("text")
    meta: dict[str, str] = {}

    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # Extract periode (look for date range pattern)
    for line in lines:
        if "Periode" in line or "periode" in line:
            parts = line.split(":", 1)
            if len(parts) == 2:
                meta["periode"] = parts[1].strip()
                break
        # Also look for date range without explicit "Periode:" label
        if re.match(r"\d{1,2}\s*(jan|january|feb|february|mar|march|apr|april|mei|may|jun|june|jul|july|agu|august|sep|september|okt|october|nov|november|des|december)\s*\d{4}", line.lower()):
            meta["periode"] = line
            break

    # Extract name (first meaningful non-label line)
    for line in lines[:20]:
        if line and not any(
            kw in line.lower()
            for kw in [
                "gojek",
                "riwayat",
                "transaksi",
                "periode",
                "periode transaksi",
                "total",
                "email",
                "phone",
                "+62",
                "@",
            ]
        ):
            # Skip lines that look like addresses or status messages
            if not any(jl in line for jl in ["jl.", "Jl.", "No.", "Jakarta", "Bogor", "Depok"]):
                meta.setdefault("nama", line)
                break

    return meta
