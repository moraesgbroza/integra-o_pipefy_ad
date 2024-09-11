# integra-o_pipefy_ad
Automação para atualizar os dados do active directory no banco de colaboradores do pipefy

#itens que devem ser incluidos antes de rodar o projeto.

Criar Estrutura do Banco data base: name: pipefy_database. campos ou fields que devem conter no banco. mail(TEXT) telephone(TEXT) cc(TEXT) name(TEXT) cc_name(TEXT) active(TEXT) fullcc(TEXT)

Atualizar lista de Pessoas do AD localmente com o GET_AD_DATA isso irá gerar um json "filtered_users" com a lista de pessoas do ad.

Atualizar Lista de Pessoas Inativas no AD.

Depois dar um update no banco local UPDATE_DB_DATA

Gerar lista de centros de custo ou atualizar lista com o .py "see_list".

PIPEFY_PROJECT_REFRESH_PIPE para atualizar a lista de usários.

Os 3 scripts devem ser rodados em ordem para a atualização ocorrer da maneira correta
ordem ->GET_AD_DATA.py -> UPDATE_DB_DATA.py -> PIPEFY_PROJECT_REFRESH_PIPE.py
see_list.py é um passo opcional caso a base de dados de centros de custos no pipefy não estejam atualizadas. O código atualiza essas informações quando é rodado.
