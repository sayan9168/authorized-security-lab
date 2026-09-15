from __future__ import annotations

import json
from typing import Iterable

from aslab.core.findings import Finding


_LEVEL = {"info": "note", "low": "warning", "medium": "warning", "high": "error", "critical": "error"}


def to_sarif(findings: Iterable[Finding], tool_name: str = "Authorized Security Lab") -> str:
    rules = []
    results = []
    seen: set[str] = set()
    for finding in findings:
        rule_id = "aslab." + "".join(c.lower() if c.isalnum() else "-" for c in finding.title).strip("-")
        if rule_id not in seen:
            seen.add(rule_id)
            rules.append({"id": rule_id, "name": finding.title, "shortDescription": {"text": finding.title}})
        results.append({
            "ruleId": rule_id,
            "level": _LEVEL[finding.severity],
            "message": {"text": finding.description},
            "locations": [{"physicalLocation": {"artifactLocation": {"uri": finding.asset}}}],
            "properties": {"severity": finding.severity, "evidence": finding.evidence},
        })
    document = {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{"tool": {"driver": {"name": tool_name, "rules": rules}}, "results": results}],
    }
    return json.dumps(document, indent=2, sort_keys=True)
