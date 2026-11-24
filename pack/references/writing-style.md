# Writing style

Used by: `pm` skill, `documenter` skill, `ste-writing` skill.

When you write a durable file, apply Simplified Technical English (ASD-STE100) at about the 80% level. Do not copy the ASD dictionary. Its license forbids a copy.

Do not apply this style to a chat reply.
Do not apply this style to operator UI copy.
Do not add a linter for this style.

`.claude/skills/ste-writing/SKILL.md` holds the worked examples and the source credits.

## Where it applies

Use **Strict** mode for these texts.

1. Agent instructions.
2. Tool descriptions and command descriptions.
3. Error strings and status strings.
4. Cross-repo contract rules.

Use **STE-flavored** mode for plans, specs, PR bodies, READMEs, and agent reports.

## Strict

1. Use the active voice.
2. Put one instruction in each sentence.
3. Keep each sentence to about 20 words.
4. Use a simple tense.
5. Do not use a semicolon.
6. Do not use a phrasal verb. Write "start", not "spin up".
7. Do not use a nominalization. Write "analyze", not "perform an analysis".
8. Do not use a marketing adjective.
9. Keep a noun cluster to 3 words or fewer.
10. Put the condition before the action.
11. Use a numbered list for 3 or more steps.
12. Put each warning beside its step.

## STE-flavored

Keep these rules.

1. Use the active voice.
2. Keep each sentence to about 25 words.
3. Do not use a semicolon.
4. Do not use a nominalization.
5. Do not use a marketing adjective.

Treat every other Strict rule as advisory in this mode. Lexical rules are advisory here.

## Always

Do not break these rules to make a sentence shorter.

1. Keep every hedge. "May have failed" stays "may have failed".
2. Do not drop a condition to make a sentence shorter.
3. Do not drop a scope qualifier to make a sentence shorter.
4. Do not add a fact that the source did not state.
5. A project glossary overrides a generic synonym change. Before you replace a verb, read the glossary the project names. One example path is docs/ai/glossary.md. When that glossary defines check, verify, validate, and confirm, keep each word.

## Specs and reports

Write each acceptance criterion in EARS form. `.claude/references/spec-and-plan-depth.md` states the EARS patterns and the RFC 2119 limit.

Follow `.claude/references/agent-report.md` for a PR body or an agent report.

## Self-check

Before you finish, run this list on your draft. This list adapts the abryfs/agent-ste (MIT) self-check.

In Strict mode, fix every hit.
In STE-flavored mode, fix each structural hit. A lexical hit is advisory in that mode.
When a check objects, keep the hedge, the condition, the scope qualifier, and the glossary verb.

1. Remove each contraction.
2. Do not use "should" or "may" as a requirement. When "may" is a hedge, keep it.
3. Do not use the present perfect. Keep a hedge that uses it, such as "may have failed".
4. Remove each semicolon.
5. When "if" sits in the middle of a sentence, move that condition before the action.
6. Split a sentence that passes the word cap for its mode.
7. Compare verbs with the project glossary. Do not merge words that the glossary separates.
8. Replace each phrasal verb.
9. Replace each nominalization.
10. Remove each marketing adjective.
