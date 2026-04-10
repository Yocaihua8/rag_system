from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from backend.app.config import METADATA_PATH


DEFAULT_DEFINITION_PATH = METADATA_PATH / "metric_definitions.json"


@dataclass
class MetricDefinition:
    name: str
    aliases: List[str]
    unit: str
    better_direction: str
    definition: str


@dataclass
class MetricRecord:
    metric_name: str
    metric_alias: str
    value: str
    unit: str
    subject: str
    source_text: str
    confidence: float


def _load_definitions(def_path: Optional[Path] = None) -> List[MetricDefinition]:
    path = def_path or DEFAULT_DEFINITION_PATH
    if not path.exists():
        return []

    data = json.loads(path.read_text(encoding="utf-8"))
    definitions = []
    for item in data.get("metrics", []):
        definitions.append(
            MetricDefinition(
                name=item.get("name", ""),
                aliases=item.get("aliases", []),
                unit=item.get("unit", ""),
                better_direction=item.get("better_direction", ""),
                definition=item.get("definition", ""),
            )
        )
    return definitions


def _build_alias_map(defs: List[MetricDefinition]) -> Dict[str, str]:
    alias_map: Dict[str, str] = {}
    for d in defs:
        if d.name:
            alias_map[d.name.lower()] = d.name
        for a in d.aliases:
            alias_map[a.lower()] = d.name
    return alias_map


def _split_sentences(text: str) -> List[str]:
    parts = re.split(r"[。！？\n]", text)
    return [p.strip() for p in parts if p.strip()]


def _split_clauses(sentence: str) -> List[str]:
    parts = re.split(r"[；;]", sentence)
    return [p.strip() for p in parts if p.strip()]


def _has_number(text: str) -> bool:
    return bool(re.search(r"\d", text))


def _extract_value_unit(clause: str) -> List[Dict[str, str]]:
    results = []
    patterns = [
        r"(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>%|％)",
        r"(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>ms|毫秒|秒|s|分钟|min)",
        r"(?P<value>\d+)\s*(?P<unit>次|条|个|项|单|接口|工单)",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, clause):
            results.append({"value": match.group("value"), "unit": match.group("unit")})
    return results


def _match_metric_name(clause: str, alias_map: Dict[str, str]) -> Optional[Dict[str, str]]:
    matches = []
    for alias, canonical in alias_map.items():
        if alias and alias in clause.lower():
            matches.append((alias, canonical))
    if not matches:
        return None
    matches.sort(key=lambda x: len(x[0]), reverse=True)
    return {"alias": matches[0][0], "name": matches[0][1]}


def _extract_subjects(clause: str, metric_alias: str) -> List[str]:
    # Pattern: A和B的指标
    m = re.search(r"([\u4e00-\u9fffA-Za-z0-9_、/]+)的" + re.escape(metric_alias), clause)
    if m:
        raw = m.group(1)
        parts = re.split(r"[、/]|和|及|与|以及", raw)
        subjects = [p.strip() for p in parts if p.strip()]
        if subjects:
            return subjects

    # Fallback: take short prefix before alias
    idx = clause.lower().find(metric_alias)
    if idx > 0:
        prefix = clause[:idx].strip()
        if len(prefix) > 12:
            prefix = prefix[-12:]
        return [prefix]
    return [""]


def _multi_subject_ambiguous(subjects: List[str]) -> bool:
    # If more than 2 subjects and they are long, skip to avoid mixing
    if len(subjects) >= 3:
        if any(len(s) > 8 for s in subjects):
            return True
    return False


def extract_metrics(text: str, doc_id: str = "", def_path: Optional[Path] = None) -> List[MetricRecord]:
    if not text or not _has_number(text):
        return []

    defs = _load_definitions(def_path)
    alias_map = _build_alias_map(defs)
    if not alias_map:
        return []

    records: List[MetricRecord] = []
    for sentence in _split_sentences(text):
        for clause in _split_clauses(sentence):
            if not _has_number(clause):
                continue

            metric = _match_metric_name(clause, alias_map)
            if not metric:
                continue

            values = _extract_value_unit(clause)
            if not values:
                continue

            subjects = _extract_subjects(clause, metric["alias"])
            if _multi_subject_ambiguous(subjects):
                continue

            for item in values:
                value = item["value"]
                unit = item["unit"]
                if unit in ["%", "％"] and "." in value:
                    continue

                for subject in subjects:
                    confidence = 0.6
                    if metric["alias"] != metric["name"].lower():
                        confidence += 0.1
                    if unit:
                        confidence += 0.1
                    if subject:
                        confidence += 0.05

                    records.append(
                        MetricRecord(
                            metric_name=metric["name"],
                            metric_alias=metric["alias"],
                            value=value,
                            unit=unit,
                            subject=subject,
                            source_text=clause.strip(),
                            confidence=round(min(confidence, 0.95), 2),
                        )
                    )
    return records
