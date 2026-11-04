"""Review-only gallery for multi-page public-document development questions."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
qs=json.loads((ROOT/'questions_manifest.json').read_text())['questions']
truth={t['id']:t for t in json.loads((ROOT/'private/ground_truth.json').read_text())}
sources={s['source_id']:s for s in json.loads((ROOT/'source_manifest.json').read_text())}
records=[]
for q in qs:
    t=truth[q['id']];rp=ROOT/'runs'/q['id']/'result.json'
    records.append({'question':q,'truth':t,'prompt':(ROOT/q['directory']/'prompt.txt').read_text(),
                    'result':json.loads(rp.read_text()) if rp.exists() else None})
payload=json.dumps(records,ensure_ascii=False).replace('</','<\/')
html='''<!doctype html><html lang="zh"><meta charset="utf-8"><title>公开财务文档：难度升级10题</title>
<style>body{font:16px/1.6 system-ui;margin:20px auto;max-width:1850px;padding:0 20px;background:#f3f5f8;color:#14202a}header,section{background:white;padding:20px;margin:16px 0;border-radius:10px}button,select{font:inherit;padding:8px;cursor:pointer}button{margin:4px}.pages{display:grid;grid-template-columns:repeat(auto-fit,minmax(350px,1fr));gap:14px}.canvas{position:relative}.canvas img{display:block;width:100%;border:1px solid #ddd}.box{position:absolute;border:2px solid #dc3434;box-sizing:border-box;pointer-events:none;display:none}body.boxes .box{display:block}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f1f4f7;padding:12px}td,th{padding:7px;border-bottom:1px solid #ddd;text-align:left}table{border-collapse:collapse;width:100%}.notice{padding:12px;background:#fff0c9}a{color:#175db7}</style>
<header><h1>公开财务文档：难度升级10题</h1><p>跨页一致性、7–11处差异枚举、正负号、小数、单位及年度标签；包含官方重述和页序变化的正常对照。</p><p class="notice">此页是含答案的审阅页，不属于模型输入。图像长边仍为1800像素，点击图片可打开原分辨率。每题冻结后仅尝试一次，无工具探索。H02与H03共用同一修改版本，全部题来自同一公开发布方，不是独立正式测试集。</p><select id="pick"></select><button id="prev">上一题</button><button id="next">下一题</button><button id="boxes">切换修改框</button></header>
<section><h2 id="title"></h2><p id="pattern"></p><details><summary>题面及附件顺序</summary><pre id="prompt"></pre></details><div class="pages" id="pages"></div></section>
<section><details><summary>查看构造真值</summary><p id="relations"></p><table><thead><tr><th>页及字段</th><th>A值</th><th>B值</th></tr></thead><tbody id="truth"></tbody></table></details></section>
<section><h2>Luna实际回答</h2><p id="status"></p><pre id="answer"></pre></section>
<script>const records=PAYLOAD;const esc=x=>String(x??'').replace(/[&<>\"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[c]));const pick=document.querySelector('#pick');records.forEach((r,i)=>{const o=document.createElement('option');o.value=i;o.textContent=r.question.id+' · '+r.question.kind;pick.append(o)});
function show(){const r=records[Number(pick.value)],q=r.question,t=r.truth;document.querySelector('#title').textContent=q.id+' · '+(q.kind==='single'?'多页内部核查':'多页双版本对比');document.querySelector('#pattern').textContent=t.pattern;document.querySelector('#prompt').textContent=r.prompt;
document.querySelector('#pages').innerHTML=q.images.map((im,i)=>{const side=im.version==='A'?'a':'b',index=im.version_page;const ids=side==='a'?t.pages:t.b_order,pid=ids[index-1];const boxes=t.expected_changes.filter(c=>c.page_id===pid).map(c=>{const b=c['bbox_'+side];return '<span class="box" style="left:'+b[0]*100+'%;top:'+b[1]*100+'%;width:'+(b[2]-b[0])*100+'%;height:'+(b[3]-b[1])*100+'%"></span>'}).join('');return '<div><h3>附件'+(i+1)+' · '+im.version+index+' · '+pid+'</h3><div class="canvas"><a href="'+esc(im.path)+'" target="_blank"><img src="'+esc(im.path)+'" alt="'+q.id+' '+im.version+index+'"></a>'+boxes+'</div></div>'}).join('');
document.querySelector('#relations').textContent=t.expected_relations.join('；');document.querySelector('#truth').innerHTML=t.expected_changes.length?t.expected_changes.map(c=>'<tr><td>'+esc(c.page_id+' / '+c.label)+'</td><td>'+esc(c.before)+'</td><td>'+esc(c.after)+'</td></tr>').join(''):'<tr><td colspan="3">没有引入业务内容修改；正常重述、页序或编码变化不计为篡改。</td></tr>';document.querySelector('#status').textContent=r.result?r.result.status+' · '+r.result.model+' · 工具事件'+r.result.tool_events.length:'尚无运行结果';document.querySelector('#answer').textContent=r.result?JSON.stringify(r.result.answer,null,2):'等待结果';document.body.classList.remove('boxes');}
pick.onchange=show;document.querySelector('#prev').onclick=()=>{pick.value=(Number(pick.value)+records.length-1)%records.length;show()};document.querySelector('#next').onclick=()=>{pick.value=(Number(pick.value)+1)%records.length;show()};document.querySelector('#boxes').onclick=()=>document.body.classList.toggle('boxes');show();</script></html>'''.replace('PAYLOAD',payload)
(ROOT/'report.html').write_text(html)
print('Review updated:',len(records),'questions;',sum(r['result'] is not None for r in records),'results')
