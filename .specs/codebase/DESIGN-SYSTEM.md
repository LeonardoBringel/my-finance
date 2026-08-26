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

Estrutura **3 famílias de matiz × 3 tons**. A separação entre categorias vem de **luminosidade +
um deslocamento curto de matiz** — nunca de trocar de família de cor.

| | 300 · claro | 500 · médio | 700 · escuro |
| --- | --- | --- | --- |
| **Lima** (92°) | `#A1C680` | `#7AAF4B` | `#547D31` |
| **Marca** (122°) | `#80C683` | `#4CAF50` ★ | `#317D33` |
| **Menta** (152°) | `#80C6A6` | `#4BAF80` | `#317D59` |

★ = a âncora.

**Invariantes** (todos afirmados por `test_color_guard.py`):

| Invariante | Valor |
| ---------- | ----- |
| Arco de matiz | 92°–152° — o arco mais largo que ainda lê como a mesma família de verde |
| Saturação | 38%–44% — ancorada nos 39% do botão |
| Contraste vs. fundo `#0E1117` | 3,70:1 – 9,81:1 |
| ΔE mínimo entre quaisquer duas | 11,8 |
| ΔE entre vizinhos do ciclo | ≥ 19,9 |

### Ordem do ciclo — não reordene

```
1. Marca 500    #4CAF50
2. Menta 300    #80C6A6
3. Lima  700    #547D31
4. Menta 500    #4BAF80
5. Lima  300    #A1C680
6. Marca 700    #317D33
7. Lima  500    #7AAF4B
8. Marca 300    #80C683
9. Menta 700    #317D59
```

A ordem alterna **família e tom a cada passo**. Isso é o que garante que dois segmentos vizinhos
de um donut — ou duas fatias adjacentes de uma barra empilhada — nunca caiam na mesma família
nem no mesmo nível de luz. **Reordenar a lista quebra essa propriedade** mesmo mantendo as
mesmas 9 cores.

### Acima de 9 categorias

Da 10ª à 18ª, `expense_palette()` usa `EXPENSE_PALETTE_MUTED`: as mesmas 9 cores dessaturadas
(`S × 0.55`, `L` puxada 35% em direção a 46%). Acima de 18 o ciclo reinicia com repetição — a
legenda desambigua.

**Por que dessaturação e não opacidade.** Alpha mescla a cor em direção ao fundo escuro. Medido
contra `#0E1117`, uma segunda volta com `opacity=0.78` derruba os três tons `700` para ~2,7:1 de
contraste — eles somem — e o ΔE mínimo global cai de 11,8 para 5,8. A dessaturação preserva o
matiz, entrega a mesma leitura de "esmaecido" e **nenhuma cor da 2ª volta fica pior que a pior
cor da 1ª**.

---

## Tokens semânticos

| Token | Hex | Vem de | Usar em |
| ----- | --- | ------ | ------- |
| `GREEN_LIGHT` | `#80C683` | Marca 300 | Barra de entradas do gráfico anual |
| `GREEN_MAIN` | `#4CAF50` | Marca 500 ★ | Botão primário, barras de despesa, histórico, valores de entrada |
| `GREEN_DARK` | `#317D33` | Marca 700 | Linha de saldo acumulado, hover do botão, valores de investimento |
| `RED_MAIN` | `#EF5350` | — | Saídas. **Único token fora do arco verde**, e de propósito: vermelho ali é semântica, não identidade |
| `TEXT_COLOR` | `#FAFAFA` | — | Texto de gráfico |
| `TEXT_MUTED` | `#8A9A8C` | — | Delta neutro nos cards ("sem despesas") |
| `TEXT_FAINT` | `rgba(255,255,255,.15)` | `WHITE` @ 15% | Rodapé de versão no login |
| `WHITE` | `#FFFFFF` | — | Texto do botão primário; base de `TEXT_FAINT` e `CHART_GRID` |
| `BG_DARK` | `#0E1117` | — | Fundo do tema Streamlit. Base de **todo** contraste medido aqui |
| `CHART_BG` / `CHART_TRANSPARENT` | `rgba(0,0,0,0)` | — | Fundo de figura; traces e shapes invisíveis |
| `CHART_GRID` | `rgba(255,255,255,.08)` | `WHITE` @ 8% | Grade e linha de eixo |

Os três verdes semânticos **são** a coluna Marca — apelidos, não hexes independentes. Isso
existe para que não haja dois "verdes escuros" ligeiramente diferentes no sistema.

O hover do botão primário passou de `#43A047` (Material Green 600, órfão) para `GREEN_DARK`.
É um escurecimento um pouco mais forte que o anterior, e agora vem da rampa.

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
| Preenchimento de gráfico (não-texto) | 3,0:1 | Toda a paleta passa (mín. 3,70) |
| Texto normal | 4,5:1 (WCAG AA) | ⚠️ ver abaixo |

⚠️ **`GREEN_DARK` (3,70:1) não atinge AA como texto.** É adequado como preenchimento de barra
ou linha, mas está abaixo do mínimo no uso de texto (valores de investimento em
`pages/transactions.py`). Decisão explícita e consciente — ver `CONCERNS.md`. Alternativas já
medidas, ambas dentro do arco da marca: Marca 600 `#3B973E` (5,11:1, mas só ΔE 9,1 de
`GREEN_MAIN` — diferenciação fraca a 13px) e Menta 500 `#4BAF80` (6,97:1, ΔE 25,6). Trocar é
alterar **uma constante** em `utils/theme.py`.

---

## Adicionando uma cor

1. **Precisa mesmo?** 9 categóricas + 8 semânticas cobrem a aplicação hoje. Uma cor nova quase
   sempre significa que um token existente serve.
2. Se for **categórica**: ela precisa cair no arco 92°–152°, com S 38–44%, contraste ≥ 3,7:1, e
   ΔE ≥ 11,8 de todas as outras. Encaixe-a no ciclo mantendo a alternância família/tom.
3. Se for **semântica**: derive-a da coluna Marca se puder. Se não puder (como `RED_MAIN`),
   documente aqui **por que** ela sai do arco.
4. Adicione o token em `utils/theme.py`, atualize esta tabela e rode
   `uv run pytest tests/unit/test_color_guard.py`.

---

## Histórico

| Quando | O quê |
| ------ | ----- |
| `df92100` (2026-08-23) | Paleta aparada por contraste medido + interpolação por contagem de categorias (AD-023). Corrigiu legibilidade, **quebrou a identidade**: a rampa cruzava verde 122° e teal 174°, e a interpolação gerava tons intermediários que não pertenciam a nenhuma das duas famílias |
| `brand-color-palette` (2026-08-25) | Substitui a rampa interpolada por paleta discreta 3×3 derivada da âncora; centraliza todos os tokens em `utils/theme.py`; investimento deixa de ser azul. Substitui AD-023 |
