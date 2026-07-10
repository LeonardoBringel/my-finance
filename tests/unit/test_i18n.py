import json

import pytest

from utils import i18n
from utils.i18n import DEFAULT_LOCALE, load_locale, t, t_raw


@pytest.fixture
def fake_locale(tmp_path, monkeypatch):
    """Escreve um locale temporário e aponta o loader para ele.

    Devolve uma função `write(mapping) -> locale_name`. O cache do loader é
    limpo antes e depois, para não vazar entre testes.
    """
    monkeypatch.setattr(i18n, "_LOCALES_DIR", tmp_path)
    i18n.load_locale.cache_clear()

    def write(mapping: dict, locale: str = "xx_XX") -> str:
        (tmp_path / f"{locale}.json").write_text(
            json.dumps(mapping), encoding="utf-8"
        )
        return locale

    yield write
    i18n.load_locale.cache_clear()


def test_chave_simples_resolve_o_texto():
    """Uma chave pontilhada existente devolve o texto correspondente."""
    assert t("common.all") == "Todos"
    assert t("common.no_data") == "Sem dados"


def test_chave_ausente_levanta_key_error_com_o_caminho():
    """Chave inexistente é bug de digitação: falha alto, com o caminho na mensagem."""
    with pytest.raises(KeyError, match="chave ausente 'common.inexistente'"):
        t("common.inexistente")
    with pytest.raises(KeyError, match="chave ausente 'nao.existe.nada'"):
        t("nao.existe.nada")


def test_chave_que_aponta_para_grupo_levanta_key_error():
    """Um nó intermediário não é um texto e não pode ser renderizado."""
    with pytest.raises(KeyError, match="aponta para um grupo"):
        t("common")


def test_interpolacao_substitui_os_placeholders(fake_locale):
    """kwargs são interpolados via str.format."""
    locale = fake_locale({"msg": {"count": "{count} item(s) de {name}"}})
    assert (
        i18n.t("msg.count", locale=locale, count=3, name="teste")
        == "3 item(s) de teste"
    )


def test_texto_com_chaves_literais_nao_estoura_sem_kwargs(fake_locale):
    """Sem kwargs, `.format` não roda — textos com `{` literal passam intactos."""
    locale = fake_locale({"css": "body { color: red; }"})
    assert i18n.t("css", locale=locale) == "body { color: red; }"
    assert i18n.t_raw("css", locale=locale) == "body { color: red; }"


def test_valor_vazio_retorna_string_vazia(fake_locale):
    """Chave com valor '' é legítima e não deve ser confundida com ausência."""
    locale = fake_locale({"msg": {"none": ""}})
    assert i18n.t("msg.none", locale=locale) == ""


def test_lista_preserva_ordem_e_devolve_copia():
    """`months.full` é indexada, fatiada e buscada por `.index()` nos call sites."""
    months = t("months.full")
    assert len(months) == 12
    assert months[0] == "Janeiro"
    assert months[11] == "Dezembro"
    assert months.index("Março") == 2
    assert months[2][:3] == "Mar"

    # Mutar o retorno não pode corromper o cache do loader.
    months.append("Décimo Terceiro")
    assert len(t("months.full")) == 12
    assert len(t_raw("months.full")) == 12


def test_loader_e_cacheado():
    """O mapping é lido do disco uma única vez por processo."""
    assert load_locale(DEFAULT_LOCALE) is load_locale(DEFAULT_LOCALE)


def test_locale_inexistente_falha_no_carregamento():
    """Locale ausente é fail-fast: um app sem textos é pior que um app que não sobe."""
    with pytest.raises(
        FileNotFoundError, match="locale 'zz_ZZ' não encontrado"
    ):
        load_locale("zz_ZZ")


def test_locale_malformado_falha_com_erro_explicito(fake_locale, tmp_path):
    """JSON inválido não pode degradar para um dict vazio."""
    (tmp_path / "yy_YY.json").write_text("{ nao é json", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON inválido"):
        i18n.load_locale("yy_YY")
