from __future__ import annotations

from datetime import date, time

from pydantic import BaseModel


class Transaction(BaseModel):
    """Single Gojek transaction record."""

    tanggal: date
    waktu: time
    no_transaksi: str
    layanan: str
    dari: str
    tujuan: str
    metode_bayar: str
    total_dibayar: int


class Receipt(BaseModel):
    """Gojek transaction history receipt."""

    nama: str
    periode: str
    total_transaksi: int
    transactions: list[Transaction]
