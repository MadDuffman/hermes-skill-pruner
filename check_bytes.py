#!/usr/bin/env python3
"""Check that a prune lost nothing: bytes before vs after, per skill.

For every skill with a SKILL.md.bak.<date> it compares the original size against
the current SKILL.md plus the reference files touched on that date. The expected
result is a small POSITIVE difference: each new reference adds a header and each
pointer adds a few lines. A large negative difference means content went missing.

Usage:
    check_bytes.py [--skills-root DIR] [--date YYYYMMDD] [--tolerance KB]

Defaults: root ~/.hermes/skills, date today, tolerance 8 KB.
Exit codes: 0 all within tolerance, 1 something looks lost.
"""
from __future__ import annotations

import datetime
import pathlib
import sys


def opt(name: str, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


root = pathlib.Path(opt('--skills-root', str(pathlib.Path.home() / '.hermes' / 'skills'))).expanduser()
stamp = opt('--date', datetime.date.today().strftime('%Y%m%d'))
tol = float(opt('--tolerance', '8')) * 1024
dia = datetime.datetime.strptime(stamp, '%Y%m%d').date()

baks = sorted(root.rglob('SKILL.md.bak.%s*' % stamp))
if not baks:
    sys.exit('no SKILL.md.bak.%s* under %s' % (stamp, root))

bad = 0
for bak in baks:
    d = bak.parent
    antes = bak.stat().st_size
    despues = (d / 'SKILL.md').stat().st_size
    nuevas = [f for f in (d / 'references').glob('*.md')
              if datetime.date.fromtimestamp(f.stat().st_mtime) == dia]
    cuadre = despues + sum(f.stat().st_size for f in nuevas) - antes
    ok = abs(cuadre) <= tol
    bad += 0 if ok else 1
    print('%-40s %6.1f KB -> %5.1f KB | %2d new refs %5.1f KB | %+6.1f KB %s' % (
        d.name, antes / 1024, despues / 1024, len(nuevas),
        sum(f.stat().st_size for f in nuevas) / 1024, cuadre / 1024, 'OK' if ok else 'REVIEW'))

print('---')
print('%d skill(s) checked, %d outside tolerance' % (len(baks), bad))
sys.exit(1 if bad else 0)
