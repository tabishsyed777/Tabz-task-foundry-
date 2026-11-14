"""Bounded candidate execution and evaluator-owned comparisons."""
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import tempfile
import time
import uuid

BASE_IMAGE='python:3.11-slim@sha256:07d4824036af339fa1b6ef769cc99d9c10a141769538b52b3b597c84f7a7b535'
IMAGE='taskfoundry-runner:0.1.0'
OUTPUT_LIMIT=131072


def bounded_run(command, payload, timeout, *, cwd=None, drop_uid=False, isolate=False):
    with tempfile.TemporaryFile() as incoming:
        incoming.write(json.dumps(payload,allow_nan=False).encode());incoming.seek(0)
        if drop_uid: command=[*command[:-1],"--drop-uid",command[-1]]
        proc=subprocess.Popen(command,stdin=incoming,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
            cwd=cwd,start_new_session=True,
            env=dict(PATH='/usr/local/bin:/usr/bin:/bin',PYTHONHASHSEED='0',PYTHONDONTWRITEBYTECODE='1'))
        output=bytearray();deadline=time.monotonic()+timeout
        selector=selectors.DefaultSelector();selector.register(proc.stdout,selectors.EVENT_READ)
        reason=None
        try:
            while True:
                remaining=deadline-time.monotonic()
                if remaining<=0:reason='timeout';break
                ready=selector.select(min(remaining,.1))
                if not ready:continue
                chunk=os.read(proc.stdout.fileno(),8192)
                if not chunk:break
                output.extend(chunk)
                if len(output)>OUTPUT_LIMIT:reason='output_limit';break
            if reason:
                os.killpg(proc.pid,signal.SIGKILL)
            try:proc.wait(timeout=max(.1,deadline-time.monotonic()))
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid,signal.SIGKILL);proc.wait();reason='timeout'
        finally:
            selector.close();proc.stdout.close()
            if proc.poll() is None:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
        return dict(returncode=proc.returncode,output=bytes(output[:OUTPUT_LIMIT]).decode('utf-8',errors='replace'),error=reason)


def compare(result,cases):
    if result['error'] or result['returncode']!=0:
        return dict(passed=False,passed_cases=0,total_cases=len(cases),error=result['error'] or 'candidate_error',details=result['output'][-1500:])
    try:
        outputs=json.loads(result['output'],parse_constant=lambda x: (_ for _ in ()).throw(ValueError('nonfinite number')))
        if not isinstance(outputs,list) or len(outputs)!=len(cases):raise ValueError('incorrect result count')
        canonical=lambda value:json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
        matches=[canonical(actual)==canonical(case['expected']) for actual,case in zip(outputs,cases)]
    except (ValueError,TypeError):
        return dict(passed=False,passed_cases=0,total_cases=len(cases),error='invalid_output')
    return dict(passed=all(matches),passed_cases=sum(matches),total_cases=len(cases),error=None,
                cases=[dict(id=c['id'],visibility=c['visibility'],passed=m) for c,m in zip(cases,matches)])


def build_image():
    runner=Path(__file__).with_name('runner.py')
    with tempfile.TemporaryDirectory(prefix='taskfoundry-build-') as tmp:
        root=Path(tmp)
        (root/'runner.py').write_bytes(runner.read_bytes())
        (root/'Dockerfile').write_text(f'FROM {BASE_IMAGE}\nCOPY --chmod=644 runner.py /runner.py\nUSER 65534:65534\nENTRYPOINT ["python", "-I", "/runner.py", "/candidate.py"]\n')
        subprocess.run(['docker','build','-t',IMAGE,str(root)],check=True,timeout=300)


def evaluate(candidate,cases,engine='docker',timeout=8):
    candidate=Path(candidate)
    if candidate.is_symlink() or not candidate.is_file() or candidate.stat().st_size>262144:
        raise ValueError('candidate must be a regular non-symlink Python file under 256 KiB')
    runner=Path(__file__).with_name('runner.py')
    payload=[c['input'] for c in cases]
    if engine=='process':
        with tempfile.TemporaryDirectory(prefix='taskfoundry-candidate-') as tmp:
            source=Path(tmp)/'pipeline.py';source.write_bytes(candidate.read_bytes())
            result=bounded_run([sys.executable,'-I',str(runner),str(source)],payload,timeout,cwd=tmp,isolate=True)
    elif engine=='docker':
        name='taskfoundry-'+uuid.uuid4().hex
        with tempfile.TemporaryDirectory(prefix='taskfoundry-candidate-') as tmp:
            # Docker evaluates the bind mount as UID 65534.  The temporary
            # directory therefore needs traversal permission; the candidate is
            # still mounted read-only and the container has no host directory
            # mount besides that one file.
            Path(tmp).chmod(0o755)
            source=Path(tmp)/'pipeline.py';source.write_bytes(candidate.read_bytes());source.chmod(0o644)
            command=['docker','run','--rm','-i','--name',name,'--network','none','--read-only','--tmpfs','/tmp:rw,nosuid,size=16m',
                     '--cap-drop','ALL','--security-opt','no-new-privileges','--memory','256m','--cpus','1','--pids-limit','32',
                     '--ulimit','cpu=3:3','--mount',f'type=bind,source={source},target=/candidate.py,readonly',IMAGE]
            # The image already uses UID/GID 65534.  Asking the process to drop
            # privileges again would fail because it no longer has that right.
            try:result=bounded_run(command,payload,timeout)
            finally:subprocess.run(['docker','rm','-f',name],capture_output=True,timeout=15)
    else:raise ValueError('engine must be docker or process')
    return compare(result,cases)
