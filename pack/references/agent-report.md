# Agent report

Used by: `documenter` skill (PR bodies and agent reports), `pm` skill (requested reports), `ste-writing` skill.

Use these headings, in this order, for a PR body and for an agent report. Write the body in STE-flavored English. `.claude/references/writing-style.md` states the style rules.

Do not drop a heading. When a heading has no content, write "None".
Do not add a fact that the source did not state.
Keep every hedge.

The feature summary that `/feature-merge` stores is a different document. The `documenter` skill defines the summary sections. When you write the PR body, use the headings below. Do not copy security findings into the PR body. The `documenter` skill forbids that.

## Summary

Write 2 or 3 sentences. State what changed and why.

## Actions taken

List each action you took. When you list 3 or more actions, use a numbered list.

## Assumptions

List each assumption you used. Keep each hedge.

## Open risks

List each risk that remains. Put the condition before the effect.

## Verification checklist

Name each check you ran and the result. Do not report a check you did not run.

## Not done / follow-ups

List work you did not do. When you know the owner, name the owner.

## Blank form

```markdown
## Summary

<2 or 3 sentences. What changed, and why.>

## Actions taken

1. <action>

## Assumptions

- <assumption, with its hedge>

## Open risks

- <condition, then the risk>

## Verification checklist

- <check you ran>: <result>

## Not done / follow-ups

- <item>
```
