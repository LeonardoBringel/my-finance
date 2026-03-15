import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import database as db

st.set_page_config(page_title="Categorias", page_icon="🏷️", layout="wide")
db.init_db()

st.markdown("""
<style>
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("## 🏷️ Gerenciar Categorias")

col_back, _ = st.columns([1, 5])
with col_back:
    if st.button("🏠 Voltar ao Dashboard"):
        st.switch_page("app.py")

st.divider()

# ── Add New Category ───────────────────────────────────────────────────────────
with st.expander("➕ Nova Categoria", expanded=False):
    col1, col2, col3 = st.columns([2, 1.5, 1])
    with col1:
        new_name = st.text_input("Nome da categoria", key="new_cat_name")
    with col2:
        new_type = st.selectbox(
            "Tipo",
            ["saida", "entrada", "ambos"],
            format_func=lambda x: {"saida": "💸 Saída", "entrada": "💰 Entrada", "ambos": "🔄 Ambos"}[x],
            key="new_cat_type"
        )
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 Adicionar", type="primary", use_container_width=True):
            if new_name.strip():
                ok, msg = db.add_category(new_name.strip(), new_type)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
            else:
                st.error("Digite um nome para a categoria.")

# ── Category List ──────────────────────────────────────────────────────────────
categories = db.get_all_categories()

type_labels = {"entrada": "💰 Entrada", "saida": "💸 Saída", "ambos": "🔄 Ambos"}

# Filter
f_type = st.selectbox("Filtrar por tipo", ["Todos", "entrada", "saida", "ambos"],
                      format_func=lambda x: "Todos" if x == "Todos" else type_labels[x])

if f_type != "Todos":
    categories = [c for c in categories if c["type"] == f_type]

st.markdown(f"**{len(categories)} categoria(s)**")
st.divider()

if not categories:
    st.info("Nenhuma categoria encontrada.")
else:
    header = st.columns([3, 2, 0.8, 0.8])
    for h, label in zip(header, ["Nome", "Tipo", "✏️", "🗑️"]):
        h.markdown(f"**{label}**")
    st.divider()

    for cat in categories:
        cols = st.columns([3, 2, 0.8, 0.8])
        cols[0].markdown(cat["name"])
        cols[1].markdown(type_labels.get(cat["type"], cat["type"]))

        if cols[2].button("✏️", key=f"edit_cat_{cat['id']}"):
            st.session_state[f"editing_cat_{cat['id']}"] = True

        if cols[3].button("🗑️", key=f"del_cat_{cat['id']}"):
            st.session_state[f"confirm_del_cat_{cat['id']}"] = True

        # Inline edit form
        if st.session_state.get(f"editing_cat_{cat['id']}"):
            with st.container():
                ec1, ec2, ec3, ec4 = st.columns([3, 2, 1, 1])
                with ec1:
                    edit_name = st.text_input("Nome", value=cat["name"], key=f"ename_{cat['id']}")
                with ec2:
                    edit_type = st.selectbox(
                        "Tipo",
                        ["saida", "entrada", "ambos"],
                        index=["saida", "entrada", "ambos"].index(cat["type"]),
                        format_func=lambda x: type_labels[x],
                        key=f"etype_{cat['id']}"
                    )
                with ec3:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("💾", key=f"save_cat_{cat['id']}", type="primary"):
                        ok, msg = db.update_category(cat["id"], edit_name, edit_type)
                        if ok:
                            st.success(msg)
                            st.session_state.pop(f"editing_cat_{cat['id']}", None)
                            st.rerun()
                        else:
                            st.error(msg)
                with ec4:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("❌", key=f"cancel_cat_{cat['id']}"):
                        st.session_state.pop(f"editing_cat_{cat['id']}", None)
                        st.rerun()

        # Delete confirm
        if st.session_state.get(f"confirm_del_cat_{cat['id']}"):
            st.warning(f"⚠️ Excluir categoria **{cat['name']}**?")
            cc1, cc2, _ = st.columns([1, 1, 4])
            if cc1.button("✅ Confirmar", key=f"conf_cat_{cat['id']}", type="primary"):
                db.delete_category(cat["id"])
                st.session_state.pop(f"confirm_del_cat_{cat['id']}", None)
                st.rerun()
            if cc2.button("❌ Cancelar", key=f"canc_cat_{cat['id']}"):
                st.session_state.pop(f"confirm_del_cat_{cat['id']}", None)
                st.rerun()
