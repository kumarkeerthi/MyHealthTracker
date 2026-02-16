from app.models import VitalsEntry


def calculate_vitals_risk_score(vitals_entries: list[VitalsEntry]) -> dict[str, bool | str]:
    if not vitals_entries:
        return {"metabolic_stress_rising": False, "flag": "Normal"}

    latest = vitals_entries[-1]
    high_resting_hr = (latest.resting_hr or 0) > 85
    low_sleep = (latest.sleep_hours or 24) < 6

    waist_trend_up = False
    if len(vitals_entries) >= 3:
        recent = vitals_entries[-3:]
        waists = [entry.waist_cm for entry in recent]
        if all(w is not None for w in waists):
            waist_trend_up = waists[0] < waists[1] < waists[2]

    rising = high_resting_hr and low_sleep and waist_trend_up
    return {
        "metabolic_stress_rising": rising,
        "flag": "Metabolic Stress Rising" if rising else "Normal",
    }
