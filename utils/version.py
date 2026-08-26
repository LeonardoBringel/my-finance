import os

# Versão exibida quando o arquivo `.version` não existe (ex: execução local).
FALLBACK_VERSION = "latest"

_VERSION_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".version"
)


def get_app_version() -> str:
    """Lê a versão da aplicação do arquivo `.version` na raiz do projeto.

    O sufixo de build (tudo após o primeiro '-') é descartado, de forma que
    'v1.0.0-rc1' vira 'v1.0.0'.

    Returns:
        A versão da aplicação, ou 'latest' se o arquivo não existir.
    """
    if not os.path.exists(_VERSION_FILE):
        return FALLBACK_VERSION

    with open(_VERSION_FILE) as f:
        version = f.read().strip()

    return version.split("-")[0] if version else FALLBACK_VERSION
