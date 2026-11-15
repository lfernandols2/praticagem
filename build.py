#!/usr/bin/env python3
"""Gera a apostila HTML a partir dos fragmentos em src/ e dos metadados em data/partes.json."""

from __future__ import annotations

import html
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "partes.json"
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


def topbar(prefix: str, label: str, show_nav: bool) -> str:
    nav_btn = (
        f'<button class="icon-btn nav-toggle" type="button" data-nav-toggle aria-expanded="false" aria-controls="sumario" aria-label="Abrir sumário">{ICON_MENU}</button>'
        if show_nav
        else ""
    )
    return f"""
    <header class="topbar">
      {nav_btn}
      <a class="brand" href="{prefix}index.html">
        <span class="brand__mark">{BRAND_ICON}</span>
        <span>Apostila de Praticagem<small>Estudos para o prático</small></span>
      </a>
      <div class="topbar__spacer"></div>
      <span class="topbar__label">{html.escape(label)}</span>
      <button class="icon-btn" type="button" data-print title="Imprimir / salvar em PDF" aria-label="Imprimir ou salvar em PDF">{ICON_PRINT}</button>
      <button class="icon-btn" type="button" data-theme-toggle aria-label="Alternar tema">{ICON_SUN}</button>
    </header>"""


def page_shell(title: str, description: str, body_class: str, data_attrs: str, prefix: str, content: str) -> str:
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
  {topbar('../', f'Capítulo {part["numero"]} de {len(meta["partes"]):02d}', True)}
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


def build_index(meta: dict, minutes_by_part: dict[str, int]) -> str:
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
  {topbar('', 'Biblioteca de estudos', False)}
  <header class="index-hero">
    <div class="index-hero__inner">
      <span class="index-hero__kicker">Curso de praticagem · edição de estudo</span>
      <h1>Apostila de <em>Praticagem</em></h1>
      <p class="index-hero__lead">Uma travessia organizada por assunto pelos fundamentos de arquitetura naval, manobra, navegação, legislação e meteorologia — com sínteses, quadros, fórmulas, diagramas e perguntas de revisão.</p>
      <div class="index-hero__actions">
        <a class="btn btn--gold" href="partes/{meta["partes"][0]["id"]}.html">Começar pelo capítulo 01 →</a>
        <a class="btn btn--ghost" href="#biblioteca">Explorar os {total} capítulos</a>
        <a class="btn btn--ghost" href="conteudo-programatico.html">Conteúdo programático</a>
        <a class="btn btn--ghost" href="cobertura-bibliografica.html">Cobertura bibliográfica</a>
      </div>
      <div class="index-hero__stats">
        <div><b>{total}</b><span>capítulos</span></div>
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

    (ROOT / "index.html").write_text(build_index(meta, minutes_by_part), encoding="utf-8")
    print(f"  ok  index.html ({len(meta['partes'])} capítulos, ~{sum(minutes_by_part.values())} min)")
    if missing:
        print(f"\n  ATENÇÃO: fragmentos ausentes em src/: {', '.join(missing)}")


if __name__ == "__main__":
    main()
