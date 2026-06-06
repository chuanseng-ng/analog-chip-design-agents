<#
.SYNOPSIS
  One-step installer for the analog-chip-design-agents marketplace (Windows / PowerShell).

.DESCRIPTION
  Registers this marketplace with Claude Code and installs its plugins. Plugin names are
  read from .claude-plugin/marketplace.json so the list stays in sync with the registry.

.PARAMETER Plugins
  Optional plugin name(s) to install. When omitted, every plugin in the registry is installed.

.PARAMETER List
  List the plugins that would be installed, then exit.

.EXAMPLE
  ./install.ps1
  ./install.ps1 -List
  ./install.ps1 analog-design-circuit analog-design-simulation

.NOTES
  Requires the `claude` CLI on PATH.
#>
[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Plugins,
    [switch]$List
)

$ErrorActionPreference = 'Stop'

$RepoSlug    = 'chuanseng-ng/analog-chip-design-agents'
$Marketplace = 'analog-chip-design-agents'
$ScriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$Registry    = Join-Path $ScriptDir '.claude-plugin/marketplace.json'

if (-not (Test-Path $Registry)) {
    Write-Error "registry not found: $Registry"; exit 1
}

function Get-RegistryPlugins {
    (Get-Content -Raw $Registry | ConvertFrom-Json).plugins |
        ForEach-Object { $_.name } | Where-Object { $_ }
}

if ($List) {
    Get-RegistryPlugins
    exit 0
}

if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
    Write-Error "the 'claude' CLI was not found on PATH — install Claude Code first"; exit 1
}

$ToInstall = if ($Plugins -and $Plugins.Count -gt 0) { $Plugins } else { @(Get-RegistryPlugins) }
if (-not $ToInstall -or $ToInstall.Count -eq 0) {
    Write-Error "no plugins to install"; exit 1
}

Write-Host "Registering marketplace '$Marketplace' (github:$RepoSlug)..."
try {
    & claude plugin marketplace add "github:$RepoSlug"
} catch {
    Write-Host "note: marketplace add failed (it may already be registered) — continuing"
}

$failed = @()
foreach ($plugin in $ToInstall) {
    Write-Host "Installing $plugin@$Marketplace..."
    & claude plugin install "$plugin@$Marketplace"
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "failed to install $plugin"
        $failed += $plugin
    }
}

Write-Host ''
if ($failed.Count -eq 0) {
    Write-Host "Done — installed $($ToInstall.Count) plugin(s) from $Marketplace."
} else {
    Write-Error "Completed with $($failed.Count) failure(s): $($failed -join ', ')"
    exit 1
}
