# Reference Project Analysis: project-maker

## 📋 Ringkasan Struktur
Project-maker adalah **monorepo** dari 5 CLI tools yang terintegrasi dengan library bersama. Fokus: PDF-to-text conversion dan CLI tool architecture pattern.

---

## 🔄 1. KONVERSI PDF KE TEXT

### Mekanisme PDF → Markdown
**File**: `src/file_converter/core/converters.py::pdf_to_md()` (lines 162-199)

**Library**: PyMuPDF (`fitz`)
```python
import fitz  # PyMuPDF
doc = fitz.open(str(input_path))
for page in doc:
    page_dict = page.get_text("dict", flags=flags)
```

**Proses**:
1. **Parse PDF blocks** → `page.get_text("dict")` menghasilkan struktur dengan 2 tipe blok:
   - `type=0`: Text blocks
   - `type=1`: Image blocks

2. **Heuristics for Headings** (lines 202-232):
   - Font size ≥ 20pt → H1 (#)
   - Font size ≥ 16pt → H2 (##)
   - Font size ≥ 14pt → H3 (###)
   - Bold text → **bold**

3. **Extract Text Spans**:
   ```python
   for line in block.get("lines", []):
       for span in line.get("spans", []):
           text = span.get("text")
           size = span.get("size")  # Font size
           flags = span.get("flags")  # Bold, italic, etc
   ```

4. **Embed Images as Base64** (optional):
   - `fitz.TEXT_PRESERVE_IMAGES` flag
   - Encoded as `![image](data:image/{ext};base64,{b64})`

5. **Page Separation**: Pages dipisahkan dengan `---` (thematic break)

**Output**: Text + Markdown formatting, dengan opsional base64 images

---

### Dependency Management
```toml
[project.optional-dependencies]
converter = [
    "pymupdf>=1.24",
    "pdf2docx>=0.5.8",
]
```

**Error handling** (lines 169-175):
- Throws `RuntimeError` dengan helpful message jika PyMuPDF tidak tersedia
- User diberi opsi: `pip install 'project-suite[converter]'` atau `pip install pymupdf`

---

## 🛠️ 2. MEKANISME PEMBANGUNAN CLI TOOLS

### A. Struktur Folder CLI Tool
```
src/{tool_name}/
├── __init__.py
├── __main__.py          # Entry point: from {tool}.cli import app; app()
├── cli.py               # Typer app definition
└── core/
    ├── __init__.py
    ├── models.py        # Pydantic models (data validation)
    ├── parser.py        # File/YAML parsing
    ├── prompt_builder.py # LLM prompt generation
    ├── renderer.py      # Output generation
    ├── validator.py     # Spec validation
    └── wizard_prompt.py # Interactive CLI prompts
```

### B. Typer Framework Pattern
**File**: `src/file_converter/cli.py` (lines 40-84)

```python
app = typer.Typer(
    name="file-converter",
    help="Convert documents between DOCX, PDF, and Markdown formats.",
    context_settings={"help_option_names": ["-h", "--help"]},
    invoke_without_command=True,
    no_args_is_help=False,
)

@app.callback(invoke_without_command=True)
def _main(
    ctx: typer.Context,
    input_path: Optional[Path] = typer.Option(
        None,
        "--input", "-i",
        exists=True,
        dir_okay=False,
        help="Input file (.docx, .pdf, or .md).",
    ),
    # ... more options
) -> None:
    # Main logic
    pass
```

**Key Features**:
1. **Typer Options**:
   - `typer.Option()` → CLI flags (--input, --output)
   - `typer.Argument()` → Positional arguments
   - `exists=True` → Validate file exists
   - `dir_okay=False` → Must be file
   - `callback=_version_callback` → Eager version check

2. **Context Handling**:
   - `ctx.invoked_subcommand` → Check if subcommand called
   - `typer.Exit(code)` → Exit with status code

3. **Interactive Prompts**:
   ```python
   choice = typer.prompt(f"Output format [{choices}]", default=targets[0])
   ```

### C. Subcommands Pattern
**File**: `src/file_converter/cli.py` (lines 171-216)

```python
@app.command("strip-images")
def strip_images_cmd(
    input_path: Path = typer.Argument(...),
    output_path: Optional[Path] = typer.Option(None, "--output", "-o"),
) -> None:
    """Remove embedded images from a Markdown file."""
    # Command logic
    pass
```

**Usage**:
```bash
file-converter convert -i input.pdf -o output.md
file-converter strip-images prd.md -o prd-clean.md
```

### D. Entry Point Configuration
**File**: `pyproject.toml` (lines 38-45)

```toml
[project.scripts]
timeline-maker = "timeline_maker.cli:app"
quote-maker = "quote_maker.cli:app"
proposal-maker = "proposal_maker.cli:app"
deck-maker = "deck_maker.cli:app"
project-maker = "project_maker.cli:app"
suite-gui = "suite_gui.app:main"
convert = "file_converter.cli:app"
```

**Mekanisme**:
1. Setuptools membuat executable di `~/.venv/bin/{command_name}`
2. Executable langsung memanggil function yang di-specify
3. `__main__.py` memungkinkan `python -m {package_name}`

---

## 📦 3. SHARED UTILITIES PATTERN

```
src/shared/
├── prompt/
│   ├── io.py           # File I/O helpers
│   └── wizard.py       # Interactive prompts
├── schemas/
│   └── common.py       # Pydantic base schemas
└── utils/
    ├── files.py        # File operations
    └── yaml_io.py      # YAML read/write
```

**Digunakan oleh**: Semua tools (`from shared.prompt import write_or_preview`)

---

## 🎯 4. ERROR HANDLING & USER FEEDBACK

### A. Rich Console for Pretty Output
```python
from rich.console import Console

console = Console()
console.print(f"[green]Done:[/green] {output_path}")
console.print(f"[bold red]Error:[/bold red] {exc}")
console.print(f"[dim]Note: --no-images has no effect[/dim]")
```

**Markup tags**:
- `[green]...[/green]` → Success
- `[bold red]...[/bold red]` → Error
- `[yellow]...[/yellow]` → Warning
- `[dim]...[/dim]` → Muted

### B. Validation Flow
```python
if pair not in _SUPPORTED:
    supported_str = "  ".join(f".{a} → .{b}" for a, b in sorted(_SUPPORTED))
    console.print(f"[bold red]Error:[/bold red] Unsupported conversion...")
    raise typer.Exit(1)
```

---

## 📚 5. BUILD & DISTRIBUTION

### Monorepo Setup
- **Build system**: setuptools + wheel
- **Package discovery**: `setuptools.find_packages()` in `src/`
- **Multiple entry points**: Semua tools di 1 package

### Installation
```bash
pip install project-suite                    # Core + basic tools
pip install 'project-suite[converter]'       # Tambah PDF conversion
pip install 'project-suite[gui]'             # Tambah GUI
pip install 'project-suite[dev]'             # Dev dependencies
```

### Development
```bash
pytest tests/                  # Unit + integration tests
ruff check src/                # Linting
```

---

## 🔗 6. FLOW CONTOH: PDF → MARKDOWN

```
User: file-converter -i receipt.pdf -o receipt.md
  ↓
cli.py::_main() validates inputs
  ↓
converters.py::pdf_to_md()
  1. Opens PDF with fitz.open()
  2. Extracts text blocks + metadata (font size, bold)
  3. Applies heading heuristics
  4. Optionally embeds images as base64
  ↓
Output: receipt.md (Markdown dengan proper heading structure)
```

---

## 💡 KEY TAKEAWAYS FOR RECEIPT-TO-XLSX

1. **PDF Extraction**: Gunakan PyMuPDF (fitz), bukan OCR (kalau PDF sudah text-based)
2. **Text Heuristics**: Font size bisa guide struktur data (header, items, total)
3. **CLI Pattern**: Typer + `@app.callback()` untuk main logic, `@app.command()` untuk subcommands
4. **Shared Utils**: Extract common patterns ke `src/shared/`
5. **Entry Points**: Define dalam `pyproject.toml` `[project.scripts]`
6. **Error Messages**: Gunakan Rich console untuk pretty output
7. **Optional Dependencies**: `[project.optional-dependencies]` untuk feature flags

