"""Guards estáticos que mantêm a extração de i18n íntegra ao longo do tempo.

Três invariantes, verificados por AST (sem rodar o Streamlit):

1. Nenhum literal de texto voltado ao usuário em `pages/` ou `components/`.
2. Toda chave passada a `t()`/`t_raw()` existe em `pt_BR.json`.
3. Toda chave folha do `pt_BR.json` é usada em algum lugar (sem órfãs).

Sem isto, a refatoração de i18n se desfaz no primeiro `st.button("texto")` novo.
"""

import ast
import re
from pathlib import Path

from utils.category_types import ALL_TYPES
from utils.i18n import load_locale

ROOT = Path(__file__).resolve().parents[2]
UI_DIRS = [ROOT / "pages", ROOT / "components"]
SOURCE_DIRS = [
    ROOT / "pages",
    ROOT / "components",
    ROOT / "utils",
    ROOT / "repositories",
]

# ── Regras do que NÃO é texto de idioma ────────────────────────────────────────
TAGS = re.compile(r"<[^>]*>")
HAS_LETTER = re.compile(r"[^\W\d_]")
HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{3,8}$")
# Sintaxe de cor do Streamlit markdown: ":green[...]", ":red[...]".
ST_COLOR = re.compile(r"^:\w+\[.*\]$")

# Valores de domínio persistidos (criptografados no banco), nunca traduzíveis.
DOMAIN_VALUES = set(ALL_TYPES)

# Constantes de API do Streamlit/Plotly passadas como string.
MAGIC = {
    "primary",
    "secondary",
    "password",
    "large",
    "small",
    "medium",
    "wide",
    "centered",
    "stretch",
    "collapsed",
    "visible",
    "hidden",
    "DD/MM/YYYY",
    "%Y-%m-%d",
    "%d/%m/%Y",
    "green",
    "red",
    "blue",
}

# Argumento posicional de texto destes widgets/funções.
ST_TEXT_POSITIONAL = {
    "markdown",
    "write",
    "button",
    "error",
    "success",
    "warning",
    "info",
    "toast",
    "caption",
    "header",
    "subheader",
    "title",
    "text",
    "text_input",
    "number_input",
    "selectbox",
    "date_input",
    "checkbox",
    "expander",
    "spinner",
    "metric",
    "radio",
    "multiselect",
    "text_area",
    "dialog",
    "form_submit_button",
    "download_button",
    "slider",
    "file_uploader",
    "link_button",
    "page_link",
    "pills",
    "segmented_control",
}
PROJECT_TEXT_POSITIONAL = {"page_header"}
TEXT_KWARGS = {"label", "help", "placeholder", "page_title", "body", "title"}

# Chamadas cujos argumentos-lista carregam valores, não texto (chaves, larguras).
NON_TEXT_CALLS = {
    "get",
    "pop",
    "setdefault",
    "switch_page",
    "columns",
    "getenv",
    "join",
    "dirname",
    "abspath",
    "insert",
    "open",
    "t",
    "t_raw",
    "session_state",
    "init_onboarding",
    "dict",
}
NON_TEXT_KWARGS = {
    "key",
    "type",
    "format",
    "page_icon",
    "width",
    "layout",
    "icon",
    "label_visibility",
    "delta_color",
    "mime",
    "color",
    "state",
    "cleanup_keys",
    "colors",
    "marker_color",
    "line_color",
}

# Único ponto onde uma chave de `t()` é montada dinamicamente (domínio fechado).
DYNAMIC_KEY_PREFIXES = {"domain.category_type"}


def _is_copy(s: str) -> bool:
    """True se a string é texto de idioma (não markup, cor, magic ou domínio)."""
    st = s.strip()
    if not st or st in MAGIC or st in DOMAIN_VALUES:
        return False
    if HEX_COLOR.match(st) or ST_COLOR.match(st) or st.startswith("<style"):
        return False
    return bool(HAS_LETTER.search(TAGS.sub("", st)))


def _fixed_text(node: ast.AST) -> str | None:
    """Texto fixo de um Constant str ou f-string; None se não for string."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(
            v.value
            for v in node.values
            if isinstance(v, ast.Constant) and isinstance(v.value, str)
        )
    return None


def _call_name(call: ast.Call) -> str | None:
    f = call.func
    base = getattr(f, "value", None)
    if isinstance(base, ast.Attribute) and base.attr == "session_state":
        return "session_state"
    return f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", None)


def _suppressed_list_items(tree: ast.AST) -> set[int]:
    """Ids de literais em listas que são argumento não-textual (chaves, larguras)."""
    out: set[int] = set()

    def drop(node: ast.AST) -> None:
        if isinstance(node, (ast.List, ast.Tuple)):
            out.update(id(el) for el in node.elts)

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if _call_name(node) in NON_TEXT_CALLS:
            for a in node.args:
                drop(a)
        for kw in node.keywords:
            if kw.arg in NON_TEXT_KWARGS:
                drop(kw.value)
    return out


def _literal_copy_hits(path: Path) -> list[tuple[int, str]]:
    """Literais de texto de idioma em duas superfícies: arg de st.* e item de lista."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    skip = _suppressed_list_items(tree)
    hits: list[tuple[int, str]] = []

    def report(node: ast.AST, text: str) -> None:
        if id(node) not in skip and _is_copy(text):
            hits.append((node.lineno, text.strip()[:60]))

    for node in ast.walk(tree):
        if isinstance(node, (ast.List, ast.Tuple)):
            for el in node.elts:
                txt = _fixed_text(el)
                if txt is not None:
                    report(el, txt)
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node)
        if name in ST_TEXT_POSITIONAL | PROJECT_TEXT_POSITIONAL and node.args:
            txt = _fixed_text(node.args[0])
            if txt is not None:
                report(node.args[0], txt)
        for kw in node.keywords:
            if kw.arg in TEXT_KWARGS:
                txt = _fixed_text(kw.value)
                if txt is not None:
                    report(kw.value, txt)
    return sorted(set(hits))


def _t_calls(path: Path) -> list[tuple[int, str | None]]:
    """Chamadas a t()/t_raw(): (linha, chave-literal ou None se dinâmica)."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    out: list[tuple[int, str | None]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _call_name(node) in {"t", "t_raw"}:
            if node.args and isinstance(node.args[0], ast.Constant):
                out.append((node.lineno, node.args[0].value))
            else:
                out.append((node.lineno, None))
    return out


def _leaf_keys(node, prefix=""):
    """Todas as chaves folha do mapping, em notação pontilhada."""
    for k, v in node.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            yield from _leaf_keys(v, key)
        else:
            yield key


def _key_exists(key: str) -> bool:
    node = load_locale()
    for part in key.split("."):
        if not isinstance(node, dict) or part not in node:
            return False
        node = node[part]
    return not isinstance(node, dict)


# ── Guard 1: nenhum literal de texto na UI ─────────────────────────────────────
def test_no_hardcoded_ui_text():
    """pages/ e components/ não podem conter texto de idioma hardcoded."""
    offenders = []
    for d in UI_DIRS:
        for path in sorted(d.rglob("*.py")):
            for ln, text in _literal_copy_hits(path):
                offenders.append(f"{path.relative_to(ROOT)}:{ln}: {text!r}")
    assert (
        not offenders
    ), "Texto hardcoded — extraia para pt_BR.json via t():\n" + "\n".join(
        offenders
    )


# ── Guard 2: toda chave de t() existe ──────────────────────────────────────────
def test_every_t_key_exists():
    """Uma chave passada a t() que não existe no JSON estoura em runtime."""
    missing = []
    for d in SOURCE_DIRS:
        for path in sorted(d.rglob("*.py")):
            for ln, key in _t_calls(path):
                if key is not None and not _key_exists(key):
                    missing.append(f"{path.relative_to(ROOT)}:{ln}: {key!r}")
    assert not missing, "Chaves de t() ausentes em pt_BR.json:\n" + "\n".join(
        missing
    )


def test_dynamic_keys_are_whitelisted():
    """Chaves dinâmicas não são verificáveis: só o domínio fechado é permitido."""
    dynamic_sites = []
    for d in SOURCE_DIRS:
        for path in sorted(d.rglob("*.py")):
            src = path.read_text(encoding="utf-8")
            tree = ast.parse(src, filename=str(path))
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Call)
                    and _call_name(node) in {"t", "t_raw"}
                    and node.args
                    and not isinstance(node.args[0], ast.Constant)
                ):
                    fixed = _fixed_text(node.args[0]) or ""
                    if not any(
                        fixed.startswith(p) for p in DYNAMIC_KEY_PREFIXES
                    ):
                        dynamic_sites.append(
                            f"{path.relative_to(ROOT)}:{node.lineno}"
                        )
    assert not dynamic_sites, (
        "Chave de t() montada dinamicamente fora do whitelist "
        f"({DYNAMIC_KEY_PREFIXES}):\n" + "\n".join(dynamic_sites)
    )


# ── Guard 3: nenhuma chave órfã ────────────────────────────────────────────────
def test_no_orphan_keys():
    """Toda chave do mapping deve ser referenciada em algum lugar do código."""
    used: set[str] = set()
    for d in SOURCE_DIRS:
        for path in sorted(d.rglob("*.py")):
            for _, key in _t_calls(path):
                if key is not None:
                    used.add(key)

    def is_used(key: str) -> bool:
        # Direto, ou consumido via prefixo dinâmico (domain.category_type.<valor>).
        return key in used or any(
            key.startswith(f"{p}.") for p in DYNAMIC_KEY_PREFIXES
        )

    orphans = [k for k in _leaf_keys(load_locale()) if not is_used(k)]
    assert (
        not orphans
    ), "Chaves órfãs em pt_BR.json (definidas e nunca usadas):\n" + "\n".join(
        orphans
    )
