"""Fonte única dos textos de interface da aplicação.

Todo texto visível ao usuário vive em `utils/locales/<locale>.json` e é lido por
`t()`. Nenhum arquivo de `pages/` ou `components/` deve conter literal de texto —
o teste `tests/unit/test_i18n_guard.py` falha se isso acontecer.

O loader é puro (json + cache), sem `streamlit`: `t()` é chamado em tempo de
import por decorators como `@st.dialog(t(...))`, quando nenhum cache do Streamlit
está disponível ainda.
"""

import json
from functools import cache
from pathlib import Path

DEFAULT_LOCALE = "pt_BR"

_LOCALES_DIR = Path(__file__).parent / "locales"


@cache
def load_locale(locale: str = DEFAULT_LOCALE) -> dict:
    """Carrega e cacheia o mapping de textos de um locale.

    Args:
        locale: Nome do locale (arquivo `utils/locales/<locale>.json`).

    Returns:
        Dicionário aninhado com os textos.

    Raises:
        FileNotFoundError: Se o arquivo do locale não existir.
        ValueError: Se o arquivo não for um JSON válido.
    """
    path = _LOCALES_DIR / f"{locale}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"i18n: locale '{locale}' não encontrado em {path}"
        )
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"i18n: locale '{locale}' é um JSON inválido: {exc}"
        ) from exc


def _resolve(key: str, locale: str) -> str | list[str]:
    """Navega a chave pontilhada dentro do mapping do locale.

    Raises:
        KeyError: Se qualquer segmento da chave não existir.
    """
    node = load_locale(locale)
    for part in key.split("."):
        if not isinstance(node, dict) or part not in node:
            raise KeyError(f"i18n: chave ausente '{key}' em '{locale}'")
        node = node[part]
    if isinstance(node, dict):
        raise KeyError(
            f"i18n: chave '{key}' em '{locale}' aponta para um grupo, não um texto"
        )
    return node


def t(key: str, /, locale: str = DEFAULT_LOCALE, **kwargs) -> str | list[str]:
    """Resolve um texto pelo caminho pontilhado da sua chave.

    Args:
        key: Caminho da chave (ex: `pages.login.title`).
        locale: Locale a consultar.
        **kwargs: Valores de interpolação, aplicados via `str.format`.

    Returns:
        O texto correspondente, ou uma cópia da lista quando a chave aponta para
        uma (ex: `months.full`).

    Raises:
        KeyError: Se a chave não existir no locale.
    """
    value = _resolve(key, locale)
    if isinstance(value, list):
        # Cópia: `t()` devolve a instância cacheada; mutá-la corromperia o cache.
        return list(value)
    # `.format` só quando há o que interpolar, para não estourar em textos que
    # contenham chaves literais `{` `}`.
    return value.format(**kwargs) if kwargs else value


def t_raw(key: str, /, locale: str = DEFAULT_LOCALE) -> str | list[str]:
    """Resolve um texto sem nenhuma interpolação.

    Use quando o texto contém `{` ou `}` literais e não deve passar por `format`.
    """
    value = _resolve(key, locale)
    return list(value) if isinstance(value, list) else value
