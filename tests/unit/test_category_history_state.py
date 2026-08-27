"""Testes unitários da limpeza de estado do dialog de histórico de categoria.

O dialog é disparado por `cat_history_open` e memoriza o resultado da consulta em
`cat_hist_<categoria>_<ano>_<mês>`. Sem uma limpeza na entrada da página, fechar o
dialog pelo X nativo deixa o gatilho vivo e o dialog reabre sozinho no próximo rerun.
"""

import streamlit as st

from components.category_history import clear_category_history_states


def _reset_session_state() -> None:
    """Zera o session_state para isolar cada teste."""
    for key in list(st.session_state):
        st.session_state.pop(key, None)


def test_clears_trigger_and_memoized_history():
    """Remove o gatilho do dialog e todo cache memorizado do histórico."""
    _reset_session_state()
    st.session_state["cat_history_open"] = "Mercado"
    st.session_state["cat_hist_Mercado_2026_8"] = [{"month": "08/26"}]
    st.session_state["cat_hist_Lazer_2025_12"] = []

    clear_category_history_states()

    assert "cat_history_open" not in st.session_state
    assert [k for k in st.session_state if k.startswith("cat_hist_")] == []


def test_preserves_unrelated_session_keys():
    """Não toca em chaves que não pertencem ao dialog de histórico."""
    _reset_session_state()
    st.session_state["cat_history_open"] = "Mercado"
    st.session_state["cat_hist_Mercado_2026_8"] = [{"month": "08/26"}]
    st.session_state["current_user"] = {"id": 1}
    st.session_state["last_tipo"] = "saida"
    st.session_state["dash_onboarding_done"] = True

    clear_category_history_states()

    assert st.session_state["current_user"] == {"id": 1}
    assert st.session_state["last_tipo"] == "saida"
    assert st.session_state["dash_onboarding_done"] is True


def test_is_idempotent_on_empty_state():
    """Chamar com o estado já limpo não levanta exceção nem cria chaves."""
    _reset_session_state()

    clear_category_history_states()
    clear_category_history_states()

    assert "cat_history_open" not in st.session_state
    assert [k for k in st.session_state if k.startswith("cat_hist_")] == []
