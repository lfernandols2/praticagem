(() => {
  "use strict";

  const STORAGE_KEY = "apostila-praticagem-progresso-v1";
  const QUESTOES_KEY = "apostila-praticagem-questoes-v1";
  const RESPOSTAS_KEY = "apostila-praticagem-respostas-v1";
  const THEME_KEY = "apostila-praticagem-tema";
  const doc = document;
  const root = doc.documentElement;

  /* ---------- tema ---------- */
  function applyTheme(theme) {
    root.setAttribute("data-theme", theme);
    const btn = doc.querySelector("[data-theme-toggle]");
    if (btn) {
      const dark = theme === "dark";
      btn.setAttribute("aria-label", dark ? "Ativar tema claro" : "Ativar tema escuro");
      btn.setAttribute("title", dark ? "Tema claro" : "Tema escuro");
      btn.innerHTML = dark
        ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2.2M12 19.3v2.2M4.6 4.6l1.6 1.6M17.8 17.8l1.6 1.6M2.5 12h2.2M19.3 12h2.2M4.6 19.4l1.6-1.6M17.8 6.2l1.6-1.6"/></svg>'
        : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M20.5 14.2A8.4 8.4 0 1 1 9.8 3.5a6.9 6.9 0 0 0 10.7 10.7Z"/></svg>';
    }
  }

  function initTheme() {
    const stored = localStorage.getItem(THEME_KEY);
    const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    applyTheme(stored || (prefersDark ? "dark" : "light"));
  }

  function toggleTheme() {
    const current = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    localStorage.setItem(THEME_KEY, current);
    applyTheme(current);
  }

  /* ---------- progresso ---------- */
  function getProgress() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
    } catch {
      return {};
    }
  }

  function setDone(partId, done) {
    const data = getProgress();
    if (done) data[partId] = Date.now();
    else delete data[partId];
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    paintProgress(data);
  }

  function paintProgress(data = getProgress()) {
    doc.querySelectorAll("[data-progress-total]").forEach((el) => {
      const total = Number(el.getAttribute("data-progress-total"));
      const count = Object.keys(data).filter((k) => data[k]).length;
      el.textContent = String(count).padStart(2, "0");
      const fill = el.closest(".sidebar__progress")?.querySelector(".bar__fill");
      if (fill && total) fill.style.width = `${Math.min(100, (count / total) * 100)}%`;
    });

    doc.querySelectorAll(".part-nav a[data-part-id]").forEach((a) => {
      const id = a.getAttribute("data-part-id");
      const hasDot = a.querySelector(".part-nav__done");
      if (data[id] && !hasDot) {
        const dot = doc.createElement("i");
        dot.className = "part-nav__done";
        dot.setAttribute("aria-label", "capítulo concluído");
        a.appendChild(dot);
      } else if (!data[id] && hasDot) {
        hasDot.remove();
      }
    });

    doc.querySelectorAll(".part-card[data-part-id]").forEach((card) => {
      card.classList.toggle("is-done", Boolean(data[card.getAttribute("data-part-id")]));
    });

    const stat = doc.querySelector("[data-index-progress]");
    if (stat) {
      const total = Number(stat.getAttribute("data-index-progress"));
      const count = Object.keys(data).filter((k) => data[k]).length;
      stat.textContent = total ? `${count}/${total}` : "0";
    }
  }

  function initCompleteButton() {
    const btn = doc.querySelector("[data-complete]");
    if (!btn) return;
    const partId = btn.getAttribute("data-complete");
    const label = btn.querySelector("span");

    const sync = () => {
      const done = Boolean(getProgress()[partId]);
      btn.classList.toggle("btn--done", done);
      btn.classList.toggle("btn--gold", !done);
      if (label) label.textContent = done ? "Capítulo concluído" : "Marcar como concluído";
      btn.setAttribute("aria-pressed", String(done));
    };

    btn.addEventListener("click", () => {
      const done = Boolean(getProgress()[partId]);
      setDone(partId, !done);
      sync();
    });

    sync();
  }

  /* ---------- barra de leitura ---------- */
  function initReadingProgress() {
    const bar = doc.querySelector(".read-progress");
    if (!bar) return;
    let ticking = false;
    const update = () => {
      const max = doc.documentElement.scrollHeight - window.innerHeight;
      const pct = max > 0 ? (window.scrollY / max) * 100 : 0;
      bar.style.width = `${Math.min(100, Math.max(0, pct))}%`;
      ticking = false;
    };
    window.addEventListener("scroll", () => {
      if (!ticking) {
        window.requestAnimationFrame(update);
        ticking = true;
      }
    }, { passive: true });
    update();
  }

  /* ---------- sidebar mobile ---------- */
  function initSidebar() {
    const sidebar = doc.querySelector(".sidebar");
    const toggle = doc.querySelector("[data-nav-toggle]");
    if (!sidebar || !toggle) return;

    let scrim = doc.querySelector(".scrim");
    if (!scrim) {
      scrim = doc.createElement("div");
      scrim.className = "scrim";
      doc.body.appendChild(scrim);
    }

    const close = () => {
      sidebar.classList.remove("is-open");
      scrim.classList.remove("is-visible");
      toggle.setAttribute("aria-expanded", "false");
    };
    const open = () => {
      sidebar.classList.add("is-open");
      scrim.classList.add("is-visible");
      toggle.setAttribute("aria-expanded", "true");
    };

    toggle.addEventListener("click", () => {
      if (sidebar.classList.contains("is-open")) close();
      else open();
    });
    scrim.addEventListener("click", close);
    doc.addEventListener("keydown", (ev) => {
      if (ev.key === "Escape") close();
    });
    sidebar.querySelectorAll("a").forEach((a) => a.addEventListener("click", close));
  }

  /* ---------- âncoras nos títulos ---------- */
  function initAnchors() {
    doc.querySelectorAll(".content h2[id], .content h3[id]").forEach((heading) => {
      if (heading.querySelector(".anchor")) return;
      const a = doc.createElement("a");
      a.className = "anchor";
      a.href = `#${heading.id}`;
      a.textContent = "#";
      a.setAttribute("aria-label", `Link para: ${heading.textContent.trim()}`);
      heading.appendChild(a);
    });
  }

  /* ---------- scrollspy do sumário ---------- */
  function initScrollSpy() {
    const links = [...doc.querySelectorAll(".toc-card a[href^='#']")];
    if (!links.length || !("IntersectionObserver" in window)) return;
    const byId = new Map(links.map((l) => [l.getAttribute("href").slice(1), l]));
    const targets = [...byId.keys()].map((id) => doc.getElementById(id)).filter(Boolean);
    if (!targets.length) return;

    const setActive = (id) => {
      links.forEach((l) => l.classList.remove("is-current"));
      const link = byId.get(id);
      if (link) link.classList.add("is-current");
    };

    const observer = new IntersectionObserver((entries) => {
      const visible = entries
        .filter((e) => e.isIntersecting)
        .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
      if (visible[0]) setActive(visible[0].target.id);
    }, { rootMargin: "-90px 0px -65% 0px", threshold: 0 });

    targets.forEach((t) => observer.observe(t));
  }

  /* ---------- busca e filtros do índice ---------- */
  function initIndex() {
    const cards = [...doc.querySelectorAll(".part-card")];
    const search = doc.querySelector("[data-search]");
    const chips = [...doc.querySelectorAll(".filter-chip")];
    const empty = doc.querySelector(".no-results");
    if (!cards.length) return;

    let module = "todos";
    let term = "";

    const apply = () => {
      let shown = 0;
      cards.forEach((card) => {
        const text = (card.textContent + " " + (card.dataset.tags || "")).toLowerCase();
        const matchesTerm = !term || text.includes(term);
        const matchesModule = module === "todos" || card.dataset.module === module;
        const show = matchesTerm && matchesModule;
        card.style.display = show ? "" : "none";
        if (show) shown += 1;
      });
      if (empty) empty.classList.toggle("is-visible", shown === 0);
    };

    if (search) {
      search.addEventListener("input", () => {
        term = search.value.trim().toLowerCase();
        apply();
      });
    }

    chips.forEach((chip) => {
      chip.addEventListener("click", () => {
        module = chip.getAttribute("data-filter") || "todos";
        chips.forEach((c) => c.setAttribute("aria-pressed", String(c === chip)));
        apply();
      });
    });

    doc.addEventListener("keydown", (ev) => {
      if (ev.key === "/" && search && doc.activeElement !== search) {
        ev.preventDefault();
        search.focus();
      }
    });
  }

  /* ---------- banco de questões ---------- */
  function normalizeText(value) {
    return (value || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase();
  }

  function getQuestaoProgress() {
    try {
      return JSON.parse(localStorage.getItem(QUESTOES_KEY) || "{}");
    } catch {
      return {};
    }
  }

  function getRespostas() {
    try {
      return JSON.parse(localStorage.getItem(RESPOSTAS_KEY) || "{}");
    } catch {
      return {};
    }
  }

  function saveRespostas(value) {
    try {
      localStorage.setItem(RESPOSTAS_KEY, JSON.stringify(value));
    } catch {
      /* navegação privada: a seleção dura apenas nesta sessão */
    }
  }

  function paintSelection(card, answers) {
    const id = card.getAttribute("data-question-id");
    const selected = answers[id] || "";
    if (selected) {
      const radio = card.querySelector('input[data-alternative][value="' + selected + '"]');
      if (radio) radio.checked = true;
    }
    card.querySelectorAll(".alternative").forEach((li) => {
      li.classList.toggle("is-selected", !!selected && li.getAttribute("data-letter") === selected);
    });
    return selected;
  }

  function setAnswer(card, show) {
    const box = card.querySelector("[data-answer-box]");
    if (!box) return;
    box.hidden = !show;
    const btn = card.querySelector("[data-reveal]");
    if (btn) {
      btn.setAttribute("aria-pressed", String(show));
      btn.textContent = show ? "Ocultar gabarito" : "Verificar / gabarito";
    }

    const correct = (card.getAttribute("data-answer-letter") || "").toLowerCase();
    const checked = card.querySelector("input[data-alternative]:checked");
    const selected = checked ? checked.value.toLowerCase() : "";
    const result = card.querySelector("[data-answer-result]");

    card.querySelectorAll(".alternative").forEach((li) => {
      const letter = li.getAttribute("data-letter");
      li.classList.toggle("is-correct", show && !!correct && letter === correct);
      li.classList.toggle("is-wrong", show && !!selected && letter === selected && selected !== correct);
    });

    if (result) {
      result.textContent = "";
      result.classList.remove("is-right", "is-wrong");
      if (show && correct) {
        if (!selected) {
          result.textContent = "Selecione uma alternativa para comparar com o gabarito.";
        } else if (selected === correct) {
          result.textContent = "Você acertou!";
          result.classList.add("is-right");
        } else {
          result.textContent = `Você marcou ${selected.toUpperCase()}. Resposta correta: ${correct.toUpperCase()}.`;
          result.classList.add("is-wrong");
        }
      }
    }
  }

  function initQuestions() {
    const page = doc.querySelector("[data-questoes-page]");
    if (!page || !doc.body.classList.contains("questoes-page")) return;

    const cards = [...doc.querySelectorAll(".question-card")];
    const grid = doc.querySelector("[data-questions-grid]");
    const pageSize = Math.max(1, Number(page.getAttribute("data-questoes-page-size") || 10));
    const yearChips = [...doc.querySelectorAll("[data-quest-year]")];
    const topicChips = [...doc.querySelectorAll("[data-quest-topic]")];
    const sourceChips = [...doc.querySelectorAll("[data-quest-source]")];
    const search = doc.querySelector("[data-questoes-search]");
    const counter = doc.querySelector("[data-questoes-count]");
    const range = doc.querySelector("[data-questoes-range]");
    const empty = doc.querySelector("[data-questoes-empty]");
    const revealAll = doc.querySelector("[data-reveal-all]");
    const hideAll = doc.querySelector("[data-hide-all]");
    const doneEls = [...doc.querySelectorAll("[data-questoes-done]")];
    const answeredEls = [...doc.querySelectorAll("[data-questoes-answered]")];
    const bar = doc.querySelector("[data-questoes-bar]");
    const currentEls = [...doc.querySelectorAll("[data-page-current]")];
    const totalEls = [...doc.querySelectorAll("[data-page-total]")];
    const prevButtons = [...doc.querySelectorAll("[data-page-prev]")];
    const nextButtons = [...doc.querySelectorAll("[data-page-next]")];
    const total = Number(page.getAttribute("data-questoes-total") || cards.length);

    let year = "todos";
    let topic = "todos";
    let source = "todos";
    let term = "";
    let currentPage = 1;
    let matching = cards;

    const paintAnswers = () => {
      const answers = getRespostas();
      let answered = 0;
      cards.forEach((card) => {
        const selected = paintSelection(card, answers);
        if (selected && card.getAttribute("data-answer-letter")) answered += 1;
        const box = card.querySelector("[data-answer-box]");
        if (box && !box.hidden) setAnswer(card, true);
      });
      answeredEls.forEach((el) => { el.textContent = String(answered); });
    };

    const apply = (scrollToGrid = false) => {
      matching = cards.filter((card) => {
        const text = normalizeText(card.getAttribute("data-search"));
        const okYear = year === "todos" || card.getAttribute("data-question-year") === year;
        const okTopic = topic === "todos" || card.getAttribute("data-topic") === topic;
        const okSource = source === "todos" || (source === "pna" && card.getAttribute("data-pna") === "1");
        const okTerm = !term || text.includes(term);
        return okYear && okTopic && okSource && okTerm;
      });

      const pageCount = Math.max(1, Math.ceil(matching.length / pageSize));
      currentPage = Math.min(Math.max(1, currentPage), pageCount);
      const start = (currentPage - 1) * pageSize;
      const visible = new Set(matching.slice(start, start + pageSize));
      cards.forEach((card) => { card.hidden = !visible.has(card); });

      const shown = matching.length;
      if (counter) counter.textContent = String(shown);
      if (range) {
        if (!shown) {
          range.textContent = "Nenhuma questão para os filtros atuais";
        } else if (pageSize === 1) {
          range.textContent = `Questão ${currentPage} de ${shown}`;
        } else {
          range.textContent = `Mostrando ${start + 1}–${Math.min(start + pageSize, shown)} de ${shown}`;
        }
      }
      currentEls.forEach((el) => { el.textContent = String(currentPage); });
      totalEls.forEach((el) => { el.textContent = String(pageCount); });
      prevButtons.forEach((btn) => { btn.disabled = currentPage <= 1; });
      nextButtons.forEach((btn) => { btn.disabled = currentPage >= pageCount; });
      if (empty) empty.classList.toggle("is-visible", shown === 0);

      if (scrollToGrid && grid) {
        const top = grid.getBoundingClientRect().top + window.scrollY - 88;
        window.scrollTo({ top, behavior: "smooth" });
      }
    };

    const resetPage = () => {
      currentPage = 1;
      apply();
    };

    if (search) {
      search.addEventListener("input", () => {
        term = normalizeText(search.value.trim());
        resetPage();
      });
    }

    yearChips.forEach((chip) => {
      chip.addEventListener("click", () => {
        year = chip.getAttribute("data-quest-year") || "todos";
        yearChips.forEach((c) => c.setAttribute("aria-pressed", String(c === chip)));
        resetPage();
      });
    });
    topicChips.forEach((chip) => {
      chip.addEventListener("click", () => {
        topic = chip.getAttribute("data-quest-topic") || "todos";
        topicChips.forEach((c) => c.setAttribute("aria-pressed", String(c === chip)));
        resetPage();
      });
    });
    sourceChips.forEach((chip) => {
      chip.addEventListener("click", () => {
        source = chip.getAttribute("data-quest-source") || "todos";
        sourceChips.forEach((c) => c.setAttribute("aria-pressed", String(c === chip)));
        resetPage();
      });
    });

    prevButtons.forEach((btn) => btn.addEventListener("click", () => {
      if (currentPage > 1) {
        currentPage -= 1;
        apply(true);
      }
    }));
    nextButtons.forEach((btn) => btn.addEventListener("click", () => {
      if (currentPage < Math.max(1, Math.ceil(matching.length / pageSize))) {
        currentPage += 1;
        apply(true);
      }
    }));

    cards.forEach((card) => {
      card.querySelectorAll("input[data-alternative]").forEach((radio) => {
        radio.addEventListener("change", () => {
          const id = card.getAttribute("data-question-id");
          const answers = getRespostas();
          answers[id] = radio.value;
          saveRespostas(answers);
          paintAnswers();
        });
      });
    });

    doc.querySelectorAll(".question-card [data-clear-choice]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const card = btn.closest(".question-card");
        if (!card) return;
        const id = card.getAttribute("data-question-id");
        const answers = getRespostas();
        delete answers[id];
        saveRespostas(answers);
        card.querySelectorAll("input[data-alternative]").forEach((radio) => { radio.checked = false; });
        paintAnswers();
      });
    });

    doc.querySelectorAll(".question-card [data-reveal]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const card = btn.closest(".question-card");
        if (card) setAnswer(card, btn.getAttribute("aria-pressed") !== "true");
      });
    });
    if (revealAll) revealAll.addEventListener("click", () => cards.forEach((c) => setAnswer(c, true)));
    if (hideAll) hideAll.addEventListener("click", () => cards.forEach((c) => setAnswer(c, false)));

    const doneButtons = [...doc.querySelectorAll("[data-qdone]")];
    const paintDone = () => {
      const progress = getQuestaoProgress();
      let count = 0;
      doneButtons.forEach((btn) => {
        const id = btn.getAttribute("data-qdone");
        const done = Boolean(progress[id]);
        if (done) count += 1;
        btn.classList.toggle("is-done", done);
        btn.classList.toggle("btn--gold", !done);
        btn.setAttribute("aria-pressed", String(done));
        btn.textContent = done ? "Estudada ✓" : "Marcar como estudada";
      });
      doneEls.forEach((el) => { el.textContent = String(count); });
      if (bar) bar.style.width = total ? `${Math.min(100, (count / total) * 100)}%` : "0%";
    };

    doneButtons.forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = btn.getAttribute("data-qdone");
        if (!id) return;
        const progress = getQuestaoProgress();
        if (progress[id]) delete progress[id];
        else progress[id] = Date.now();
        localStorage.setItem(QUESTOES_KEY, JSON.stringify(progress));
        paintDone();
      });
    });

    doc.addEventListener("keydown", (ev) => {
      if (ev.key === "/" && search && doc.activeElement !== search) {
        ev.preventDefault();
        search.focus();
      }
    });

    paintDone();
    paintAnswers();
    apply();
  }

  /* ---------- inicialização ---------- */
  initTheme();
  paintProgress();
  initReadingProgress();
  initSidebar();
  initAnchors();
  initScrollSpy();
  initCompleteButton();
  initIndex();
  initQuestions();

  doc.querySelectorAll("[data-theme-toggle]").forEach((btn) => btn.addEventListener("click", toggleTheme));

  const printBtn = doc.querySelector("[data-print]");
  if (printBtn) printBtn.addEventListener("click", () => window.print());

  // Apenas o rodapé usa este marcador; os cards de questões têm atributo próprio.
  doc.querySelectorAll("span[data-year]").forEach((el) => {
    if (!el.textContent.trim()) el.textContent = String(new Date().getFullYear());
  });
})();
