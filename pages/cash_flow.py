import os
import sys
from datetime import datetime

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from components.styles import (
    init_onboarding,
    inject_global_css,
    inject_subpage_css,
    page_header,
)
from repositories import (
    CashFlowEntryRepository,
    CashFlowMonthRepository,
    CashFlowTemplateRepository,
)
from utils.auth import require_login
from utils.data_format_utils import (
    MONTH_NAMES,
    format_currency,
)
from utils.i18n import t

inject_global_css()

st.set_page_config(
    page_title=t("pages.cash_flow.page_title"),
    page_icon="💵",
    layout="wide",
)

inject_subpage_css()

require_login()
user_id = st.session_state["current_user"]["id"]

page_header(t("pages.cash_flow.header"))

# ── Seletor de ano ─────────────────────────────────────────────────────────────
current_year = datetime.now().year
selected_year = st.selectbox(
    t("pages.cash_flow.year"),
    list(range(current_year - 3, current_year + 3)),
    index=3,
    key="cf_year",
)

st.divider()

# Limpa estado de edição ao entrar na página (evita abertura automática do modal)
st.session_state.pop("cf_edit_month", None)

# ── Carregar dados ─────────────────────────────────────────────────────────────
# Uma única consulta traz todos os meses do ano com seus lançamentos (sem N+1).
existing_months = CashFlowMonthRepository.list_months_with_entries(
    user_id, selected_year
)
existing_month_nums = {m["month"] for m in existing_months}

init_onboarding("cf", not CashFlowMonthRepository.has_any_month(user_id))


# ── Dialogs ────────────────────────────────────────────────────────────────────


@st.dialog(t("pages.cash_flow.template_dialog_title"), width="large")
def template_dialog():
    """Dialog para configurar os lançamentos padrão do template de fluxo de caixa."""
    st.markdown(t("pages.cash_flow.template_intro"))
    tmpl = CashFlowTemplateRepository.get_template(user_id)
    items = tmpl["items"] if tmpl else []

    tmpl_items_key = f"tmpl_items_{user_id}"
    tmpl_sorted_key = f"tmpl_items_sorted_{user_id}"

    if tmpl_items_key not in st.session_state:
        st.session_state[tmpl_items_key] = [dict(i) for i in items]

    if tmpl_sorted_key not in st.session_state:
        st.session_state[tmpl_items_key] = sorted(
            st.session_state[tmpl_items_key],
            key=lambda x: (x["day"], x["name"].lower()),
        )
        st.session_state[tmpl_sorted_key] = True
    tmpl_items = st.session_state[tmpl_items_key]

    if tmpl_items:
        h = st.columns([3, 1, 2, 1.5, 0.7])
        for col, label in zip(
            h,
            [
                t("pages.cash_flow.col_name"),
                t("pages.cash_flow.col_day"),
                t("pages.cash_flow.col_value_brl"),
                t("pages.cash_flow.col_type"),
                "🗑️",
            ],
        ):
            col.markdown(f"**{label}**")

    to_remove = None
    for idx, item in enumerate(tmpl_items):
        c = st.columns([3, 1, 2, 1.5, 0.7])
        item["name"] = c[0].text_input(
            t("pages.cash_flow.col_name"),
            value=item["name"],
            key=f"ti_name_{idx}",
            label_visibility="collapsed",
        )
        item["day"] = c[1].number_input(
            t("pages.cash_flow.col_day"),
            value=item["day"],
            key=f"ti_day_{idx}",
            label_visibility="collapsed",
            min_value=1,
            max_value=31,
            step=1,
        )
        item["value"] = c[2].number_input(
            t("pages.cash_flow.col_value"),
            value=item["value"],
            key=f"ti_val_{idx}",
            label_visibility="collapsed",
            min_value=0.0,
            format="%.2f",
            step=0.01,
        )
        item["type"] = c[3].selectbox(
            t("pages.cash_flow.col_type"),
            ["saida", "entrada"],
            index=0 if item["type"] == "saida" else 1,
            format_func=lambda x: (
                t("domain.category_type.saida")
                if x == "saida"
                else t("domain.category_type.entrada")
            ),
            key=f"ti_type_{idx}",
            label_visibility="collapsed",
        )
        if c[4].button("🗑️", key=f"ti_del_{idx}"):
            to_remove = idx

    if to_remove is not None:
        st.session_state[tmpl_items_key].pop(to_remove)
        st.rerun(scope="fragment")

    if st.button(t("pages.cash_flow.add_item"), use_container_width=True):
        st.session_state[tmpl_items_key].append(
            {"name": "", "day": 1, "value": 0.0, "type": "saida"}
        )
        st.rerun(scope="fragment")

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button(
            t("pages.cash_flow.save_template"),
            type="primary",
            use_container_width=True,
        ):
            valid = [
                i
                for i in st.session_state[tmpl_items_key]
                if i["name"].strip() and i["value"] > 0
            ]
            if not valid:
                st.error(t("pages.cash_flow.template_needs_item"))
            else:
                CashFlowTemplateRepository.save_template(user_id, valid)
                st.session_state.pop(tmpl_items_key, None)
                st.session_state.pop(tmpl_sorted_key, None)
                st.success(t("pages.cash_flow.template_saved"))
                st.rerun()
    with c2:
        if st.button(t("pages.cash_flow.close"), use_container_width=True):
            st.session_state.pop(tmpl_items_key, None)
            st.session_state.pop(tmpl_sorted_key, None)
            st.rerun()


@st.dialog(t("pages.cash_flow.new_month_dialog_title"), width="small")
def new_month_dialog():
    """Dialog para criar um novo mês no fluxo de caixa."""
    available = [m for m in range(1, 13) if m not in existing_month_nums]
    if not available:
        st.info(t("pages.cash_flow.all_months_created"))
        if st.button(t("pages.cash_flow.close"), use_container_width=True):
            st.rerun()
        return

    month_name = st.selectbox(
        t("pages.cash_flow.month_required"),
        [MONTH_NAMES[m - 1] for m in available],
        key="new_month_sel",
    )
    selected_m = available[
        [MONTH_NAMES[m - 1] for m in available].index(month_name)
    ]

    tmpl = CashFlowTemplateRepository.get_template(user_id)
    if tmpl and tmpl["items"]:
        st.info(t("pages.cash_flow.template_applied", count=len(tmpl["items"])))
    else:
        st.warning(t("pages.cash_flow.no_template"))

    c1, c2 = st.columns(2)
    with c1:
        if st.button(
            t("pages.cash_flow.create_month"),
            type="primary",
            use_container_width=True,
        ):
            CashFlowMonthRepository.create_month(
                user_id, selected_year, selected_m
            )
            st.rerun()
    with c2:
        if st.button(t("pages.cash_flow.cancel"), use_container_width=True):
            st.rerun()


@st.dialog(t("pages.cash_flow.edit_month_dialog_title"), width="large")
def edit_month_dialog(month_data: dict):
    """Dialog para adicionar, editar e remover lançamentos de um mês do fluxo de caixa."""
    month_label = MONTH_NAMES[month_data["month"] - 1]
    st.markdown(
        t(
            "pages.cash_flow.month_heading",
            month=month_label,
            year=month_data["year"],
        )
    )

    fresh = CashFlowMonthRepository.get_month_with_entries(
        user_id, month_data["year"], month_data["month"]
    )
    entries = (
        sorted(fresh["entries"], key=lambda x: (x["day"], x["name"].lower()))
        if fresh
        else []
    )
    month_data = fresh or month_data

    # ── Formulário de novo lançamento ──────────────────────────────────────────
    add_key = st.session_state.get("cf_add_entry_key", 0)
    st.markdown(t("pages.cash_flow.new_entry"))
    ec1, ec2, ec3, ec4, ec5 = st.columns([3, 1, 2, 1.5, 1])
    new_name = ec1.text_input(
        t("pages.cash_flow.name_required"), key=f"new_entry_name_{add_key}"
    )
    new_day = ec2.number_input(
        t("pages.cash_flow.day_required"),
        min_value=1,
        max_value=31,
        value=1,
        step=1,
        key=f"new_entry_day_{add_key}",
    )
    new_value = ec3.number_input(
        t("pages.cash_flow.value_required"),
        min_value=0.0,
        format="%.2f",
        step=0.01,
        key=f"new_entry_value_{add_key}",
    )
    new_type = ec4.selectbox(
        t("pages.cash_flow.type_required"),
        ["saida", "entrada"],
        format_func=lambda x: (
            t("domain.category_type.saida")
            if x == "saida"
            else t("domain.category_type.entrada")
        ),
        key=f"new_entry_type_{add_key}",
    )
    ec5.markdown("<br>", unsafe_allow_html=True)
    if ec5.button("💾", type="primary", key=f"new_entry_save_{add_key}"):
        if not new_name.strip() or new_value <= 0:
            st.error(t("pages.cash_flow.name_value_required"))
        else:
            CashFlowEntryRepository.add_entry(
                month_id=month_data["id"],
                name=new_name.strip(),
                day=int(new_day),
                value=new_value,
                type_=new_type,
            )
            st.session_state["cf_add_entry_key"] = add_key + 1
            st.session_state["cf_edit_month"] = (
                CashFlowMonthRepository.get_month_with_entries(
                    user_id, month_data["year"], month_data["month"]
                )
            )
            st.rerun(scope="fragment")
    st.divider()

    # ── Tabela de lançamentos ──────────────────────────────────────────────────
    if not entries:
        st.info(t("pages.cash_flow.no_entries"))
    else:
        header = st.columns([3, 1, 2, 1.5, 0.7, 0.7])
        for h, label in zip(
            header,
            [
                t("pages.cash_flow.col_name"),
                t("pages.cash_flow.col_day"),
                t("pages.cash_flow.col_value"),
                t("pages.cash_flow.col_type"),
                "✏️",
                "🗑️",
            ],
        ):
            h.markdown(f"**{label}**")
        st.divider()

        for e in entries:
            if st.session_state.get(f"editing_entry_{e['id']}"):
                ec = st.columns([3, 1, 2, 1.5, 0.7, 0.7])
                e_name = ec[0].text_input(
                    t("pages.cash_flow.col_name"),
                    value=e["name"],
                    key=f"ee_name_{e['id']}",
                    label_visibility="collapsed",
                )
                e_day = ec[1].number_input(
                    t("pages.cash_flow.col_day"),
                    value=e["day"],
                    key=f"ee_day_{e['id']}",
                    label_visibility="collapsed",
                    min_value=1,
                    max_value=31,
                    step=1,
                )
                e_value = ec[2].number_input(
                    t("pages.cash_flow.entry_col_value"),
                    value=e["value"],
                    key=f"ee_val_{e['id']}",
                    label_visibility="collapsed",
                    min_value=0.0,
                    format="%.2f",
                    step=0.01,
                )
                e_type = ec[3].selectbox(
                    t("pages.cash_flow.col_type"),
                    ["saida", "entrada"],
                    index=0 if e["type"] == "saida" else 1,
                    format_func=lambda x: (
                        t("domain.category_type.saida")
                        if x == "saida"
                        else t("domain.category_type.entrada")
                    ),
                    key=f"ee_type_{e['id']}",
                    label_visibility="collapsed",
                )
                if ec[4].button("💾", key=f"ee_save_{e['id']}", type="primary"):
                    if not e_name.strip() or e_value <= 0:
                        st.error(t("pages.cash_flow.name_value_required_short"))
                    else:
                        CashFlowEntryRepository.update_entry(
                            e["id"], e_name.strip(), int(e_day), e_value, e_type
                        )
                        st.session_state.pop(f"editing_entry_{e['id']}", None)
                        st.session_state["cf_edit_month"] = (
                            CashFlowMonthRepository.get_month_with_entries(
                                user_id, month_data["year"], month_data["month"]
                            )
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
                row[3].markdown(
                    t("domain.category_type.entrada")
                    if e["type"] == "entrada"
                    else t("domain.category_type.saida")
                )
                if row[4].button("✏️", key=f"edit_entry_{e['id']}"):
                    st.session_state[f"editing_entry_{e['id']}"] = True
                    st.rerun(scope="fragment")
                if row[5].button("🗑️", key=f"del_entry_{e['id']}"):
                    CashFlowEntryRepository.delete_entry(e["id"])
                    st.session_state["cf_edit_month"] = (
                        CashFlowMonthRepository.get_month_with_entries(
                            user_id, month_data["year"], month_data["month"]
                        )
                    )
                    st.rerun(scope="fragment")

    # ── Resumo do mês ──────────────────────────────────────────────────────────
    if entries:
        st.divider()
        total_in = sum(e["value"] for e in entries if e["type"] == "entrada")
        total_out = sum(e["value"] for e in entries if e["type"] == "saida")
        saldo = total_in - total_out
        s1, s2, s3 = st.columns(3)
        s1.metric(
            t("pages.cash_flow.summary_income"), format_currency(total_in)
        )
        s2.metric(
            t("pages.cash_flow.summary_expenses"), format_currency(total_out)
        )
        saldo_delta_color = "normal" if saldo >= 0 else "inverse"
        s3.metric(
            t("pages.cash_flow.summary_balance"),
            "",
            delta=format_currency(saldo),
            delta_color=saldo_delta_color,
        )

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button(
            t("pages.cash_flow.finish"),
            type="primary",
            use_container_width=True,
        ):
            st.session_state.pop("cf_edit_month", None)
            st.session_state.pop("cf_confirm_delete_month", None)
            st.rerun()
    with c2:
        if st.button(
            t("pages.cash_flow.delete_month"), use_container_width=True
        ):
            st.session_state["cf_confirm_delete_month"] = True
            st.rerun(scope="fragment")

    if st.session_state.get("cf_confirm_delete_month"):
        st.warning(t("pages.cash_flow.confirm_delete_month", month=month_label))
        cc1, cc2 = st.columns(2)
        if cc1.button(
            t("pages.cash_flow.confirm_delete"),
            type="primary",
            use_container_width=True,
            key="confirm_del_month",
        ):
            CashFlowMonthRepository.delete_month(user_id, month_data["id"])
            st.session_state.pop("cf_edit_month", None)
            st.session_state.pop("cf_confirm_delete_month", None)
            st.rerun()
        if cc2.button(
            t("pages.cash_flow.cancel"),
            use_container_width=True,
            key="cancel_del_month",
        ):
            st.session_state.pop("cf_confirm_delete_month", None)
            st.rerun(scope="fragment")


@st.dialog(t("pages.cash_flow.onboarding_title"), width="large")
def onboarding_dialog():
    """Dialog de boas-vindas com explicação sobre o funcionamento do fluxo de caixa."""
    st.markdown(t("pages.cash_flow.onboarding_body"))

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button(
            t("pages.cash_flow.onboarding_config_template"),
            type="primary",
            use_container_width=True,
        ):
            st.session_state["cf_onboarding_done"] = True
            st.session_state["cf_show_template"] = True
            st.rerun()
    with c2:
        if st.button(
            t("pages.cash_flow.onboarding_skip"), use_container_width=True
        ):
            st.session_state["cf_onboarding_done"] = True
            st.session_state["cf_show_new_month"] = True
            st.rerun()


# ── Botões de ação ─────────────────────────────────────────────────────────────
col_a, col_b, col_c = st.columns([2, 2, 6])
with col_a:
    if st.button(
        t("pages.cash_flow.register_new_month"),
        type="primary",
        use_container_width=True,
    ):
        st.session_state["cf_show_new_month"] = True
with col_b:
    if st.button(
        t("pages.cash_flow.template_dialog_title"), use_container_width=True
    ):
        st.session_state["cf_show_template"] = True

# ── Tabela anual de fluxo de caixa ─────────────────────────────────────────────
st.markdown(t("pages.cash_flow.annual_header", year=selected_year))

if not existing_months:
    st.info(t("pages.cash_flow.no_months"))
else:
    months_data = {m["month"]: m for m in existing_months}

    name_days: dict[str, list[int]] = {}
    for m_num in sorted(months_data.keys()):
        for e in months_data[m_num]["entries"]:
            name_days.setdefault(e["name"], []).append(e["day"])

    all_names = sorted(
        name_days.keys(), key=lambda n: (min(name_days[n]), n.lower())
    )

    sorted_months = sorted(months_data.keys())
    col_headers = [MONTH_NAMES[m - 1][:3] for m in sorted_months]

    col_widths = [0.8, 2.5] + [1] * len(sorted_months)
    header_cols = st.columns(col_widths)
    header_cols[0].markdown(t("pages.cash_flow.table_day"))
    header_cols[1].markdown(t("pages.cash_flow.table_description"))
    for i, (m_num, label) in enumerate(zip(sorted_months, col_headers)):
        if header_cols[i + 2].button(
            f"**{label}**", key=f"open_month_{m_num}", use_container_width=True
        ):
            st.session_state["cf_edit_month"] = months_data[m_num]
    st.divider()

    for name in all_names:
        days = name_days[name]
        min_day, max_day = min(days), max(days)
        day_label = (
            str(min_day) if min_day == max_day else f"{min_day}–{max_day}"
        )

        row_cols = st.columns(col_widths)
        row_cols[0].markdown(day_label)
        row_cols[1].markdown(name)
        for i, m_num in enumerate(sorted_months):
            entries = months_data[m_num]["entries"]
            match = next((e for e in entries if e["name"] == name), None)
            if match:
                color = "green" if match["type"] == "entrada" else "red"
                row_cols[i + 2].markdown(
                    f":{color}[{format_currency(match['value'])}]"
                )
            else:
                row_cols[i + 2].markdown(t("common.empty_cell"))

    month_totals = {
        m_num: (
            sum(
                e["value"]
                for e in months_data[m_num]["entries"]
                if e["type"] == "entrada"
            ),
            sum(
                e["value"]
                for e in months_data[m_num]["entries"]
                if e["type"] == "saida"
            ),
        )
        for m_num in sorted_months
    }

    st.divider()
    total_in_cols = st.columns(col_widths)
    total_in_cols[0].markdown("")
    total_in_cols[1].markdown(t("pages.cash_flow.total_income"))
    for i, m_num in enumerate(sorted_months):
        total_in, _ = month_totals[m_num]
        total_in_cols[i + 2].markdown(f":green[{format_currency(total_in)}]")

    total_out_cols = st.columns(col_widths)
    total_out_cols[0].markdown("")
    total_out_cols[1].markdown(t("pages.cash_flow.total_expenses"))
    for i, m_num in enumerate(sorted_months):
        _, total_out = month_totals[m_num]
        total_out_cols[i + 2].markdown(f":red[{format_currency(total_out)}]")

    saldo_cols = st.columns(col_widths)
    saldo_cols[0].markdown("")
    saldo_cols[1].markdown(t("pages.cash_flow.total_balance"))
    for i, m_num in enumerate(sorted_months):
        total_in, total_out = month_totals[m_num]
        saldo = total_in - total_out
        color = "green" if saldo >= 0 else "red"
        saldo_cols[i + 2].markdown(f":{color}[**{format_currency(saldo)}**]")

    accum_cols = st.columns(col_widths)
    accum_cols[0].markdown("")
    accum_cols[1].markdown(t("pages.cash_flow.total_cumulative"))
    running = 0.0
    for i, m_num in enumerate(sorted_months):
        total_in, total_out = month_totals[m_num]
        running += total_in - total_out
        color = "green" if running >= 0 else "red"
        accum_cols[i + 2].markdown(f":{color}[{format_currency(running)}]")


# ── Disparar dialogs ────────────────────────────────────────────────────────────
if st.session_state.pop("cf_show_onboarding", False):
    onboarding_dialog()
elif st.session_state.pop("cf_show_new_month", False):
    new_month_dialog()

if st.session_state.pop("cf_show_template", False):
    template_dialog()

if "cf_edit_month" in st.session_state:
    edit_month_dialog(st.session_state["cf_edit_month"])
