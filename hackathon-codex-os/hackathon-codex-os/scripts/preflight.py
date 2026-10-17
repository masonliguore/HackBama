#!/usr/bin/env python3
"""Offline documentation and secret-name hygiene checks; not a substitute for real tests."""
from pathlib import Path
import re
root=Path(__file__).resolve().parents[1]
required=['AGENTS.md','HACKATHON.md','PLAN.md','DECISIONS.md','DEMO.md','.env.example']
issues=[]
for name in required:
    if not (root/name).is_file(): issues.append(f'Missing {name}')
for name in ['HACKATHON.md','PLAN.md']:
    if (root/name).is_file() and (root/name).stat().st_size < 80: issues.append(f'{name} looks empty')
for p in root.rglob('*'):
    if not p.is_file() or any(x in p.parts for x in ['.git','node_modules','.venv','__pycache__']): continue
    if p.name == '.env': issues.append('A real .env exists: ensure it is untracked and never submit it')
    if p.suffix in {'.py','.ts','.tsx','.js','.json','.md'} and p.stat().st_size < 2_000_000:
        txt=p.read_text(encoding='utf-8',errors='ignore')
        if re.search(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',txt): issues.append(f'Possible private key in {p.relative_to(root)}')
print('Hackathon preflight:', 'PASS' if not issues else 'REVIEW')
for i in issues: print(' -',i)
print('Reminder: project-specific tests, contest rules, and deployment still require manual verification.')
raise SystemExit(1 if issues else 0)
