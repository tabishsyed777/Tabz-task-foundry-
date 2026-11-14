# Task design and data acceptance guide

TaskFoundry is intended for the conversion of supplied code and domain data into an evaluable repair environment. A source is suitable only when a reviewer can answer each question below.

## Minimum intake record

| Question | Required answer |
|---|---|
| What action is being scored? | A stable, observable contract such as `transform(data) -> JSON`. |
| What makes a run correct? | Independently reviewed expected outputs and invariants. |
| What is the data status? | License, retention, privacy classification, and permission to create fixtures. |
| What is held out? | Cases, dimensions, entities, time ranges, or bug families unavailable to the agent. |
| What should fail? | Known broken implementations and shortcut attempts. |
| How is it reproduced? | Versioned source manifest, seed, container image, evaluator version, and command. |

The structural intake command is useful for inventory, but it never turns data into a task automatically. It does not decide whether data is safe, licensed, representative, or semantically labeled.

## Split and leakage policy

For repair tasks, random fixture splits are usually weak: a near-duplicate record can reveal the expected behavior. Prefer splits that hold out a meaningful unit such as a bug family, data source, customer, schema version, or time period. Document the unit and any exceptions.

The included catalog uses family-level splits. Its source, reference implementations, and fixtures are public for auditability, so it is a **development catalog**, not a confidential benchmark or a valid estimate of performance on unknown proprietary tasks.

## Verifier threat model

A verifier must score behavior rather than a message or a mutable test file. TaskFoundry keeps expected outputs outside the submitted candidate process, runs multiple hidden fixtures, canonicalizes JSON, bounds CPU/wall time/output, and records malformed or failed executions distinctly.

This resists common low-effort shortcuts such as returning a fixed visible answer, printing a success phrase, modifying a local test, or relying on network access. It does not claim resistance to a malicious container escape, host compromise, test-set contamination, or semantic errors in a supplied oracle. High-stakes use needs isolated infrastructure, independent review, and adversarial test generation.
