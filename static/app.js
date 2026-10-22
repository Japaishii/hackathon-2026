
"use strict";

// ========================================
// ESTADO DA APLICAÇÃO
// ========================================

const $ = (selector) => document.querySelector(selector);

let questionData = [];
let ruleData = [];
let sourceData = [];
let animalData = [];

let currentAssessment = null;
let historyPage = 1;
let pendingDeleteId = null;


// ========================================
// FUNÇÕES AUXILIARES
// ========================================

function rulesSourceById(id) {
  return sourceData.find((source) => source.id === id);
}

function escapeHtml(value) {
  return String(value ?? "").replace(
    /[&<>"']/g,
    (character) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;"
    })[character]
  );
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    }
  });

  const data = response.status === 204
    ? null
    : await response.json().catch(() => ({}));

  if (!response.ok) {
    const detail = data?.detail;

    throw new Error(
      typeof detail === "string"
        ? detail
        : `Erro ${response.status}`
    );
  }

  return data;
}


// ========================================
// QUESTIONÁRIO
// ========================================

function renderQuestionInput(question) {
  const id = escapeHtml(question.id);

  if (question.type === "boolean") {
    return `
      <select id="q-${id}" name="${id}">
        <option value="unknown">
          Não sei / não foi possível verificar
        </option>
        <option value="true">
          Sim, observei esse sinal
        </option>
        <option value="false">
          Não, esse sinal não foi observado
        </option>
      </select>
    `;
  }

  if (question.type === "enum") {
    const options = question.options.map((value) => {
      const label = question.option_labels?.[value] || value;

      return `
        <option value="${escapeHtml(value)}">
          ${escapeHtml(label)}
        </option>
      `;
    }).join("");

    return `
      <select id="q-${id}" name="${id}">
        <option value="">Selecione / não sei</option>
        ${options}
      </select>
    `;
  }

  return `
    <div class="input-with-unit">
      <input
        id="q-${id}"
        name="${id}"
        type="number"
        min="0"
        step="1"
        placeholder="Não informado"
      >
      <span>horas</span>
    </div>
  `;
}

function renderQuestions() {
  const root = $("#questions");

  const groupNames = {
    urgent: [
      "respiratory_distress",
      "unable_to_rise",
      "sudden_left_abdominal_distension"
    ],
    udder: [
      "abnormal_milk",
      "udder_inflammation"
    ],
    context: [
      "fever_state",
      "reduced_appetite",
      "milk_drop",
      "onset_hours"
    ]
  };

  const groups = [
    [
      "urgent",
      "Sinais prioritários",
      "Comece por estes sinais. Marque o que está acontecendo agora."
    ],
    [
      "udder",
      "Leite e úbere",
      "Observe o leite e o aspecto do úbere, sem fazer procedimentos."
    ],
    [
      "context",
      "Contexto e evolução",
      "Informações adicionais ajudam a organizar o histórico."
    ]
  ];

  root.innerHTML = groups.map(([key, title, hint]) => {
    const items = questionData.filter(
      (question) => groupNames[key].includes(question.id)
    );

    return `
      <section class="question-group">
        <div class="group-heading">
          <h3>${title}</h3>
          <p>${hint}</p>
        </div>

        ${items.map((question) => `
          <div class="question">
            <label for="q-${escapeHtml(question.id)}">
              ${escapeHtml(question.label)}

              ${question.required_for_clear_result
                ? '<span class="required-mark">PRIORITÁRIO</span>'
                : ""}
            </label>

            ${renderQuestionInput(question)}
          </div>
        `).join("")}
      </section>
    `;
  }).join("");

  root.querySelectorAll("select").forEach((select) => {
    select.addEventListener("change", () => {
      updateAdaptiveQuestions();
      updateProgress();
    });
  });

  updateAdaptiveQuestions();
  updateProgress();
}

function updateAdaptiveQuestions() {
  const mammary = [
    "abnormal_milk",
    "udder_inflammation"
  ].some((id) => $(`#q-${id}`)?.value === "true");

  const context = questionData.filter((question) =>
    [
      "fever_state",
      "reduced_appetite",
      "milk_drop",
      "onset_hours"
    ].includes(question.id)
  );

  for (const question of context) {
    const input = $(`#q-${question.id}`);
    const container = input?.closest(".question");

    if (!container) {
      continue;
    }

    container.classList.toggle(
      "context-relevant",
      mammary
    );
  }

  const hint = $(".adaptive-help");

  if (hint) {
    hint.textContent = mammary
      ? "Alteração mamária informada: verifique temperatura, apetite e produção para complementar a triagem."
      : "Comece pelos sinais prioritários. As respostas complementares ajudam a contextualizar o caso e permanecem opcionais.";
  }
}

function updateProgress() {
  const required = questionData.filter(
    (question) => question.required_for_clear_result
  );

  const completed = required.filter((question) => {
    const value = $(`#q-${question.id}`)?.value;

    return value !== "unknown"
      && value !== ""
      && value !== undefined;
  }).length;

  $("#progress-text").textContent =
    `${completed} de ${required.length} respondidos`;

  $("#progress-fill").style.width = required.length
    ? `${(completed / required.length) * 100}%`
    : "0%";
}

function answerPayload() {
  const answers = {};

  for (const question of questionData) {
    const value = $(`#q-${question.id}`).value;

    if (question.type === "boolean") {
      answers[question.id] =
        value === "unknown" ? null : value === "true";

    } else if (question.type === "enum") {
      answers[question.id] = value === ""
        ? null
        : value;

    } else {
      answers[question.id] = value === ""
        ? null
        : Number(value);
    }
  }

  return answers;
}


// ========================================
// FATOS E INFERÊNCIA
// ========================================

function factLabel(id) {
  return questionData.find(
    (question) => question.id === id
  )?.label || id;
}

function factValue(id, answers) {
  const value = answers[id];

  if (value === true) {
    return { text: "Sim, observado", cls: "yes" };
  }

  if (value === false) {
    return { text: "Não observado", cls: "no" };
  }

  if (value === null || value === undefined) {
    return { text: "Desconhecido", cls: "unknown" };
  }

  if (value === "fever_present") {
    return { text: "Febre observada", cls: "yes" };
  }

  if (value === "normal_temperature") {
    return { text: "Temperatura normal", cls: "no" };
  }

  if (value === "not_measured") {
    return { text: "Temperatura não medida", cls: "unknown" };
  }

  return {
    text: `${value} h`,
    cls: "no"
  };
}

function relevantFacts(record) {
  const ids = new Set();

  const firedIds = new Set(
    record.result.fired_rules.map((item) => item.id)
  );

  for (const rule of ruleData) {
    if (!firedIds.has(rule.id)) {
      continue;
    }

    const when = rule.when || {};

    (when.all || []).forEach((item) => {
      ids.add(item.fact);
    });

    (when.any || [])
      .filter(
        (item) =>
          record.answers[item.fact] === (item.is ?? true)
      )
      .forEach((item) => ids.add(item.fact));

    (when.any_systemic || [])
      .filter(
        (item) =>
          record.answers[item.fact] === (item.is ?? true)
      )
      .forEach((item) => ids.add(item.fact));

    Object.keys(when.equals || {}).forEach((id) => {
      ids.add(id);
    });
  }

  if (!ids.size) {
    questionData
      .filter((question) => question.required_for_clear_result)
      .forEach((question) => ids.add(question.id));
  }

  return [...ids].map((id) => ({
    id,
    label: factLabel(id),
    ...factValue(id, record.answers)
  }));
}

function renderInference(record) {
  const result = record.result;
  const facts = relevantFacts(record);
  const fired = result.fired_rules;

  const rules = fired.length
    ? fired.map((item) => {
        const full = ruleData.find(
          (rule) => rule.id === item.id
        );

        const sourceLinks = (item.source_ids || [])
          .map((id) => rulesSourceById(id))
          .filter(Boolean)
          .map((source) => `
            <a
              href="${escapeHtml(source.url)}"
              target="_blank"
              rel="noopener noreferrer"
            >
              ${escapeHtml(source.publisher)} ↗
            </a>
          `)
          .join(" · ");

        const evidenceLimit = full?.evidence_limit
          ? `
            <p class="evidence-limit">
              Limite da evidência:
              ${escapeHtml(full.evidence_limit)}
            </p>
          `
          : "";

        const priority = full?.priority === "immediate"
          ? "PRIORIDADE IMEDIATA"
          : "AVALIAÇÃO VETERINÁRIA";

        return `
          <div class="rule-chip">
            <strong>
              ${escapeHtml(item.id)} ·
              ${escapeHtml(item.label)}
            </strong>

            <span>${escapeHtml(item.because)}</span>
            <em>${priority}</em>

            <div class="source-evidence">
              Fontes:
              ${sourceLinks || "Referência não cadastrada"}
            </div>

            ${evidenceLimit}
          </div>
        `;
      }).join("")
    : `
      <p class="empty-stage">
        Nenhuma condição das regras de alerta foi
        satisfeita com as respostas registradas.
      </p>
    `;

  const factHtml = facts.map((fact) => `
    <div class="fact-chip">
      <strong class="${fact.cls}">
        ${escapeHtml(fact.text)}
      </strong>

      ${escapeHtml(fact.label)}
    </div>
  `).join("");

  const conclusionLabel = result.conclusions.length
    ? [...new Set(
        result.conclusions.map((item) => item.label)
      )].map(escapeHtml).join("; ")
    : "Nenhuma conclusão de alerta";

  const statusLabel = result.status === "insufficient"
    ? "Dados incompletos"
    : "Conclusão das regras";

  return `
    <div class="inference-title">
      <h3>Como o sistema chegou a este resultado</h3>

      <span>
        trilha de inferência · base
        ${escapeHtml(result.knowledge_base_version)}
      </span>
    </div>

    <div
      class="inference-flow"
      role="group"
      aria-label="Visualização da inferência: fatos, regras e conclusão"
    >
      <section class="flow-stage">
        <h4>01 · Fatos</h4>

        ${factHtml || `
          <p class="empty-stage">
            Nenhum fato prioritário informado.
          </p>
        `}
      </section>

      <div class="flow-arrow" aria-hidden="true">→</div>

      <section class="flow-stage">
        <h4>02 · Regras</h4>
        ${rules}
      </section>

      <div class="flow-arrow" aria-hidden="true">→</div>

      <section class="flow-stage">
        <h4>03 · Resultado</h4>

        <div class="conclusion-chip">
          <strong>${conclusionLabel}</strong>

          <span>
            ${escapeHtml(statusLabel)} ·
            prioridade
            ${escapeHtml(
              result.priority.replaceAll("_", " ")
            )}
          </span>
        </div>
      </section>
    </div>
  `;
}


// ========================================
// RESULTADO DA TRIAGEM
// ========================================

function renderResult(record) {
  currentAssessment = record;

  $("#follow-up-status").textContent = "";

  const result = record.result;
  const element = $("#result");

  element.className =
    `card result-card ${result.priority}`;

  const symbol = result.priority === "immediate"
    ? "!"
    : result.priority === "none"
      ? "✓"
      : "↗";

  const unknownHtml = result.unknowns.length
    ? `
      <div class="unknown-note">
        <strong>Dados ainda desconhecidos:</strong>

        ${result.unknowns
          .map((id) => escapeHtml(factLabel(id)))
          .join(" · ")}
      </div>
    `
    : "";

  const guidanceHtml = result.guidance.map((item) => `
    <li>${escapeHtml(item)}</li>
  `).join("");
  
  const followUpHtml = record.follow_up?.trim()
    ? `
      <section class="result-section follow-up-section">
        <div class="follow-up-section-header">
          <div>
            <span class="follow-up-section-label">
              EVOLUÇÃO DO CASO
            </span>
            <h3>Acompanhamento registrado</h3>
          </div>

          <span class="follow-up-saved-badge">
            ✓ Registrado
          </span>
        </div>

        <p class="follow-up-saved-text">
          ${escapeHtml(record.follow_up)}
        </p>

        <button
          type="button"
          class="button secondary"
          id="edit-follow-up"
        >
          Editar acompanhamento
        </button>
      </section>
    `
    : "";


  element.innerHTML = `
    <div class="result-head">
      <span class="result-symbol" aria-hidden="true">
        ${symbol}
      </span>

      <div>
        <p class="result-kicker">
          Resultado da triagem
        </p>

        <h2 class="result-title">
          ${escapeHtml(result.summary)}
        </h2>

        <p class="result-meta">
          Avaliação #${record.id} ·
          ${new Date(record.created_at).toLocaleString("pt-BR")}
        </p>
      </div>
    </div>

    <p class="result-disclaimer">
      ${escapeHtml(result.disclaimer)}
    </p>

    ${renderInference(record)}

    ${unknownHtml}

    <section class="result-section">
      <h3>Orientação</h3>
      <ul>${guidanceHtml}</ul>
    </section>
    ${followUpHtml}

    <div class="result-actions">
      <button
        class="button secondary"
        id="print"
        type="button"
      >
        Imprimir / salvar como PDF
      </button>

      <button
        class="button secondary"
        id="follow-up"
        type="button"
      >
        Registrar acompanhamento
      </button>

      <button
        class="button"
        id="confirm-assessment"
        type="button"
      >
        Concluir e iniciar outra triagem
      </button>
    </div>
  `;

  $("#print").onclick = () => window.print();

  $("#follow-up").onclick = () => {
    openFollowUpModal(record);
  };

  const editFollowUpButton = $("#edit-follow-up");

if (editFollowUpButton) {
  editFollowUpButton.onclick = () => {
    openFollowUpModal(currentAssessment);
  };
}

  $("#confirm-assessment").onclick = () => {
    currentAssessment = null;

    element.innerHTML = "";
    element.className = "card result-card hidden";

    $("#assessment-form").reset();

    updateAdaptiveQuestions();
    updateProgress();

    $("#assessment-form").scrollIntoView({
      behavior: "smooth",
      block: "start"
    });

    $("#q-respiratory_distress")?.focus({
      preventScroll: true
    });
  };

  element.scrollIntoView({
    behavior: "smooth",
    block: "start"
  });
}


// ========================================
// ACOMPANHAMENTO
// ========================================

function openFollowUpModal(record) {
  const modal = $("#follow-up-modal");

  $("#follow-up-assessment-id").textContent =
    `#${record.id}`;

  $("#follow-up-note").value =
    record.follow_up || "";

  $("#follow-up-error").textContent = "";

  modal.showModal();
  $("#follow-up-note").focus();
}

function closeFollowUpModal() {
  $("#follow-up-modal").close();
}

$("#follow-up-cancel").addEventListener(
  "click",
  closeFollowUpModal
);

$("#follow-up-modal").addEventListener(
  "click",
  (event) => {
    if (event.target === event.currentTarget) {
      closeFollowUpModal();
    }
  }
);

$("#follow-up-form").addEventListener(
  "submit",
  async (event) => {
    event.preventDefault();

    if (!currentAssessment) {
      return;
    }

    const note = $("#follow-up-note").value.trim();
    const error = $("#follow-up-error");
    const save = $("#follow-up-save");

    error.textContent = "";

    if (!note) {
      error.textContent =
        "Descreva o acompanhamento antes de salvar.";
      return;
    }

    save.disabled = true;

    try {
      const updated = await api(
        `/api/assessments/${currentAssessment.id}/follow-up`,
        {
          method: "PATCH",
          body: JSON.stringify({
            follow_up: note
          })
        }
      );

      
      currentAssessment = updated;

      closeFollowUpModal();

      renderResult(updated);

      await loadHistory();


      $("#follow-up-status").textContent =
        `Acompanhamento da avaliação #${updated.id} salvo com sucesso.`;

    } catch (error) {
      $("#follow-up-error").textContent =
        error.message;

    } finally {
      save.disabled = false;
    }
  }
);


// ========================================
// CADASTRO DE ANIMAIS
// ========================================

async function loadAnimals() {
  const animals = await api("/api/animals");

  animalData = animals;

  $("#animal").innerHTML = `
    <option value="">Sem animal cadastrado</option>
  ` + animals.map((animal) => `
    <option value="${animal.id}">
      ${escapeHtml(animal.identifier)}
      ${animal.breed
        ? ` — ${escapeHtml(animal.breed)}`
        : ""}
    </option>
  `).join("");
}


// ========================================
// HISTÓRICO PAGINADO
// ========================================

function animalPhase(animal) {
  if (!animal) {
    return "Sem cadastro";
  }

  if (animal.transition_stage === "postpartum") {
    return "Pós-parto";
  }

  if (animal.transition_stage === "prepartum") {
    return "Pré-parto";
  }

  if (animal.productive_state === "dry") {
    return "Período seco";
  }

  if (animal.productive_state === "lactating") {
    return "Lactação";
  }

  return "Fase não informada";
}

function assessmentRisk(record) {
  const result = record.result;

  if (result.priority === "immediate") {
    return "Atenção imediata";
  }

  if (result.priority === "veterinary_assessment") {
    return "Avaliação veterinária";
  }

  if (result.status === "insufficient") {
    return "Dados incompletos";
  }

  return "Sem alerta nas regras";
}

async function openAssessment(id) {
  try {
    const record = await api(
      `/api/assessments/${id}`
    );

    renderResult(record);

  } catch (error) {
    alert(error.message);
  }
}

function renderHistoryRow(record) {
  const animal = animalData.find(
    (item) => item.id === record.animal_id
  );

  const date = new Date(record.created_at);

  const risk = assessmentRisk(record);

  const badgeClass = escapeHtml(
    record.result.status === "insufficient"
      ? "insufficient"
      : record.result.priority
  );

  const animalName = animal
    ? `Vaca ${escapeHtml(animal.identifier)}`
    : "Animal não identificado";

  return `
    <li class="history-row">
      <span class="history-cow" aria-hidden="true">
        ♧
      </span>

      <div class="history-item-main">
        <div class="history-top">
          <span class="history-number">
            #${record.id}
          </span>

          <span class="history-badge ${badgeClass}">
            ${escapeHtml(risk)}
          </span>

          ${record.follow_up?.trim()
            ? `
              <span class="history-follow-up-badge">
                ✓ Com acompanhamento
              </span>
            `
            : ""}
        </div>

        <div class="history-animal">
          ${animalName} ·
          ${escapeHtml(animalPhase(animal))}
        </div>
      </div>

      <div class="history-item-date">
        ${date.toLocaleDateString("pt-BR")}
        <br>
        ${date.toLocaleTimeString("pt-BR", {
          hour: "2-digit",
          minute: "2-digit"
        })}
      </div>

      <span class="history-chevron" aria-hidden="true">
        ›
      </span>

      <button
        type="button"
        class="history-row-open"
        data-id="${record.id}"
        aria-label="Abrir triagem ${record.id}"
      ></button>

      <button
        type="button"
        class="history-delete"
        data-id="${record.id}"
        aria-label="Excluir triagem ${record.id}"
        title="Excluir triagem"
      >
        ✕
      </button>
    </li>
  `;
}

async function loadHistory() {
  const data = await api(
    `/api/assessments/page?page=${historyPage}&page_size=5`
  );

  const pages = Math.max(
    1,
    Math.ceil(data.total / data.page_size)
  );

  if (historyPage > pages) {
    historyPage = pages;
    return loadHistory();
  }

  const records = data.items;

  $("#history-list").innerHTML = records.length
    ? records.map(renderHistoryRow).join("")
    : `
      <li class="muted">
        Ainda não há triagens registradas.
      </li>
    `;

  renderHistoryPagination(data, pages);
  bindHistoryEvents();
}

function renderHistoryPagination(data, pages) {
  const container = $("#history-pagination");

  if (!data.total) {
    container.innerHTML = "";
    return;
  }

  const start =
    (historyPage - 1) * data.page_size + 1;

  const end = Math.min(
    historyPage * data.page_size,
    data.total
  );

  container.innerHTML = `
    <span>
      Exibindo ${start}–${end}
      de ${data.total}
    </span>

    <div class="history-page-controls">
      <button
        type="button"
        id="history-prev"
        ${historyPage === 1 ? "disabled" : ""}
        aria-label="Página anterior"
      >
        ‹
      </button>

      <span>
        Página ${historyPage} de ${pages}
      </span>

      <button
        type="button"
        id="history-next"
        ${historyPage === pages ? "disabled" : ""}
        aria-label="Próxima página"
      >
        ›
      </button>
    </div>
  `;
}

function bindHistoryEvents() {
  // Toda a área principal da linha abre a triagem.

  document.querySelectorAll(
    ".history-row-open"
  ).forEach((button) => {
    button.addEventListener("click", () => {
      openAssessment(Number(button.dataset.id));
    });
  });

  // A lixeira é independente do botão de abertura.

  document.querySelectorAll(
    ".history-delete"
  ).forEach((button) => {
    button.addEventListener("click", () => {
      pendingDeleteId = Number(
        button.dataset.id
      );

      $("#delete-assessment-id").textContent =
        `#${pendingDeleteId}`;

      $("#delete-assessment-error").textContent = "";

      $("#delete-assessment-modal").showModal();
    });
  });

  const previous = $("#history-prev");
  const next = $("#history-next");

  if (previous) {
    previous.addEventListener("click", async () => {
      if (historyPage > 1) {
        historyPage--;
        await loadHistory();
      }
    });
  }

  if (next) {
    next.addEventListener("click", async () => {
      historyPage++;
      await loadHistory();
    });
  }
}


// ========================================
// EXCLUSÃO DE TRIAGENS
// ========================================

function closeDeleteModal() {
  $("#delete-assessment-modal").close();
  pendingDeleteId = null;
}

$("#delete-assessment-close").addEventListener(
  "click",
  closeDeleteModal
);

$("#delete-assessment-cancel").addEventListener(
  "click",
  closeDeleteModal
);

$("#delete-assessment-modal").addEventListener(
  "close",
  () => {
    pendingDeleteId = null;
  }
);

$("#delete-assessment-confirm").addEventListener(
  "click",
  async () => {
    if (pendingDeleteId === null) {
      return;
    }

    const id = pendingDeleteId;

    const button = $("#delete-assessment-confirm");

    button.disabled = true;

    try {
      await api(
        `/api/assessments/${id}`,
        { method: "DELETE" }
      );

      if (currentAssessment?.id === id) {
        currentAssessment = null;

        $("#result").innerHTML = "";
        $("#result").className =
          "card result-card hidden";
      }

      closeDeleteModal();

      await loadHistory();

    } catch (error) {
      $("#delete-assessment-error").textContent =
        error.message;

    } finally {
      button.disabled = false;
    }
  }
);


// ========================================
// INICIALIZAÇÃO
// ========================================

async function init() {
  try {
    const [questions, rules] = await Promise.all([
      api("/api/questions"),
      api("/api/rules")
    ]);

    questionData = questions.questions;
    ruleData = rules.rules;
    sourceData = rules.sources;

    renderQuestions();

    $("#kb-version").textContent = rules.version;

    $("#sources").innerHTML = rules.sources.map(
      (source) => `
        <p>
          <a
            href="${escapeHtml(source.url)}"
            target="_blank"
            rel="noopener noreferrer"
          >
            ${escapeHtml(source.title)}
          </a>
          — ${escapeHtml(source.publisher)}
          <br>
          ${escapeHtml(source.supports)}
        </p>
      `
    ).join("");

    const preview = $("#source-preview");

    if (preview) {
      preview.innerHTML = rules.sources
        .slice(0, 4)
        .map((source) => `
          <a
            class="knowledge-row"
            href="${escapeHtml(source.url)}"
            target="_blank"
            rel="noopener noreferrer"
          >
            <span class="knowledge-icon">▤</span>

            <span>
              <strong>
                ${escapeHtml(source.title)}
              </strong>

              <small>
                ${escapeHtml(source.publisher)}
              </small>
            </span>

            <span class="knowledge-arrow">›</span>
          </a>
        `).join("");
    }

    await loadAnimals();
    await loadHistory();

  } catch (error) {
    alert(
      `Não foi possível carregar o BoviHealth: ${error.message}`
    );
  }
}


// ========================================
// ENVIO DA TRIAGEM
// ========================================

$("#assessment-form").addEventListener(
  "submit",
  async (event) => {
    event.preventDefault();

    const animal = $("#animal").value;

    try {
      const record = await api(
        "/api/assessments",
        {
          method: "POST",
          body: JSON.stringify({
            animal_id: animal
              ? Number(animal)
              : null,
            answers: answerPayload()
          })
        }
      );

      renderResult(record);

      historyPage = 1;
      await loadHistory();

    } catch (error) {
      alert(error.message);
    }
  }
);

$("#assessment-form").addEventListener(
  "reset",
  () => {
    setTimeout(() => {
      updateAdaptiveQuestions();
      updateProgress();
    }, 0);
  }
);


// ========================================
// CADASTRO DE ANIMAL
// ========================================

$("#animal-form").addEventListener(
  "submit",
  async (event) => {
    event.preventDefault();

    try {
      await api(
        "/api/animals",
        {
          method: "POST",
          body: JSON.stringify({
            identifier: $("#identifier").value.trim(),
            breed: $("#breed").value || null,
            age_months: $("#age").value
              ? Number($("#age").value)
              : null,
            days_in_milk: $("#dim").value
              ? Number($("#dim").value)
              : null,
            productive_state:
              $("#productive_state").value,
            transition_stage:
              $("#transition_stage").value
          })
        }
      );

      event.target.reset();

      await loadAnimals();

      alert("Animal cadastrado.");

    } catch (error) {
      alert(error.message);
    }
  }
);


// ========================================
// INICIAR APLICAÇÃO
// ========================================

init();
