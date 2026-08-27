# Design System — Cores

> **Fonte da verdade no código:** `utils/theme.py`.
> **Contrato automatizado:** `tests/unit/test_color_guard.py`.
> Este documento explica o *porquê*; o módulo é o *o quê*. Se divergirem, o módulo vence e
> este documento está desatualizado.

---

## Regra única

**Nenhum literal de cor fora de `utils/theme.py`.** Nem hex, nem `rgba()`, nem nome CSS de cor,
nem a sintaxe `:cor[...]` do Streamlit. Isso vale para `pages/`, `components/`, `utils/` e para
`utils/locales/pt_BR.json`.

Se você precisa de uma cor, ela já existe como token. Se não existe, leia
[Adicionando uma cor](#adicionando-uma-cor) antes de inventar uma.

---

## A âncora

```
#4CAF50   H 122°   S 39%   L 49%
```

É a cor de fundo do botão "Novo Registro" — o elemento mais reconhecível da plataforma. **Toda**
cor de marca do sistema é uma derivação dela. Mudar `#4CAF50` significa refazer a paleta inteira;
o guard test trava esse valor de propósito, para que a mudança seja consciente.

---

## A paleta categórica

**Monocromática.** Um único verde — o da âncora, matiz 122° e saturação 39% — em 9 degraus de
luminosidade. Não há segunda família de cor.

| Degrau | Hex | Contraste | Papel |
| ------ | --- | --------- | ----- |
| 900 | `#377E39` | 3,78 | |
| 800 | `#3C893F` | 4,36 | |
| 700 | `#419745` | 5,16 | `GREEN_DARK` |
| 600 | `#47A24A` | 5,88 | |
| **500** | **`#4CAF50`** ★ | **6,80** | **`GREEN_MAIN`** — a âncora |
| 400 | `#5FB963` | 7,74 | |
| 300 | `#76C379` | 8,87 | `GREEN_LIGHT` |
| 200 | `#8BCD8E` | 10,10 | |
| 100 | `#A2D6A4` | 11,42 | |

Os degraus são espaçados de forma **perceptualmente uniforme**, em `L*` de Lab (4,25 unidades
por passo, ±0,5 de quantização) e não em `L` de HSL. Espaçar em HSL agruparia os tons claros e
espalharia os escuros — os passos iriam de 2,9 a 6,4.

**Invariantes** (todos afirmados por `test_color_guard.py`):

| Invariante | Valor |
| ---------- | ----- |
| Arco de matiz | 1,1° — quantização apenas; o alvo é 0° |
| Saturação | 39% ± 1,5 ponto |
| Contraste vs. fundo `#0E1117` | 3,78:1 – 11,42:1 |
| ΔE mínimo entre quaisquer duas | 4,9 |
| ΔE entre vizinhos do ciclo | 8,7 |

### A ordem do ciclo — não reordene

`EXPENSE_PALETTE` **não** percorre a rampa em sequência. Ela intercala pares e ímpares:

```
900 → 700 → 500 → 300 → 100 → 800 → 600 → 400 → 200
```

Cada cor salta **dois degraus** em relação à anterior. É isso, e só isso, que torna o
monocromático legível num donut: percorrendo a rampa em ordem, fatias vizinhas ficariam a ΔE
4,9; intercaladas, ficam a 8,7 — com exatamente as mesmas 9 cores. Reordenar a lista quebra a
propriedade sem mudar nenhum hex, e o guard test pega.

### Acima de 9 categorias

O ciclo reinicia com repetição; a legenda desambigua.

**Não existe segunda volta esmaecida.** Dessaturar um verde único produz cinza, não "verde
esmaecido" — a marca se perde. Uma versão anterior desta paleta cobria 18 categorias porque
tinha 3 famílias de matiz para dessaturar; o monocromático abre mão disso.

### O custo, explicitamente

ΔE mínimo global de **4,9** é baixo. Fatias em pontos opostos de um donut são genuinamente
difíceis de parear com a legenda. É o preço direto de tirar a matiz da equação: sobra só
luminosidade para separar 9 categorias, e a faixa utilizável é limitada pelo contraste nas duas
pontas. Escolha consciente, por coesão visual — a paleta anterior tinha ΔE mínimo 11,8 num arco
de 60°, e lia como três cores diferentes em vez de um verde.

---

## Tokens semânticos

| Token | Hex | Vem de | Usar em |
| ----- | --- | ------ | ------- |
| `GREEN_LIGHT` | `#76C379` | Degrau 300 | Barra de entradas do gráfico anual |
| `GREEN_MAIN` | `#4CAF50` | Degrau 500 ★ | Botão primário, barras de despesa, histórico, valores de entrada |
| `GREEN_DARK` | `#419745` | Degrau 700 | Linha de saldo acumulado, hover do botão, valores de investimento |
| `RED_MAIN` | `#EF5350` | — | Saídas. **Único token fora do verde**, e de propósito: vermelho ali é semântica, não identidade |
| `TEXT_COLOR` | `#FAFAFA` | — | Texto de gráfico |
| `TEXT_MUTED` | `#8A9A8C` | — | Delta neutro nos cards ("sem despesas") |
| `TEXT_FAINT` | `rgba(255,255,255,.15)` | `WHITE` @ 15% | Rodapé de versão no login |
| `WHITE` | `#FFFFFF` | — | Texto do botão primário; base de `TEXT_FAINT` e `CHART_GRID` |
| `BG_DARK` | `#0E1117` | — | Fundo do tema Streamlit. Base de **todo** contraste medido aqui |
| `CHART_BG` / `CHART_TRANSPARENT` | `rgba(0,0,0,0)` | — | Fundo de figura; traces e shapes invisíveis |
| `CHART_GRID` | `rgba(255,255,255,.08)` | `WHITE` @ 8% | Grade e linha de eixo |

Os três verdes semânticos **são** degraus da rampa — apelidos, não hexes independentes. Isso
existe para que não haja dois "verdes escuros" ligeiramente diferentes no sistema.

`GREEN_DARK` é o degrau **700** e não o 800 por um motivo específico: ele também pinta *texto*
(o valor de investimento em Lançamentos). O 700 dá 5,16:1, que atende WCAG AA; o 800 daria
4,36:1, que não atende.

---

## O espelho em `.streamlit/config.toml`

O Streamlit resolve as cores do **próprio chrome** (o delta do `st.metric`, o foco de widget, o
`primaryColor`) a partir de `config.toml` — não de Python. Esse é o **único** lugar onde um
token é duplicado:

```toml
[theme]
base = "dark"
primaryColor = "#4CAF50"   # GREEN_MAIN
greenColor   = "#4CAF50"   # GREEN_MAIN
redColor     = "#EF5350"   # RED_MAIN
```

`test_color_guard.py` verifica que esses valores continuam iguais aos tokens. Ao mudar um token,
mude os dois lugares.

`base = "dark"` é obrigatório e não é preferência estética: sem ele o tema segue o
`prefers-color-scheme` do browser, e no modo claro o texto dos gráficos (`TEXT_COLOR`, `#FAFAFA`)
fica branco sobre branco. É também o que garante que o fundo seja de fato `#0E1117` — a base de
todo contraste medido neste documento.

O Streamlit **clareia** `redColor`/`greenColor` para desenhar o delta do `st.metric`, então o
pixel final ali é um tom derivado, não o token literal. É esperado.

---

## Regras de uso

**Categoria de despesa em gráfico** → `expense_palette(n)`, nunca escolher a dedo.
Índice `i` da categoria = cor `i`.

**Valor monetário colorido em texto** → `t("components.value_colored", color=<token>, value=...)`
com `unsafe_allow_html=True`.
A sintaxe `:cor[texto]` do Streamlit **não serve**: ela aceita apenas as cores nomeadas
(`red`, `green`, `blue`, `violet`, `gray`, `primary`), nenhuma delas é da marca. Verificado em
`streamlit/elements/lib/color_util.py`.

**Cor em bloco `<style>`** → f-string interpolando o token. Para transparência, `rgba(TOKEN, α)`.
Escape as chaves literais do CSS como `{{` / `}}`.

**Fundo/transparência de gráfico** → `CHART_BG`, `CHART_GRID`, `CHART_TRANSPARENT`.

---

## Contraste

Todo valor deste documento foi medido contra `#0E1117`, o fundo do tema escuro do Streamlit.

| Uso | Mínimo | Nota |
| --- | ------ | ---- |
| Preenchimento de gráfico (não-texto) | 3,0:1 | Toda a rampa passa (mín. 3,78) |
| Texto normal | 4,5:1 (WCAG AA) | atendido por `GREEN_DARK`, o único degrau usado como texto |

Toda a rampa atende o mínimo de preenchimento (3,0:1). `GREEN_DARK` atende WCAG AA (5,16:1) —
foi por isso que ele é o degrau 700 e não o 800. Os degraus 900 e 800 **não** servem para texto.

---

## Adicionando uma cor

1. **Precisa mesmo?** 9 categóricas + 8 semânticas cobrem a aplicação hoje. Uma cor nova quase
   sempre significa que um token existente serve.
2. Se for **categórica**: a rampa é monocromática e tem 9 degraus espaçados uniformemente em
   `L*`. Adicionar um 10º comprime todos os outros e derruba o ΔE mínimo abaixo de 4,5 — o guard
   test recusa. A resposta certa quase sempre é agrupar categorias, não adicionar cor.
3. Se for **semântica**: derive-a de um degrau da rampa. Se não puder (como `RED_MAIN`),
   documente aqui **por que** ela sai do verde. Se for para pintar *texto*, o degrau precisa de
   contraste ≥ 4,5:1 — o que exclui os degraus 900 e 800.
4. Adicione o token em `utils/theme.py`, atualize esta tabela e rode
   `uv run pytest tests/unit/test_color_guard.py`.

---

## Histórico

| Quando | O quê |
| ------ | ----- |
| `df92100` (2026-08-23) | Paleta aparada por contraste medido + interpolação por contagem de categorias (AD-023). Corrigiu legibilidade, **quebrou a identidade**: a rampa cruzava verde 122° e teal 174°, e a interpolação gerava tons intermediários que não pertenciam a nenhuma das duas famílias |
| `brand-color-palette` (2026-08-25) | Substitui a rampa interpolada por paleta discreta 3×3 derivada da âncora; centraliza todos os tokens em `utils/theme.py`; investimento deixa de ser azul. Substitui AD-023 |
| `v0.23.0` (2026-08-26) | **Colapsa as 3 famílias de matiz numa só.** As 3×3 liam como três cores diferentes, não como um verde. Rampa monocromática de 9 degraus, ordem intercalada. Custo: ΔE mínimo 11,8 → 4,9; cobertura 18 → 9 categorias. Ganho: `GREEN_DARK` passa a atender WCAG AA como texto (3,70:1 → 5,16:1) |
