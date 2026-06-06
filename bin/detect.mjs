// detect.mjs — read-only detection of installed AI coding agents.
//
// A target counts as "installed" if EITHER its CLI binary is on PATH OR its
// config directory exists in the user's home. This is the single source of
// truth for the npm installer's auto-detect mode; install.sh / install.ps1
// replicate the same signatures natively.
//
// Detection performs no writes and spawns no processes — it only inspects
// PATH entries and checks for directories.

import { accessSync, constants, existsSync, statSync } from "node:fs";
import { homedir, platform } from "node:os";
import { join, delimiter } from "node:path";

// ── PATH lookup (cross-platform `which`, no external dependency) ───────────────
// Resolves whether `bin` is an executable on PATH. On Windows, candidate
// extensions come from PATHEXT (.COM;.EXE;.BAT;.CMD;...).
function onPath(bin) {
  const dirs = (process.env.PATH || "").split(delimiter).filter(Boolean);
  const isWin = platform() === "win32";
  const exts = isWin
    ? (process.env.PATHEXT || ".COM;.EXE;.BAT;.CMD").split(";").filter(Boolean)
    : [""];
  for (const dir of dirs) {
    for (const ext of exts) {
      const candidate = join(dir, bin + (isWin ? ext.toLowerCase() : ext));
      const candidateUpper = join(dir, bin + ext);
      for (const c of new Set([candidate, candidateUpper])) {
        try {
          if (!statSync(c).isFile()) continue;
          // On Windows the PATHEXT match is the executability signal; elsewhere
          // require the execute bit so we match the shell's `command -v` contract
          // (a non-executable file on PATH is not an installed CLI).
          if (isWin) return c;
          accessSync(c, constants.X_OK);
          return c;
        } catch {
          /* not here / not executable, keep looking */
        }
      }
    }
  }
  return null;
}

function dirExists(p) {
  try {
    return existsSync(p) && statSync(p).isDirectory();
  } catch {
    return false;
  }
}

// ── Target catalogue ──────────────────────────────────────────────────────────
// Each entry knows how to detect itself and how to describe where it installs.
// `destination(global)` returns a human-readable path shown in the confirm step.
const HOME = homedir();

export const TARGETS = [
  {
    id: "claude",
    label: "Claude Code",
    bins: ["claude"],
    dirs: [process.env.CLAUDE_CONFIG_DIR || join(HOME, ".claude")],
    destination: () =>
      `${process.env.CLAUDE_CONFIG_DIR || join(HOME, ".claude")} (global plugin cache)`,
  },
  {
    id: "codex",
    label: "OpenAI Codex CLI",
    bins: ["codex"],
    dirs: [join(HOME, ".codex")],
    destination: (global) =>
      global ? join(HOME, ".codex", "instructions.md") : join(process.cwd(), "AGENTS.md"),
  },
  {
    id: "opencode",
    label: "OpenCode",
    bins: ["opencode"],
    dirs: [join(HOME, ".config", "opencode")],
    destination: (global) =>
      global
        ? join(HOME, ".config", "opencode", "config.json")
        : join(process.cwd(), "opencode.json"),
  },
  {
    id: "gemini",
    label: "Gemini Code Assist",
    bins: ["gemini"],
    dirs: [join(HOME, ".gemini")],
    destination: (global) =>
      global ? join(HOME, "GEMINI.md") : join(process.cwd(), "GEMINI.md"),
  },
  {
    // Copilot is project-scoped and has no reliable home-dir marker, so it is
    // only auto-detected via the `gh` / `copilot` CLI. Users can still add it
    // explicitly with --ide copilot.
    id: "copilot",
    label: "GitHub Copilot",
    bins: ["copilot", "gh"],
    dirs: [],
    destination: () => join(process.cwd(), ".github"),
  },
];

// Returns one record per target with whether it was found and why.
export function detectAgents({ global = false } = {}) {
  return TARGETS.map((t) => {
    const reasons = [];
    let foundBin = null;
    for (const b of t.bins) {
      if (onPath(b)) {
        foundBin = b;
        break;
      }
    }
    if (foundBin) reasons.push(`'${foundBin}' on PATH`);
    const foundDir = t.dirs.find(dirExists);
    if (foundDir) reasons.push(`${foundDir} exists`);
    return {
      id: t.id,
      label: t.label,
      installed: reasons.length > 0,
      reason: reasons.join(", "),
      destination: t.destination(global),
    };
  });
}
