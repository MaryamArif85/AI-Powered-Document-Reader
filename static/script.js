const API = ""; // same origin, since FastAPI serves frontend

async function updateHealth(){
  try{
    const r = await fetch(API+"/health");
    const d = await r.json();
    document.getElementById("health").innerHTML = `🟢 ${d.indexed_chunks || 0} chunks indexed`;
  }catch{ document.getElementById("health").innerHTML = "🔴 API offline" }
}
updateHealth();

const drop = document.getElementById("drop");
const fileInput = document.getElementById("fileInput");
drop.onclick = ()=> fileInput.click();
drop.ondragover = e=>{e.preventDefault(); drop.style.borderColor="#7c3aed"};
drop.ondrop = e=>{e.preventDefault(); handleFiles(e.dataTransfer.files)};
fileInput.onchange = ()=> handleFiles(fileInput.files);

async function handleFiles(files){
  if(!files.length) return;
  const fd = new FormData();
  fd.append("file", files[0]);
  document.getElementById("uploadResult").innerHTML = "⏳ Uploading & indexing...";
  try{
    const r = await fetch(API+"/rag/upload", {method:"POST", body:fd});
    const d = await r.json();
    if(!r.ok) throw new Error(d.detail);
    document.getElementById("uploadResult").innerHTML = `✅ <b>${d.filename}</b> indexed: ${d.chunks_indexed} chunks. Total: ${d.total_chunks_in_db}`;
    updateHealth();
  }catch(e){ document.getElementById("uploadResult").innerHTML = "❌ "+e.message }
}

async function ask(){
  const q = document.getElementById("question").value;
  const style = document.getElementById("style").value;
  if(!q.trim()) return alert("Enter question");
  document.getElementById("results").innerHTML = "⏳ Thinking with "+style+"...";
  try{
    const r = await fetch(API+"/rag/query", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({question:q, style, top_k:5})});
    const d = await r.json();
    if(!r.ok) throw new Error(d.detail);
    renderSingle(d);
  }catch(e){ document.getElementById("results").innerHTML = "❌ "+e.message }
}

async function compare(){
  const q = document.getElementById("question").value;
  if(!q.trim()) return alert("Enter question");
  document.getElementById("results").innerHTML = "⏳ Comparing 3 prompting styles...";
  try{
    const r = await fetch(API+"/rag/compare", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({question:q, top_k:5})});
    const d = await r.json();
    if(!r.ok) throw new Error(d.detail);
    renderCompare(d);
  }catch(e){ document.getElementById("results").innerHTML = "❌ "+e.message }
}

function renderSingle(d){
  let html = `<div class="card"><h3>Answer [${d.style}]</h3><div class="answer">${d.answer}</div>`;
  html += `<div style="margin-top:16px"><b>Sources:</b>`;
  d.sources.forEach(s=>{ html += `<div class="source">📄 ${s.source} | Page: ${s.page} | Chunk: ${s.chunk}<br><small>${s.text.substring(0,200)}...</small></div>` });
  html += `</div></div>`;
  document.getElementById("results").innerHTML = html;
}

function renderCompare(d){
  let html = `<div class="card"><h3>Comparison: ${d.question}</h3></div><div class="grid3">`;
  for(const [style, ans] of Object.entries(d.comparison)){
    html += `<div class="card"><h4>${style}</h4><div class="answer">${ans}</div></div>`;
  }
  html += `</div>`;
  document.getElementById("results").innerHTML = html;
}