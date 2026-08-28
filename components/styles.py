import streamlit as st

from utils.i18n import t
from utils.theme import (
    GREEN_DARK,
    GREEN_MAIN,
    TEXT_FAINT,
    WHITE,
    expense_palette,
)
from utils.version import get_app_version


def inject_global_css() -> None:
    """Injeta o CSS global da aplicação com o tema de botões primários em verde."""
    st.markdown(
        f"""
    <style>
        [data-testid="stBaseButton-primary"] {{
            background-color: {GREEN_MAIN} !important;
            border-color: {GREEN_MAIN} !important;
            color: {WHITE} !important;
        }}
        [data-testid="stBaseButton-primary"]:hover {{
            background-color: {GREEN_DARK} !important;
            border-color: {GREEN_DARK} !important;
        }}
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
        if st.button(
            t("components.styles.back_to_dashboard"), use_container_width=True
        ):
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


def render_app_version() -> None:
    """Renderiza a versão da aplicação como rodapé discreto e centralizado."""
    st.markdown(
        f"<p style='text-align: center; color: {TEXT_FAINT}; "
        f"font-size: 0.9rem;'>{get_app_version()}</p>",
        unsafe_allow_html=True,
    )


def category_pills_css(key: str, n: int) -> str:
    """Monta as regras CSS que pintam o marcador de cor de cada pill de categoria.

    Cada categoria vira uma pill do `st.pills`; como o widget não tem API de
    cor por opção, o marcador é um `::before` posicional (`nth-of-type`),
    escopado pela classe `st-key-{key}` que o Streamlit gera para o widget.
    O índice `i` usado aqui é o mesmo que `expense_palette` usa para colorir o
    trace correspondente no gráfico — a correspondência pill x barra é
    estrutural (por posição), não por texto da categoria.

    Quando a pill não está selecionada (`aria-pressed` diferente de `"true"`),
    o marcador continua visível, só atenuado — ele é a legenda mesmo quando a
    categoria está oculta do gráfico.

    Args:
        key: Chave do widget `st.pills` (mesma passada em `st.pills(key=...)`).
        n: Quantidade de categorias/pills a colorir.

    Returns:
        String CSS pronta para um bloco `<style>` (sem as tags); string vazia
        quando `n <= 0`, sem gerar regra órfã.
    """
    if n <= 0:
        return ""

    colors = expense_palette(n)
    scope = f'.st-key-{key} [data-testid="stButtonGroup"] button'
    rules = []
    for i, color in enumerate(colors):
        position = i + 1
        rules.append(f"""
    {scope}:nth-of-type({position})::before {{
        content: "";
        display: inline-block;
        width: 10px;
        height: 10px;
        margin-right: 6px;
        border-radius: 2px;
        vertical-align: middle;
        background-color: {color};
    }}
    {scope}:not([aria-pressed="true"]):nth-of-type({position})::before {{
        opacity: 0.45;
    }}""")
    return "\n".join(rules)


def inject_category_pills_css(key: str, n: int) -> None:
    """Injeta o CSS dos marcadores de cor das pills de categoria, se houver algum.

    Args:
        key: Chave do widget `st.pills` (mesma passada em `st.pills(key=...)`).
        n: Quantidade de categorias/pills a colorir.
    """
    css = category_pills_css(key, n)
    if css:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
