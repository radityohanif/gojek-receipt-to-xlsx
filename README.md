# Gojek Receipt to XLSX Converter

A Python command-line tool and library to convert Gojek transaction-history PDF statement receipts into a beautifully formatted Excel (`.xlsx`) workbook.

---

## ✨ Features

- 📑 **Accurate PDF Parsing:** Extracts transaction tables directly from text-based PDF statements using [PyMuPDF](https://github.com/pymupdf/PyMuPDF) (no OCR needed).
- 🏷️ **Metadata Extraction:** Automatically captures the owner's name, billing period, and total transaction count.
- 🎨 **Elegant Excel Styling:**
  - **Color-Coded Rows:** Distinguishes Gojek services automatically (GoRide is light green, GoFood is light yellow, GoTransit is light blue, and others are default white).
  - **Visual Header Block:** Includes a prominent header with the statement owner's details, transaction period, and logo integration (if `logo.png` is present).
  - **Frozen Headers:** Table headers (`A7:H7`) are frozen for seamless scrolling.
  - **Auto-calculated Totals:** Adds a footer row with an active Excel `=SUM` formula for the total amount paid.
  - **Formated Values:** Properly formats dates, times, and IDR currency fields.
- 💻 **Robust CLI:** Built with [Typer](https://typer.tiangolo.com/) and [Rich](https://github.com/Textualize/rich) for a clean, user-friendly command-line experience with colorized status messages.
- 🔌 **Python API:** Easily import the core engine to programmatically parse and write files in custom scripts.

---

## 🛠️ Installation

### Prerequisites

- Python 3.11 or higher installed.

### Steps

1. **Clone or Navigate to the Directory:**
   ```bash
   cd gojek-receipt-to-xlsx
   ```

2. **Create and Activate a Virtual Environment (Recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate     # On Windows
   ```

3. **Install the Package:**
   
   To install the package along with its command-line tool:
   ```bash
   pip install .
   ```

   For developers who want to run tests or lint the codebase:
   ```bash
   pip install -e ".[dev]"
   ```

---

## 🚀 CLI Usage

After installation, the CLI command `gojek-receipt` will be available in your path.

### Get Help

To see all available arguments and options:
```bash
gojek-receipt --help
```

### Basic Conversion

To convert a Gojek transaction PDF into Excel (output will default to the same directory and filename, but with `.xlsx` extension):
```bash
gojek-receipt Riwayat_transaksi_Gojek_010426-290426.pdf
```

### Custom Output Path

To specify a custom output path or filename:
```bash
gojek-receipt Riwayat_transaksi_Gojek_010426-290426.pdf --output /path/to/my_report.xlsx
# or using the shorthand:
gojek-receipt Riwayat_transaksi_Gojek_010426-290426.pdf -o my_report.xlsx
```

### Show Version
```bash
gojek-receipt --version
```

---

## 🐍 Python API Usage

You can also use this project as a library in your own Python scripts:

```python
from pathlib import Path
from gojek_receipt.core.extractor import extract
from gojek_receipt.core.renderer import render

# 1. Parse PDF file into a structured Pydantic model
input_pdf = Path("Riwayat_transaksi_Gojek_010426-290426.pdf")
receipt = extract(input_pdf)

# Access parsed details
print(f"Pemilik: {receipt.nama}")
print(f"Periode: {receipt.periode}")
print(f"Total Transaksi: {receipt.total_transaksi}")

for tx in receipt.transactions[:3]:
    print(f"- {tx.tanggal} {tx.waktu} | {tx.layanan} | Rp{tx.total_dibayar:,}")

# 2. Write the receipt model into a styled Excel workbook
output_xlsx = Path("formatted_output.xlsx")
render(receipt, output_xlsx)
print(f"Excel report saved to {output_xlsx}")
```

---

## 📂 Project Structure

```text
gojek-receipt-to-xlsx/
├── pyproject.toml         # Project metadata and dependencies configuration
├── logo.png               # Optional brand logo inserted in the generated Excel header
├── src/
│   └── gojek_receipt/
│       ├── __init__.py    # Versioning
│       ├── __main__.py    # Python executable entry point
│       ├── cli.py         # Typer-based command line interface
│       └── core/
│           ├── __init__.py
│           ├── extractor.py # PDF parsing logic using PyMuPDF
│           ├── models.py    # Pydantic schemas for structured data
│           └── renderer.py  # Excel worksheet rendering and styling using openpyxl
└── tests/                 # Unit and integration test suite
```

---

## 🧪 Development & Testing

Run tests to make sure everything functions properly:

```bash
# Run the test suite
pytest

# Run code style and linting check
ruff check .
```

---

## 📝 License

This project is licensed under the [MIT License](LICENSE).
