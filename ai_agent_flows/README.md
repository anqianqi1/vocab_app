# AI Agent Flows

Use this folder to capture runbooks, prompts, or session summaries when agents tackle multi-step tasks.

## Relationship to docs/

- **`ai_agent_flows/`** = session logs & narrative history ("how we got here")
- **`docs/`** = reference documentation ("what you need to know now")

After each session, create a dated log here AND update the relevant reference docs in `docs/` with any new facts, commands, or architecture decisions.

## Session Logs

| Date | Session | Summary |
|------|---------|---------|
| 2026-05-22 | [iOS Adaptive Layout](2026-05-22-ios-adaptive-layout/session.md) | Fixed iPad layout: GeometryReader-based branching, custom HStack split-view, scheme post-action script |

## Template

1. Create a dated subfolder (e.g., `2026-05-16-grade5-polish/`).
2. Drop a `session.md` with goals, decisions, files changed, known issues, and lessons learned.
3. Update the reference docs in `docs/` with any new permanent knowledge.
4. Add a row to the Session Logs table above.
5. Add a bullet to the "Recent Updates" list in [docs/README.md](../docs/README.md).

Keeping these notes current helps new agents understand context without re-reading entire transcripts.
