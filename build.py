#!/usr/bin/env python3
"""Gera a apostila HTML a partir dos fragmentos em src/ e dos metadados em data/partes.json."""

from __future__ import annotations

import html
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "partes.json"
QUESTOES_DATA = ROOT / "data" / "questoes.json"
SRC = ROOT / "src"
OUT = ROOT / "partes"
PDF = "resumo curso h.pdf"

BRAND_ICON = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="8.2"/><path d="M12 3.8v2M12 18.2v2M3.8 12h2M18.2 12h2"/><path d="M14.9 9.1l-1.6 4.2-4.2 1.6 1.6-4.2 4.2-1.6Z"/></svg>"""

ICON_BOOK = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v16H6.5A2.5 2.5 0 0 0 4 21.5v-16Z"/><path d="M4 18.5A2.5 2.5 0 0 1 6.5 16H20"/></svg>"""
ICON_CLOCK = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 1.8"/></svg>"""
ICON_TAG = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 4h7l9 9-7 7-9-9V4Z"/><circle cx="8.2" cy="8.2" r="1.3"/></svg>"""
ICON_PDF = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 3h8l4 4v14H6V3Z"/><path d="M14 3v4h4M9 12h6M9 16h6"/></svg>"""
ICON_CHECK = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m5 12.5 4.5 4.5L19 7"/></svg>"""
ICON_SUN = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2.2M12 19.3v2.2M4.6 4.6l1.6 1.6M17.8 17.8l1.6 1.6M2.5 12h2.2M19.3 12h2.2M4.6 19.4l1.6-1.6M17.8 6.2l1.6-1.6"/></svg>"""
ICON_PRINT = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 8V3h10v5"/><rect x="4" y="8" width="16" height="9" rx="2"/><path d="M7 14h10v7H7z"/></svg>"""
ICON_MENU = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>"""
ICON_QUEST = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 4.5h11l3 3V20H5V4.5Z"/><path d="M8 9h7M8 12.5h7M8 16h4"/><path d="M16 4.5V8h3"/></svg>"""

THEME_SCRIPT = """<script>
  (() => {
    try {
      const stored = localStorage.getItem("apostila-praticagem-tema");
      const dark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
      document.documentElement.setAttribute("data-theme", stored || (dark ? "dark" : "light"));
    } catch (e) {}
  })();
</script>"""

FAVICON = (
    "data:image/svg+xml,"
    "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E"
    "%3Crect width='64' height='64' rx='14' fill='%230a2238'/%3E"
    "%3Ccircle cx='32' cy='32' r='19' fill='none' stroke='%23d9ad58' stroke-width='2'/%3E"
    "%3Cpath d='M39 23l-5 11-11 5 5-11 11-5z' fill='%23d9ad58'/%3E"
    "%3C/svg%3E"
)
FAVICON = FAVICON.replace("\n", "")


def slugify(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE).strip().lower()
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-{2,}", "-", text)
    return text or "secao"


def reading_minutes(fragment: str) -> int:
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", fragment, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    words = len(re.findall(r"\w+", text, flags=re.UNICODE))
    return max(1, round(words / 210))


def process_headings(fragment: str):
    """Garante ids únicos em h2/h3 e devolve o fragmento e o sumário (h2)."""
    used: set[str] = set()
    toc: list[tuple[str, str]] = []

    def repl(match: re.Match) -> str:
        level, attrs, inner = match.group(1), match.group(2) or "", match.group(3)
        id_match = re.search(r'id="([^"]+)"', attrs)
        if id_match:
            hid = id_match.group(1)
        else:
            base = slugify(inner)
            hid = base
            n = 2
            while hid in used:
                hid = f"{base}-{n}"
                n += 1
            attrs = f' id="{hid}"' + attrs
        used.add(hid)
        if level == "2":
            toc.append((hid, re.sub(r"<[^>]+>", "", inner).strip()))
        return f"<h{level}{attrs}>{inner}</h{level}>"

    fragment = re.sub(r"<h([23])(\s[^>]*)?>(.*?)</h\1>", repl, fragment, flags=re.S | re.I)
    return fragment, toc


def pages_label(pages: list[int]) -> str:
    if pages[0] == pages[1]:
        return f"p. {pages[0]}"
    return f"pp. {pages[0]}–{pages[1]}"


def pdf_link(pages: list[int], prefix: str, pdf_file: str | None = None) -> str:
    fname = (pdf_file or PDF).replace(' ', '%20')
    return f"{prefix}{fname}#page={pages[0]}"


def module_name(meta: dict, module_id: str) -> str:
    for m in meta["modulos"]:
        if m["id"] == module_id:
            return m["nome"]
    return module_id


def sidebar(meta: dict, active_id: str | None, prefix: str) -> str:
    groups = []
    for mod in meta["modulos"]:
        items = [p for p in meta["partes"] if p["modulo"] == mod["id"]]
        if not items:
            continue
        lis = []
        for p in items:
            is_active = p["id"] == active_id
            cls = ' class="is-active" aria-current="page"' if is_active else ""
            lis.append(
                f'<li><a href="{prefix}{p["id"]}.html"{cls} data-part-id="{p["id"]}">'
                f'<span class="part-nav__num">{p["numero"]}</span>'
                f'<span>{html.escape(p["titulo"])}</span></a></li>'
            )
        groups.append(
            f'<div class="sidebar__group"><p class="sidebar__group-title">{html.escape(mod["nome"])}</p>'
            f'<ul class="part-nav">{"".join(lis)}</ul></div>'
        )
    total = len(meta["partes"])
    return f"""
      <aside class="sidebar" id="sumario">
        <p class="sidebar__eyebrow">Sumário da apostila</p>
        {''.join(groups)}
        <div class="sidebar__progress">
          <p><span>Seu progresso</span> <strong><span data-progress-total="{total}">00</span>/{total:02d}</strong></p>
          <div class="bar"><div class="bar__fill"></div></div>
        </div>
      </aside>
      <div class="scrim"></div>"""


def topbar(prefix: str, label: str, show_nav: bool, active: str = "") -> str:
    nav_btn = (
        f'<button class="icon-btn nav-toggle" type="button" data-nav-toggle aria-expanded="false" aria-controls="sumario" aria-label="Abrir sumário">{ICON_MENU}</button>'
        if show_nav
        else ""
    )

    tabs = [
        ("apostila", f"{prefix}index.html", "Apostila", ICON_BOOK, ""),
        ("questoes", f"{prefix}questoes.html", "Questões", ICON_QUEST, " data-topbar-questoes"),
        ("programa", f"{prefix}conteudo-programatico.html", "Programa", ICON_CLOCK, ""),
        ("bibliografia", f"{prefix}cobertura-bibliografica.html", "Bibliografia", ICON_BOOK, ""),
    ]
    tab_links = "".join(
        f'<a class="topbar-nav__link{" is-active" if active == key else ""}" href="{href}"{attrs}>{icon}<span>{text}</span></a>'
        for key, href, text, icon, attrs in tabs
    )

    return f"""
    <header class="topbar">
      {nav_btn}
      <a class="brand" href="{prefix}index.html">
        <span class="brand__mark">{BRAND_ICON}</span>
        <span>Apostila de Praticagem<small>Estudos para o prático</small></span>
      </a>
      <div class="topbar__spacer"></div>
      <nav class="topbar-nav" aria-label="Navegação principal">{tab_links}</nav>
      <span class="topbar__label">{html.escape(label)}</span>
      <button class="icon-btn" type="button" data-print title="Imprimir / salvar em PDF" aria-label="Imprimir ou salvar em PDF">{ICON_PRINT}</button>
      <button class="icon-btn" type="button" data-theme-toggle aria-label="Alternar tema">{ICON_SUN}</button>
    </header>"""


def page_shell(
    title: str,
    description: str,
    body_class: str,
    data_attrs: str,
    prefix: str,
    content: str,
    *,
    extra_head: str = "",
    extra_scripts: str = "",
) -> str:
    css = (ROOT / "assets" / "style.css").read_text(encoding="utf-8")
    js = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
    # escape closing tags for safe inlining
    css = css.replace("</style", "<\\/style")
    js = js.replace("</script", "<\\/script")
    return f"""<!DOCTYPE html>
<html lang="pt-BR" data-theme="light">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light dark">
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(description)}">
  <link rel="icon" href="{FAVICON}">
  {extra_head}
  <style>
{css}
  </style>
  {THEME_SCRIPT}
</head>
<body class="{body_class}"{data_attrs}>
  <a class="skip-link" href="#conteudo">Pular para o conteúdo</a>
  <div class="read-progress" aria-hidden="true"></div>
  {content}
  <script>
{js}
  </script>
  {extra_scripts}
</body>
</html>
"""


def build_part(part: dict, meta: dict, index: int) -> str:
    pid = part["id"]
    source = SRC / f"{pid}.html"
    missing = not source.exists()
    fragment = source.read_text(encoding="utf-8") if source.exists() else (
        '<section class="section"><h2>Conteúdo em produção</h2>'
        "<p>Este capítulo ainda está sendo redigido.</p></section>"
    )
    fragment, toc = process_headings(fragment)
    minutes = reading_minutes(fragment)
    pages = part["paginas"]
    plabel = pages_label(pages)
    src_link = pdf_link(pages, "../../", part.get("pdfFile"))
    tags = "".join(f"<span>{html.escape(t)}</span>" for t in part.get("tags", []))
    mod = module_name(meta, part["modulo"])

    toc_html = ""
    if len(toc) >= 2:
        items = "".join(f'<li><a href="#{hid}">{html.escape(text)}</a></li>' for hid, text in toc)
        toc_html = f"""
      <nav class="toc-card" aria-label="Neste capítulo">
        <div>
          <h2>Neste capítulo</h2>
          <p>{len(toc)} seções · leitura estimada de {minutes} min</p>
        </div>
        <ol>{items}</ol>
      </nav>"""

    prev_part = meta["partes"][index - 1] if index > 0 else None
    next_part = meta["partes"][index + 1] if index < len(meta["partes"]) - 1 else None
    nav_links = []
    if prev_part:
        nav_links.append(
            f'<a class="prev" href="{prev_part["id"]}.html"><small>← Capítulo anterior</small>'
            f'<span>{prev_part["numero"]} · {html.escape(prev_part["titulo"])}</span></a>'
        )
    else:
        nav_links.append('<span></span>')
    if next_part:
        nav_links.append(
            f'<a class="next" href="{next_part["id"]}.html"><small>Próximo capítulo →</small>'
            f'<span>{next_part["numero"]} · {html.escape(next_part["titulo"])}</span></a>'
        )
    else:
        nav_links.append('<span></span>')

    content = f"""
  {topbar('../', f'Capítulo {part["numero"]} de {len(meta["partes"]):02d}', True, active='apostila')}
  <div class="layout">
    {sidebar(meta, pid, '')}
    <main class="main" id="conteudo">
      <div class="content">
        <nav class="breadcrumb" aria-label="Trilha de navegação">
          <a href="../index.html">Apostila</a>
          <span aria-hidden="true">/</span>
          <span>{html.escape(mod)}</span>
          <span aria-hidden="true">/</span>
          <span>Capítulo {part["numero"]}</span>
        </nav>

        <header class="part-hero">
          <span class="part-hero__num" aria-hidden="true">{part["numero"]}</span>
          <span class="part-hero__kicker">{html.escape(part["eyebrow"])}</span>
          <h1>{html.escape(part["titulo"])}</h1>
          <p class="part-hero__subtitle">{html.escape(part["subtitulo"])}</p>
          <div class="hero-tags">{tags}</div>
          <div class="part-hero__meta">
            <span>{ICON_BOOK} {plabel} da fonte</span>
            <span>{ICON_CLOCK} ~{minutes} min de leitura</span>
            <span>{ICON_TAG} {html.escape(mod)}</span>
            <span>{ICON_PDF} <a href="{src_link}" target="_blank" rel="noopener">abrir PDF original</a></span>
          </div>
        </header>
        {toc_html}

        <article class="chapter-body">
{fragment}
        </article>

        <section class="chapter-end">
          <p class="section-kicker">Fim do capítulo</p>
          <h2>{html.escape(part["titulo"])}</h2>
          <p>Conteúdo sintetizado de <strong>{html.escape(part["fonteNome"])}</strong>, {plabel} da fonte. Consulte o original para detalhes, figuras e redação normativa.</p>
          <button class="btn btn--gold" type="button" data-complete="{pid}" aria-pressed="false">{ICON_CHECK}<span>Marcar como concluído</span></button>
        </section>

        <nav class="chapter-nav" aria-label="Navegação entre capítulos">
          {''.join(nav_links)}
        </nav>

        <footer class="site-footer">
          <p><strong>Apostila de Praticagem</strong> · material de estudo gerado a partir de <em>{PDF}</em>.</p>
          <p>Não substitui as publicações oficiais (PNA, NORMAM, RIPEAM, CIS, cartas e avisos). Confirme sempre os dados críticos na fonte vigente.</p>
        </footer>
      </div>
    </main>
  </div>"""

    return page_shell(
        f'{part["numero"]} · {part["titulo"]} — Apostila de Praticagem',
        part["subtitulo"],
        "part-page",
        f' data-part="{pid}"',
        "../",
        content,
    )


def render_question_body(question: dict) -> str:
    parts = []
    for paragraph in question["statement"]:
        if paragraph == "[[TABELA]]" and question.get("tableHtml"):
            parts.append(question["tableHtml"])
        elif paragraph == "[[FIGURA]]" and question.get("figure"):
            alt = html.escape(question.get("figureAlt") or "Figura do enunciado", quote=True)
            parts.append(
                f'<figure class="question-figure"><img src="{html.escape(question["figure"], quote=True)}" '
                f'alt="{alt}" loading="lazy"><figcaption>Figura do enunciado · fonte: {html.escape(question["source"])}</figcaption></figure>'
            )
        else:
            parts.append(f"<p>{html.escape(paragraph)}</p>")
    return "".join(parts)


def build_questoes(data: dict) -> str:
    questions = data.get("questoes", [])
    years = sorted({q["year"] for q in questions})
    topics = sorted({q["topic"] for q in questions})
    total = len(questions)
    page_size = 1
    total_pages = max(1, (total + page_size - 1) // page_size)
    page_label = "Questão" if page_size == 1 else "Página"
    prev_label = "← Questão anterior" if page_size == 1 else "← Anterior"
    next_label = "Próxima questão →" if page_size == 1 else "Próxima →"

    pagination_html = f"""
      <nav class="questions-pagination" aria-label="Navegação entre questões">
        <button class="btn btn--small btn--ghost" type="button" data-page-prev disabled>{prev_label}</button>
        <span>{page_label} <strong data-page-current>1</strong> de <strong data-page-total>{total_pages}</strong></span>
        <button class="btn btn--small btn--ghost" type="button" data-page-next>{next_label}</button>
      </nav>"""

    year_chips = ['<button class="filter-chip" type="button" data-quest-year="todos" aria-pressed="true">Todos os anos</button>']
    for year in years:
        count = sum(1 for q in questions if q["year"] == year)
        year_chips.append(
            f'<button class="filter-chip" type="button" data-quest-year="{html.escape(year)}" aria-pressed="false">{html.escape(year)} <small>{count}</small></button>'
        )
    topic_chips = ['<button class="filter-chip" type="button" data-quest-topic="todos" aria-pressed="true">Todos os temas</button>']
    for topic in topics:
        count = sum(1 for q in questions if q["topic"] == topic)
        topic_chips.append(
            f'<button class="filter-chip" type="button" data-quest-topic="{html.escape(topic, quote=True)}" aria-pressed="false">{html.escape(topic)} <small>{count}</small></button>'
        )

    cards = []
    for q in questions:
        qid = f'q-{q["year"]}-{q["num"]}'
        answer = q.get("answer")
        answer_upper = answer.upper() if answer else ""
        if answer:
            answer_html = (
                f'<div class="answer-box" data-answer-box hidden>'
                f'<span class="answer-box__label">Gabarito: <strong>{answer_upper}</strong></span>'
                f'<span>{html.escape(q.get("answerText", ""))}</span>'
                f'<span class="answer-box__result" data-answer-result></span></div>'
            )
            reveal_btn = (
                f'<button class="btn btn--small btn--gold" type="button" data-reveal aria-pressed="false">'
                f'Verificar / gabarito</button>'
            )
        else:
            answer_html = (
                '<div class="answer-box answer-box--annulled">'
                '<span class="answer-box__label">Questão anulada</span>'
                '<span>Sem gabarito vigente na prova original.</span></div>'
            )
            reveal_btn = ""

        note_html = ""
        if q.get("note"):
            note_html = (
                f'<div class="question-note"><strong>Observação da banca:</strong> {html.escape(q["note"])}</div>'
            )

        alternatives = "".join(
            f'<li class="alternative" data-letter="{html.escape(a["letter"], quote=True)}">'
            f'<label class="alternative__label">'
            f'<input type="radio" name="resposta-{qid}" value="{html.escape(a["letter"], quote=True)}" '
            f'data-alternative aria-label="Alternativa {html.escape(a["letter"].upper())}">'
            f'<span class="alternative__letter">{html.escape(a["letter"])}</span>'
            f'<span class="alternative__text">{html.escape(a["text"])}</span>'
            f'</label></li>'
            for a in q["alternatives"]
        )

        badges = [f'<span class="badge">{html.escape(q["year"])}</span>',
                  f'<span class="badge badge--topic">{html.escape(q["topic"])}</span>']
        if q.get("pontos"):
            label = "ponto" if q["pontos"].replace(",", ".") == "1.0" else "pontos"
            badges.append(f'<span class="badge badge--muted">{html.escape(q["pontos"])} {label}</span>')
        if q.get("annulled"):
            badges.append('<span class="badge badge--annulled">Anulada</span>')

        search_text = " ".join(
            [q["year"], str(q["num"]), q["topic"]]
            + q["statement"]
            + [a["text"] for a in q["alternatives"]]
            + [q.get("answerText", ""), q.get("note") or ""]
        )
        source_url = f'../{quote(q["source"])}#page={q["page"]}'

        cards.append(f"""
        <article class="question-card{' is-annulled' if q.get('annulled') else ''}" id="{qid}"
                 data-question-id="{qid}" data-question-year="{html.escape(q['year'])}"
                 data-topic="{html.escape(q['topic'], quote=True)}"
                 data-answer-letter="{html.escape(answer or '', quote=True)}"
                 data-search="{html.escape(search_text.lower(), quote=True)}">
          <header class="question-card__head">
            <span class="question-card__num">Q{int(q['num']):02d}</span>
            <div class="question-card__badges">{''.join(badges)}</div>
          </header>
          <div class="question-card__body">
            {render_question_body(q)}
            {note_html}
            <ol class="alternatives">{alternatives}</ol>
            {answer_html}
          </div>
          <footer class="question-actions">
            {reveal_btn}
            {'' if not answer else '<button class="btn btn--small btn--text" type="button" data-clear-choice>Limpar escolha</button>'}
            <button class="btn btn--small btn--ghost" type="button" data-qdone="{qid}" aria-pressed="false">Marcar como estudada</button>
            <a class="btn btn--small btn--text" href="{source_url}" target="_blank" rel="noopener">PDF original · p. {q['page']}</a>
          </footer>
        </article>""")

    content = f"""
  {topbar('', f'Banco de questões · {total}', False, active='questoes')}
  <main class="main questions-main" id="conteudo">
    <div class="content">
      <header class="questions-hero" data-questoes-page>
        <span class="part-hero__kicker">Banco de questões · provas de praticagem</span>
        <h1>Questões de <em>2006 a 2012</em></h1>
        <p>Os enunciados das quatro provas organizados para estudo: texto digitado, figuras necessárias recortadas das provas e equações em LaTeX. Navegue de questão em questão, selecione uma alternativa e confira o gabarito.</p>
        <div class="questions-hero__stats">
          <div><b>{total}</b><span>questões</span></div>
          <div><b>{len(years)}</b><span>provas</span></div>
          <div><b>{len(topics)}</b><span>temas</span></div>
          <div><b data-questoes-done>0</b><span>estudadas</span></div>
        </div>
        <div class="questions-hero__actions">
          <a class="btn btn--ghost" href="index.html">← Voltar à apostila</a>
          <button class="btn btn--gold" type="button" data-reveal-all>Mostrar todos os gabaritos</button>
        </div>
      </header>

      <section class="questions-toolbar" aria-label="Buscar questões">
        <h2>Banco de questões</h2>
        <label class="search">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.2"/><path d="m15.3 15.3 4.2 4.2"/></svg>
          <input type="search" placeholder="Buscar por tema, palavra, norma ou número…" aria-label="Buscar questões" data-questoes-search>
        </label>
      </section>

      <section class="questions-filters" aria-label="Filtrar questões">
        <div class="filter-group">
          <p class="filter-group__label">Ano da prova</p>
          <div class="filter-row">{''.join(year_chips)}</div>
        </div>
        <div class="filter-group">
          <p class="filter-group__label">Tema</p>
          <div class="filter-row">{''.join(topic_chips)}</div>
        </div>
      </section>

      <section class="questions-progress" aria-label="Progresso de estudo">
        <div class="questions-progress__info">
          <p><strong><span data-questoes-count>{total}</span> questões encontradas</strong> · <span data-questoes-answered>0</span> respondidas · <span data-questoes-done>0</span>/{total} estudadas</p>
          <p class="questions-progress__range" data-questoes-range>{(f'Questão 1 de {total}' if page_size == 1 else f'Mostrando 1–{min(page_size, total)} de {total}')}</p>
        </div>
        <div class="bar"><div class="bar__fill" data-questoes-bar></div></div>
        <button class="btn btn--small btn--ghost" type="button" data-hide-all>Ocultar gabaritos</button>
        {pagination_html}
      </section>

      <div class="questions-grid" data-questions-grid>{''.join(cards)}</div>
      <div class="no-results" data-questoes-empty>Nenhuma questão encontrada com esses filtros. Tente outro termo ou tema.</div>
      <div class="questions-pagination questions-pagination--bottom" data-questoes-pagination-bottom>{pagination_html}</div>

      <footer class="site-footer">
        <p><strong>Apostila de Praticagem</strong> · banco reunido de <em>praticante_de_pratico_de_2006.pdf</em>, <em>praticante_de_pratico_08.pdf</em>, <em>prova_objetiva_com_gabarito_2011_1.pdf</em> e <em>PROVAROSA2012-GABARITODEFINITIVO-22FEV2013.pdf</em>.</p>
        <p>Questões anuladas foram mantidas e identificadas. Confira sempre a redação e o gabarito na publicação oficial vigente.</p>
      </footer>
    </div>
  </main>"""

    katex_head = '<link rel="stylesheet" href="assets/vendor/katex/katex.min.css">'
    katex_scripts = """
  <script src="assets/vendor/katex/katex.min.js"></script>
  <script src="assets/vendor/katex/contrib/auto-render.min.js"></script>
  <script>
    if (window.renderMathInElement) {
      renderMathInElement(document.querySelector("[data-questoes-page]") || document.body, {
        delimiters: [{ left: "$", right: "$", display: false }],
        throwOnError: false,
        ignoredTags: ["script", "noscript", "style", "textarea"]
      });
    }
  </script>"""
    return page_shell(
        f"Banco de questões 2006–2012 — Apostila de Praticagem",
        "Questões das provas de praticagem de 2006, 2008, 2011 e 2012, com figuras, tabelas, equações em LaTeX e gabaritos.",
        "questoes-page",
        f' data-questoes-page data-questoes-total="{total}" data-questoes-page-size="{page_size}"',
        "",
        content,
        extra_head=katex_head,
        extra_scripts=katex_scripts,
    )


def build_index(meta: dict, minutes_by_part: dict[str, int], question_total: int = 0) -> str:
    total = len(meta["partes"])
    total_min = sum(minutes_by_part.values())
    cards = []
    for part in meta["partes"]:
        tags = " ".join(part.get("tags", []))
        data_tags = html.escape(f'{part["titulo"]} {part["descricao"]} {tags}'.lower(), quote=True)
        cards.append(
            f"""
        <a class="part-card reveal" href="partes/{part["id"]}.html" data-part-id="{part["id"]}" data-module="{part["modulo"]}" data-tags="{data_tags}">
          <span class="done-badge">{ICON_CHECK} concluído</span>
          <div class="part-card__top">
            <span class="part-card__num">CAP. {part["numero"]}</span>
            <span class="part-card__module">{html.escape(module_name(meta, part["modulo"]))}</span>
          </div>
          <h3>{html.escape(part["titulo"])}</h3>
          <p>{html.escape(part["descricao"])}</p>
          <div class="part-card__meta">
            <span>{ICON_BOOK} {pages_label(part["paginas"])}</span>
            <span>{ICON_CLOCK} {minutes_by_part.get(part["id"], 1)} min</span>
          </div>
        </a>"""
        )

    chips = [
        '<button class="filter-chip" type="button" data-filter="todos" aria-pressed="true">Todos os módulos</button>'
    ]
    for mod in meta["modulos"]:
        chips.append(
            f'<button class="filter-chip" type="button" data-filter="{mod["id"]}" aria-pressed="false">{html.escape(mod["nome"])}</button>'
        )

    content = f"""
  {topbar('', 'Biblioteca de estudos', False, active='apostila')}
  <header class="index-hero">
    <div class="index-hero__inner">
      <span class="index-hero__kicker">Curso de praticagem · edição de estudo</span>
      <h1>Apostila de <em>Praticagem</em></h1>
      <p class="index-hero__lead">Uma travessia organizada por assunto pelos fundamentos de arquitetura naval, manobra, navegação, legislação e meteorologia — com sínteses, quadros, fórmulas, diagramas e perguntas de revisão.</p>
      <div class="index-hero__actions">
        <a class="btn btn--gold" href="questoes.html">{ICON_QUEST} Banco de questões ({question_total})</a>
        <a class="btn btn--ghost" href="partes/{meta["partes"][0]["id"]}.html">Começar pelo capítulo 01 →</a>
        <a class="btn btn--ghost" href="#biblioteca">Explorar os {total} capítulos</a>
        <a class="btn btn--ghost" href="conteudo-programatico.html">Conteúdo programático</a>
        <a class="btn btn--ghost" href="cobertura-bibliografica.html">Cobertura bibliográfica</a>
      </div>
      <div class="index-hero__stats">
        <div><b>{total}</b><span>capítulos</span></div>
        <div><b>{question_total}</b><span>questões de prova</span></div>
        <div><b>{meta["totalPaginasFonte"]}</b><span>páginas de fonte</span></div>
        <div><b>{len(meta["modulos"])}</b><span>módulos</span></div>
        <div><b>~{total_min}</b><span>minutos de leitura</span></div>
        <div><b data-index-progress="{total}">0/{total}</b><span>concluídos</span></div>
      </div>
    </div>
  </header>

  <main class="index-main" id="biblioteca">
    <div class="index-toolbar">
      <h2>Biblioteca de capítulos</h2>
      <label class="search">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.2"/><path d="m15.3 15.3 4.2 4.2"/></svg>
        <input type="search" placeholder="Buscar assunto, termo ou norma…" aria-label="Buscar capítulos" data-search>
      </label>
    </div>
    <div class="filters" aria-label="Filtrar por módulo">
      {''.join(chips)}
    </div>
    <div class="parts-grid">
      {''.join(cards)}
    </div>
    <div class="no-results">Nenhum capítulo encontrado para esta busca. Tente outro termo ou módulo.</div>

    <aside class="index-note">
      <p><strong>Como esta apostila foi feita.</strong> O conteúdo foi extraído de <em>{PDF}</em> (373 páginas digitalizadas, com OCR) e reorganizado por assunto em linguagem de estudo, com complementos pontuais das referências disponíveis na pasta (PNA Vol. II, Crenshaw e <em>Tug Use in Port</em>, edições indicadas). O material original mistura português e inglês e contém ruído de digitalização.</p>
      <p><strong>Uso responsável.</strong> Esta é uma síntese didática, não uma publicação oficial. Antes de aplicar qualquer procedimento, confirme requisitos, números e redação vigente nas fontes oficiais: PNA, NORMAM/DPC, RIPEAM, CIS, Lista de Faróis, Roteiro e avisos aos navegantes. Veja o <a href="conteudo-programatico.html"><strong>conteúdo programático (NORMAM-311, Anexo 2-A)</strong></a> mapeado capítulo a capítulo e a <a href="cobertura-bibliografica.html"><strong>cobertura bibliográfica</strong></a> estimada. O botão de impressão permite salvar cada capítulo em PDF.</p>
    </aside>

    <footer class="site-footer">
      <p><strong>Apostila de Praticagem</strong> · <span data-year></span> · estudo individual e sem fins comerciais.</p>
      <p>Atalho de busca: pressione <kbd>/</kbd>. O progresso fica salvo neste navegador.</p>
    </footer>
  </main>"""

    return page_shell(
        "Apostila de Praticagem — do casco ao passadiço",
        "Apostila de estudos para praticagem: arquitetura naval, manobra, navegação, legislação, meteorologia e GMDSS.",
        "index-page",
        "",
        "",
        content,
    )


def main() -> None:
    meta = json.loads(DATA.read_text(encoding="utf-8"))
    questoes = json.loads(QUESTOES_DATA.read_text(encoding="utf-8")) if QUESTOES_DATA.exists() else {"questoes": []}
    question_total = len(questoes.get("questoes", []))
    OUT.mkdir(exist_ok=True)
    minutes_by_part: dict[str, int] = {}
    missing = []

    for i, part in enumerate(meta["partes"]):
        source = SRC / f"{part['id']}.html"
        if not source.exists():
            missing.append(part["id"])
        fragment = source.read_text(encoding="utf-8") if source.exists() else ""
        minutes_by_part[part["id"]] = reading_minutes(fragment)
        (OUT / f"{part['id']}.html").write_text(build_part(part, meta, i), encoding="utf-8")
        print(f"  ok  partes/{part['id']}.html ({minutes_by_part[part['id']]} min)")

    (ROOT / "index.html").write_text(build_index(meta, minutes_by_part, question_total), encoding="utf-8")
    print(f"  ok  index.html ({len(meta['partes'])} capítulos, ~{sum(minutes_by_part.values())} min)")

    (ROOT / "questoes.html").write_text(build_questoes(questoes), encoding="utf-8")
    print(f"  ok  questoes.html ({question_total} questões)")
    if missing:
        print(f"\n  ATENÇÃO: fragmentos ausentes em src/: {', '.join(missing)}")


if __name__ == "__main__":
    main()
