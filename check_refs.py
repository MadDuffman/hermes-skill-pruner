#!/usr/bin/env python3
"""Check that every `references/x.md` a SKILL.md points at exists and has a body.

A pointer to a file that does not exist is worse than not pruning at all: the
detail becomes unreachable while the skill still claims it is there. Cross-skill
pointers ("see `other-skill`, `references/y.md`") are resolved by looking for the
file anywhere under the root before being reported as broken.

Usage:
    check_refs.py [--skills-root DIR] [--min-bytes N]

Defaults: root ~/.hermes/skills, min body 200 bytes.
Exit codes: 0 all good, 1 broken or empty reference found.
"""
from __future__ import annotations

import pathlib
import re
import sys


def opt(name: str, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


root = pathlib.Path(opt('--skills-root', str(pathlib.Path.home() / '.hermes' / 'skills'))).expanduser()
min_bytes = int(opt('--min-bytes', '200'))
PAT = re.compile(r'`references/([A-Za-z0-9._\-]+\.md)`')

bad = 0
for md in sorted(root.rglob('SKILL.md')):
    txt = md.read_text(encoding='utf-8', errors='replace')
    refs = sorted(set(PAT.findall(txt)))
    rotas = [r for r in refs
             if not (md.parent / 'references' / r).exists()
             and not list(root.rglob('references/' + r))]
    vacias = [r for r in refs
              if (md.parent / 'references' / r).exists()
              and (md.parent / 'references' / r).stat().st_size < min_bytes]
    bad += len(rotas) + len(vacias)
    if refs:
        print('%-40s %2d refs cited  broken:%d  empty:%d' % (
            md.parent.name, len(refs), len(rotas), len(vacias)))
    for r in rotas:
        print('    BROKEN: references/%s' % r)
    for r in vacias:
        print('    EMPTY:  references/%s' % r)

print('---')
print('broken or empty references: %d' % bad)
sys.exit(1 if bad else 0)
