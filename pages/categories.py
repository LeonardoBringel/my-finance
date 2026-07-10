import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from components.styles import (
    init_onboarding,
    inject_global_css,
    inject_subpage_css,
    page_header,
)
from repositories import CategoriesRepository, TransactionsRepository
from utils.auth import require_login
from utils.category_types import ALL_TYPES, TYPE_LABELS, migration_targets
from utils.filters import ALL_FILTER
from utils.i18n import t

inject_global_css()

st.set_page_config(
    page_title=t("pages.categories.page_title"),
    page_icon="🏷️",
    layout="wide",
)

inject_subpage_css()

require_login()
user_id = st.session_state["current_user"]["id"]


# ── Onboarding ─────────────────────────────────────────────────────────────────
@st.dialog(t("pages.categories.onboarding_title"), width="large")
def onboarding_dialog():
    """Dialog de boas-vindas com instruções sobre o gerenciamento de categorias."""
    st.markdown(t("pages.categories.onboarding_body"))
    st.divider()
    if st.button(
        t("pages.categories.onboarding_confirm"),
        type="primary",
        use_container_width=True,
    ):
        st.rerun()


init_onboarding("cat", not CategoriesRepository.has_any_category(user_id))
if st.session_state.pop("cat_show_onboarding", False):
    onboarding_dialog()

page_header(
    t("pages.categories.header"),
    cleanup_keys=["show_form", "form_reset_counter"],
)

st.divider()

if success_msg := st.session_state.pop("cat_success_msg", None):
    st.success(success_msg)

# ── Nova Categoria ─────────────────────────────────────────────────────────────
if "new_cat_v" not in st.session_state:
    st.session_state["new_cat_v"] = 0

_v = st.session_state["new_cat_v"]

with st.expander(t("pages.categories.new_category"), expanded=False):
    col1, col2, col3 = st.columns([2, 1.5, 1])
    with col1:
        new_name = st.text_input(
            t("pages.categories.name"), key=f"new_cat_name_{_v}"
        )
    with col2:
        new_type = st.selectbox(
            t("pages.categories.type"),
            ALL_TYPES,
            format_func=lambda x: TYPE_LABELS[x],
            key=f"new_cat_type_{_v}",
        )
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(
            t("pages.categories.add"),
            type="primary",
            use_container_width=True,
        ):
            if new_name.strip():
                ok, msg = CategoriesRepository.create_category(
                    user_id, new_name.strip(), new_type
                )
                if ok:
                    st.session_state["cat_success_msg"] = msg
                    st.session_state["new_cat_v"] += 1
                    st.rerun()
                else:
                    st.error(msg)
            else:
                st.error(t("pages.categories.empty_name"))

# ── Lista de Categorias ────────────────────────────────────────────────────────
all_categories = CategoriesRepository.list_categories(user_id)
txn_counts = CategoriesRepository.get_transaction_counts_by_category(user_id)

f_type = st.selectbox(
    t("pages.categories.filter_by_type"),
    [ALL_FILTER, *ALL_TYPES],
    format_func=lambda x: (
        t("common.all") if x == ALL_FILTER else TYPE_LABELS[x]
    ),
)

categories = all_categories
if f_type != ALL_FILTER:
    categories = [c for c in all_categories if c["type"] == f_type]

st.markdown(t("pages.categories.count", count=len(categories)))
st.divider()

if not categories:
    st.info(t("pages.categories.none_found"))
else:
    header = st.columns([2.5, 1.5, 1.5, 0.8, 0.8])
    for h, label in zip(
        header,
        [
            t("pages.categories.col_name"),
            t("pages.categories.col_type"),
            t("pages.categories.col_transactions"),
            "✏️",
            "🗑️",
        ],
    ):
        h.markdown(f"**{label}**")
    st.divider()

    for cat in categories:
        cols = st.columns([2.5, 1.5, 1.5, 0.8, 0.8])
        cols[0].markdown(cat["name"])
        cols[1].markdown(TYPE_LABELS.get(cat["type"], cat["type"]))
        count = txn_counts.get(cat["id"], 0)
        cols[2].markdown(f"{count}")

        if cols[3].button("✏️", key=f"edit_cat_{cat['id']}"):
            st.session_state[f"editing_cat_{cat['id']}"] = True

        if cols[4].button("🗑️", key=f"del_cat_{cat['id']}"):
            st.session_state["confirm_del_cat_id"] = cat["id"]
            st.session_state["confirm_del_cat_name"] = cat["name"]

        # ── Descriptions expander ──────────────────────────────────────────────
        active_key = f"active_desc_{cat['id']}"
        descs = TransactionsRepository.get_descriptions_with_counts(
            user_id, cat["id"]
        )
        is_expanded = st.session_state.get(active_key) is not None
        with st.expander(
            t("pages.categories.descriptions", count=len(descs)),
            expanded=is_expanded,
        ):
            if not descs:
                st.info(t("pages.categories.no_descriptions"))
            else:
                dh = st.columns([3.5, 0.8, 0.7, 0.7, 0.7])
                dh[0].markdown(t("pages.categories.desc_col_description"))
                dh[1].markdown(t("pages.categories.desc_col_count"))
                dh[2].markdown(t("pages.categories.desc_col_edit"))
                dh[3].markdown(t("pages.categories.desc_col_migrate"))
                dh[4].markdown(t("pages.categories.desc_col_delete"))

                for idx, di in enumerate(descs):
                    dc = st.columns([3.5, 0.8, 0.7, 0.7, 0.7])
                    dc[0].markdown(di["description"])
                    dc[1].markdown(str(di["count"]))

                    if dc[2].button("✏️", key=f"drename_{cat['id']}_{idx}"):
                        st.session_state[active_key] = {
                            "idx": idx,
                            "action": "rename",
                        }
                        st.rerun()

                    if dc[3].button("↗️", key=f"dmigrate_{cat['id']}_{idx}"):
                        st.session_state[active_key] = {
                            "idx": idx,
                            "action": "migrate",
                        }
                        st.rerun()

                    if dc[4].button("🗑️", key=f"ddelete_{cat['id']}_{idx}"):
                        st.session_state[active_key] = {
                            "idx": idx,
                            "action": "delete",
                        }
                        st.rerun()

                    active = st.session_state.get(active_key)
                    if active and active["idx"] == idx:
                        if active["action"] == "rename":
                            rf1, rf2, rf3 = st.columns([3.5, 0.7, 0.7])
                            new_desc_val = rf1.text_input(
                                t("pages.categories.new_description"),
                                value=di["description"],
                                key=f"rnew_{cat['id']}_{idx}",
                            )
                            rf2.markdown("<br>", unsafe_allow_html=True)
                            if rf2.button(
                                "💾",
                                key=f"rsave_{cat['id']}_{idx}",
                                type="primary",
                            ):
                                trimmed = new_desc_val.strip()
                                if not trimmed:
                                    st.error(
                                        t("pages.categories.empty_description")
                                    )
                                elif trimmed == di["description"]:
                                    st.error(
                                        t("pages.categories.same_description")
                                    )
                                else:
                                    updated = TransactionsRepository.rename_description(
                                        user_id,
                                        cat["id"],
                                        di["description"],
                                        trimmed,
                                    )
                                    st.session_state.pop(active_key, None)
                                    st.session_state["cat_success_msg"] = t(
                                        "pages.categories.renamed",
                                        count=updated,
                                    )
                                    st.rerun()
                            rf3.markdown("<br>", unsafe_allow_html=True)
                            if rf3.button(
                                "❌", key=f"rcancel_{cat['id']}_{idx}"
                            ):
                                st.session_state.pop(active_key, None)
                                st.rerun()

                        elif active["action"] == "migrate":
                            mf1, mf2, mf3, mf4 = st.columns([2, 2, 0.7, 0.7])
                            # Destinos na mesma direção do dinheiro: uma despesa
                            # pode virar investimento, mas nunca entrada.
                            allowed = migration_targets(cat["type"])
                            tgt_cats = [
                                c
                                for c in all_categories
                                if c["type"] in allowed
                            ]
                            tgt_cat = mf1.selectbox(
                                t("pages.categories.target_category"),
                                tgt_cats,
                                format_func=lambda c: t(
                                    "pages.categories.target_category_label",
                                    name=c["name"],
                                    type=TYPE_LABELS[c["type"]],
                                ),
                                key=f"mtgtcat_{cat['id']}_{idx}",
                            )
                            tgt_descs = TransactionsRepository.get_descriptions_with_counts(
                                user_id, tgt_cat["id"]
                            )
                            tgt_desc_list = [
                                d["description"]
                                for d in tgt_descs
                                if not (
                                    tgt_cat["id"] == cat["id"]
                                    and d["description"] == di["description"]
                                )
                            ]
                            # Migrar para outra categoria preserva a descrição por
                            # padrão — sem isso, um destino vazio não teria opção.
                            if tgt_cat["id"] != cat["id"]:
                                tgt_desc_list = [di["description"]] + [
                                    d
                                    for d in tgt_desc_list
                                    if d != di["description"]
                                ]
                            if tgt_desc_list:
                                tgt_desc = mf2.selectbox(
                                    t("pages.categories.target_description"),
                                    tgt_desc_list,
                                    index=0,
                                    accept_new_options=True,
                                    key=f"mtgtdesc_{cat['id']}_{idx}_{tgt_cat['id']}",
                                )
                            else:
                                tgt_desc = None
                                mf2.info(
                                    t("pages.categories.target_category_empty")
                                )
                            mf3.markdown("<br>", unsafe_allow_html=True)
                            if mf3.button(
                                "💾",
                                key=f"msave_{cat['id']}_{idx}",
                                type="primary",
                            ):
                                tgt_desc = (tgt_desc or "").strip()
                                if not tgt_desc:
                                    st.error(
                                        t(
                                            "pages.categories.empty_target_description"
                                        )
                                    )
                                elif (
                                    tgt_cat["id"] == cat["id"]
                                    and tgt_desc == di["description"]
                                ):
                                    st.error(t("pages.categories.same_target"))
                                else:
                                    updated = TransactionsRepository.migrate_description(
                                        user_id,
                                        cat["id"],
                                        di["description"],
                                        tgt_cat["id"],
                                        tgt_desc,
                                    )
                                    st.session_state.pop(active_key, None)
                                    st.session_state["cat_success_msg"] = t(
                                        "pages.categories.migrated",
                                        count=updated,
                                    )
                                    st.rerun()
                            mf4.markdown("<br>", unsafe_allow_html=True)
                            if mf4.button(
                                "❌", key=f"mcancel_{cat['id']}_{idx}"
                            ):
                                st.session_state.pop(active_key, None)
                                st.rerun()

                        elif active["action"] == "delete":
                            df1, df2, df3 = st.columns([3.5, 0.7, 0.7])
                            df1.markdown(
                                t(
                                    "pages.categories.confirm_remove_description",
                                    count=di["count"],
                                )
                            )
                            df2.markdown("<br>", unsafe_allow_html=True)
                            if df2.button(
                                "💾",
                                key=f"ddsave_{cat['id']}_{idx}",
                                type="primary",
                            ):
                                updated = (
                                    TransactionsRepository.delete_description(
                                        user_id, cat["id"], di["description"]
                                    )
                                )
                                st.session_state.pop(active_key, None)
                                st.session_state["cat_success_msg"] = t(
                                    "pages.categories.description_updated",
                                    count=updated,
                                )
                                st.rerun()
                            df3.markdown("<br>", unsafe_allow_html=True)
                            if df3.button(
                                "❌", key=f"ddcancel_{cat['id']}_{idx}"
                            ):
                                st.session_state.pop(active_key, None)
                                st.rerun()

        if st.session_state.get(f"editing_cat_{cat['id']}"):
            with st.container():
                ec1, ec2, ec3, ec4 = st.columns([3, 2, 1, 1])
                with ec1:
                    edit_name = st.text_input(
                        t("pages.categories.edit_name"),
                        value=cat["name"],
                        key=f"ename_{cat['id']}",
                    )
                with ec2:
                    edit_type = st.selectbox(
                        t("pages.categories.type"),
                        ALL_TYPES,
                        index=(
                            ALL_TYPES.index(cat["type"])
                            if cat["type"] in ALL_TYPES
                            else 0
                        ),
                        format_func=lambda x: TYPE_LABELS[x],
                        key=f"etype_{cat['id']}",
                    )
                with ec3:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button(
                        "💾", key=f"save_cat_{cat['id']}", type="primary"
                    ):
                        ok, msg = CategoriesRepository.update_category(
                            user_id, cat["id"], edit_name, edit_type
                        )
                        if ok:
                            st.success(msg)
                            st.session_state.pop(
                                f"editing_cat_{cat['id']}", None
                            )
                            st.rerun()
                        else:
                            st.error(msg)
                with ec4:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("❌", key=f"cancel_cat_{cat['id']}"):
                        st.session_state.pop(f"editing_cat_{cat['id']}", None)
                        st.rerun()

        if st.session_state.get("confirm_del_cat_id") == cat["id"]:
            st.warning(t("pages.categories.confirm_delete", name=cat["name"]))
            cc1, cc2, _ = st.columns([1, 1, 4])
            if cc1.button(
                t("pages.categories.confirm"),
                key=f"conf_cat_{cat['id']}",
                type="primary",
            ):
                CategoriesRepository.delete_category(user_id, cat["id"])
                st.session_state.pop("confirm_del_cat_id", None)
                st.session_state.pop("confirm_del_cat_name", None)
                st.rerun()
            if cc2.button(
                t("pages.categories.cancel"), key=f"canc_cat_{cat['id']}"
            ):
                st.session_state.pop("confirm_del_cat_id", None)
                st.session_state.pop("confirm_del_cat_name", None)
                st.rerun()
