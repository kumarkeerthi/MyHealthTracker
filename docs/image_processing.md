# Image Processing Pipeline

## Endpoint
`POST /analyze-food-image`

## Pipeline
1. Upload byte validation and max-size enforcement.
2. Image persistence in `FOOD_IMAGE_UPLOAD_DIR`.
3. Vision model extraction (or deterministic fallback sample).
4. Portion scaling via reference-card calibration.
5. Macro and insulin-impact projection.
6. Optional confirm endpoint writes normalized entries to logs.

## Guardrails
- Size limit: `MAX_FOOD_IMAGE_BYTES`
- Input sanitization for context strings
- Confidence metadata persisted for auditability
