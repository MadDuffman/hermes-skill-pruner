#!/usr/bin/env bash
# Self-check: prunes a fake skill and then proves the checks discriminate.
# Run: bash test.sh   (exit 0 = all good, 1 = something broke)
set -u
here=$(cd "$(dirname "$0")" && pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
skill="$tmp/skills/demo"
mkdir -p "$skill"
fail=0

ck() { if [ "$1" = "$2" ]; then echo "  ok   $3"; else echo "  FAIL $3 (got $1, want $2)"; fail=1; fi; }
nrefs() { if [ -d "$skill/references" ]; then ls "$skill/references"/*.md 2>/dev/null | wc -l | tr -d ' '; else echo 0; fi; }

# --- a skill big enough to need pruning (3 heavy sections + a small one)
{
  echo '---'
  echo 'name: demo'
  echo 'description: "fake skill for the self-check."'
  echo '---'
  echo
  echo '# Demo'
  echo
  echo '## Small rules'
  echo 'Keep this.'
  for s in alpha beta gamma; do
    echo
    echo "## Section $s"
    echo "MARKER-$s stays searchable in the reference."
    for i in $(seq 1 40); do echo "filler line $i of $s"; done
  done
} > "$skill/SKILL.md"
cp "$skill/SKILL.md" "$skill/SKILL.md.bak.$(date +%Y%m%d_%H%M%S)"
before=$(wc -c < "$skill/SKILL.md")

echo "1. prune_to_target (target 1200 bytes, min section 400)"
python3 "$here/prune_to_target.py" "$skill" 1200 --min-bytes 400 --apply >/dev/null 2>&1
ck "$?" 0 "prune_to_target exits 0"
after=$(wc -c < "$skill/SKILL.md")
[ "$after" -lt "$before" ] && echo "  ok   body shrank ${before} -> ${after} bytes" || { echo "  FAIL body did not shrink"; fail=1; }
[ "$after" -le 1600 ] && echo "  ok   body reached the target" || { echo "  FAIL body still ${after} bytes"; fail=1; }

echo "2. content survived the move"
ck "$(nrefs)" 3 "three references created"
moved=$(cat "$skill"/references/*.md 2>/dev/null | grep -c 'MARKER-')
ck "$moved" 3 "every marker is in a reference"
grep -q 'MARKER-alpha' "$skill/SKILL.md" && { echo "  FAIL section left its body in SKILL.md"; fail=1; } || echo "  ok   moved out of SKILL.md"
lines_after=$(( $(cat "$skill/SKILL.md" "$skill"/references/*.md | wc -l) ))
lines_before=$(wc -l < "$skill/SKILL.md.bak."*)
[ "$lines_after" -gt "$lines_before" ] && echo "  ok   nothing vanished (${lines_before} -> ${lines_after} lines, +headers/pointers)" || { echo "  FAIL lines went down"; fail=1; }

echo "3. check_bytes and check_refs accept a good prune"
python3 "$here/check_bytes.py" --skills-root "$tmp/skills" >/dev/null 2>&1
ck "$?" 0 "check_bytes passes"
python3 "$here/check_refs.py" --skills-root "$tmp/skills" >/dev/null 2>&1
ck "$?" 0 "check_refs passes"

echo "4. the checks must FAIL when something is broken"
mv "$skill/references/"*.md "$tmp/" 2>/dev/null
python3 "$here/check_refs.py" --skills-root "$tmp/skills" >/dev/null 2>&1
ck "$?" 1 "check_refs flags a dangling pointer"
mv "$tmp/"*.md "$skill/references/" 2>/dev/null
: > "$skill/references/$(ls "$skill/references" | head -1)"
python3 "$here/check_refs.py" --skills-root "$tmp/skills" >/dev/null 2>&1
ck "$?" 1 "check_refs flags an empty reference"

echo
[ "$fail" -eq 0 ] && { echo "ALL CHECKS PASSED"; exit 0; } || { echo "SOMETHING FAILED"; exit 1; }
