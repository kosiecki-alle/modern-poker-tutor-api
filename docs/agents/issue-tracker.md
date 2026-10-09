# Issue tracker: Local Markdown

Issues and specs live under `spec/`.

## Conventions

- One feature per directory: `spec/<feature-slug>/`.
- Feature specification: `spec/<feature-slug>/spec.md`.
- Implementation tickets: `spec/<feature-slug>/issues/<NN>-<slug>.md`,
  numbered from 01, one file per ticket.
- Record triage state as a `Status:` line near the top of specs and tickets.
- Append comments under a `## Comments` heading.
- Publishing means creating or updating the relevant Markdown file.
- Fetching means reading the referenced file.

## Wayfinding

- Map: `spec/<effort>/map.md`.
- Child tickets: `spec/<effort>/issues/<NN>-<slug>.md`.
- Record ticket type with `Type:` and dependencies with `Blocked by:`.
- An open ticket is unblocked when all listed dependencies are resolved.
- Claim a ticket with `Status: claimed` before working.
- Resolve with `Status: resolved`, append an `## Answer`, and update the map.
- Choose the lowest-numbered open, unblocked, unclaimed ticket first.
