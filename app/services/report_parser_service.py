import json
from dataclasses import dataclass
from typing import Any
from urllib import error, request

from app.core.config import settings


@dataclass
class StructuredReportParameter:
    name: str
    normalized_key: str
    value: float
    unit: str
    reference_range: str | None = None


@dataclass
class StructuredReport:
    report_date: str | None
    parameters: list[StructuredReportParameter]


NORMALIZED_KEYS = {
    'hba1c': 'HbA1c',
    'triglycerides': 'Triglycerides',
    'hdl': 'HDL',
    'ldl': 'LDL',
    'total cholesterol': 'Total Cholesterol',
    'fasting glucose': 'Fasting Glucose',
}


def normalize_parameter_name(name: str) -> str:
    key = name.strip().lower()
    return NORMALIZED_KEYS.get(key, name.strip())


def _validate_payload(payload: Any) -> StructuredReport:
    if not isinstance(payload, dict) or 'parameters' not in payload:
        raise ValueError('Invalid payload')
    params = payload.get('parameters', [])
    if not isinstance(params, list):
        raise ValueError('Invalid parameters')
    seen: set[str] = set()
    cleaned: list[StructuredReportParameter] = []
    for item in params:
      if not isinstance(item, dict):
        continue
      raw_name = str(item.get('name', '')).strip()
      if not raw_name:
        continue
      normalized = normalize_parameter_name(raw_name)
      key = normalized.lower()
      if key in seen:
        continue
      seen.add(key)
      value = item.get('value')
      if not isinstance(value, (int, float)):
        continue
      unit = str(item.get('unit', '')).strip() or 'unknown'
      reference_range = item.get('reference_range')
      cleaned.append(StructuredReportParameter(name=raw_name, normalized_key=normalized, value=float(value), unit=unit, reference_range=str(reference_range).strip() if reference_range else None))
    return StructuredReport(report_date=payload.get('report_date'), parameters=cleaned)


def parse_lab_report(text: str) -> StructuredReport:
    if not settings.openai_api_key:
        raise ValueError('OpenAI API key is required for report parsing')

    schema = {
        'type': 'object',
        'additionalProperties': False,
        'properties': {
            'report_date': {'type': ['string', 'null']},
            'parameters': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'additionalProperties': False,
                    'properties': {
                        'name': {'type': 'string'},
                        'value': {'type': 'number'},
                        'unit': {'type': 'string'},
                        'reference_range': {'type': ['string', 'null']},
                    },
                    'required': ['name', 'value', 'unit', 'reference_range'],
                },
            },
        },
        'required': ['report_date', 'parameters'],
    }

    body = {
        'model': settings.openai_model,
        'response_format': {'type': 'json_schema', 'json_schema': {'name': 'lab_report', 'strict': True, 'schema': schema}},
        'messages': [
            {'role': 'system', 'content': 'Extract only numeric lab parameters. Return strict JSON. No commentary.'},
            {'role': 'user', 'content': text[:12000]},
        ],
        'temperature': 0,
        'max_tokens': 900,
    }

    for _ in range(3):
        req = request.Request(
            url='https://api.openai.com/v1/chat/completions',
            data=json.dumps(body).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {settings.openai_api_key}'},
            method='POST',
        )
        try:
            with request.urlopen(req, timeout=30) as response:
                payload = json.loads(response.read().decode('utf-8'))
            content = payload.get('choices', [{}])[0].get('message', {}).get('content', '')
            parsed = json.loads(content)
            return _validate_payload(parsed)
        except (error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
            continue

    raise ValueError('Invalid LLM output for report parsing')
