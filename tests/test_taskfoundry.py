import json
from pathlib import Path

import pytest

from taskfoundry.catalog import SPECS
from taskfoundry.compiler import build_catalog, compile_task
from taskfoundry.execution import evaluate
from taskfoundry.harbor_export import export_catalog
from taskfoundry.intake import inspect_source


def catalog(tmp_path):
    build_catalog(tmp_path / "catalog", tmp_path / "source")
    return tmp_path / "catalog"


def test_catalog_contains_disjoint_family_splits_and_both_case_visibilities(tmp_path):
    root = catalog(tmp_path)
    manifest = json.loads((root / "catalog.json").read_text())
    assert len(manifest["tasks"]) == 24 == len(SPECS)
    family_split = {task["family"]: task["split"] for task in manifest["tasks"]}
    assert set(family_split.values()) == {"train", "validation", "test"}
    for task in manifest["tasks"]:
        cases = json.loads((root / task["id"] / "oracle" / "cases.json").read_text())
        assert {case["visibility"] for case in cases} == {"visible", "heldout"}


def test_catalog_can_reuse_a_reviewed_source_repository(tmp_path):
    first = catalog(tmp_path)
    source = tmp_path / "source"
    original = (source / "pipelines" / "latest-record.py").read_bytes()
    second = tmp_path / "catalog-rebuilt"
    build_catalog(second, source)
    assert (second / "catalog.json").is_file()
    assert (source / "pipelines" / "latest-record.py").read_bytes() == original


def test_every_reference_passes_and_every_starter_fails_in_process(tmp_path):
    root = catalog(tmp_path)
    for task in json.loads((root / "catalog.json").read_text())["tasks"]:
        path = root / task["id"]
        cases = json.loads((path / "oracle" / "cases.json").read_text())
        assert evaluate(path / "oracle" / "reference.py", cases, "process")["passed"]
        assert not evaluate(path / "workspace" / "pipeline.py", cases, "process")["passed"]


def test_evaluator_rejects_hardcoded_visible_examples_and_bad_output(tmp_path):
    root = catalog(tmp_path)
    task = root / "latest-record"
    cases = json.loads((task / "oracle" / "cases.json").read_text())
    cheat = tmp_path / "cheat.py"
    cheat.write_text("def transform(data):\n    return []\n")
    assert not evaluate(cheat, cases, "process")["passed"]
    malformed = tmp_path / "malformed.py"
    malformed.write_text("def transform(data):\n    return {1, 2}\n")
    assert evaluate(malformed, cases, "process")["error"] == "candidate_error"


def test_evaluator_bounds_timeout_and_output(tmp_path):
    root = catalog(tmp_path)
    cases = json.loads((root / "latest-record" / "oracle" / "cases.json").read_text())
    loop = tmp_path / "loop.py"
    loop.write_text("def transform(data):\n    while True: pass\n")
    assert evaluate(loop, cases, "process", timeout=2)["error"] in {"timeout", "candidate_error"}
    noisy = tmp_path / "noisy.py"
    noisy.write_text("def transform(data):\n    print('x' * 200000)\n    return []\n")
    assert evaluate(noisy, cases, "process")["error"] in {"output_limit", "candidate_error"}


def test_compiler_rejects_escape_and_missing_provenance(tmp_path):
    source = tmp_path / "source"; source.mkdir()
    (source / "candidate.py").write_text("def transform(data): return data\n")
    (source / "reference.py").write_text("def transform(data): return data\n")
    (source / "cases.json").write_text('[{"id":"a","visibility":"visible","input":{},"expected":{}},{"id":"b","visibility":"heldout","input":{},"expected":{}}]')
    blueprint = {"id":"valid-id","family":"x","split":"train","title":"x","contract":"x","difficulty":"easy","license":"MIT","provenance":"synthetic","candidate":"candidate.py","reference":"reference.py","cases":"cases.json"}
    path = source / "task.json"; path.write_text(json.dumps(blueprint))
    assert compile_task(source, path, tmp_path / "out")["id"] == "valid-id"
    blueprint["candidate"] = "../candidate.py"; path.write_text(json.dumps(blueprint))
    with pytest.raises(ValueError): compile_task(source, path, tmp_path / "out2")
    blueprint.pop("provenance"); path.write_text(json.dumps(blueprint))
    with pytest.raises(ValueError): compile_task(source, path, tmp_path / "out3")


def test_intake_does_not_execute_source_and_export_has_separate_verifier(tmp_path):
    source = tmp_path / "input"; source.mkdir()
    marker = tmp_path / "marker"
    (source / "evil.py").write_text(f"open({marker!r}, 'w').write('ran')\ndef transform(data): return data\n")
    report = inspect_source(source)
    assert not marker.exists() and report["candidate_entrypoints"] == ["evil.py"]
    root = catalog(tmp_path)
    export_catalog(root, tmp_path / "harbor")
    task = (tmp_path / "harbor" / "latest-record" / "task.toml").read_text()
    assert 'environment_mode = "separate"' in task and 'network_mode = "public"' in task
    assert (tmp_path / "harbor" / "latest-record" / "tests" / "cases.json").exists()
