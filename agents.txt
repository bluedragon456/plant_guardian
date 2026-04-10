# AGENTS.md

## Project
Plant Guardian

## Purpose
Plant Guardian is the codebase for this project. Agents should treat this repository as the source of truth and build context from the code and docs before making changes.

## Workspace Notes
The local workspace for active development is currently:

`C:\dev\plant_guardian`

This project was previously worked on from a OneDrive-based path. Any older workspace-specific references should be treated as historical only and not assumed to still apply.

## Agent Instructions
When assisting in this repository:

1. Read this file first.
2. Inspect the repository structure before making assumptions.
3. Prefer existing patterns and conventions over introducing new ones.
4. Preserve in-progress user work unless explicitly asked to change it.
5. Explain changes clearly and keep guidance practical.
6. Ask for clarification only when a decision has real product or technical tradeoffs.
7. Treat repo files and current code as more authoritative than past thread memory.

## Priorities
Current high-level priorities:

1. Maintain continuity after the workspace move
2. Keep the project easy to work on locally
3. Improve features and stability without unnecessary rewrites
4. Preserve useful context in repo documentation instead of relying on chat history alone

## Expected Workflow
For most tasks:

1. Read relevant docs and configuration files
2. Inspect the affected area of the codebase
3. Summarize the current state briefly
4. Make focused changes
5. Verify changes where practical
6. Report what changed and any follow-up items

## Files To Check Early
Agents should look for and use these first when relevant:

- `README.md`
- `AGENTS.md`
- `package.json`
- app entry files
- config files
- environment example files
- docs folder contents, if present

## Conventions
Follow these principles unless the repo clearly indicates otherwise:

- Prefer minimal, targeted changes
- Avoid unnecessary file churn
- Preserve established naming and structure
- Keep code readable over clever
- Add comments only when they clarify non-obvious logic
- Flag risks and assumptions clearly

## Context Handling
This repository may outlive individual chat threads. To preserve continuity:

- Store durable project guidance in repo docs
- Store implementation details in code and comments where appropriate
- Do not depend on archived thread history to understand the project
- If important decisions are made, document them in a suitable repo file

## When Starting A New Session
A new agent/session should:

1. Read `AGENTS.md`
2. Inspect the repo structure
3. Identify the stack and main app entry points
4. Summarize the current state before making major changes
5. Continue work using repo context as the primary memory source

## Notes
If additional long-term guidance is needed, add it here only if it is appropriate for a public repository.
