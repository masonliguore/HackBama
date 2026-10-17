#!/usr/bin/env python3
"""Reports demo checklist completeness. Does not prove app functionality."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
t=(root/'DEMO.md').read_text(encoding='utf-8')
checks=[l.strip() for l in t.splitlines() if l.strip().startswith('- [')]
done=sum(l.startswith('- [x]') or l.startswith('- [X]') for l in checks)
print(f'Demo readiness checklist: {done}/{len(checks)} marked complete')
for line in checks:
    if line.startswith('- [ ]'): print(' TODO',line[6:])
raise SystemExit(0 if checks and done == len(checks) else 1)
