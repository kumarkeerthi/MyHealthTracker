# Food Image Processing Pipeline

This pipeline powers image-assisted food interpretation while preserving deterministic safety checks and auditability.

## Primary endpoints

- `POST /analyze-food-image`
- (Optional follow-up) confirmation endpoint flow that persists normalized interpreted entries

## End-to-end pipeline

1. **Upload validation**
   - Validates content type and enforces payload byte-size limits (`MAX_FOOD_IMAGE_BYTES`).
2. **File persistence**
   - Stores accepted files in `FOOD_IMAGE_UPLOAD_DIR` for traceability and optional re-processing.
3. **Vision extraction**
   - Invokes model-assisted ingredient/portion interpretation.
   - If model output is unavailable or malformed, deterministic fallback behavior is used.
4. **Portion normalization**
   - Applies calibration/reference-card scaling when available.
5. **Macro + insulin projection**
   - Converts interpreted foods to normalized nutrition estimates.
   - Projects insulin-impact metadata used by metabolic scoring logic.
6. **Confidence and audit metadata**
   - Stores confidence/context metadata for later review and debugging.

## Safety and guardrails

- Request payload sanitization blocks obvious script injection patterns.
- Upload size limits prevent oversized image abuse.
- Deterministic fallback path protects endpoint availability when AI services degrade.
- Endpoint-level rate limits (plus global limits) reduce abuse risk.

## Data quality guidance

For best results:

- Capture image in strong lighting with minimal blur.
- Use top-down framing where possible.
- Keep mixed dishes separated visually when practical.
- Include scale hints (plate size, reference card, known object) if calibration is used.

## Operational recommendations

- Track confidence trends over time to identify drift.
- Periodically sample interpreted logs against manual annotations.
- Keep upload storage lifecycle-managed (retention/archival policies).
- Alert on repeated low-confidence outputs for the same user/device.

## Failure modes and expected behavior

- **Model timeout/unavailable** → service returns fallback interpretation behavior or controlled error.
- **Oversize file** → request rejected before expensive processing.
- **Malformed metadata** → validation error response with actionable feedback.
