from api_planilhas import listar_meses 
from api_planilhas import adicionar_listas_fim
from api_energia import req_energia

lista_meses = listar_meses()

todos_dados = {}
for i in lista_meses:
    todos_dados.update(req_energia(i[0], i[1]))
    
adicionar_listas_fim(todos_dados)