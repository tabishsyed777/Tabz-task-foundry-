# Reproducibility record

Build date: 2026-11-14.

## Pinned components

| Component | Value |
|---|---|
| TaskFoundry | 0.1.0 |
| Python package runtime | 3.11+ |
| Direct evaluator image | `python:3.11-slim@sha256:07d4824036af339fa1b6ef769cc99d9c10a141769538b52b3b597c84f7a7b535` |
| Harbor package | 0.26.0 |
| Harbor source commit | `3cb627394b95d3ae605f31e0d694edf508cf4b7b` |
| Harbor task schema | 1.4 |

## Commands recorded

```bash
taskfoundry build-catalog
taskfoundry validate --engine process --repeat 2 --workers 4 --output artifacts/validation-process.json
taskfoundry build-image
taskfoundry validate --engine docker --repeat 1 --workers 1 --output artifacts/validation-docker.json
taskfoundry export-harbor
harbor run --agent oracle --path exports/harbor/latest-record --jobs-dir runs/harbor --n-concurrent 1 --yes
```

The process repeat run accepted 48 reference executions and rejected 48 broken starter executions with deterministic verdicts. The Docker run accepted 24 references and rejected 24 starters. The Harbor run tested one exported task with the built-in oracle agent and separate verification.

## Direct Docker guardrails

The direct runner uses a pinned image, non-root UID 65534, `--network none`, read-only root filesystem, `/tmp` tmpfs of 16 MiB, `--cap-drop ALL`, `no-new-privileges`, 256 MiB memory, one CPU, 32 process IDs, a CPU ulimit of three seconds, a 256 KiB submitted-file limit, 128 KiB output limit, and an eight-second wall-clock limit. These are resource and isolation controls, not proof of security against container escape.

## Harbor compatibility note

The local Docker provider in Harbor 0.26.0 rejects no-network tasks because it cannot enforce that policy. The generated Harbor task metadata uses public networking for local compatibility, while direct TaskFoundry validation uses Docker's enforced no-network mode. The Harbor run is a format and separate-verifier compatibility check, not evidence that its local provider isolated network access.
