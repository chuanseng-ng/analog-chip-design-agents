#!/usr/bin/env python3
"""Single source of truth for memory-root resolution (analog flavor).

Resolution order (highest priority first):
  1. an explicit path argument (e.g. the caller's ``--memory-root``)
  2. the ``$CHIP_DESIGN_MEMORY_ROOT`` environment variable
  3. the central default ``<xdg_data>/chip-design-agents/<FLAVOR>/memory``
  4. the in-repo ``memory/`` seed as a last resort (only if the central
     location cannot be created)

The in-repo ``memory/`` tree is the version-controlled SEED. On first
resolution the central root is created and each ``<domain>/knowledge.md`` is
copied in if absent (never overwriting accumulated data). Runtime artifacts
(``experiences.jsonl`` / ``run_state.md``) are never seeded or overwritten.

Both ``distill.py`` and ``tools/qor_trends.py`` import this module so writers
(orchestrators) and readers (analysis tools) resolve the same root.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

FLAVOR = "analog"  # "digital" in the digital repo

# plugins/infrastructure/skills/memory-keeper/memory_root.py -> repo root is parents[4]
REPO_ROOT = Path(__file__).resolve().parents[4]
SEED_ROOT = REPO_ROOT / "memory"


def _xdg_data_home() -> Path:
    """Base data dir, honoring XDG_DATA_HOME and platform conventions."""
    if sys.platform.startswith("win"):
        base = os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local")
        return Path(base)
    # macOS uses the same XDG rule for cross-platform parity; honor XDG_DATA_HOME if set.
    xdg = os.environ.get("XDG_DATA_HOME")
    return Path(xdg) if xdg else Path.home() / ".local" / "share"


def central_root() -> Path:
    """The central, machine-level memory root for this flavor."""
    return _xdg_data_home() / "chip-design-agents" / FLAVOR / "memory"


def seed_if_absent(seed_root: Path, dest_root: Path) -> list[str]:
    """Copy each ``<domain>/knowledge.md`` seed into ``dest_root`` only when absent.

    Never touches ``experiences.jsonl`` / ``run_state.md`` and never overwrites an
    existing ``knowledge.md``. Returns the list of domains seeded.
    """
    seeded: list[str] = []
    if not seed_root.is_dir() or seed_root.resolve() == dest_root.resolve():
        return seeded
    for know in sorted(seed_root.glob("*/knowledge.md")):
        target = dest_root / know.parent.name / "knowledge.md"
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(know, target)
            seeded.append(know.parent.name)
    return seeded


def migrate_repo_local(seed_root: Path, dest_root: Path) -> list[str]:
    """One-time move of repo-local runtime data into the central root.

    Moves ``<domain>/experiences.jsonl`` and ``run_state.md`` from the in-repo
    seed tree to ``dest_root`` only when the destination does not already exist.
    Never merges. Returns a list of ``"<domain>/<file>"`` entries moved.
    """
    moved: list[str] = []
    if not seed_root.is_dir() or seed_root.resolve() == dest_root.resolve():
        return moved
    for name in ("experiences.jsonl", "run_state.md"):
        for src in sorted(seed_root.glob(f"*/{name}")):
            target = dest_root / src.parent.name / name
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(target))
                moved.append(f"{src.parent.name}/{name}")
    return moved


def resolve_memory_root(explicit: str | None = None, *, create: bool = True,
                        seed: bool = True) -> Path:
    """Resolve the active memory root following the documented order."""
    if explicit:
        # An explicit path is honored verbatim and never auto-created or seeded,
        # so callers that treat a missing root as "not found" keep working.
        return Path(explicit).expanduser()
    env = os.environ.get("CHIP_DESIGN_MEMORY_ROOT")
    root = Path(env).expanduser() if env else central_root()
    if create:
        try:
            root.mkdir(parents=True, exist_ok=True)
        except OSError:
            # Central location unwritable: fall back to the in-repo seed tree.
            return SEED_ROOT
        if seed:
            seed_if_absent(SEED_ROOT, root)
    return root


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Resolve (and optionally seed) the chip-design memory root.")
    ap.add_argument("--memory-root", default=None,
                    help="Explicit memory root (highest precedence).")
    ap.add_argument("--no-seed", action="store_true",
                    help="Do not copy seed knowledge.md files into the resolved root.")
    ap.add_argument("--init", action="store_true",
                    help="Seed knowledge.md and migrate any repo-local runtime data, then report.")
    args = ap.parse_args(argv)

    root = resolve_memory_root(args.memory_root, create=True, seed=not args.no_seed)

    if args.init:
        seeded = seed_if_absent(SEED_ROOT, root)
        moved = migrate_repo_local(SEED_ROOT, root)
        print(f"memory root: {root}")
        print(f"flavor:      {FLAVOR}")
        print(f"seeded:      {', '.join(seeded) if seeded else '(none — all present)'}")
        print(f"migrated:    {', '.join(moved) if moved else '(none)'}")
    else:
        print(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
