# CLAUDE.md — Claude Code Project Guide

## Overview
《더 커뮤니티 2: 보이지 않는 손》 Monte Carlo simulation engine and interactive web dashboard.

## Key Invariants
- **UI Mode**: Light Mode only (`bg-white`, `bg-slate-50`). No dark mode.
- **Fonts**: Cafe24ProSlim ONLY for the main hero heading; Pretendard for everything else.
- **Resource Rules**:
  - Life: 43 initial capital + 50 subterranean reserve = 93 total.
  - War: Dynamic nightly price by Black (D-5 was 15💎).
  - Teams: White (6), Blue (3), Red (3) in 3 columns; Black Mart (1) isolated.
  - Sole survivor: Last resident per team survives at 0 life.

## Commands
- **Run Tests**: `python -m pytest`
- **Run Server**: `python web_server.py` (serves at http://localhost:8000)
- **Git Push**: `git add <files>; git commit -m "<msg>"; git push origin main`

For full details, see [HANDOFF.md](file:///E:/project/community2/HANDOFF.md) and [PROGRESS.md](file:///E:/project/community2/PROGRESS.md).
