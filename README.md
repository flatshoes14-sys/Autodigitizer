# Autodigitizer

A lightweight local Python tool for extracting approximate point-by-point coordinates from scientific graph images (PNG/JPG/JPEG), especially thermoelectric property plots such as **zT(T)**, **PF(T)**, **Seebeck(T)**, **conductivity(T)**, and **thermal conductivity(T)**.

The tool is intentionally conservative and inspectable:
- Supports **semi-automatic digitization** (manual clicking after calibration)
- Supports **optional automatic extraction** for clean/simple graphs only
- Handles **multiple curves** in one image (as multiple named datasets)
- Exports CSV + verification artifacts (overlay/replot/report)

## Project structure

```text
Autodigitizer/
├── app.py
├── main.py
├── calibration.py
├── digitizer.py
├── auto_extract.py
├── io_utils.py
├── validators.py
├── requirements.txt
├── README.md
├── sample_output/
└── tests/
    └── test_calibration.py
```

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

Run with a single image:

```bash
python main.py --image /path/to/graph.png --output sample_output
```

(`app.py` is an alias entrypoint and supports the same arguments.)

### Workflow

1. **Load image** (PNG/JPG/JPEG).
2. **Calibration**:
   - Click 2 points on x-axis and enter their true values.
   - Click 2 points on y-axis and enter their true values.
   - Set axis scales (`linear` or `log`) independently for x and y.
   - Reversed axes are supported by the two-point mapping.
3. Choose mode:
   - **semi**: click curve points manually (repeat for multiple dataset names).
   - **auto**: select ROI + pick target color + tolerances, then extract candidate pixels.
4. Tool saves:
   - CSV(s) per dataset
   - Overlay image(s) on original figure
   - Replot image(s) from extracted points
   - `summary_report.md` with warnings and confidence notes

## Automatic extraction behavior

Automatic extraction is deliberately conservative:
- Uses color thresholding in HSV within selected ROI
- Applies small morphological cleanup
- Filters tiny components
- Emits warnings/confidence when complexity is high (dense masks, many disconnected regions, very few points)

If confidence is low or curves overlap heavily, use **semi-automatic mode**.

## Edge-case guidance

The report warns when extraction quality may degrade for:
- low resolution
- overlapping curves
- error bars
- legends/text on top of data
- inset plots
- sparse scatter plots
- thick lines or mixed markers
- unclear ticks
- log scales with weak calibration

## Tests

Run unit tests for calibration and conversion behavior:

```bash
pytest
```

## Important caution

Digitized points are **approximate reconstructions from plotted images** and are **not** equivalent to original raw measurements from the paper. Use caution for precise fitting, uncertainty quantification, or publication-grade inference.
