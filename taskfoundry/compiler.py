import ast
import hashlib
import json
from pathlib import Path
import re


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def safe_path(root,relative):
    root=Path(root).resolve();raw=Path(relative)
    if raw.is_absolute() or '..' in raw.parts:raise ValueError('source paths must be relative and stay inside the source repository')
    path=root/raw
    if any(part.is_symlink() for part in [path,*path.parents] if part!=root and root in part.parents):raise ValueError('symlink source paths are not allowed')
    if not path.is_file() or root not in path.resolve().parents:raise ValueError(f'invalid source file: {relative}')
    if path.stat().st_size>2*1024*1024:raise ValueError('source file exceeds 2 MiB')
    return path


def compile_task(source,blueprint,output):
    source=Path(source);blueprint=Path(blueprint)
    spec=json.loads(blueprint.read_text())
    required=('id','family','split','title','contract','difficulty','license','provenance','candidate','reference','cases')
    if any(not spec.get(k) for k in required):raise ValueError('blueprint is missing required task or provenance fields')
    if not re.fullmatch('[a-z0-9][a-z0-9-]{0,79}',spec['id']):raise ValueError('invalid task id')
    if spec['split'] not in ('train','validation','test'):raise ValueError('invalid split')
    candidate=safe_path(source,spec['candidate']);reference=safe_path(source,spec['reference']);casefile=safe_path(source,spec['cases'])
    for file in (candidate,reference):
        tree=ast.parse(file.read_text())
        if not any(isinstance(n,ast.FunctionDef) and n.name=='transform' for n in tree.body):raise ValueError('source must define transform(data)')
    cases=json.loads(casefile.read_text())
    if not isinstance(cases,list) or not cases:raise ValueError('nonempty cases required')
    seen=set()
    for case in cases:
        if not all(k in case for k in ('id','visibility','input','expected')):raise ValueError('invalid case fields')
        if case['id'] in seen or case['visibility'] not in ('visible','heldout'):raise ValueError('invalid case id or visibility')
        seen.add(case['id']);json.dumps(case,allow_nan=False)
    if {c['visibility'] for c in cases}!={'visible','heldout'}:raise ValueError('visible and heldout cases are both required')
    out=Path(output)
    if out.exists():raise FileExistsError(out)
    (out/'workspace').mkdir(parents=True);(out/'oracle').mkdir()
    (out/'workspace/pipeline.py').write_bytes(candidate.read_bytes())
    (out/'oracle/reference.py').write_bytes(reference.read_bytes())
    (out/'oracle/cases.json').write_text(json.dumps(cases,indent=2)+'\n')
    (out/'workspace/examples.json').write_text(json.dumps([c for c in cases if c['visibility']=='visible'],indent=2)+'\n')
    instruction=f"# {spec['title']}\n\nRepair `/app/pipeline.py`. Implement `transform(data)` using the Python standard library.\n\n{spec['contract']}\n\nReturn JSON-serializable data with exactly the documented types and ordering. Examples are in `/app/examples.json`. Do not read external files or use the network; evaluation supplies inputs directly. Evaluation includes additional cases. Only pipeline.py is submitted.\n"
    (out/'instruction.md').write_text(instruction)
    metadata={k:spec[k] for k in ('id','family','split','title','contract','difficulty','license','provenance')}
    metadata.update(schema_version='1.0',source_files={spec[k]:sha(safe_path(source,spec[k])) for k in ('candidate','reference','cases')},visible_cases=sum(c['visibility']=='visible' for c in cases),heldout_cases=sum(c['visibility']=='heldout' for c in cases))
    (out/'task.json').write_text(json.dumps(metadata,indent=2)+'\n')
    return metadata


def build_catalog(output,source_output):
    from .catalog import SPECS,SPLITS,fixtures
    source=Path(source_output)
    if Path(output).exists():raise FileExistsError('catalog output already exists')
    generate_source=not source.exists()
    if generate_source:
        for name in ('pipelines','reference','data','blueprints'):(source/name).mkdir(parents=True,exist_ok=True)
    manifests=[]
    for spec in SPECS:
        bp=source/f'blueprints/{spec.slug}.json'
        if generate_source:
            (source/f'pipelines/{spec.slug}.py').write_text(spec.broken)
            (source/f'reference/{spec.slug}.py').write_text(spec.source)
            (source/f'data/{spec.slug}.json').write_text(json.dumps(fixtures(spec),indent=2)+'\n')
            blueprint=dict(id=spec.slug,family=spec.family,split=SPLITS[spec.family],title=spec.title,contract=spec.contract,difficulty=spec.difficulty,
                           license='MIT',provenance='TaskFoundry authored synthetic pipeline and fixtures; no customer data or third-party repository extracted.',
                           candidate=f'pipelines/{spec.slug}.py',reference=f'reference/{spec.slug}.py',cases=f'data/{spec.slug}.json')
            bp.write_text(json.dumps(blueprint,indent=2)+'\n')
        manifests.append(compile_task(source,bp,Path(output)/spec.slug))
    (Path(output)/'catalog.json').write_text(json.dumps(dict(schema_version='1.0',tasks=manifests),indent=2)+'\n')
    return manifests
