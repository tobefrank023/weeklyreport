"""Static, self-contained review UI; solver inputs do not include this file."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
questions = json.loads((ROOT/'questions_manifest.json').read_text())['questions']
truth = {x['id']: x for x in json.loads((ROOT/'private/ground_truth.json').read_text())}
sources = {x['source_id']: x for x in json.loads((ROOT/'source_manifest.json').read_text())}
records = []
for q in questions:
    t = truth[q['id']]
    rpath = ROOT/'runs'/q['id']/'result.json'
    records.append({'question': q, 'truth': t, 'source': sources[t['source_id']],
                    'prompt': (ROOT/q['directory']/'prompt.txt').read_text(),
                    'result': json.loads(rpath.read_text()) if rpath.exists() else None})
payload = json.dumps(records,ensure_ascii=False).replace('</','<\/')
page = '''<!doctype html><html lang="zh"><meta charset="utf-8"><title>公开财务文档：10题小样</title>
<style>body{font:16px/1.6 system-ui;margin:24px auto;max-width:1440px;padding:0 20px;background:#f5f7fa;color:#17202a}header,section{background:white;padding:20px;margin:16px 0;border-radius:10px}button,select{font:inherit;padding:7px 12px;cursor:pointer}button{margin-right:8px}.pages{display:flex;gap:16px;align-items:flex-start}.frame{flex:1;min-width:0}.canvas{position:relative}.canvas img{display:block;width:100%}.box{position:absolute;border:2px solid #e53b3b;box-sizing:border-box;pointer-events:none;display:none}body.boxes .box{display:block}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f1f4f8;padding:14px}table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid #ddd;padding:7px;text-align:left}.notice{background:#fff0c9;padding:12px}a{color:#175ec9}@media(max-width:800px){.pages{display:block}}</style>
<header><h1>公开财务文档：10题造题与盲答小样</h1><p>两份美国财政部公开财务报表，四个基础页面。5道单页题、5道双版本题。所有修改件均为研究构造，不代表官方发布内容。</p><p class="notice">此页供审阅，包含可展开的答案。模型的业务材料输入仅含题面和整页图片，没有答案、字段框、OCR或原始PDF。题目之间存在同源页面，不构成独立测试集。</p><select id="pick"></select> <button id="prev">上一题</button><button id="next">下一题</button><button id="boxes">切换答案框</button></header>
<section><h2 id="title"></h2><p id="provenance"></p><details><summary>题面</summary><pre id="prompt"></pre></details><div class="pages" id="pages"></div></section>
<section><details><summary>查看修改真值与数值核验</summary><p id="pattern"></p><table><thead><tr><th>字段及列标识</th><th>参照值</th><th>修改值</th></tr></thead><tbody id="truth"></tbody></table><pre id="math"></pre></details></section>
<section><h2>Luna实际回答</h2><p id="status"></p><pre id="answer"></pre></section>
<script>const records=PAYLOAD;const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pick=document.querySelector('#pick');records.forEach((r,i)=>{const o=document.createElement('option');o.value=i;o.textContent=r.question.id+' · '+r.question.kind;pick.append(o)});
function show(){const r=records[Number(pick.value)],q=r.question,t=r.truth;document.querySelector('#title').textContent=q.id+' · '+(q.kind==='single'?'单页内部核查':'双版本内容对比');document.querySelector('#provenance').innerHTML='来源：<a target="_blank" href="'+esc(r.source.url)+'">'+esc(t.source_id)+'</a>；PDF物理第'+t.physical_page+'页，印刷页码'+t.printed_page+'。';document.querySelector('#prompt').textContent=r.prompt;
document.querySelector('#pages').innerHTML=q.images.map((im,i)=>{const side=q.kind==='paired'?(i===0?'a':'b'):'b';let boxes=t.expected_changes.map(c=>{const b=c['bbox_'+side];return '<span class="box" style="left:'+b[0]*100+'%;top:'+b[1]*100+'%;width:'+(b[2]-b[0])*100+'%;height:'+(b[3]-b[1])*100+'%"></span>'}).join('');return '<div class="frame"><h3>'+ (q.kind==='paired'?(i===0?'版本A':'版本B'):'题目唯一附件')+'</h3><div class="canvas"><img src="'+esc(im.path)+'" alt="'+q.id+'整页输入">'+boxes+'</div></div>'}).join('');
document.querySelector('#pattern').textContent=t.pattern+'；本题引入业务字段修改：'+t.introduced_content_edit;document.querySelector('#truth').innerHTML=t.expected_changes.length?t.expected_changes.map(c=>'<tr><td>'+esc(c.label+' / '+c.id)+'</td><td>'+esc(c.before)+'</td><td>'+esc(c.after)+'</td></tr>').join(''):'<tr><td colspan="3">没有引入业务字段变化。</td></tr>';document.querySelector('#math').textContent=JSON.stringify(t.arithmetic_check,null,2);document.querySelector('#status').textContent=r.result?('状态：'+r.result.status+'；模型：'+r.result.model+'；工具事件：'+r.result.tool_events.length):'尚无运行结果';document.querySelector('#answer').textContent=r.result?JSON.stringify(r.result.answer,null,2):'等待结果';document.body.classList.remove('boxes');}
pick.onchange=show;document.querySelector('#prev').onclick=()=>{pick.value=(Number(pick.value)+records.length-1)%records.length;show()};document.querySelector('#next').onclick=()=>{pick.value=(Number(pick.value)+1)%records.length;show()};document.querySelector('#boxes').onclick=()=>document.body.classList.toggle('boxes');show();</script></html>'''.replace('PAYLOAD',payload)
(ROOT/'report.html').write_text(page)
print('Review page updated:',len(records),'questions;',sum(r['result'] is not None for r in records),'results')
