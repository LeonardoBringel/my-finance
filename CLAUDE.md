# CLAUDE.md — Arquitetura do Projeto my-finance

## Visão Geral

Aplicação web de gestão financeira pessoal construída com **Streamlit** e **PostgreSQL** via **SQLAlchemy**. Dados sensíveis são criptografados em repouso com **Fernet** (biblioteca `cryptography`).

---

## Estrutura de Diretórios

```
my-finance/
├── app.py                        # Ponto de entrada — redireciona para pages/dashboard.py
├── alembic/                      # Migrações de banco de dados
│   ├── env.py
│   └── versions/
├── alembic.ini                   # Configuração do Alembic
├── components/                   # Componentes Streamlit reutilizáveis (usam st.*)
│   ├── charts.py                 # Gráficos Plotly (donut, barras, evolução anual)
│   ├── new_transaction.py        # Dialog de criação/edição de transação
│   └── styles.py                 # CSS global injetado via st.markdown
├── models/                       # Modelos ORM (SQLAlchemy) - um arquivo por tabela
│   ├── base.py                   # Base declarativa do SQLAlchemy
│   ├── user.py
│   ├── category.py
│   ├── transaction.py
│   ├── cash_flow_template.py
│   ├── cash_flow_template_item.py
│   ├── cash_flow_month.py
│   └── cash_flow_entry.py
├── pages/                        # Páginas Streamlit — cada arquivo é uma rota/página
│   ├── dashboard.py              # Dashboard principal com KPIs e gráficos
│   ├── transactions.py           # Listagem e filtro de lançamentos
│   ├── cash_flow.py              # Fluxo de caixa mensal planejado
│   ├── categories.py             # Gerenciamento de categorias
│   ├── profile.py                # Perfil e troca de senha do usuário
│   ├── admin.py                  # Gerenciamento de usuários (somente admins)
│   └── login.py                  # Autenticação
├── repositories/                 # Acesso ao banco de dados - um arquivo por tabela
│   ├── base_repository.py        # Engine e sessão
│   ├── users_repository.py
│   ├── categories_repository.py
│   ├── transactions_repository.py
│   ├── cash_flow_template_repository.py
│   ├── cash_flow_month_repository.py
│   └── cash_flow_entry_repository.py
└── utils/                        # Utilitários puros (sem chamadas diretas ao Streamlit)
    ├── auth.py                   # Autenticação, sessão e guards de login/admin
    ├── crypto.py                 # Criptografia Fernet (encrypt/decrypt)
    ├── data_format_utils.py      # Formatação de moeda, data e parsing de valores
    ├── category_types.py         # Tipos de categoria/transação + TYPE_LABELS
    ├── filters.py                # Sentinela ALL_FILTER dos selects de filtro
    ├── i18n.py                   # Loader e t() — fonte única do texto de UI
    ├── locales/                  # Mappings de texto por locale
    │   └── pt_BR.json            # Textos em pt-BR (único locale hoje)
    └── password_utils.py         # Hash e verificação de senha bcrypt
```

---

## Regras de Arquitetura

### `models/`
- Um arquivo por tabela do banco de dados.
- Apenas definição de colunas, relacionamentos e métodos `to_json()` / `get_*()`.
- Sem lógica de negócio.
- Campos sensíveis são criptografados via `utils.crypto` (importado diretamente no model).
- Nunca importar `streamlit` nos models.

### `repositories/`
- Um arquivo por tabela (mesmo padrão dos models).
- Toda interação com o banco de dados passa pelos repositories.
- Métodos são `@staticmethod` dentro de classes nomeadas `*Repository`.
- Usar sempre o context manager `get_session()` de `base_repository.py`.
- Retornar `dict` ou `list[dict]` — nunca objetos ORM fora do bloco `with get_session()`.
- Nunca importar `streamlit` nos repositories.
- `base_repository.py` fornece: `get_engine()`, `get_session()`.

### `utils/`
- Funções puras que não dependem do Streamlit.
- **Exceção:** `utils/auth.py` acessa `st.session_state` e `st.switch_page` porque gerencia o estado de sessão da aplicação - isso é necessário e aceitável.
- `utils/crypto.py` centraliza toda criptografia/descriptografia Fernet.
- `utils/password_utils.py` centraliza hash e verificação de senha bcrypt.
- `utils/data_format_utils.py` centraliza formatação de exibição (moeda, datas).
- `utils/i18n.py` centraliza todo o texto de interface (ver seção **i18n**).

### i18n — Texto de interface
- **Nenhum literal de texto voltado ao usuário** em `pages/`, `components/`, `repositories/`
  ou `utils/`. Todo texto vive em `utils/locales/pt_BR.json` e é lido por
  `t("chave.pontilhada", **kwargs)` de `utils/i18n.py`.
- Interpolação usa `str.format`: `t("pages.x.count", count=3)` para o JSON `"{count} itens"`.
  Texto com `{` literal e sem interpolação usa `t_raw()`.
- **Chave ausente levanta `KeyError`** (sem fallback silencioso). Chaves montadas
  dinamicamente são **proibidas** — exceto `f"domain.category_type.{tipo}"` (domínio fechado).
- **Não são texto e ficam no código:** `page_icon` (emoji), blocos `<style>`/CSS, sintaxe de
  cor do Streamlit (`:green[...]`), e as **constantes de domínio** persistidas
  (`entrada`/`saida`/`ambos`/`investimento` — são valores criptografados no banco, não copy).
- `tests/unit/test_i18n_guard.py` é o contrato: falha se um literal de texto aparecer na UI,
  se uma chave de `t()` não existir no JSON, ou se o JSON tiver chave órfã. Rode-o antes de commitar UI.

### `components/`
- Funções e dialogs Streamlit reutilizáveis entre páginas.
- Podem e devem usar `st.*` diretamente.
- Não acessam o banco de dados diretamente - usam repositories.

### `pages/`
- Cada arquivo é uma página Streamlit (rota da aplicação).
- Toda página começa com `require_login()` (e `require_admin()` quando necessário).
- Não contêm lógica de negócio complexa - delegam para repositories e components.
- Navegação entre páginas via `st.switch_page("pages/nome.py")`.
- `app.py` é o ponto de entrada do Streamlit e apenas redireciona para `pages/dashboard.py`.

### Criptografia
- Campos sensíveis (username, nome de categoria, data, valor, descrição) são criptografados com Fernet antes de persistir.
- `encrypt()` e `decrypt()` estão em `utils/crypto.py`.
- A chave é carregada da variável de ambiente `FERNET_KEY` via `.env`.

### Banco de Dados
- Migrações gerenciadas pelo **Alembic**.
- URL de conexão montada a partir das variáveis: `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`.

---

## Padrões de Código

- **Docstrings:** Todo método/função deve ter uma docstring breve descrevendo sua responsabilidade. Use `Args:` e `Returns:` quando relevante.
- **Type hints:** Use em assinaturas de funções públicas.
- **Nomes:** Classes em PascalCase, funções/variáveis em snake_case. Repositórios seguem o padrão `<Entidade>Repository`.
- **Retornos de repository:** Sempre `dict` ou `list[dict]`, nunca objetos ORM.
- **Session management:** Sempre use `with get_session() as s:` - nunca manipule sessões manualmente.

---

## Fluxo de Trabalho com Git

### Commits por Tarefa
- Cada tarefa deve ser **commitada antes de iniciar a próxima**.
- Mensagem de commit no formato:
  ```
  <Nome Pagina / Feature>: <breve descricao em lower case sem caracteres especiais>
  ```
  Exemplos:
  - `Transactions: fix category filter by type`
  - `Cash Flow: add sum income and outcome`
- Importante:
    - As mensagens de commit devem ser sempre em inglês e apenas o primeiro caracter deve ser maiúsculo
    - As mensagens de commit devem ter apenas uma linha e não devem ter menção de Claude Code
    - NUNCA coloque na mensagem `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>`

### Tags de Versão
- Cada commit de tarefa deve ser **taggeado** seguindo o padrão `v*.*.*` (semver).
- A escolha do componente a incrementar (major/minor/patch) é feita caso a caso.
    - major só deverá ser incrementada quando for explicitamente solicitado.
    - minor deverá ser incrementada quando novas funcionalidades forem adicionadas, zerando o valor de patch.
    - patch deverá ser incrementada quando forem realizados fix, sem novas funcionalidades.

---

## Fluxo de Dados

```
Página Streamlit (pages/)
    │
    ├─► Component (components/)   ← reutilizável entre páginas
    │       │
    │       └─► Repository (repositories/)
    │                   │
    │                   └─► Model ORM (models/)
    │                               │
    │                               └─► PostgreSQL
    │
    └─► Utils (utils/)             ← formatação, crypto, auth
```
