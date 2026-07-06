# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository purpose

This is a documentation-only repository (no source code, build system, tests, or package manifest). It holds Vietnamese-language how-to guides about using Claude Code and related tooling. There is nothing to build, lint, or test — work here consists of editing/extending the Markdown guides themselves.

## Contents

- [huong-dan-claude-code.md](huong-dan-claude-code.md) — comprehensive Claude Code (VS Code) guide, from basic setup to automation. Numbered sections (0–11) cover: quick setup, slash commands/hooks/plugins, sub-agents & agent teams, git worktrees for parallel work, context/token management, deploying an API to Modal, advanced features, running multiple Claude instances in parallel, MCP, token optimization for large projects, building automation (incl. GitHub Actions), and the `.claude/` directory structure/conventions.
- [huong-dan-claude-swap.md](huong-dan-claude-swap.md) — step-by-step Windows install guide for `claude-swap` (`cswap`), a tool for switching between multiple Claude accounts (e.g. Team vs Pro) via Python/`uv`.

## Working in this repo

- Content is written in Vietnamese; keep new edits consistent with that language and the existing tone (concise, practical, instructional).
- Both files use numbered `##`/`###` section headers with fenced code blocks (`powershell`, `bash`, `json`, `markdown`) for copy-pasteable commands/config. Follow this structure when adding new sections.
- The guides explicitly cross-reference official docs (e.g. `https://docs.claude.com/en/docs/claude-code/overview`) and note that Claude Code changes frequently — when updating content, prefer verifying against current official docs rather than assuming prior guide text is still accurate.
