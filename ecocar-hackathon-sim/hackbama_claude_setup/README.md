# HackBama Claude Code Setup

Copy this folder's contents into the root of `ecocar-hackathon-sim`.

In PowerShell from that repo:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\setup_claude.ps1
```

Then restart Claude Code from the repository root.

The setup script downloads the current Everything Claude Code repository and runs its Claude/Python installer. The included `.claude` directory adds HackBama-specific rules and an `ecocar-reliability` skill.

Review third-party installation scripts before running them. ECC changes over time, so this package intentionally installs the current upstream version instead of bundling a stale copy.
