#!/usr/bin/env python3
"""Move one '## ' section of a SKILL.md into references/<slug>.md and leave a pointer.

Why: an oversized SKILL.md costs its full size in context every time it is loaded,
and a 100 KB skill is ~25k tokens. Moving whole sections out keeps the content
(the section is copied verbatim, never summarised) while the body stays small.

Usage:
    prune_section.py <skill_dir> "<exact heading>" [slug] [--apply]

Without --apply it only prints what it would do. Exit codes: 0 ok, 1 heading not
found, 2 bad arguments.
"""
from __future__ import annotations

import re
import sys
import pathlib

args = [a for a in sys.argv[1:] if not a.startswith('--')]
apply = '--apply' in sys.argv
if len(args) < 2:
    sys.exit(__doc__)
skill_dir, titulo = pathlib.Path(args[0]), args[1]
if not (skill_dir / 'SKILL.md').exists():
    sys.exit('no SKILL.md in %s' % skill_dir)


def slugify(t: str) -> str:
    s = re.sub(r'[^a-z0-9]+', '-', t.lstrip('# ').lower()).strip('-')
    return s[:60] or 'section'


slug = args[2] if len(args) > 2 else slugify(titulo)

md = skill_dir / 'SKILL.md'
lines = md.read_text(encoding='utf-8').splitlines()

start = next((i for i, l in enumerate(lines) if l.strip() == titulo.strip()), None)
if start is None:
    sys.exit('heading not found: %r' % titulo)
end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith('## ')), len(lines))
cuerpo = lines[start:end]
while cuerpo and not cuerpo[-1].strip():
    cuerpo.pop()

ref = skill_dir / 'references' / ('%s.md' % slug)
texto_ref = '# %s\n\n> Moved out of `SKILL.md` so the skill fits in context. Content is verbatim.\n\n%s\n' % (
    cuerpo[0].lstrip('# ').strip(), '\n'.join(cuerpo[1:]).lstrip('\n'))

puntero = [
    cuerpo[0],
    '',
    'Full detail (rules, cases, commands) lives in `references/%s.md`: **read it** before acting on' % slug,
    'this topic. Only the reason is left here, so you know it exists.',
    '',
]

print('section    : %s' % cuerpo[0])
print('lines      : %d -> %d in SKILL.md' % (len(cuerpo), len(puntero)))
print('reference  : references/%s.md (%d lines, %.1f KB)' % (slug, len(cuerpo), len(texto_ref.encode()) / 1024))
print('SKILL.md   : %.1f KB -> %.1f KB' % (
    md.stat().st_size / 1024,
    len('\n'.join(lines[:start] + puntero + lines[end:]).encode()) / 1024))

if not apply:
    print('\n(dry run: nothing written; add --apply)')
    sys.exit(0)

ref.parent.mkdir(parents=True, exist_ok=True)
if ref.exists() and not ref.with_suffix('.md.bak').exists():
    ref.rename(ref.with_suffix('.md.bak'))
ref.write_text(texto_ref, encoding='utf-8')
md.write_text('\n'.join(lines[:start] + puntero + lines[end:]), encoding='utf-8')
print('\nwritten. Verify with check_bytes.py and check_refs.py.')
