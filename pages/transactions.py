import streamlit as st
import sys
import os
from datetime import datetime, date

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import database as db

st.set_page_config(page_title="Lançamentos", page_icon="📋", layout="wide")
# db.init_db()

st.markdown("""
<style>
    #MainMenu, footer { visibility: hidden; }
    [data-testid="stHeader"] { background: transparent; }
    .block-container { padding-top: 1.5rem; }
    [data-testid="metric-container"] {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(76,175,80,0.2);
        border-radius: 12px;
        padding: 12px 16px;
    }
</style>
""", unsafe_allow_html=True)


def fmt(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_date(d: str) -> str:
    """YYYY-MM-DD → DD/MM/YYYY"""
    try:
        return datetime.strptime(d, "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return d


def parse_valor(s):
    s = s.strip().replace(" ", "")
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


st.markdown("## 📋 Lançamentos")

# ── Filters ────────────────────────────────────────────────────────────────────
with st.expander("🔍 Filtros", expanded=True):
    col1, col2, col3, col4 = st.columns(4)
    years = db.get_available_years()
    with col1:
        year_options = ["Todos"] + [str(y) for y in years]
        f_year_str = st.selectbox("Ano", year_options)
        f_year = None if f_year_str == "Todos" else int(f_year_str)
    month_names = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                   "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    with col2:
        f_month_name = st.selectbox("Mês", ["Todos"] + month_names)
        f_month = month_names.index(f_month_name) + 1 if f_month_name != "Todos" else None
    with col3:
        f_type = st.selectbox(
            "Tipo", ["Todos", "entrada", "saida"],
            format_func=lambda x: "Todos" if x == "Todos" else ("💰 Entrada" if x == "entrada" else "💸 Saída")
        )
    with col4:
        f_cat = st.text_input("Categoria (contém)", "")

col_new, col_back = st.columns([1, 5])
with col_new:
    if st.button("➕ Novo Registro", type="primary"):
        st.session_state["show_form_txn"] = True
        st.session_state.setdefault("form_txn_reset", 0)
with col_back:
    if st.button("🏠 Voltar ao Dashboard"):
        st.switch_page("app.py")


# ── New Transaction Dialog ─────────────────────────────────────────────────────
@st.dialog("➕ Novo Registro")
def new_transaction_dialog():
    all_cats = db.get_all_categories()
    reset_key = st.session_state.get("form_txn_reset", 0)

    tipo = st.selectbox("Tipo *", ["saida", "entrada"],
                        format_func=lambda x: "💸 Saída" if x == "saida" else "💰 Entrada")

    col1, col2 = st.columns(2)
    with col1:
        data = st.date_input("Data *", value=datetime.today(), format="DD/MM/YYYY")
    with col2:
        valor_str = st.text_input("Valor Total (R$) *", value="",
                                  key=f"txn_valor_{reset_key}", placeholder="ex: 1.250,00")

    cats_filtered = [c["name"] for c in all_cats if c["type"] in (tipo, "ambos")]
    used_cats = db.get_autocomplete_values("category")
    cat_options = sorted(set(cats_filtered + used_cats))
    categoria = st.selectbox("Categoria *", [""] + cat_options, key=f"txn_cat_{reset_key}")

    # ── Campo único de descrição com autocomplete ──────────────────────────────
    desc_options = db.get_autocomplete_values("description")
    descricao_final = st.selectbox(
        "Descrição",
        options=desc_options,
        index=None,
        accept_new_options=True,
        placeholder="Digite ou selecione uma descrição...",
        key=f"txn_desc_{reset_key}"
    ) or ""

    parcelado = st.checkbox("Parcelado?", key=f"txn_parc_{reset_key}")
    parcelas = 1
    if parcelado:
        parcelas = st.number_input("Número de parcelas", min_value=2, max_value=60,
                                   value=2, step=1, key=f"txn_nparc_{reset_key}")

    valor_parsed = parse_valor(valor_str) if valor_str else None
    if parcelado and valor_parsed:
        st.info(f"💡 Valor por parcela: **{fmt(valor_parsed / parcelas)}** × {int(parcelas)}x")

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 Salvar", type="primary", use_container_width=True):
            if not categoria:
                st.error("Selecione uma categoria.")
            elif not valor_parsed or valor_parsed <= 0:
                st.error("Informe um valor válido (ex: 1.250,00).")
            else:
                db.add_transaction(tipo, data.strftime("%Y-%m-%d"), categoria,
                                   descricao_final, valor_parsed, int(parcelas))
                st.success("✅ Salvo! Preencha o próximo ou feche.")
                st.session_state["form_txn_reset"] = reset_key + 1
                st.rerun()
    with c2:
        if st.button("Fechar", use_container_width=True):
            st.session_state.pop("show_form_txn", None)
            st.session_state.pop("form_txn_reset", None)
            st.rerun()


if st.session_state.get("show_form_txn"):
    new_transaction_dialog()


# ── Edit Transaction Dialog ────────────────────────────────────────────────────
@st.dialog("✏️ Editar Lançamento")
def edit_transaction_dialog(txn):
    all_cats = db.get_all_categories()
    tipo = st.selectbox("Tipo *", ["saida", "entrada"],
                        index=0 if txn["type"] == "saida" else 1,
                        format_func=lambda x: "💸 Saída" if x == "saida" else "💰 Entrada")
    col1, col2 = st.columns(2)
    with col1:
        data = st.date_input("Data *", value=date.fromisoformat(txn["date"]),
                             format="DD/MM/YYYY")
    with col2:
        valor_str = st.text_input(
            "Valor (R$) *",
            value=f"{txn['value']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            placeholder="ex: 1.250,00"
        )

    cats_filtered = [c["name"] for c in all_cats if c["type"] in (tipo, "ambos")]
    used_cats = db.get_autocomplete_values("category")
    cat_options = sorted(set(cats_filtered + used_cats))
    cat_idx = cat_options.index(txn["category"]) if txn["category"] in cat_options else 0
    categoria = st.selectbox("Categoria *", cat_options, index=cat_idx)

    # ── Campo único de descrição com autocomplete ──────────────────────────────
    desc_options = db.get_autocomplete_values("description")
    current_desc = txn["description"] or ""
    # Pre-select existing value if it's in options, otherwise it appears as typed value
    desc_index = desc_options.index(current_desc) if current_desc in desc_options else None
    descricao = st.selectbox(
        "Descrição",
        options=desc_options,
        index=desc_index,
        accept_new_options=True,
        placeholder="Digite ou selecione uma descrição...",
        key="edit_desc"
    ) or ""

    if txn.get("installment_total"):
        st.info(f"⚠️ Parcela {txn['installment_number']}/{txn['installment_total']} — editar só esta parcela")

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 Salvar", type="primary", use_container_width=True):
            valor_parsed = parse_valor(valor_str) if valor_str else None
            if not valor_parsed or valor_parsed <= 0:
                st.error("Informe um valor válido.")
            else:
                db.update_transaction(txn["id"], tipo, data.strftime("%Y-%m-%d"),
                                      categoria, descricao, valor_parsed)
                st.success("✅ Atualizado!")
                st.session_state.pop("edit_txn", None)
                st.rerun()
    with c2:
        if st.button("Cancelar", use_container_width=True):
            st.session_state.pop("edit_txn", None)
            st.rerun()


if "edit_txn" in st.session_state:
    edit_transaction_dialog(st.session_state["edit_txn"])


# ── Load & Filter Transactions ─────────────────────────────────────────────────
transactions = db.get_transactions(year=f_year, month=f_month)
if f_type != "Todos":
    transactions = [t for t in transactions if t["type"] == f_type]
if f_cat:
    transactions = [t for t in transactions if f_cat.lower() in t["category"].lower()]

# ── Summary Metrics ────────────────────────────────────────────────────────────
total_in = sum(t["value"] for t in transactions if t["type"] == "entrada")
total_out = sum(t["value"] for t in transactions if t["type"] == "saida")

col1, col2, col3 = st.columns(3)
col1.metric("💰 Total Entradas", fmt(total_in))
col2.metric("💸 Total Saídas", fmt(total_out))
col3.metric("📈 Saldo", fmt(total_in - total_out))

st.divider()

# ── Table ──────────────────────────────────────────────────────────────────────
if not transactions:
    st.info("Nenhum lançamento encontrado para os filtros selecionados.")
else:
    st.markdown(f"**{len(transactions)} lançamento(s) encontrado(s)**")

    header = st.columns([1.2, 1.5, 1.8, 2.5, 1.5, 1.2, 0.8, 0.8])
    for h, label in zip(header, ["Tipo", "Data", "Categoria", "Descrição", "Valor", "Parcela", "✏️", "🗑️"]):
        h.markdown(f"**{label}**")
    st.divider()

    for txn in transactions:
        cols = st.columns([1.2, 1.5, 1.8, 2.5, 1.5, 1.2, 0.8, 0.8])
        tipo_icon = "💰" if txn["type"] == "entrada" else "💸"
        tipo_label = "Entrada" if txn["type"] == "entrada" else "Saída"

        cols[0].markdown(f"{tipo_icon} {tipo_label}")
        cols[1].markdown(fmt_date(txn["date"]))
        cols[2].markdown(txn["category"])
        cols[3].markdown(txn["description"] or "—")

        val_color = "green" if txn["type"] == "entrada" else "red"
        cols[4].markdown(f":{val_color}[{fmt(txn['value'])}]")

        if txn.get("installment_total"):
            cols[5].markdown(f"{txn['installment_number']}/{txn['installment_total']}")
        else:
            cols[5].markdown("—")

        if cols[6].button("✏️", key=f"edit_{txn['id']}"):
            st.session_state["edit_txn"] = txn
            st.rerun()

        if cols[7].button("🗑️", key=f"del_{txn['id']}"):
            st.session_state[f"confirm_del_{txn['id']}"] = True

        if st.session_state.get(f"confirm_del_{txn['id']}"):
            st.warning(f"⚠️ Confirmar exclusão de **{txn['category']}** — {fmt(txn['value'])}?")
            c1, c2, _ = st.columns([1, 1, 4])
            if c1.button("✅ Confirmar", key=f"conf_{txn['id']}", type="primary"):
                db.delete_transaction(txn["id"])
                st.session_state.pop(f"confirm_del_{txn['id']}", None)
                st.rerun()
            if c2.button("❌ Cancelar", key=f"canc_{txn['id']}"):
                st.session_state.pop(f"confirm_del_{txn['id']}", None)
                st.rerun()
