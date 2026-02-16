# Apple Health Integration

Apple Health data can be ingested through `POST /import-apple-health`.

## Supported data
- Steps
- Resting heart rate
- Sleep hours
- Workout sessions (mapped to exercise entries)

## Mapping behavior
- Daily activity contributes to exercise summaries and recovery metrics.
- Input validation ensures numerical ranges remain sane.
- Derived trends are used by coaching and metabolic advisor reports.
