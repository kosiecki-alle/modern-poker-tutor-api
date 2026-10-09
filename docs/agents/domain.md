# Domain documentation

## Layout

This is a single-context project:
- Glossary: root `CONTEXT.md`.
- Architecture decision records: `docs/adr/`.

## Consumer rules

- Read the glossary before exploring and use its domain vocabulary.
- Read ADRs relevant to the work.
- If a root `CONTEXT-MAP.md` is introduced, follow its relevant context links.
- Proceed silently when glossary or ADR files are absent.
- Create domain documents lazily through domain modeling, not during setup.
- Surface conflicts with ADRs rather than silently overriding them.
- Consult `ARCHITECTURE.md` for the confirmed poker-tutor design.
