"""Static, data-only catalog browser for local inspection."""
import html
import json
from pathlib import Path


def render(catalog, validation, output):
    catalog = Path(catalog)
    manifest = json.loads((catalog / "catalog.json").read_text())
    report = json.loads(Path(validation).read_text())
    stats = {}
    for record in report["records"]:
        stat = stats.setdefault(record["task"], {"reference": [], "broken": []})
        stat[record["variant"]].append(record["passed"])
    rows = []
    for task in manifest["tasks"]:
        check = stats.get(task["id"], {})
        reference_ok = all(check.get("reference", []))
        broken_rejected = all(not value for value in check.get("broken", []))
        rows.append({**task, "reference_ok": reference_ok, "broken_rejected": broken_rejected})
    payload = json.dumps(rows).replace("<", "\\u003c")
    page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TaskFoundry catalog</title>
<style>body{margin:0;background:#0b1120;color:#e5edf7;font:16px system-ui}main{max-width:1100px;margin:auto;padding:42px 24px}small{color:#9cb3cd;letter-spacing:.08em}h1{font-size:42px;margin:8px 0}p{line-height:1.55;color:#b9c9dc}.controls{display:flex;gap:12px;flex-wrap:wrap;margin:26px 0}input,select{padding:10px;border:1px solid #53647a;border-radius:8px;background:#15243a;color:#fff}article{background:#101d30;border:1px solid #34445b;border-radius:12px;padding:17px;margin:12px 0}h2{margin:0 0 6px;font-size:20px}.tag{font-size:12px;border:1px solid #53647a;border-radius:999px;padding:3px 8px;margin-right:5px;color:#b9d8f4}.ok{color:#75e6b3}.bad{color:#ffb2a3}code{color:#b9d8f4}</style>
<main><small>DATA-PIPELINE REPAIR TASKS · TABISH SYED</small><h1>TaskFoundry catalog</h1><p id="summary"></p><div class="controls"><input id="q" placeholder="Search tasks"><select id="split"><option value="">All splits</option><option>train</option><option>validation</option><option>test</option></select><select id="family"><option value="">All families</option></select></div><section id="tasks"></section></main>
<script>const tasks=DATA,section=document.querySelector('#tasks'),q=document.querySelector('#q'),split=document.querySelector('#split'),family=document.querySelector('#family');for(const value of [...new Set(tasks.map(t=>t.family))])family.add(new Option(value,value));function draw(){const term=q.value.toLowerCase();const shown=tasks.filter(t=>(!split.value||t.split===split.value)&&(!family.value||t.family===family.value)&&JSON.stringify(t).toLowerCase().includes(term));document.querySelector('#summary').textContent=`${shown.length} of ${tasks.length} tasks shown. Every task has visible and held-out cases; evaluator results are recorded separately.`;section.replaceChildren(...shown.map(t=>{const a=document.createElement('article');a.innerHTML=`<h2>${t.title}</h2><p><span class="tag">${t.family}</span><span class="tag">${t.split}</span><span class="tag">${t.difficulty}</span></p><p>${t.contract}</p><p class="${t.reference_ok&&t.broken_rejected?'ok':'bad'}">Reference passes: ${t.reference_ok} · Broken starter rejected: ${t.broken_rejected}</p><small><code>${t.id}</code> · ${t.visible_cases} visible / ${t.heldout_cases} held-out cases</small>`;return a}))}for(const el of [q,split,family])el.addEventListener('input',draw);draw();</script></html>'''
    Path(output).write_text(page.replace("DATA", payload))
