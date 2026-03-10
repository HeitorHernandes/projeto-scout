Projeto Scout — CRUD de Futebol
Sistema de gerenciamento de dados de futebol desenvolvido em Python com SQLite3.
Permite cadastrar times, jogadores, partidas e registrar o desempenho individual de cada jogador por partida (scout).

Estrutura do projeto
main.py          # CRUD principal com todas as operações do banco
test_crud.py     # Testes automatizados com pytest
futebol.db       # Banco de dados gerado automaticamente em runtime

Modelo de dados
O banco é composto por 4 tabelas relacionadas:

Times — clubes cadastrados (nome, estado, ano de fundação)
Jogadores — atletas vinculados a um time (nome, posição, data de nascimento)
Partidas — confrontos entre dois times (placar, campeonato, data)
Scout_Desempenho — desempenho individual de um jogador em uma partida (gols, assistências, passes certos, passes tentados, desarmes, cartões amarelos, cartão vermelho, minutos jogados, faltas)

Testes
O projeto conta com 40 testes automatizados cobrindo:

Todas as operações CRUD
Validações de campos (estado, ano, posição, data, gols, cartões etc.)
Regras de negócio (passes certos ≤ passes tentados, times distintos por partida etc.)
Integridade referencial (impede deleção com registros vinculados)
Fluxo completo de criação e remoção em ordem correta

Todos os testes rodam em banco isolado — o futebol.db real nunca é tocado durante os testes.

Tecnologias
Tecnologia          Uso
Python 3.12         Linguagem principal
SQLite3             Banco de dados relacional
pytest              Framework de testes

Autor
Heitor Hernandes
Desenvolvido em março de 2026
Possíveis implementações e ajustes ainda podem ser feitos.
