# OPTIGUIDE — PHASE 3.3 REPORT
## Astigmatism, Color Vision Screening & Referral Triage

**Author:** OptiGuide Clinical Architecture & Application Security Team  
**Status:** COMPLETED & VERIFIED  
**Date:** November 3, 2026  
**Version:** 1.0.0  

---

## 1. Astigmatism Screening (Radial Clock Dial Protocol)

### 1.1 Clinical Background & Protocol
Astigmatism occurs when the corneal or crystalline lens surface has asymmetric curvature, creating two focal lines instead of a single point focus.
OptiGuide employs the **Clock Dial / Radial Fan Chart** preliminary screening method:
- The chart displays radial lines arranged at 30-degree intervals corresponding to clock dial hour positions (1 to 12).
- **Uniformity Evaluation:** The subject inspects the dial monocularly or binocularly.
  - If all radial spokes appear equally sharp and dark, the result is classified as **Uniform Clarity** (`has_uniform_clarity = true`).
  - If one or more lines appear notably darker, sharper, or more prominent than orthogonal lines, the result indicates **Asymmetric Meridian Clarity** (`has_uniform_clarity = false`).

### 1.2 Meridian-to-Axis Geometry
Clock dial hours correspond to standard ophthalmic axis degrees $\theta \in [0^\circ, 180^\circ]$:
$$\theta = (\text{hour} \times 30^\circ) \pmod{180^\circ}$$
- Hour 12 (vertical, 12-to-6): $90^\circ$
- Hour 3 (horizontal, 3-to-9): $180^\circ$ / $0^\circ$
- Hour 1 / 7: $30^\circ$
- Hour 2 / 8: $60^\circ$

*Clinical Note:* The sharpest line on a clock dial identifies the meridian closest to the focal line on the retina, requiring trial frame cylindrical lens confirmation by an eye care professional.

### 1.3 Database Model: `astigmatism_assessments`
- `id`: UUID (Primary Key)
- `session_id`: UUID (Foreign Key to `screening_sessions.id`, ON DELETE CASCADE, Indexed)
- `chart_type`: VARCHAR(32) — `'clock_dial'`
- `has_uniform_clarity`: BOOLEAN
- `indicated_axes`: TEXT / JSON (Nullable) — array of indicated hour marks, e.g. `"[12, 6]"`
- `sharpest_meridian_hour`: INTEGER (Nullable) — e.g., `12`
- `screening_observation`: TEXT (Nullable)
- `recorded_at`: TIMESTAMPTZ

---

## 2. Color Vision Screening (Pseudoisochromatic Plates Protocol)

### 2.1 Clinical Background & Test Battery
OptiGuide implements a 4-plate preliminary screening battery based on the pseudoisochromatic plate paradigm (Ishihara standard):
1. **Plate 1 (Demonstration Plate — "12"):** High luminance contrast numeral designed to be visible to individuals with normal color vision as well as congenital red-green color deficiency. Confirms subject comprehension.
2. **Plate 2 (Screening Plate — "8"):** Differentiates normal trichromatic vision from protanopia/deuteranopia.
3. **Plate 3 (Screening Plate — "29"):** Tests red-green chromatic discrimination along confusion lines.
4. **Plate 4 (Screening Plate — "5"):** Confirmatory red-green plate.

### 2.2 Scoring & Classification
- Correct Demonstration Plate verifies valid task execution.
- If fewer than 3 of the 4 plates are correctly identified, `deficiency_indicated = true` with classification `'protan_deutan_red_green'`.
- Responses are stored as individual plate audit objects (`responses_detail` JSON).

### 2.3 Database Model: `color_vision_assessments`
- `id`: UUID (Primary Key)
- `session_id`: UUID (Foreign Key to `screening_sessions.id`, ON DELETE CASCADE, Indexed)
- `test_protocol`: VARCHAR(64) — `'pseudoisochromatic_plates'`
- `total_plates_presented`: INTEGER
- `correct_plate_count`: INTEGER
- `deficiency_indicated`: BOOLEAN
- `deficiency_type`: VARCHAR(64) (Nullable) — `'protan_deutan_red_green'`, `'none'`
- `responses_detail`: TEXT / JSON (Nullable)
- `recorded_at`: TIMESTAMPTZ

---

## 3. Clinical Session Summary & Referral Triage

The endpoint `GET /api/v1/screening/sessions/{id}/summary` computes holistic session recommendations according to clinical screening referral thresholds:

### 3.1 Referral Criteria Matrix
| Finding | Threshold / Condition | Recommendation Triggered |
|---|---|---|
| Reduced Distance Acuity | Monocular logMAR $\ge 0.4$ ($20/50$ or worse) | Flagged: "Reduced distance visual acuity in [eye] eye" |
| Interocular Asymmetry | $|\text{OD logMAR} - \text{OS logMAR}| \ge 0.3$ | Flagged: "Interocular visual acuity asymmetry of $\ge 0.3$ logMAR" (Amblyopia / anisometropia risk) |
| Astigmatic Asymmetry | Clock dial `has_uniform_clarity == false` | Flagged: "Meridian clarity variation noted under clock dial screening" |
| Color Vision Variance | `deficiency_indicated == true` | Flagged: "Pseudoisochromatic plate screening indicated possible color variance" |

### 3.2 Mandatory Clinical Disclaimer
Every summary response incorporates the standardized disclaimer:
> *"OptiGuide is a preliminary vision screening aid and not a diagnostic medical device. It cannot independently prescribe optical lens power or replace a comprehensive ocular examination by a qualified optometrist or ophthalmologist."*

---

## 4. Test Evidence

1. **Clock Dial Unit Tests:** `backend/tests/unit/test_clinical_scoring.py::test_astigmatism_clock_dial_axis_angles`
   - Verified that hour 12 maps to $90^\circ$ and hour 3 maps to $180^\circ$.
2. **Astigmatism API Test:** `backend/tests/api/test_clinical_screening_api.py::test_astigmatism_dial_screening_recording` (Passed).
3. **Color Vision API Test:** `backend/tests/api/test_clinical_screening_api.py::test_color_vision_plate_recording` (Passed).
4. **Summary & Triage API Test:** `backend/tests/api/test_clinical_screening_api.py::test_clinical_session_summary_and_triage`
   - Tested combination of OD 20/20 and OS 20/70 (logMAR 0.54) with non-uniform clock dial.
   - Verified `referral_recommended = true`, verified 2+ referral reasons generated, verified disclaimer presence.
5. **Live E2E Verification Runner:** Journeys 14, 15, and 16 executed cleanly against running server.
