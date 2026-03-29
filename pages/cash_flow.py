import os
import sys
from datetime import datetime

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import database as db
from auth import require_login
from components.styles import inject_global_css
from repositories import CashFlowRepository
from utils.data_format_utils import format_currency, parse_value_text

inject_global_css()

st.set_page_config(page_title="Fluxo de Caixa", page_icon="💵", layout="wide")
db.init_db()

st.markdown(
    """
<style>
    #MainMenu, footer { visibility: hidden; }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] { display: none; }
    [data-testid="collapsedControl"] { display: none; }
    .block-container { padding-top: 1.5rem; }
</style>
""",
    unsafe_allow_html=True,
)

require_login()
user_id = st.session_state["current_user"]["id"]

MONTH_NAMES = [
    "Janeiro",
    "Fevereiro",
    "Março",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro",
]

# ── Header ─────────────────────────────────────────────────────────────────────
col_title, col_back = st.columns([4, 1])
with col_title:
    st.markdown("## 💵 Fluxo de Caixa")
with col_back:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🏠 Dashboard", use_container_width=True):
        st.switch_page("app.py")

# ── Year selector ──────────────────────────────────────────────────────────────
current_year = datetime.now().year
selected_year = st.selectbox(
    "📅 Ano",
    list(range(current_year - 3, current_year + 3)),
    index=3,
    key="cf_year",
)

st.divider()

# ── Load data ──────────────────────────────────────────────────────────────────
existing_months = CashFlowRepository.list_months(user_id, selected_year)
existing_month_nums = {m["month"] for m in existing_months}


# ── Dialogs ────────────────────────────────────────────────────────────────────


@st.dialog("📋 Gerenciar Template", width="large")
def template_dialog():
    st.markdown("Configure os lançamentos padrão aplicados ao criar um novo mês.")
    tmpl = CashFlowRepository.get_template(user_id)
    items = tmpl["items"] if tmpl else []

    # Editable table state
    if "tmpl_items" not in st.session_state:
        st.session_state["tmpl_items"] = [dict(i) for i in items]

    tmpl_items = st.session_state["tmpl_items"]

    # Header
    if tmpl_items:
        h = st.columns([3, 1, 2, 1.5, 0.7])
        for col, label in zip(h, ["Nome", "Dia", "Valor (R$)", "Tipo", "🗑️"]):
            col.markdown(f"**{label}**")

    to_remove = None
    for idx, item in enumerate(tmpl_items):
        c = st.columns([3, 1, 2, 1.5, 0.7])
        item["name"] = c[0].text_input(
            "Nome",
            value=item["name"],
            key=f"ti_name_{idx}",
            label_visibility="collapsed",
        )
        item["day"] = c[1].number_input(
            "Dia",
            value=item["day"],
            key=f"ti_day_{idx}",
            label_visibility="collapsed",
            min_value=1,
            max_value=31,
            step=1,
        )
        item["value"] = c[2].number_input(
            "Valor",
            value=item["value"],
            key=f"ti_val_{idx}",
            label_visibility="collapsed",
            min_value=0.0,
            format="%.2f",
            step=0.01,
        )
        item["type"] = c[3].selectbox(
            "Tipo",
            ["saida", "entrada"],
            index=0 if item["type"] == "saida" else 1,
            format_func=lambda x: "💸 Saída" if x == "saida" else "💰 Entrada",
            key=f"ti_type_{idx}",
            label_visibility="collapsed",
        )
        if c[4].button("🗑️", key=f"ti_del_{idx}"):
            to_remove = idx

    if to_remove is not None:
        st.session_state["tmpl_items"].pop(to_remove)
        st.rerun(scope="fragment")

    if st.button("➕ Adicionar Item", use_container_width=True):
        st.session_state["tmpl_items"].append(
            {"name": "", "day": 1, "value": 0.0, "type": "saida"}
        )
        st.rerun(scope="fragment")

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 Salvar Template", type="primary", use_container_width=True):
            valid = [
                i
                for i in st.session_state["tmpl_items"]
                if i["name"].strip() and i["value"] > 0
            ]
            if not valid:
                st.error(
                    "Adicione ao menos um item válido (nome e valor obrigatórios)."
                )
            else:
                CashFlowRepository.save_template(user_id, valid)
                st.session_state.pop("tmpl_items", None)
                st.success("✅ Template salvo!")
                st.rerun()
    with c2:
        if st.button("Fechar", use_container_width=True):
            st.session_state.pop("tmpl_items", None)
            st.rerun()


@st.dialog("📅 Novo Mês", width="small")
def new_month_dialog():
    available = [m for m in range(1, 13) if m not in existing_month_nums]
    if not available:
        st.info("Todos os meses do ano já foram criados.")
        if st.button("Fechar", use_container_width=True):
            st.rerun()
        return

    month_name = st.selectbox(
        "Mês *",
        [MONTH_NAMES[m - 1] for m in available],
        key="new_month_sel",
    )
    selected_m = available[[MONTH_NAMES[m - 1] for m in available].index(month_name)]

    tmpl = CashFlowRepository.get_template(user_id)
    if tmpl and tmpl["items"]:
        st.info(f"✅ Template aplicado automaticamente ({len(tmpl['items'])} item(ns))")
    else:
        st.warning("Nenhum template configurado. O mês será criado vazio.")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("✅ Criar Mês", type="primary", use_container_width=True):
            CashFlowRepository.create_month(user_id, selected_year, selected_m)
            st.rerun()
    with c2:
        if st.button("Cancelar", use_container_width=True):
            st.rerun()


@st.dialog("✏️ Editar Mês", width="large")
def edit_month_dialog(month_data: dict):
    month_label = MONTH_NAMES[month_data["month"] - 1]
    st.markdown(f"### {month_label} / {month_data['year']}")

    # Always reload fresh data from DB so edits reflect immediately
    fresh = CashFlowRepository.get_month_with_entries(
        user_id, month_data["year"], month_data["month"]
    )
    entries = sorted(fresh["entries"], key=lambda x: x["day"]) if fresh else []
    month_data = fresh or month_data

    # ── Add entry form ─────────────────────────────────────────────────────────
    add_key = st.session_state.get("cf_add_entry_key", 0)
    st.markdown("**➕ Novo Lançamento**")
    ec1, ec2, ec3, ec4, ec5 = st.columns([3, 1, 2, 1.5, 1])
    new_name = ec1.text_input("Nome *", key=f"new_entry_name_{add_key}")
    new_day = ec2.number_input(
        "Dia *",
        min_value=1,
        max_value=31,
        value=1,
        step=1,
        key=f"new_entry_day_{add_key}",
    )
    new_value = ec3.number_input(
        "Valor *",
        min_value=0.0,
        format="%.2f",
        step=0.01,
        key=f"new_entry_value_{add_key}",
    )
    new_type = ec4.selectbox(
        "Tipo *",
        ["saida", "entrada"],
        format_func=lambda x: "💸 Saída" if x == "saida" else "💰 Entrada",
        key=f"new_entry_type_{add_key}",
    )
    ec5.markdown("<br>", unsafe_allow_html=True)
    if ec5.button("💾", type="primary", key=f"new_entry_save_{add_key}"):
        if not new_name.strip() or new_value <= 0:
            st.error("Nome e valor são obrigatórios.")
        else:
            CashFlowRepository.add_entry(
                month_id=month_data["id"],
                name=new_name.strip(),
                day=int(new_day),
                value=new_value,
                type_=new_type,
            )
            st.session_state["cf_add_entry_key"] = add_key + 1
            st.session_state[
                "cf_edit_month"
            ] = CashFlowRepository.get_month_with_entries(
                user_id, month_data["year"], month_data["month"]
            )
            st.rerun(scope="fragment")
    st.divider()

    # ── Entries table ──────────────────────────────────────────────────────────
    if not entries:
        st.info("Nenhum lançamento cadastrado neste mês.")
    else:
        header = st.columns([3, 1, 2, 1.5, 0.7, 0.7])
        for h, label in zip(header, ["Nome", "Dia", "Valor", "Tipo", "✏️", "🗑️"]):
            h.markdown(f"**{label}**")
        st.divider()

        for e in entries:
            if st.session_state.get(f"editing_entry_{e['id']}"):
                # Inline edit row
                ec = st.columns([3, 1, 2, 1.5, 0.7, 0.7])
                e_name = ec[0].text_input(
                    "Nome",
                    value=e["name"],
                    key=f"ee_name_{e['id']}",
                    label_visibility="collapsed",
                )
                e_day = ec[1].number_input(
                    "Dia",
                    value=e["day"],
                    key=f"ee_day_{e['id']}",
                    label_visibility="collapsed",
                    min_value=1,
                    max_value=31,
                    step=1,
                )
                e_value = ec[2].number_input(
                    "Valor",
                    value=e["value"],
                    key=f"ee_val_{e['id']}",
                    label_visibility="collapsed",
                    min_value=0.0,
                    format="%.2f",
                    step=0.01,
                )
                e_type = ec[3].selectbox(
                    "Tipo",
                    ["saida", "entrada"],
                    index=0 if e["type"] == "saida" else 1,
                    format_func=lambda x: "💸 Saída" if x == "saida" else "💰 Entrada",
                    key=f"ee_type_{e['id']}",
                    label_visibility="collapsed",
                )
                if ec[4].button("💾", key=f"ee_save_{e['id']}", type="primary"):
                    if not e_name.strip() or e_value <= 0:
                        st.error("Nome e valor obrigatórios.")
                    else:
                        CashFlowRepository.update_entry(
                            e["id"], e_name.strip(), int(e_day), e_value, e_type
                        )
                        st.session_state.pop(f"editing_entry_{e['id']}", None)
                        st.session_state[
                            "cf_edit_month"
                        ] = CashFlowRepository.get_month_with_entries(
                            user_id, month_data["year"], month_data["month"]
                        )
                        st.rerun(scope="fragment")
                if ec[5].button("❌", key=f"ee_cancel_{e['id']}"):
                    st.session_state.pop(f"editing_entry_{e['id']}", None)
                    st.rerun(scope="fragment")
            else:
                row = st.columns([3, 1, 2, 1.5, 0.7, 0.7])
                row[0].markdown(e["name"])
                row[1].markdown(str(e["day"]))
                val_color = "green" if e["type"] == "entrada" else "red"
                row[2].markdown(f":{val_color}[{format_currency(e['value'])}]")
                row[3].markdown("💰 Entrada" if e["type"] == "entrada" else "💸 Saída")
                if row[4].button("✏️", key=f"edit_entry_{e['id']}"):
                    st.session_state[f"editing_entry_{e['id']}"] = True
                    st.rerun(scope="fragment")
                if row[5].button("🗑️", key=f"del_entry_{e['id']}"):
                    CashFlowRepository.delete_entry(e["id"])
                    st.session_state[
                        "cf_edit_month"
                    ] = CashFlowRepository.get_month_with_entries(
                        user_id, month_data["year"], month_data["month"]
                    )
                    st.rerun(scope="fragment")

    # ── Summary ────────────────────────────────────────────────────────────────
    if entries:
        st.divider()
        total_in = sum(e["value"] for e in entries if e["type"] == "entrada")
        total_out = sum(e["value"] for e in entries if e["type"] == "saida")
        saldo = total_in - total_out
        s1, s2, s3 = st.columns(3)
        s1.metric("💰 Entradas", format_currency(total_in))
        s2.metric("💸 Saídas", format_currency(total_out))
        saldo_delta_color = "normal" if saldo >= 0 else "inverse"
        s3.metric(
            "📈 Saldo", "", delta=format_currency(saldo), delta_color=saldo_delta_color
        )

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("✅ Concluir", type="primary", use_container_width=True):
            st.session_state.pop("cf_edit_month", None)
            st.rerun()
    with c2:
        if st.button("🗑️ Excluir Mês", use_container_width=True):
            CashFlowRepository.delete_month(user_id, month_data["id"])
            st.session_state.pop("cf_edit_month", None)
            st.rerun()


# ── Action buttons ─────────────────────────────────────────────────────────────
col_a, col_b, col_c = st.columns([2, 2, 6])
with col_a:
    if st.button("➕ Cadastrar Novo Mês", type="primary", use_container_width=True):
        st.session_state["cf_show_new_month"] = True
with col_b:
    if st.button("📋 Gerenciar Template", use_container_width=True):
        st.session_state["cf_show_template"] = True

# ── Annual summary table ───────────────────────────────────────────────────────
st.markdown(f"### Fluxo de Caixa — {selected_year}")

if not existing_months:
    st.info(
        "Nenhum mês criado para este ano. Clique em **Cadastrar Novo Mês** para começar."
    )
else:
    # Build full data for all existing months
    months_data = {}
    for m in existing_months:
        full = CashFlowRepository.get_month_with_entries(
            user_id, selected_year, m["month"]
        )
        if full:
            months_data[m["month"]] = full

    # Collect all unique entry names across months
    all_names: list[str] = []
    seen_names: set[str] = set()
    for m_num in sorted(months_data.keys()):
        for e in months_data[m_num]["entries"]:
            if e["name"] not in seen_names:
                all_names.append(e["name"])
                seen_names.add(e["name"])

    sorted_months = sorted(months_data.keys())
    col_headers = [MONTH_NAMES[m - 1][:3] for m in sorted_months]

    # ── Table header ──────────────────────────────────────────────────────────
    col_widths = [2.5] + [1] * len(sorted_months)
    header_cols = st.columns(col_widths)
    header_cols[0].markdown("**Descrição**")
    for i, (m_num, label) in enumerate(zip(sorted_months, col_headers)):
        btn_label = f"**{label}**"
        if header_cols[i + 1].button(
            btn_label, key=f"open_month_{m_num}", use_container_width=True
        ):
            st.session_state["cf_edit_month"] = months_data[m_num]
    st.divider()

    # ── Entry rows ────────────────────────────────────────────────────────────
    for name in all_names:
        row_cols = st.columns(col_widths)
        row_cols[0].markdown(name)
        for i, m_num in enumerate(sorted_months):
            entries = months_data[m_num]["entries"]
            match = next((e for e in entries if e["name"] == name), None)
            if match:
                color = "green" if match["type"] == "entrada" else "red"
                row_cols[i + 1].markdown(f":{color}[{format_currency(match['value'])}]")
            else:
                row_cols[i + 1].markdown("—")

    # ── Saldo row ─────────────────────────────────────────────────────────────
    st.divider()
    saldo_cols = st.columns(col_widths)
    saldo_cols[0].markdown("**Saldo**")
    saldo_acumulado = 0.0
    for i, m_num in enumerate(sorted_months):
        entries = months_data[m_num]["entries"]
        total_in = sum(e["value"] for e in entries if e["type"] == "entrada")
        total_out = sum(e["value"] for e in entries if e["type"] == "saida")
        saldo = total_in - total_out
        saldo_acumulado += saldo
        color = "green" if saldo >= 0 else "red"
        saldo_cols[i + 1].markdown(f":{color}[**{format_currency(saldo)}**]")

    # ── Accumulated saldo row ─────────────────────────────────────────────────
    accum_cols = st.columns(col_widths)
    accum_cols[0].markdown("**Saldo Acumulado**")
    running = 0.0
    for i, m_num in enumerate(sorted_months):
        entries = months_data[m_num]["entries"]
        total_in = sum(e["value"] for e in entries if e["type"] == "entrada")
        total_out = sum(e["value"] for e in entries if e["type"] == "saida")
        running += total_in - total_out
        color = "green" if running >= 0 else "red"
        accum_cols[i + 1].markdown(f":{color}[{format_currency(running)}]")


# ── Trigger dialogs ────────────────────────────────────────────────────────────
if st.session_state.pop("cf_show_new_month", False):
    new_month_dialog()

if st.session_state.pop("cf_show_template", False):
    template_dialog()

if "cf_edit_month" in st.session_state:
    edit_month_dialog(st.session_state["cf_edit_month"])
