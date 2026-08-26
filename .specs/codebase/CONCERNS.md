# Concerns

Riscos conhecidos e aceitos, com a razão pela qual não foram corrigidos.

---

## C-01 — `GREEN_DARK` não atinge WCAG AA como cor de texto

**Onde:** `pages/transactions.py` — coluna de valor, linhas do tipo `investimento`.

**O quê:** `GREEN_DARK` (`#317D33`) tem **3,70:1** de contraste contra o fundo `#0E1117`. É
adequado como preenchimento de barra ou linha de gráfico (mín. 3,0:1), mas está abaixo dos
**4,5:1** que o WCAG AA exige para texto normal.

**Por que está assim:** decisão explícita do usuário — o pedido foi substituir o azul de
investimento por `GREEN_DARK` especificamente. O achado foi levantado durante a especificação e
mantido conscientemente.

**Alternativas já medidas**, ambas dentro do arco verde da marca:

| Token | Hex | Contraste | ΔE vs `GREEN_MAIN` |
| ----- | --- | --------- | ------------------ |
| `GREEN_DARK` (atual) | `#317D33` | 3,70 ✗ | 21,0 |
| Marca 600 | `#3B973E` | 5,11 ✓ | 9,1 — diferenciação fraca a 13px |
| Menta 500 | `#4BAF80` | 6,97 ✓ | 25,6 ✓ |

**Custo de corrigir:** alterar **uma constante** em `utils/theme.py`. Nenhum outro arquivo é
afetado — é exatamente o motivo pelo qual os tokens foram centralizados.

**Atenção:** `GREEN_DARK` também é usado como preenchimento (linha de saldo acumulado, hover do
botão), onde 3,70:1 é adequado. Se a troca for feita, considere um token de texto separado em
vez de mudar `GREEN_DARK` para todos os usos.

---

## C-02 — `pages/` e `components/` não têm harness automatizado

**O quê:** o guard de cor cobre *literais* e as *propriedades da paleta*, mas nada verifica que
a página renderiza como esperado. O mesmo vale para o guard de i18n.

**Por que está assim:** o harness e2e com Streamlit `AppTest` está no backlog desde M1 (AD-013).

**Mitigação em uso:** verificação visual no app real sob **usuário efêmero** (AD-024) — a
aplicação tem 2 usuários reais em uso diário, e um descartável é a única forma segura de
comprovar a camada de UI sem tocar em dados reais.
