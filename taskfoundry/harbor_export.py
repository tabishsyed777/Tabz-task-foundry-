"""Harbor 0.26.0 task format, schema 1.4, separate verifier containers."""
import json
from pathlib import Path
import shutil
from .execution import BASE_IMAGE

HARBOR_VERSION='0.26.0'
HARBOR_COMMIT='3cb627394b95d3ae605f31e0d694edf508cf4b7b'

VERIFY_SCRIPT='''import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
sys.path.insert(0, '/tests')
from execution import bounded_run, compare

logs=Path('/logs/verifier');logs.mkdir(parents=True,exist_ok=True);logs.chmod(0o700)
(logs/'reward.txt').write_text('0\\n')
try:
    source=Path('/app/pipeline.py')
    if source.is_symlink() or not source.is_file() or source.stat().st_size>262144:
        raise ValueError('invalid candidate artifact')
    cases=json.loads(Path('/tests/cases.json').read_text())
    with tempfile.TemporaryDirectory(prefix='candidate-') as tmp:
        root=Path(tmp);root.chmod(0o755)
        candidate=root/'pipeline.py';candidate.write_bytes(source.read_bytes());candidate.chmod(0o644)
        result=bounded_run([sys.executable,'-I','/runner.py',str(candidate)], [c['input'] for c in cases], 8, cwd=tmp,drop_uid=True,isolate=True)
        verdict=compare(result,cases)
except Exception as exc:
    verdict=dict(passed=False,error=type(exc).__name__)
(logs/'verdict.json').write_text(json.dumps(verdict,indent=2))
(logs/'reward.txt').write_text('1\\n' if verdict['passed'] else '0\\n')
'''


def export_task(task,output):
    task=Path(task);out=Path(output)
    if out.exists():raise FileExistsError(out)
    meta=json.loads((task/'task.json').read_text())
    for name in ('environment','solution','tests'):(out/name).mkdir(parents=True,exist_ok=True)
    shutil.copy2(task/'instruction.md',out/'instruction.md')
    for name in ('pipeline.py','examples.json'):shutil.copy2(task/'workspace'/name,out/'environment'/name)
    (out/'environment/Dockerfile').write_text(f'FROM {BASE_IMAGE}\nWORKDIR /app\nCOPY --chmod=644 pipeline.py examples.json /app/\n')
    shutil.copy2(task/'oracle/reference.py',out/'solution/pipeline.py')
    (out/'solution/solve.sh').write_text('#!/bin/bash\nset -eu\ncp /solution/pipeline.py /app/pipeline.py\n')
    shutil.copy2(task/'oracle/cases.json',out/'tests/cases.json')
    shutil.copy2(Path(__file__).with_name('execution.py'),out/'tests/execution.py')
    shutil.copy2(Path(__file__).with_name('runner.py'),out/'tests/runner.py')
    (out/'tests/verify.py').write_text(VERIFY_SCRIPT)
    (out/'tests/test.sh').write_text('#!/bin/bash\nset -eu\npython /tests/verify.py\n')
    (out/'tests/Dockerfile').write_text(f'FROM {BASE_IMAGE}\nCOPY . /tests/\nCOPY --chmod=644 runner.py /runner.py\nRUN chmod 700 /tests && chmod 600 /tests/* && chmod 700 /tests/test.sh\nWORKDIR /tmp\n')
    quote=lambda x:json.dumps(x)
    (out/'task.toml').write_text(f'''schema_version = "1.4"
artifacts = ["/app/pipeline.py"]

[task]
name = "tabishsyed777/{meta['id']}"
version = "0.1.0"
description = {quote(meta['title'])}
authors = [{{name = "Tabish Syed"}}]
keywords = ["python", "data-pipeline", "{meta['family']}"]

[metadata]
difficulty = "{meta['difficulty']}"
category = "data-processing"
family = "{meta['family']}"
split = "{meta['split']}"
source = "TaskFoundry synthetic catalog"

[agent]
timeout_sec = 120

[verifier]
timeout_sec = 30
environment_mode = "separate"
user = "root"

[verifier.environment]
# Harbor's local Docker provider in v0.26.0 does not enforce no-network.
# The direct TaskFoundry runner uses --network none; hosted providers may
# enforce this policy after changing it to no-network.
network_mode = "public"
build_timeout_sec = 300
cpus = 1
memory_mb = 512
storage_mb = 256

[environment]
network_mode = "public"
build_timeout_sec = 300
cpus = 1
memory_mb = 512
storage_mb = 256
''')
    return meta['id']


def export_catalog(catalog,output):
    catalog=Path(catalog);out=Path(output)
    if out.exists():raise FileExistsError(out)
    out.mkdir(parents=True)
    manifest=json.loads((catalog/'catalog.json').read_text())
    for meta in manifest['tasks']:export_task(catalog/meta['id'],out/meta['id'])
    return dict(tasks=len(manifest['tasks']),harbor_version=HARBOR_VERSION,harbor_commit=HARBOR_COMMIT,schema_version='1.4')
