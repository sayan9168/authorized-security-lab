from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ReportGenerator:
    @staticmethod
    def json_report(title: str, findings: list[dict[str, Any]], destination: str | Path) -> Path:
        output = {
            "title": title,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "finding_count": len(findings),
            "findings": findings,
        }
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")
        temporary.replace(path)
        return path

    @staticmethod
    def markdown_report(title: str, findings: list[dict[str, Any]], destination: str | Path) -> Path:
        lines = [f"# {title}", "", f"Generated: {datetime.now(timezone.utc).isoformat()}", "", f"Findings: {len(findings)}", ""]
        for index, finding in enumerate(findings, 1):
            lines.extend([f"## Finding {index}: {finding.get('title', 'Untitled')}", "", f"- Severity: {finding.get('severity', 'informational')}", f"- Target: {finding.get('target', 'n/a')}", f"- Evidence: {finding.get('evidence', 'n/a')}", ""])
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines), encoding="utf-8")
        return path
