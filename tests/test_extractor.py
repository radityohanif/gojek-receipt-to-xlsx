from datetime import date, time

import pytest

from gojek_receipt.core.extractor import (
    _extract_short_location,
    _normalize_metode,
    _parse_tanggal,
    _parse_total,
)


class TestParseTanggal:
    def test_parse_tanggal_with_am(self):
        d, t = _parse_tanggal("29/04/2026\n10:02:32 AM")
        assert d == date(2026, 4, 29)
        assert t == time(10, 2, 32)

    def test_parse_tanggal_with_pm(self):
        d, t = _parse_tanggal("01/04/2026\n02:15:00 PM")
        assert d == date(2026, 4, 1)
        assert t == time(14, 15, 0)

    def test_parse_tanggal_space_joined(self):
        d, t = _parse_tanggal("29/04/2026 10:02:32 AM")
        assert d == date(2026, 4, 29)
        assert t == time(10, 2, 32)

    def test_parse_tanggal_no_time(self):
        d, t = _parse_tanggal("29/04/2026")
        assert d == date(2026, 4, 29)
        assert t == time(0, 0, 0)

    def test_parse_tanggal_24h_format(self):
        d, t = _parse_tanggal("15/04/2026\n14:30:00")
        assert d == date(2026, 4, 15)
        assert t == time(14, 30, 0)

    def test_parse_tanggal_invalid(self):
        with pytest.raises(ValueError, match="Cannot parse date"):
            _parse_tanggal("invalid")

    def test_parse_tanggal_empty(self):
        with pytest.raises(ValueError, match="Empty date"):
            _parse_tanggal("")


class TestExtractShortLocation:
    def test_extract_short_location_multiline(self):
        result = _extract_short_location("Gedung A\nJl. Sudirman Kav. 1\nJakarta Pusat")
        assert result == "Gedung A"

    def test_extract_short_location_single(self):
        result = _extract_short_location("Gambir")
        assert result == "Gambir"

    def test_extract_short_location_empty(self):
        assert _extract_short_location("") == ""

    def test_extract_short_location_whitespace_only(self):
        assert _extract_short_location("   \n  \n  ") == ""


class TestNormalizeMetode:
    def test_normalize_metode_split(self):
        assert _normalize_metode("Kartu\nkredit/debit") == "Kartu kredit/debit"

    def test_normalize_metode_single(self):
        assert _normalize_metode("GoPay") == "GoPay"

    def test_normalize_metode_multiple_splits(self):
        assert _normalize_metode("A\nB\nC") == "A B C"

    def test_normalize_metode_empty(self):
        assert _normalize_metode("") == ""


class TestParseTotal:
    def test_parse_total_with_rp(self):
        assert _parse_total("Rp12.000") == 12000

    def test_parse_total_with_space(self):
        assert _parse_total("Rp 15.500") == 15500

    def test_parse_total_large(self):
        assert _parse_total("Rp1.250.000") == 1250000

    def test_parse_total_no_rp(self):
        assert _parse_total("12.000") == 12000

    def test_parse_total_from_sample(self):
        assert _parse_total("Rp9.500") == 9500
        assert _parse_total("Rp23.000") == 23000
        assert _parse_total("Rp710.900") == 710900

    def test_parse_total_invalid(self):
        with pytest.raises(ValueError, match="Cannot parse amount"):
            _parse_total("abc")

    def test_parse_total_empty(self):
        with pytest.raises(ValueError, match="Empty amount"):
            _parse_total("")
