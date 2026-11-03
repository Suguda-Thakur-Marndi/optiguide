# OPTIGUIDE — PHASE 3.2 REPORT
## Visual Acuity Screening Module (Distance & Near Vision)

**Author:** OptiGuide Clinical Architecture & Vision Science Specialist  
**Status:** COMPLETED & VERIFIED  
**Date:** November 3, 2026  
**Version:** 1.0.0  

---

## 1. Clinical & Optical Foundation

The OptiGuide Visual Acuity Screening module implements standardized clinical visual acuity protocols adhering to international standard ISO 8596 and British Standard BS 4274-1.

### 1.1 Optotype Definition
The optotype used for distance acuity screening is the **Snellen Tumbling E** (4-alternative forced choice: up, right, down, left).
A standard Snellen optotype subtends an angle of $5\text{ arcminutes}$ ($5'$) at the designated test distance, with each limb and gap subtending $1\text{ arcminute}$ ($1'$).

### 1.2 Mathematical Formulation of Physical Calibration
Given:
- Viewing distance: $d$ (meters)
- Snellen test fraction: $20/D$ where $D$ is the denominator
- Angular subtense of standard 20/20 letter: $\theta = 5' = \frac{5}{60}^\circ = \left(\frac{1}{12}\right)^\circ$

The physical letter height $h$ (meters) is calculated using exact trigonometric optics:
$$h = 2 \cdot d \cdot \tan\left(\frac{5'}{2}\right) \cdot \frac{D}{20}$$

Using small-angle approximation $\tan(\alpha) \approx \alpha$ in radians:
$$\theta_{\text{rad}} = 5 \times \frac{\pi}{180 \times 60} \approx 0.00145444\text{ rad}$$
$$h \approx d \cdot 0.00145444 \cdot \frac{D}{20}$$

#### Calibration Verification at Common Distances:
1. **At Desktop / Kiosk Screening Distance ($d = 0.60\text{ m}$):**
   - For $20/20$ ($D = 20$):
     $$h = 0.60 \times 0.00145444 \approx 0.00087266\text{ m} \approx 0.873\text{ mm}$$
   - For $20/100$ ($D = 100$):
     $$h = 0.87266 \times 5 \approx 4.363\text{ mm}$$
2. **At Standard Clinical Examination Distance ($d = 6.00\text{ m}$):**
   - For $20/20$:
     $$h = 6.00 \times 0.00145444 \approx 0.0087266\text{ m} \approx 8.727\text{ mm}$$

#### Conversion from Physical Millimeters to Display Pixels:
$$h_{\text{pixels}} = \frac{h_{\text{mm}}}{25.4} \times \text{DPI}$$
where $\text{DPI} = \text{CSS DPI} \times \text{devicePixelRatio}$.

### 1.3 logMAR Scoring Formula
$$\text{logMAR} = -\log_{10}(\text{Decimal Acuity}) = \log_{10}\left(\frac{D}{20}\right)$$

| Snellen Fraction | Decimal Acuity | Exact logMAR | OptiGuide Representation |
|---|---|---|---|
| $20/20$ | 1.000 | 0.000 | 0.00 |
| $20/25$ | 0.800 | 0.097 | 0.10 |
| $20/30$ | 0.667 | 0.176 | 0.18 |
| $20/40$ | 0.500 | 0.301 | 0.30 |
| $20/50$ | 0.400 | 0.398 | 0.40 |
| $20/70$ | 0.286 | 0.544 | 0.54 |
| $20/100$ | 0.200 | 0.699 | 0.70 |

---

## 2. Near Vision Assessment Protocol

- **Target Distance:** Standardized at $38.0\text{ cm}$ ($15\text{ inches}$).
- **Typographic Scale:** N-point notation (Times Roman font equivalent).
  - **N6:** Standard newsprint body text ($\approx 0.8\text{ mm}$ x-height).
  - **N8:** Typical book text ($\approx 1.1\text{ mm}$ x-height).
  - **N10:** Large print / subheadings ($\approx 1.4\text{ mm}$ x-height).
  - **N12:** Headline print ($\approx 1.6\text{ mm}$ x-height).
- Captures clarity ratings (scale 1-5) and uncorrected vs. reading glasses usage.

---

## 3. Database Model & Migration

Table: `visual_acuity_assessments` (Alembic Migration `004_screening_clinical_assessments`)
- `id`: UUID (Primary Key)
- `session_id`: UUID (Foreign Key to `screening_sessions.id`, ON DELETE CASCADE, Indexed)
- `test_eye`: VARCHAR(16) — `'right'`, `'left'`, `'binocular'`
- `snellen_fraction`: VARCHAR(16) — e.g., `'20/20'`, `'20/60'`
- `logmar`: FLOAT — e.g., `0.0`, `0.48`
- `decimal_acuity`: FLOAT — e.g., `1.0`, `0.33`
- `tested_distance_meters`: FLOAT (Default 0.6)
- `unassisted_or_corrected`: VARCHAR(32) — `'unassisted'`, `'with_glasses'`, `'with_contacts'`
- `near_reading_label`: VARCHAR(32) (Nullable) — e.g., `'N6 at 38cm'`
- `near_reading_distance_cm`: FLOAT (Nullable)
- `is_calibrated`: BOOLEAN (Default FALSE)
- `calibration_metadata`: TEXT / JSON (Nullable) — records DPI, optotype mm, screen width/height
- `observations`: TEXT (Nullable)
- `recorded_at`: TIMESTAMPTZ

---

## 4. Test Evidence

1. **Optics & logMAR Unit Tests:** `backend/tests/unit/test_clinical_scoring.py`
   - `test_snellen_visual_angle_height_calculation` — Verified $h \approx 0.873\text{ mm}$ at 0.6m and $8.727\text{ mm}$ at 6.0m.
   - `test_logmar_calculations_across_snellen_levels` — Verified $20/20 \to 0.0$, $20/40 \to 0.301$, $20/200 \to 1.0$.
2. **API Endpoint Test:** `backend/tests/api/test_clinical_screening_api.py::test_visual_acuity_recording_and_retrieval`
   - Successfully created OD visual acuity assessment with calibration payload.
   - Verified HTTP 201 response and retrieved record via GET.
3. **Live E2E Verification Runner:**
   - Journey 13 executed against running FastAPI server:
     - OD: 20/20 (logMAR 0.0) -> HTTP 201 Created.
     - OS: 20/60 (logMAR 0.48) -> HTTP 201 Created.
