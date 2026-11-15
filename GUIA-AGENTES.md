# Guia de redação dos capítulos — Apostila de Praticagem

Você está redigindo **um ou mais capítulos** de uma apostila HTML de estudos para praticagem. O material-fonte é um PDF digitalizado de 373 páginas (`resumo curso h.pdf`), com OCR ruidoso e mistura de português e inglês. A apostila reorganiza esse conteúdo **por assunto**, em linguagem didática.

## Antes de escrever

1. Leia este guia inteiro.
2. Leia `src/_exemplo.html` para conhecer os componentes visuais disponíveis.
3. Leia o(s) arquivo(s) de fonte indicados no seu briefing, em `fonte/`. Cada arquivo tem marcadores `===== PAGINA N =====` — os números são as páginas do PDF original. Os arquivos têm 40–330 KB: **leia em blocos** (por exemplo, com `offset`/`limit` a cada 400–600 linhas) e vá tomando notas antes de redigir. Não tente carregar um arquivo inteiro de uma vez.
4. Escreva **somente** o(s) fragmento(s) `src/{id}.html` atribuído(s) a você. Não altere `build.py`, `data/partes.json`, CSS, JS, `index.html` nem capítulos de outros agentes.

## Formato de saída

- Arquivo HTML **fragmentado**: sem `<!DOCTYPE>`, `<html>`, `<head>`, `<body>`, `<style>` ou `<script>`.
- O título do capítulo, o hero, o sumário lateral, o sumário interno, a navegação e o rodapé são gerados automaticamente pelo `build.py`. **Não escreva `<h1>` nem repita o título do capítulo.**
- Comece diretamente com `<section class="section" id="...">`.
- Use `<h2>` para seções e `<h3>` para subseções. O build cria ids automáticos caso você os omita, mas prefira criá-los.
- Código HTML válido e identado. Sem Markdown, sem cercas de código, sem comentários de rascunho.
- Classes permitidas: as documentadas abaixo e as presentes em `_exemplo.html`. Não invente CSS nem estilos inline.

## Voz e estilo

- Português do Brasil, registro técnico-didático, direto e claro.
- Explique o termo em inglês na primeira ocorrência: `squat (afundamento dinâmico)`, `wake (esteira)`, `passage planning (planejamento da travessia)`.
- Prefira frases curtas e parágrafos de 2–5 linhas. Use listas e tabelas quando ajudarem a comparar.
- Fale com o leitor praticante: “no passadiço”, “na briefing”, “ao assumir o prático”. Não use primeira pessoa do plural de forma excessiva.
- Preserve a terminologia consagrada e os nomes de normas, artigos, sinais e publicações exatamente como aparecem na fonte.
- Não use emojis.

## Fidelidade ao conteúdo

- **Não invente fatos, números, regras, artigos ou procedimentos.** Use apenas o que está na fonte atribuída (e conhecimento técnico apenas para conectar e explicar o que já está lá).
- O OCR tem erros: letras trocadas, palavras coladas, trechos em inglês truncados. Interprete com cautela; se um dado estiver ilegível ou ambíguo, **omita** ou sinalize a lacuna em uma frase curta (“a fonte está truncada neste ponto”). Nunca “complete” um número normativo por conta própria.
- Não copie parágrafos longos do original. **Traduza, sintetize e reorganize.** Citações literais devem ser curtas e pontuais.
- Indique a origem dos dados específicos com `<span class="src">p. 12</span>` (página do PDF). Feche seções com `<p class="source-line">pp. 10–14</p>` quando fizer sentido.
- Em temas normativos (RIPEAM, NORMAM, LESTA, Tribunal Marítimo, GMDSS, IALA), seja especialmente conservador: prefira a regra geral e os quadros; não invente exceções.

## Profundidade esperada

Para cada capítulo:

- **8 a 14 seções `<h2>`**, com 1.800 a 3.500 palavras no total. Capítulos muito densos podem chegar a 4.000 palavras; não ultrapasse 4.500. O objetivo é síntese útil, não transcrição.
- Abertura com o problema prático e 3 cartões de objetivos (`.grid-3` + `.card`).
- Núcleo conceitual com definições (`.def`), explicações e pelo menos **um quadro/tabela** (`.table-wrap`).
- **1 ou 2 diagramas SVG simples** quando o assunto permitir (geometria, forças, balizamento, luzes, circulação, etc.). Use `_exemplo.html` como base. Se o tema for jurídico ou procedural, um fluxograma simples também vale.
- Pelo menos **um bloco “Na prática” ou “Dica de passadiço”** e um bloco de **erros comuns/atenção** quando a fonte os sugerir.
- Uma seção de **síntese** (`.keyfacts`, `.checklist` ou `.callout--tip`).
- Uma seção final de **revisão** com 5 a 8 perguntas em `<details>` (`.quiz`), com respostas comentadas.
- Feche com uma frase de transição? **Não** — a navegação e o “Fim do capítulo” são gerados automaticamente.

## Componentes disponíveis

Copie a estrutura exata de `src/_exemplo.html`. Resumo:

- `<section class="section" id="slug">` — seção; comece com `<p class="section-kicker">Rótulo</p>` e `<h2>Título</h2>`.
- `<p class="lead">` — parágrafo de abertura.
- `<span class="src">p. 12</span>` — referência de página inline.
- `<p class="source-line">pp. 10–14</p>` — referência ao fim de uma seção.
- `.grid-2`, `.grid-3`, `.grid-4` + `.card` (variantes `.card--accent`, `.card--teal`, `.card__num`).
- `.callout` + variantes `--info`, `--tip`, `--warn`, `--danger`, `--exam`, `--mnemonic`; use `.callout__label` para o rótulo.
- `.def` + `.def__term` — definição destacada.
- `.formula` + `.formula__expr` + `.formula__where`; variante `.formula--light`.
- `.table-wrap` + `<table>` + `<caption>` + `<thead>` + `<tbody>`.
- `.figure` + `<svg>` + `<figcaption>`; classes de SVG: `.diagram-line`, `.diagram-accent`, `.diagram-gold`, `.diagram-label`, `.diagram-label--strong`. Todo SVG precisa de `role="img"`, `<title>` e `<desc>` com ids únicos.
- `.steps` — lista ordenada de procedimento (não use `<ol>` comum dentro dela? use `<ol class="steps">` com `<li><strong>Título.</strong> texto</li>`).
- `.checklist` — lista de conferência (use `<ul class="checklist">`).
- `.example` + `.example__title` — caso prático.
- `.compare` com `.pro` e `.con` — vantagens/limitações.
- `.keyfacts` + `.keyfact` (`<b>` número, `<span>` legenda).
- `.quiz` + `<details><summary>…</summary><div class="quiz__answer"><p>…</p></div></details>`.
- `.tags` (opcional; o hero já gera tags a partir dos metadados).

## Estrutura sugerida

1. **Abertura** — por que importa; objetivos.
2. **Fundamentos e definições** — o vocabulário mínimo.
3. **Núcleo 1** — primeiro grande conceito.
4. **Núcleo 2** — segundo grande conceito.
5. **Núcleo 3** — desdobramentos, exceções, efeitos.
6. **Quadros comparativos** — tabela, prós/contras, critérios.
7. **Na prática** — procedimento, caso, checklist.
8. **Erros comuns / limites** — o que dá errado e por quê.
9. **Síntese** — números-chave, regra de bolso.
10. **Revisão** — perguntas com respostas.

Adapte a estrutura ao assunto. Capítulos normativos podem trocar “núcleo” por “âmbito”, “requisitos”, “procedimento”, “penalidades”; capítulos de meteorologia podem usar “elementos”, “sistemas”, “produtos”.

## Qualidade e verificação

Antes de terminar:

- [ ] O arquivo começa em `<section>` e não contém `<h1>`, `<html>`, `<body>`, `<style>` ou `<script>`.
- [ ] Todas as tags estão fechadas e os `<details>` têm `<summary>`.
- [ ] Cada SVG tem `viewBox`, `role="img"`, `<title>` e `<desc>` com ids únicos.
- [ ] Não há números, artigos ou regras inventados; dados específicos têm referência de página.
- [ ] O texto está em português, com termos em inglês explicados.
- [ ] As perguntas de revisão têm respostas que não contradizem a fonte.
- [ ] Você escreveu apenas o(s) arquivo(s) atribuído(s).

## Sobre o capítulo 01

`src/01-resistencia.html` já está pronto e pode ser lido como referência de tom, profundidade e uso de componentes. Não copie o conteúdo dele; use apenas como padrão de qualidade.

## Retorno ao coordenador

Ao final, responda em poucas linhas: arquivos criados, faixa de páginas coberta, tópicos que ficaram de fora por ilegibilidade/limite de espaço e qualquer inconsistência encontrada na fonte.
