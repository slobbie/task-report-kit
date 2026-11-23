#!/usr/bin/env python3
"""Check the visible text of an AS-IS/TO-BE report for Korean style issues.

Usage:
  python3 audit_report.py <report.html|text file> [--json]

Exit code is 1 when a violation (middle dot) is found, otherwise 0.
Review findings are hints only; a clean result does not prove the text is natural or accurate.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

REVIEW_RULES = [
    ("claim-review", r"극대화|혁신적|획기적|완벽한|완벽하게"),
    ("process-in-body", r"개발 빌드에서|임시 코드|캡처했|캡처하여|화면을 열었"),
    ("unverified-review", r"할 수 있습니다|될 수 있습니다|생길 수 있습니다|막힐 수 있습니다"),
    ("open-items-section", r"확인하지 못한 사항|미결 사항|추후 검토"),
]


def visible_text(raw: str, is_html: bool) -> str:
    if is_html:
        raw = re.sub(r"<(script|style|template)[\s\S]*?</\1>", " ", raw, flags=re.I)
        raw = re.sub(r"<br\s*/?>|</(p|div|li|h[1-6]|figcaption|td|th|section)>", "\n", raw, flags=re.I)
        raw = re.sub(r"<[^>]+>", " ", raw)
        raw = html.unescape(raw)
    raw = re.sub(r"```[\s\S]*?```", "", raw)
    raw = re.sub(r"`[^`\n]+`", "", raw)
    raw = re.sub(r"https?://\S+", "", raw)
    lines = [re.sub(r"[ \t]+", " ", x).strip() for x in raw.splitlines()]
    return "\n".join(x for x in lines if x and not x.startswith(">"))


def audit(text: str) -> dict:
    findings = []
    for i, line in enumerate(text.splitlines(), 1):
        if "·" in line:
            findings.append({"rule": "middle-dot", "severity": "violation", "line": i, "text": line[:80]})
        for rule, pat in REVIEW_RULES:
            for m in re.finditer(pat, line):
                findings.append({"rule": rule, "severity": "review", "line": i, "match": m.group(), "text": line[:80]})
    return {"chars": len(text), "middle_dots": text.count("·"), "findings": findings}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path")
    ap.add_argument("--json", action="store_true", help="print JSON")
    args = ap.parse_args()
    p = Path(args.path)
    raw = p.read_text(encoding="utf-8")
    result = audit(visible_text(raw, p.suffix.lower() in {".html", ".htm"}))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if not result["findings"]:
            print("검사 결과: 걸린 곳이 없습니다. 문장은 직접 다시 읽어 확인하세요.")
        for f in result["findings"]:
            what = f.get("match", "·")
            print(f"[{f['severity']}] {f['rule']} {what!r}: {f['text']}")
    return 1 if any(f["severity"] == "violation" for f in result["findings"]) else 0


if __name__ == "__main__":
    sys.exit(main())
