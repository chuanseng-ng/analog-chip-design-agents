#!/usr/bin/env node
// install.mjs — installs analog-chip-design-agents plugins for Claude Code.
//
// Usage (via npm):
//   npx analog-chip-design-agents            # Claude Code (default)
//   npx analog-chip-design-agents --ide claude
//
// This is the cross-platform Node port of the Claude Code path of install.sh.
// It runs as a single process and copies each plugin sequentially, so there is
// no concurrent write contention to the shared cache directory — the file-lock
// race that affected parallel marketplace installs on Windows cannot occur here.
//
// The other IDE targets (copilot, gemini, opencode, codex) are not yet ported
// to Node; use install.sh / install.ps1 for those. The shell scripts remain the
// supported fallback when Node is unavailable.

import { readFileSync, writeFileSync, existsSync, rmSync, mkdirSync, cpSync } from "node:fs";
import { homedir } from "node:os";
import { join, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const MARKETPLACE = "analog-chip-design-agents";

// Package root = parent of this bin/ directory. Resolving from import.meta.url
// (not process.cwd) makes the installer work from npm's unpacked layout.
const PACKAGE_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");

function fail(msg) {
  console.error(`ERROR: ${msg}`);
  process.exit(1);
}

function readJson(path) {
  return JSON.parse(readFileSync(path, "utf8"));
}

// ── Parse flags ───────────────────────────────────────────────────────────────
const VALID_IDES = ["claude", "copilot", "gemini", "opencode", "codex", "all"];
let ide = "claude";
const argv = process.argv.slice(2);
for (let i = 0; i < argv.length; i++) {
  const arg = argv[i];
  if (arg === "--ide") {
    if (i + 1 >= argv.length) {
      fail(`--ide requires a value (one of: ${VALID_IDES.join(", ")})`);
    }
    ide = argv[++i];
  } else if (arg === "--global") {
    // accepted for flag-parity with install.sh; only affects non-claude IDEs
  } else if (arg === "-h" || arg === "--help") {
    console.log("Usage: npx analog-chip-design-agents [--ide claude]");
    process.exit(0);
  } else {
    fail(`Unknown argument: ${arg}\nUsage: npx analog-chip-design-agents [--ide claude]`);
  }
}

if (!VALID_IDES.includes(ide)) {
  fail(`--ide must be one of: ${VALID_IDES.join(", ")}`);
}

if (ide !== "claude") {
  console.log(
    `The npm installer currently supports only --ide claude.\n` +
      `For "${ide}", run the shell installer from a cloned repo:\n` +
      `  bash install.sh --ide ${ide}      (macOS/Linux/Git Bash)\n` +
      `  .\\install.ps1 -IDE ${ide}         (Windows PowerShell)`
  );
  if (ide !== "all") process.exit(0);
  // for "all", continue with the Claude Code portion below.
}

// ── Load plugin list from the marketplace manifest (single source of truth) ────
const marketplacePath = join(PACKAGE_ROOT, ".claude-plugin", "marketplace.json");
if (!existsSync(marketplacePath)) {
  fail(`Cannot locate ${marketplacePath}. The package appears to be incomplete.`);
}
const plugins = readJson(marketplacePath).plugins;

// ── Locate the Claude config directory ─────────────────────────────────────────
// os.homedir() resolves %USERPROFILE% on Windows and $HOME elsewhere, matching
// install.sh's per-platform handling without needing a shell.
const claudeDir = process.env.CLAUDE_CONFIG_DIR || join(homedir(), ".claude");
const cacheDir = join(claudeDir, "plugins", "cache", MARKETPLACE);
// Durable copy of the marketplace source. Claude Code needs source.path to stay
// valid for catalog refresh and updates, so we copy the payload under claudeDir
// rather than pointing at the npm/npx package dir, which is reclaimable.
const installRoot = join(claudeDir, "plugins", "marketplaces", MARKETPLACE);
const settingsPath = join(claudeDir, "settings.json");

console.log(`Claude config : ${claudeDir}`);
console.log(`Plugin cache  : ${cacheDir}`);
console.log("");

if (!existsSync(claudeDir)) {
  fail(
    `Claude config directory not found at ${claudeDir}\n` +
      `  Make sure Claude Code is installed and has been run at least once.`
  );
}

// ── Copy each plugin into its own versioned cache directory ────────────────────
console.log("Installing Claude Code plugin cache...");
for (const plugin of plugins) {
  const name = plugin.name;
  const src = resolve(PACKAGE_ROOT, plugin.source);

  // Each plugin installs under the version declared in its own plugin.json, so
  // plugins at different versions (e.g. meta at 1.0.0 vs the rest at 1.2.0) land
  // in the correct cache path. Falls back to the package version if absent.
  const manifestPath = join(src, ".claude-plugin", "plugin.json");
  const version = existsSync(manifestPath)
    ? readJson(manifestPath).version
    : readJson(join(PACKAGE_ROOT, "package.json")).version;

  const dest = join(cacheDir, name, version);
  rmSync(dest, { recursive: true, force: true });
  mkdirSync(dest, { recursive: true });

  for (const sub of ["agents", "skills", ".claude-plugin"]) {
    const from = join(src, sub);
    if (existsSync(from)) cpSync(from, join(dest, sub), { recursive: true });
  }
  for (const file of ["README.md", "LICENSE"]) {
    const from = join(PACKAGE_ROOT, file);
    if (existsSync(from)) cpSync(from, join(dest, file));
  }

  console.log(`  [OK] ${name}`);
}

// ── Copy the marketplace source to a durable location under claudeDir ───────────
// This is what settings.json points at, so marketplace refresh/updates keep
// working even after the (reclaimable) npm/npx package directory is cleaned up.
rmSync(installRoot, { recursive: true, force: true });
mkdirSync(installRoot, { recursive: true });
for (const sub of [".claude-plugin", "plugins"]) {
  const from = join(PACKAGE_ROOT, sub);
  if (existsSync(from)) cpSync(from, join(installRoot, sub), { recursive: true });
}
for (const file of ["README.md", "LICENSE"]) {
  const from = join(PACKAGE_ROOT, file);
  if (existsSync(from)) cpSync(from, join(installRoot, file));
}

// ── Register plugins in settings.json (read-merge-write, replaces the Python) ───
console.log("");
console.log(`Updating ${settingsPath} ...`);

const cfg = existsSync(settingsPath) ? readJson(settingsPath) : {};
const enabled = (cfg.enabledPlugins ??= {});
for (const plugin of plugins) {
  enabled[`${plugin.name}@${MARKETPLACE}`] = true;
}
const marketplaces = (cfg.extraKnownMarketplaces ??= {});
marketplaces[MARKETPLACE] = {
  source: { source: "directory", path: installRoot },
};

writeFileSync(settingsPath, JSON.stringify(cfg, null, 2) + "\n");
console.log(`  [OK] ${plugins.length} plugins enabled in settings.json`);

console.log("");
console.log(`Done! Restart Claude Code to activate all ${plugins.length} plugins.`);
