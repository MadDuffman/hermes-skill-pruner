# hermes-skill-pruner

Move whole sections of an oversized `SKILL.md` into `references/`, verbatim, and verify nothing was lost.

Four small stdlib-only Python scripts. No dependencies, no config, no framework.

## The problem, measured

Hermes loads a skill's `SKILL.md` into context in full every time it is used. A 100 KB
skill is roughly **25,000 tokens** — and once the conversation is compacted, that content
is replaced by a one-line marker (`[SKILL_PRUNED: content lost in compression]`) telling
the agent to reload it. So the skill both costs the most and is the first thing to go.

**Important, and easy to get wrong:** that marker is *not* caused by the size of the skill.
It is emitted by the context compressor (`agent/context_compressor.py::_sum_skill_view`) when
it summarises an old `skill_view` tool result, and its own comment says *"any loaded body,
however small, leaves the marker"*. Pruning does not remove the marker. What it removes is
the cost per load (25k → 12k tokens) and the context pressure that makes compaction arrive
sooner.

Pruning 11 skills in one fleet went from ~916 KB to ~436 KB of body text (−52%), with zero
content lost: every section was moved verbatim, never summarised.

## Why move instead of summarise

Summarising is the only step that can lose information, and it is not necessary. A section
moved to `references/<topic>.md` is read only when that topic comes up. The body keeps the
heading, one line saying why the detail exists, and a pointer to it.

The failure mode to avoid is the opposite of laziness: a section silently rewritten in half
the words, with the judgement calls gone.

## Scripts

| Script | What it does |
|---|---|
| `prune_section.py <skill_dir> "<exact heading>" [slug] [--apply]` | Moves one `## ` section into `references/<slug>.md` and leaves a pointer. Dry run unless `--apply`. |
| `prune_to_target.py <skill_dir> <target_bytes> [--min-bytes N] [--apply]` | Repeatedly moves the **largest** remaining section until the body is under the target. This is the one you normally use. |
| `check_bytes.py [--skills-root DIR] [--date YYYYMMDD] [--tolerance KB]` | For each `SKILL.md.bak.<date>`: original bytes vs current body + references written that day. A small positive difference is expected (headers and pointers); a large negative one means content went missing. |
| `check_refs.py [--skills-root DIR] [--min-bytes N]` | Every `references/x.md` cited by a `SKILL.md` must exist and have a body. Resolves cross-skill pointers before declaring one broken. |

Exit codes are meaningful: `0` good, `1` something to look at. Usable in cron.

## Usage

```bash
# 1. back up first — always, per skill
cp skills/my-skill/SKILL.md skills/my-skill/SKILL.md.bak.$(date +%Y%m%d_%H%M%S)

# 2. see what would move (nothing is written without --apply)
python3 prune_to_target.py skills/my-skill 46000

# 3. do it
python3 prune_to_target.py skills/my-skill 46000 --apply

# 4. prove it
python3 check_bytes.py --skills-root skills
python3 check_refs.py  --skills-root skills
```

A target of 40–50 KB per body (~10–12k tokens) is a reasonable working ceiling. Prune the
biggest skill, measure, repeat: **the list of giants shifts**. Lower the six first and the
next five (79, 79, 69, 58, 55 KB) become the biggest — measuring only the original list
leaves the job half done.

## Self-check

```bash
bash test.sh
```

It builds a fake skill, prunes it, asserts the content survived, and then **asserts that
the two checks fail** when a reference is deleted or emptied. A check that only ever passes
is not a check.

## What this does not do

- It does not rewrite, summarise or fix prose. It moves bytes.
- It does not judge what belongs in the body. That is your editorial call: leave the rules,
  move the case histories.
- It does not touch git. Use `.bak` files or a commit; both work.
- `check_bytes.py` needs a `SKILL.md.bak.<date>` to compare against, so back up first. That
  is by design: it verifies against the state you had before, not against itself.

## Licence

MIT. See `LICENSE`.
