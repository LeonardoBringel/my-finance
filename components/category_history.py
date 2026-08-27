import streamlit as st

from components.charts import category_history_chart
from repositories import TransactionsRepository
from utils.i18n import t


@st.dialog(t("components.category_history.dialog_title"), width="large")
def category_history_dialog(
    user_id: int, category: str, year: int, month: int
) -> None:
    """Dialog com o histórico de 12 meses de uma categoria.

    Carga lazy e memorizada em `session_state` por (categoria, ano, mês) — não
    refaz a busca a cada rerun enquanto o dialog está aberto (AD-022).

    Args:
        user_id: ID do usuário autenticado.
        category: Nome da categoria exibida.
        year: Ano de referência do mês final da janela.
        month: Mês de referência do mês final da janela.
    """
    st.markdown(f"### {category}")
    cache_key = f"cat_hist_{category}_{year}_{month}"
    if cache_key not in st.session_state:
        st.session_state[cache_key] = (
            TransactionsRepository.get_category_history(
                user_id, category, year, month
            )
        )
    history = st.session_state[cache_key]
    st.plotly_chart(
        category_history_chart(history),
        width="stretch",
        key="cat_history_chart",
    )
    if st.button(
        t("components.category_history.close"), use_container_width=True
    ):
        st.session_state.pop("cat_history_open", None)
        st.rerun()


def clear_category_history_states() -> None:
    """Remove da session_state todas as chaves do dialog de histórico.

    Chamado no início de cada carregamento de página para garantir que o
    dialog não reabra sozinho em reruns subsequentes (ex: fechar via X nativo),
    e para que o cache memorizado não sobreviva ao fechamento do dialog.
    """
    st.session_state.pop("cat_history_open", None)
    for key in [k for k in st.session_state if k.startswith("cat_hist_")]:
        st.session_state.pop(key, None)
