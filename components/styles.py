import streamlit as st


def inject_global_css() -> None:
    """Injeta o CSS global da aplicação com o tema de botões primários em verde."""
    st.markdown(
        """
    <style>
        [data-testid="stBaseButton-primary"] {
            background-color: #4CAF50 !important;
            border-color: #4CAF50 !important;
            color: white !important;
        }
        [data-testid="stBaseButton-primary"]:hover {
            background-color: #43A047 !important;
            border-color: #43A047 !important;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )


def inject_subpage_css() -> None:
    """Injeta CSS de layout para subpáginas: oculta menu, header e sidebar."""
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


def page_header(title: str, cleanup_keys: list[str] | None = None) -> None:
    """Renderiza o cabeçalho padrão de subpágina com título e botão de volta ao Dashboard.

    Args:
        title: Texto do título (pode incluir emoji, ex: '📋 Lançamentos').
        cleanup_keys: Chaves de session_state a remover ao clicar em Dashboard.
    """
    col_title, col_back = st.columns([4, 1])
    with col_title:
        st.markdown(f"## {title}")
    with col_back:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🏠 Dashboard", use_container_width=True):
            for key in cleanup_keys or []:
                st.session_state.pop(key, None)
            st.switch_page("pages/dashboard.py")


def init_onboarding(state_key: str, condition: bool) -> None:
    """Agenda a exibição do dialog de onboarding uma única vez, se a condição for verdadeira.

    Args:
        state_key: Prefixo das chaves de session_state (ex: 'txn' usa 'txn_onboarding_done'
            e 'txn_show_onboarding').
        condition: True se o onboarding deve ser exibido (ex: usuário ainda não tem dados).
    """
    done_key = f"{state_key}_onboarding_done"
    if done_key not in st.session_state:
        if condition:
            st.session_state[f"{state_key}_show_onboarding"] = True
        st.session_state[done_key] = True
