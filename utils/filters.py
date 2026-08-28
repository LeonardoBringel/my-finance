"""Sentinelas de filtro da interface.

Um selectbox de filtro precisa de um valor que signifique "não filtrar". Esse
valor não pode ser o texto exibido ("Todos"/"Todas"): traduzir ou reescrever o
rótulo deixaria a comparação apontando para uma constante que ninguém mais
produz, e o filtro passaria a devolver lista vazia sem erro nenhum. Também não
pode colidir com um dado real — uma categoria chamada "Todas" quebraria o filtro.
"""

# Valor de opção que representa "sem filtro". Nunca é exibido nem persistido.
ALL_FILTER = "__all__"


def sync_all_pill_selection(
    selected: list[str], previous: list[str], real_options: list[str]
) -> list[str]:
    """Sincroniza um multi-select com uma pill `ALL_FILTER` de "selecionar tudo".

    Um widget de seleção múltipla não distingue "o usuário clicou na pill
    Todas" de "o usuário clicou numa opção real" — as duas coisas chegam como
    a mesma lista de opções marcadas. Comparar contra a seleção da rodada
    anterior resolve a ambiguidade:

    - `ALL_FILTER` entrou na seleção (não estava antes, está agora) → o
      usuário marcou "Todas": tudo passa a ficar selecionado.
    - `ALL_FILTER` saiu da seleção (estava antes, não está agora) → o usuário
      desmarcou "Todas": tudo passa a ficar desmarcado.
    - Nenhuma das duas → o usuário mexeu numa opção real: `ALL_FILTER` entra
      na seleção quando isso completa a cobertura de `real_options`, e sai
      quando quebra a cobertura.

    Args:
        selected: seleção bruta devolvida pelo widget nesta rodada (pode
            conter `ALL_FILTER` e/ou qualquer subconjunto de `real_options`).
        previous: seleção da rodada anterior, no mesmo formato.
        real_options: todas as opções reais (sem `ALL_FILTER`), na ordem de
            exibição do widget.

    Returns:
        Seleção corrigida, como subconjunto ordenado de
        `[ALL_FILTER] + real_options`.
    """
    selected_set = set(selected)
    previous_set = set(previous)

    all_was_selected = ALL_FILTER in previous_set
    all_is_selected = ALL_FILTER in selected_set

    if all_is_selected and not all_was_selected:
        corrected = set(real_options) | {ALL_FILTER}
    elif all_was_selected and not all_is_selected:
        corrected = set()
    else:
        real_selected = selected_set - {ALL_FILTER}
        if real_options and real_selected == set(real_options):
            corrected = real_selected | {ALL_FILTER}
        else:
            corrected = real_selected

    return [
        option
        for option in ([ALL_FILTER] + real_options)
        if option in corrected
    ]
