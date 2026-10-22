const $ = (s) => document.querySelector(s);
let questionData = [];
let ruleData = [];
let sourceData = [];
let animalData = [];
let currentAssessment = null;
function rulesSourceById(id) { return sourceData.find(source => source.id === id); }

function escapeHtml(value) { return String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])); }
function renderQuestionInput(q) {
  if (q.type === "boolean") return `<select id="q-${q.id}" name="${q.id}"><option value="unknown">Não sei / não foi possível verificar</option><option value="true">Sim, observei esse sinal</option><option value="false">Não, esse sinal não foi observado</option></select>`;
  if (q.type === "enum") return `<select id="q-${q.id}" name="${q.id}"><option value="">Selecione / não sei</option>${q.options.map(value => `<option value="${escapeHtml(value)}">${escapeHtml(q.option_labels?.[value] || value)}</option>`).join("")}</select>`;
  return `<div class="input-with-unit"><input id="q-${q.id}" name="${q.id}" type="number" min="0" step="1" placeholder="Não informado"><span>horas</span></div>`;
}
async function api(path, options = {}) {
  const response = await fetch(path, {headers:{"Content-Type":"application/json", ...(options.headers||{})}, ...options});
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || `Erro ${response.status}`);
  return data;
}
function renderQuestions() {
  const root = $("#questions");
  const groupNames = {
    urgent: ["respiratory_distress", "unable_to_rise", "sudden_left_abdominal_distension"],
    udder: ["abnormal_milk", "udder_inflammation"],
    context: ["fever_state", "reduced_appetite", "milk_drop", "onset_hours"],
  };
  const groups = [
    ["urgent", "Sinais prioritários", "Comece por estes sinais. Marque o que está acontecendo agora."],
    ["udder", "Leite e úbere", "Observe o leite e o aspecto do úbere, sem fazer procedimentos."],
    ["context", "Contexto e evolução", "Informações adicionais ajudam a organizar o histórico."],
  ];
  root.innerHTML = groups.map(([key, title, hint]) => {
    const items = questionData.filter(q => groupNames[key].includes(q.id));
    return `<section class="question-group"><div class="group-heading"><h3>${title}</h3><p>${hint}</p></div>${items.map(q => `<div class="question"><label for="q-${q.id}">${escapeHtml(q.label)}${q.required_for_clear_result ? " <span class=\"required-mark\">PRIORITÁRIO</span>" : ""}</label>${renderQuestionInput(q)}</div>`).join("")}</section>`;
  }).join("");
  root.querySelectorAll("select").forEach(select => select.addEventListener("change", () => { updateAdaptiveQuestions(); updateProgress(); }));
  updateAdaptiveQuestions();
  updateProgress();
}
function updateAdaptiveQuestions() {
  const mammary = ["abnormal_milk", "udder_inflammation"].some(id => $(`#q-${id}`)?.value === "true");
  const context = questionData.filter(q => ["fever_state", "reduced_appetite", "milk_drop", "onset_hours"].includes(q.id));
  for (const q of context) {
    const input = $(`#q-${q.id}`);
    const container = input?.closest(".question");
    if (!container) continue;
    // Maintain all clinical context available; highlight relevance instead of discarding answers.
    container.classList.toggle("context-relevant", mammary);
  }
  const hint = document.querySelector(".adaptive-help");
  if (hint) hint.textContent = mammary ? "Alteração mamária informada: verifique temperatura, apetite e produção para complementar a triagem." : "Comece pelos sinais prioritários. As respostas complementares ajudam a contextualizar o caso e permanecem opcionais.";
}
function updateProgress() {
  const required = questionData.filter(q => q.required_for_clear_result);
  const completed = required.filter(q => $(`#q-${q.id}`)?.value !== "unknown").length;
  $("#progress-text").textContent = `${completed} de ${required.length} respondidos`;
  $("#progress-fill").style.width = `${required.length ? completed / required.length * 100 : 0}%`;
}
function answerPayload() {
  const answers = {};
  for (const q of questionData) {
    const value = $(`#q-${q.id}`).value;
    answers[q.id] = q.type === "boolean" ? (value === "unknown" ? null : value === "true") : q.type === "enum" ? (value === "" ? null : value) : (value === "" ? null : Number(value));
  }
  return answers;
}
function factLabel(id) { return questionData.find(q => q.id === id)?.label || id; }
function factValue(id, answers) {
  const value = answers[id];
  if (value === true) return {text:"Sim, observado", cls:"yes"};
  if (value === false) return {text:"Não observado", cls:"no"};
  if (value === null || value === undefined) return {text:"Desconhecido", cls:"unknown"};
  if (value === "fever_present") return {text:"Febre observada", cls:"yes"};
  if (value === "normal_temperature") return {text:"Temperatura normal", cls:"no"};
  if (value === "not_measured") return {text:"Temperatura não medida", cls:"unknown"};
  return {text:`${value} h`, cls:"no"};
}
function relevantFacts(record) {
  const ids = new Set();
  const firedIds = new Set(record.result.fired_rules.map(item => item.id));
  for (const rule of ruleData) {
    if (!firedIds.has(rule.id)) continue;
    const when = rule.when || {};
    (when.all || []).forEach(item => ids.add(item.fact));
    (when.any || []).filter(item => record.answers[item.fact] === (item.is ?? true)).forEach(item => ids.add(item.fact));
    (when.any_systemic || []).filter(item => record.answers[item.fact] === (item.is ?? true)).forEach(item => ids.add(item.fact));
    Object.keys(when.equals || {}).forEach(id => ids.add(id));
  }
  if (!ids.size) questionData.filter(q => q.required_for_clear_result).forEach(q => ids.add(q.id));
  return [...ids].map(id => ({id, label:factLabel(id), ...factValue(id, record.answers)}));
}
function renderInference(record) {
  const result = record.result;
  const facts = relevantFacts(record);
  const fired = result.fired_rules;
  const rules = fired.length ? fired.map(item => {
    const full = ruleData.find(rule => rule.id === item.id);
    const sourceLinks = (item.source_ids || []).map(id => rulesSourceById(id)).filter(Boolean).map(source => `<a href="${escapeHtml(source.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(source.publisher)} ↗</a>`).join(" · ");
    const evidenceLimit = full?.evidence_limit ? `<p class="evidence-limit">Limite da evidência: ${escapeHtml(full.evidence_limit)}</p>` : "";
    const priority = full?.priority === "immediate" ? "PRIORIDADE IMEDIATA" : "AVALIAÇÃO VETERINÁRIA";
    return `<div class="rule-chip"><strong>${escapeHtml(item.id)} · ${escapeHtml(item.label)}</strong><span>${escapeHtml(item.because)}</span><em>${priority}</em><div class="source-evidence">Fontes: ${sourceLinks || "Referência não cadastrada"}</div>${evidenceLimit}</div>`;
  }).join("") : `<p class="empty-stage">Nenhuma condição das regras de alerta foi satisfeita com as respostas registradas.</p>`;
  const factHtml = facts.map(fact => `<div class="fact-chip"><strong class="${fact.cls}">${escapeHtml(fact.text)}</strong>${escapeHtml(fact.label)}</div>`).join("");
  const conclusionLabel = result.conclusions.length ? result.conclusions.map(item => item.label).filter((x,i,a)=>a.indexOf(x)===i).map(escapeHtml).join("; ") : "Nenhuma conclusão de alerta";
  const statusLabel = result.status === "insufficient" ? "Dados incompletos" : "Conclusão das regras";
  return `<div class="inference-title"><h3>Como o sistema chegou a este resultado</h3><span>trilha de inferência · base ${escapeHtml(result.knowledge_base_version)}</span></div><div class="inference-flow" role="group" aria-label="Visualização da inferência: fatos, regras e conclusão"><section class="flow-stage"><h4>01 · Fatos</h4>${factHtml || `<p class="empty-stage">Nenhum fato prioritário informado.</p>`}</section><div class="flow-arrow" aria-hidden="true">→</div><section class="flow-stage"><h4>02 · Regras</h4>${rules}</section><div class="flow-arrow" aria-hidden="true">→</div><section class="flow-stage"><h4>03 · Resultado</h4><div class="conclusion-chip"><strong>${escapeHtml(conclusionLabel)}</strong><span>${escapeHtml(statusLabel)} · prioridade ${escapeHtml(result.priority.replaceAll("_", " "))}</span></div></section></div>`;
}
function renderResult(record) {
  currentAssessment = record;
  $("#follow-up-status").textContent = "";
  const r = record.result;
  const el = $("#result");
  el.className = `card result-card ${r.priority}`;
  el.innerHTML = `<div class="result-head"><span class="result-symbol" aria-hidden="true">${r.priority === "immediate" ? "!" : r.priority === "none" ? "✓" : "↗"}</span><div><p class="result-kicker">Resultado da triagem</p><h2 class="result-title">${escapeHtml(r.summary)}</h2><p class="result-meta">Avaliação #${record.id} · ${new Date(record.created_at).toLocaleString("pt-BR")}</p></div></div><p class="result-disclaimer">${escapeHtml(r.disclaimer)}</p>${renderInference(record)}${r.unknowns.length ? `<div class="unknown-note"><strong>Dados ainda desconhecidos:</strong> ${r.unknowns.map(id => escapeHtml(factLabel(id))).join(" · ")}</div>` : ""}<section class="result-section"><h3>Orientação</h3><ul>${r.guidance.map(x=>`<li>${escapeHtml(x)}</li>`).join("")}</ul></section><div class="result-actions"><button class="button secondary" id="print">Imprimir / salvar como PDF</button><button class="button secondary" id="follow-up">Registrar acompanhamento</button><button class="button" id="confirm-assessment" type="button">Concluir e iniciar outra triagem</button></div>`;
  $("#print").onclick = () => window.print();
  $("#follow-up").onclick = () => openFollowUpModal(record);
  $("#confirm-assessment").onclick = () => {
    // A confirmação encerra somente a visualização; o registro permanece no histórico.
    currentAssessment = null;
    el.innerHTML = "";
    el.className = "card result-card hidden";
    $("#assessment-form").reset();
    updateAdaptiveQuestions();
    updateProgress();
    $("#assessment-form").scrollIntoView({behavior:"smooth", block:"start"});
    $("#q-respiratory_distress")?.focus({preventScroll:true});
  };
  el.scrollIntoView({behavior:"smooth", block:"start"});
}

function openFollowUpModal(record) {
  const modal = $("#follow-up-modal");
  $("#follow-up-assessment-id").textContent = `#${record.id}`;
  $("#follow-up-note").value = record.follow_up || "";
  $("#follow-up-error").textContent = "";
  modal.showModal();
  $("#follow-up-note").focus();
}
function closeFollowUpModal() { $("#follow-up-modal").close(); }
$("#follow-up-cancel").addEventListener("click", closeFollowUpModal);
$("#follow-up-modal").addEventListener("click", event => {
  if (event.target === event.currentTarget) closeFollowUpModal();
});
$("#follow-up-form").addEventListener("submit", async event => {
  event.preventDefault();
  if (!currentAssessment) return;
  const note = $("#follow-up-note").value.trim();
  const error = $("#follow-up-error");
  const save = $("#follow-up-save");
  error.textContent = "";
  if (!note) { error.textContent = "Descreva o acompanhamento antes de salvar."; return; }
  save.disabled = true;
  try {
    const updated = await api(`/api/assessments/${currentAssessment.id}/follow-up`, {
      method:"PATCH", body:JSON.stringify({follow_up:note})
    });
    currentAssessment = updated;
    closeFollowUpModal();
    await loadHistory();
    const status = $("#follow-up-status");
    status.textContent = `Acompanhamento da avaliação #${updated.id} salvo com sucesso.`;
  } catch (e) {
    error.textContent = e.message;
  } finally { save.disabled = false; }
});

async function loadAnimals() {
  const animals = await api("/api/animals");
  animalData = animals;
  $("#animal").innerHTML = `<option value="">Sem animal cadastrado</option>` + animals.map(a => `<option value="${a.id}">${escapeHtml(a.identifier)}${a.breed ? ` — ${escapeHtml(a.breed)}` : ""}</option>`).join("");
}
async function loadHistory() {
  const records = await api("/api/assessments");
  $("#history-list").innerHTML = records.length ? records.slice(0,8).map(a => {
    const animal = animalData.find(x => x.id === a.animal_id);
    const phase = animal ? (animal.transition_stage === "postpartum" ? "Pós-parto" : animal.transition_stage === "prepartum" ? "Pré-parto" : animal.productive_state === "dry" ? "Período seco" : animal.productive_state === "lactating" ? "Lactação" : "Fase não informada") : "Sem cadastro";
    const risk = a.result.priority === "immediate" ? "Atenção imediata" : a.result.priority === "veterinary_assessment" ? "Avaliação veterinária" : a.result.status === "insufficient" ? "Dados incompletos" : "Sem alerta nas regras";
    const badgeClass = escapeHtml(a.result.status === "insufficient" ? "insufficient" : a.result.priority);
    const date = new Date(a.created_at);
    return `<li class="history-row"><span class="history-cow" aria-hidden="true">♧</span><div class="history-item-main"><div class="history-top"><button class="history-open" data-id="${a.id}">#${a.id}</button><span class="history-badge ${badgeClass}">${escapeHtml(risk)}</span></div><div class="history-animal">${animal ? `Vaca ${escapeHtml(animal.identifier)}` : "Animal não identificado"} · ${escapeHtml(phase)}</div></div><div class="history-item-date">${date.toLocaleDateString("pt-BR")}<br>${date.toLocaleTimeString("pt-BR",{hour:"2-digit",minute:"2-digit"})}</div><button class="history-open history-chevron" data-id="${a.id}" aria-label="Abrir avaliação ${a.id}">›</button></li>`;
  }).join("") : "<li class=\"muted\">Ainda não há triagens registradas.</li>";
  document.querySelectorAll(".history-open").forEach(btn => btn.onclick = async () => renderResult(await api(`/api/assessments/${btn.dataset.id}`)));
}
async function init() {
  try {
    const [questions, rules] = await Promise.all([api("/api/questions"), api("/api/rules")]);
    questionData = questions.questions; ruleData = rules.rules; sourceData = rules.sources; renderQuestions(); $("#kb-version").textContent = rules.version;
    $("#sources").innerHTML = rules.sources.map(s=>`<p><a href="${escapeHtml(s.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(s.title)}</a> — ${escapeHtml(s.publisher)}<br>${escapeHtml(s.supports)}</p>`).join("");
    const preview = document.querySelector("#source-preview");
    if (preview) preview.innerHTML = rules.sources.slice(0,4).map(s => `<a class="knowledge-row" href="${escapeHtml(s.url)}" target="_blank" rel="noopener noreferrer"><span class="knowledge-icon">▤</span><span><strong>${escapeHtml(s.title)}</strong><small>${escapeHtml(s.publisher)}</small></span><span class="knowledge-arrow">›</span></a>`).join("");
    await loadAnimals(); await loadHistory();
  } catch(e) { alert(`Não foi possível carregar o BoviHealth: ${e.message}`); }
}
$("#assessment-form").addEventListener("submit", async event => {
  event.preventDefault();
  const animal = $("#animal").value;
  try {
    const record = await api("/api/assessments", {method:"POST", body:JSON.stringify({animal_id:animal ? Number(animal) : null, answers:answerPayload()})});
    renderResult(record); await loadHistory();
  } catch(e) { alert(e.message); }
});
$("#assessment-form").addEventListener("reset", () => setTimeout(() => { updateAdaptiveQuestions(); updateProgress(); }, 0));
$("#animal-form").addEventListener("submit", async event => {
  event.preventDefault();
  try {
    await api("/api/animals", {method:"POST", body:JSON.stringify({identifier:$("#identifier").value.trim(),breed:$("#breed").value||null,age_months:$("#age").value?Number($("#age").value):null,days_in_milk:$("#dim").value?Number($("#dim").value):null,productive_state:$("#productive_state").value,transition_stage:$("#transition_stage").value})});
    event.target.reset(); await loadAnimals(); alert("Animal cadastrado.");
  } catch(e) { alert(e.message); }
});
init();
