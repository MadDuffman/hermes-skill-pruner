#!/usr/bin/env python3
"""Shrink a SKILL.md down to a byte target by moving its largest sections out.

Always picks the biggest remaining section, so the minimum number of sections
moves. Delegates the actual move to prune_section.py (same pointer format).

Usage:
    prune_to_target.py <skill_dir> <target_bytes> [--min-bytes N] [--apply]

--min-bytes (default 1500) stops it from shredding a skill into confetti.
Exit codes: 0 ok, 1 nothing left to move before reaching the target.
"""
from __future__ import annotations

import subprocess
import sys
import pathlib

args = [a for a in sys.argv[1:] if not a.startswith('--')]
apply = '--apply' in sys.argv
min_bytes = 1500
if '--min-bytes' in sys.argv:
    min_bytes = int(sys.argv[sys.argv.index('--min-bytes') + 1])
if len(args) < 2:
    sys.exit(__doc__)

skill = pathlib.Path(args[0])
target = int(args[1])
md = skill / 'SKILL.md'
tool = pathlib.Path(__file__).with_name('prune_section.py')


def sections(lines: list[str]):
    """(bytes, start, end, heading) for every '## ' block, biggest first."""
    idx = [i for i, l in enumerate(lines) if l.startswith('## ')]
    out = []
    for k, i in enumerate(idx):
        end = idx[k + 1] if k + 1 < len(idx) else len(lines)
        out.append((len('\n'.join(lines[i:end]).encode()), i, end, lines[i]))
    return sorted(out, reverse=True)


moved: list[str] = []
while md.stat().st_size > target:
    lines = md.read_text(encoding='utf-8').splitlines()
    cands = [c for c in sections(lines) if c[0] > min_bytes and c[3] not in moved]
    if not cands:
        print('nothing left above %d bytes: SKILL.md stays at %.1f KB' % (min_bytes, md.stat().st_size / 1024))
        sys.exit(1)
    peso, _, _, titulo = cands[0]
    cmd = [sys.executable, str(tool), str(skill), titulo] + (['--apply'] if apply else [])
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit('failed on %r: %s' % (titulo, (r.stdout or r.stderr).strip()))
    moved.append(titulo)
    print('  %-56s %5.1f KB moved out' % (titulo[:56], peso / 1024))

print('---')
print('sections moved: %d | SKILL.md now %.1f KB (target %.1f KB)' % (
    len(moved), md.stat().st_size / 1024, target / 1024))
