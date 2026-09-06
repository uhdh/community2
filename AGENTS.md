# AGENTS.md — Instructions for Autonomous AI Agents (Codex, Claude, etc.)

Welcome to **The Community 2: Invisible Hand (더 커뮤니티 2: 보이지 않는 손)** codebase.

Before making any modifications, read:
1. [HANDOFF.md](file:///E:/project/community2/HANDOFF.md) — Comprehensive handoff guide, domain rules, and backlog.
2. [PROGRESS.md](file:///E:/project/community2/PROGRESS.md) — Progress log, 1,000-run Monte Carlo statistics, and UI specs.
3. [RULEBOOK.md](file:///E:/project/community2/RULEBOOK.md) — Official broadcast rules and economic mechanics.

---

## ⚠️ Non-Negotiable Project Constraints

1. **Light Mode Only**:
   - The UI was completely refactored to **Clean Light Mode** (`bg-white`, `bg-slate-50`). Do NOT revert to dark mode.
2. **Typography System**:
   - ONLY `<h1 class="font-hero-title">` uses `'Cafe24ProSlim'`.
   - ALL other elements (cards, text, buttons, modals) MUST use **Pretendard**.
3. **Core Economic Rules**:
   - **Life Pool (❤️)**: Initial capital **43** (White 14, Blue 19, Red 10) + Subterranean reserve **50** = **93 total**. Visualized in two distinct matrix compartments.
   - **War Declaration (💣)**: Price is NOT fixed. Determined nightly by Black (D-5 was 15💎). Prize pool (200M KRW) burns the fee permanently; winner loots 50% of loser's inventory.
   - **Teams**: 3 mortal player teams (White, Blue, Red) + 1 distinct Black Mart special entity.
   - **Sole Survivor Rule**: The last surviving member of each team is exempt from elimination even with 0 life.
4. **Testing Invariant**:
   - Always run `python -m pytest` before committing. All 14 tests must pass.

---

## 🛠️ Common Commands

```powershell
# Run test suite
python -m pytest

# Run local preview server
python web_server.py

# Git commit (in PowerShell, use ';' instead of '&&')
git add <files>; git commit -m "<message>"; git push origin main
```
