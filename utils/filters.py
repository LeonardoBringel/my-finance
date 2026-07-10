"""Sentinelas de filtro da interface.

Um selectbox de filtro precisa de um valor que signifique "não filtrar". Esse
valor não pode ser o texto exibido ("Todos"/"Todas"): traduzir ou reescrever o
rótulo deixaria a comparação apontando para uma constante que ninguém mais
produz, e o filtro passaria a devolver lista vazia sem erro nenhum. Também não
pode colidir com um dado real — uma categoria chamada "Todas" quebraria o filtro.
"""

# Valor de opção que representa "sem filtro". Nunca é exibido nem persistido.
ALL_FILTER = "__all__"
