# NLQ safety notes

## How a question is answered
1. The user types an English question.
2. `nlq/service.py` blocks unsupported questions (drivers, delivery duration, write requests).
3. The question is translated to SQL by `nlq/rules.py` (built-in rules). If an `ANTHROPIC_API_KEY` is set, Claude is used instead.
4. `nlq/validator.py` checks the SQL is a single SELECT or WITH query, has no comments, no write keywords, and uses only approved views.
5. `nlq/executor.py` runs it with the read-only role `foodflow_analytics`, a 10-second timeout and a 500-row limit.
6. The result is returned with the SQL so the dashboard can show it (Show SQL).

## Approved objects
Only the views and functions listed in `nlq/schema_context.md`. Raw tables are never queried.

## Unsupported questions
- Driver speed, distance or availability: FoodFlow has no driver data.
- Delivery duration in minutes: `delivery_time` is a clock time, not a duration.
- Ratings: not in the dataset.
- Any request to insert, update, delete or drop data: the assistant is read-only.

## Ambiguous questions
- "Best restaurant": asks whether best means revenue or order count.
- A month without a year: asks which year.

## Response format
`status` (ok, unsupported, clarify, blocked, error), `answer`, `sql`, `columns`, `rows`, `warning`.

## Secrets
Database passwords and any API key live in `.env`, which is never committed.