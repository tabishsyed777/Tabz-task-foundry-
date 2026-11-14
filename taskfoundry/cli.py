import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
from .compiler import build_catalog,compile_task
from .execution import evaluate,build_image
from .intake import inspect_source
from .harbor_export import export_catalog


def write(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,indent=2)+'\n')


def validate(catalog,output,engine='docker',repeat=2,workers=2):
    catalog=Path(catalog);manifest=json.loads((catalog/'catalog.json').read_text())
    jobs=[(meta,variant,iteration) for meta in manifest['tasks'] for variant in ('broken','reference') for iteration in range(repeat)]
    def run(job):
        meta,variant,iteration=job;task=catalog/meta['id'];source=task/('workspace/pipeline.py' if variant=='broken' else 'oracle/reference.py')
        result=evaluate(source,json.loads((task/'oracle/cases.json').read_text()),engine)
        return dict(task=meta['id'],family=meta['family'],split=meta['split'],variant=variant,repeat=iteration,**result)
    with ThreadPoolExecutor(max_workers=workers) as executor:records=list(executor.map(run,jobs))
    correct=all(row['passed']==(row['variant']=='reference') for row in records)
    grouped={}
    for row in records:grouped.setdefault((row['task'],row['variant']),set()).add(json.dumps({k:v for k,v in row.items() if k not in ('repeat','details')},sort_keys=True))
    deterministic=all(len(v)==1 for v in grouped.values())
    report=dict(engine=engine,tasks=len(manifest['tasks']),repeat=repeat,runs=len(records),reference_passed=sum(r['passed'] for r in records if r['variant']=='reference'),broken_rejected=sum(not r['passed'] for r in records if r['variant']=='broken'),all_expected_outcomes=correct,deterministic=deterministic,records=records)
    write(output,report)
    return report


def main():
    p=argparse.ArgumentParser(description='TaskFoundry: compile reproducible data-pipeline repair tasks')
    sub=p.add_subparsers(dest='command',required=True)
    b=sub.add_parser('build-catalog');b.add_argument('--output',default='catalog');b.add_argument('--source-output',default='examples/pipeline-repo')
    b.set_defaults(fn=lambda a:dict(tasks=len(build_catalog(a.output,a.source_output))))
    i=sub.add_parser('inspect');i.add_argument('source');i.add_argument('--output',default='runs/intake.json')
    def inspect(a):result=inspect_source(a.source);write(a.output,result);return result
    i.set_defaults(fn=inspect)
    c=sub.add_parser('compile');c.add_argument('--source',required=True);c.add_argument('--blueprint',required=True);c.add_argument('--output',required=True);c.set_defaults(fn=lambda a:compile_task(a.source,a.blueprint,a.output))
    d=sub.add_parser('build-image');d.set_defaults(fn=lambda a:build_image())
    v=sub.add_parser('validate');v.add_argument('--catalog',default='catalog');v.add_argument('--output',default='runs/validation.json');v.add_argument('--engine',choices=['docker','process'],default='docker');v.add_argument('--repeat',type=int,default=2);v.add_argument('--workers',type=int,default=2)
    v.set_defaults(fn=lambda a:validate(a.catalog,a.output,a.engine,a.repeat,a.workers))
    g=sub.add_parser('grade');g.add_argument('--task',required=True);g.add_argument('--candidate',required=True);g.add_argument('--engine',choices=['docker','process'],default='docker');g.add_argument('--output',default='runs/grade.json')
    def grade(a):result=evaluate(a.candidate,json.loads((Path(a.task)/'oracle/cases.json').read_text()),a.engine);write(a.output,result);return result
    g.set_defaults(fn=grade)
    e=sub.add_parser('export-harbor');e.add_argument('--catalog',default='catalog');e.add_argument('--output',default='exports/harbor');e.set_defaults(fn=lambda a:export_catalog(a.catalog,a.output))
    w=sub.add_parser('browser');w.add_argument('--catalog',default='catalog');w.add_argument('--validation',default='artifacts/validation-docker.json');w.add_argument('--output',default='artifacts/browser.html')
    def browser(a):
        from .browser import render
        render(a.catalog,a.validation,a.output);return dict(browser=a.output)
    w.set_defaults(fn=browser)
    a=p.parse_args()
    if getattr(a,'repeat',1)<1 or not 1<=getattr(a,'workers',1)<=8:p.error('repeat must be positive; workers must be between 1 and 8')
    try:
        result=a.fn(a)
        if isinstance(result,dict):print(json.dumps({k:v for k,v in result.items() if k!='records'},indent=2))
        if a.command=='validate' and not (result['all_expected_outcomes'] and result['deterministic']):p.exit(1)
        if a.command=='grade' and not result['passed']:p.exit(1)
    except (ValueError,FileNotFoundError,FileExistsError,SyntaxError) as exc:p.exit(2,f'Error: {exc}\n')

if __name__=='__main__':main()
