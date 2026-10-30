# Issue tracker: GitHub

Issues and specs for this repo live as GitHub Issues in `theihoz/ML`. Use the `gh` CLI for all operations.

## Conventions

- **Create an issue**: `gh issue create --title "..." --body "..."`. Use a heredoc for multi-line bodies.
- **Read an issue**: `gh issue view <number> --json number,title,body,labels,comments`.
- **List issues**: `gh issue list --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'` with appropriate `--label` and `--state` filters.
- **Make an issue a sub-issue**: use GitHub's native sub-issue support when available; otherwise put `Part of #<parent>` at the top of the child body.
- **Blocking**: use GitHub's native issue dependencies when available; otherwise put `Blocked by: #<n>, #<n>` at the top of the child body.
- **Comment on an issue**: `gh issue comment <number> --body "..."`.
- **Apply / remove labels**: `gh issue edit <number> --add-label "..."` / `--remove-label "..."`.
- **Close**: explain the outcome with `gh issue comment`, then run `gh issue close`.

## Pull requests as a triage surface

**PRs as a request surface: no.**

## When a skill says "publish to the issue tracker"

Create a GitHub issue in `theihoz/ML`.

## Safety

Before creating an issue, verify the target with `gh repo view --json nameWithOwner`. File issues only in this repository, never in `mattpocock/skills`.
