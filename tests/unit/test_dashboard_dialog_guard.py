"""Guard estático do ciclo de vida dos dialogs do dashboard.

Um dialog do Streamlit disparado por uma chave persistente em `session_state` reabre
sozinho no rerun seguinte quando o usuário fecha pelo X nativo (ou ESC), porque só o
botão interno de fechar remove a chave. O contrato é limpar todo gatilho na entrada da
página, antes do widget que o define. Sem este guard, `pages/` — que não tem cobertura
funcional — perde a correção na próxima edição.
"""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DASHBOARD = ROOT / "pages" / "dashboard.py"

# Gatilho persistente de dialog no dashboard → função de limpeza responsável.
CLEANUP_BY_TRIGGER = {
    "cat_history_open": (
        "clear_category_history_states",
        ROOT / "components" / "category_history.py",
    ),
    "show_form": (
        "clear_transaction_dialog_states",
        ROOT / "components" / "new_transaction.py",
    ),
}


def _is_session_state(node: ast.AST) -> bool:
    """True se o nó é o acesso `st.session_state`."""
    return isinstance(node, ast.Attribute) and node.attr == "session_state"


def _keys_popped_by(func_name: str, module_path: Path) -> set[str]:
    """Chaves literais removidas com `pop()` dentro da função de limpeza."""
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    func = next(
        n
        for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name == func_name
    )
    keys = set()
    for node in ast.walk(func):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "pop"
            and _is_session_state(node.func.value)
            and node.args
            and isinstance(node.args[0], ast.Constant)
        ):
            keys.add(node.args[0].value)
    return keys


def _cleanup_call_line(tree: ast.Module, func_name: str) -> int | None:
    """Linha da chamada de nível de módulo à função de limpeza, se houver."""
    for node in tree.body:
        if (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == func_name
        ):
            return node.lineno
    return None


def _first_write_line(tree: ast.Module, key: str) -> int | None:
    """Primeira linha em que a página escreve a chave em `session_state`."""
    lines = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (
                    isinstance(target, ast.Subscript)
                    and _is_session_state(target.value)
                    and isinstance(target.slice, ast.Constant)
                    and target.slice.value == key
                ):
                    lines.append(node.lineno)
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "setdefault"
            and _is_session_state(node.func.value)
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value == key
        ):
            lines.append(node.lineno)
    return min(lines) if lines else None


def test_dashboard_clears_every_dialog_trigger_before_defining_it():
    """Cada gatilho de dialog é limpo na entrada da página, antes do widget que o define."""
    tree = ast.parse(DASHBOARD.read_text(encoding="utf-8"))
    for trigger, (func_name, module_path) in CLEANUP_BY_TRIGGER.items():
        cleanup_line = _cleanup_call_line(tree, func_name)
        assert cleanup_line is not None, (
            f"pages/dashboard.py não chama {func_name}() no nível de módulo: "
            f"o dialog de '{trigger}' reabre sozinho após ser fechado pelo X nativo"
        )
        assert trigger in _keys_popped_by(
            func_name, module_path
        ), f"{func_name}() não remove '{trigger}' de session_state"
        write_line = _first_write_line(tree, trigger)
        assert write_line is not None, (
            f"'{trigger}' não é mais definido em pages/dashboard.py; "
            "atualize CLEANUP_BY_TRIGGER"
        )
        assert cleanup_line < write_line, (
            f"{func_name}() está na linha {cleanup_line}, depois da definição de "
            f"'{trigger}' na linha {write_line}: a limpeza apagaria o gatilho recém-criado"
        )


def test_transaction_cleanup_also_clears_the_form_reset_counter():
    """A limpeza do modal de lançamento remove gatilho e contador de reset juntos."""
    keys = _keys_popped_by(
        "clear_transaction_dialog_states",
        ROOT / "components" / "new_transaction.py",
    )
    assert {"show_form", "form_reset_counter"} <= keys
