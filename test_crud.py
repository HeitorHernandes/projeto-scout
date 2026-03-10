"""
Testes automatizados para o CRUD do banco de dados de futebol.

Executar: python -m pytest test_crud.py -v
"""

import pytest
import main


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture(autouse=True)
def banco_em_memoria(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "DB_PATH", str(tmp_path / "test.db"))
    main.inicializar_banco()


@pytest.fixture
def time_sp():
    return main.times.criar("Corinthians", "SP", 1910)

@pytest.fixture
def time_rj():
    return main.times.criar("Flamengo", "RJ", 1895)

@pytest.fixture
def jogador(time_sp):
    return main.jogadores.criar("Hugo", "Goleiro", "31/01/1999", time_sp)

@pytest.fixture
def partida(time_sp, time_rj):
    return main.partidas.criar(time_sp, time_rj, "10/03/2026", "Brasileirão", 2, 1)

@pytest.fixture
def scout(partida, jogador):
    return main.scout.criar(partida, jogador, minutos_jogados=90, gols=1,
                            passes_tentados=40, passes_certos=35)


# =============================================================================
# TIMES
# =============================================================================

class TestTimes:

    def test_criar_e_buscar(self):
        id_time = main.times.criar("Palmeiras", "sp", 1914)
        time = main.times.buscar_por_id(id_time)
        assert time["nome"] == "Palmeiras"
        assert time["estado"] == "SP"       # normalizado para maiúsculo

    @pytest.mark.parametrize("estado", ["SPP", "S1", ""])
    def test_criar_estado_invalido(self, estado):
        with pytest.raises(ValueError, match="Estado inválido"):
            main.times.criar("Teste", estado, 1950)

    @pytest.mark.parametrize("ano", [1800, 2099])
    def test_criar_ano_invalido(self, ano):
        with pytest.raises(ValueError, match="Ano de fundação inválido"):
            main.times.criar("Teste", "SP", ano)

    def test_listar_filtrado_por_estado(self):
        main.times.criar("Grêmio", "RS", 1903)
        main.times.criar("Inter",  "RS", 1909)
        main.times.criar("Flu",    "RJ", 1902)
        assert len(main.times.listar(estado="RS")) == 2

    def test_atualizar(self, time_sp):
        main.times.atualizar(time_sp, nome="SC Corinthians", ano_fundacao=1910)
        assert main.times.buscar_por_id(time_sp)["nome"] == "SC Corinthians"

    def test_deletar(self, time_sp):
        assert main.times.deletar(time_sp) is True
        assert main.times.buscar_por_id(time_sp) is None

    def test_deletar_com_jogador_vinculado(self, time_sp, jogador):
        assert main.times.deletar(time_sp) is False


# =============================================================================
# JOGADORES
# =============================================================================

class TestJogadores:

    def test_criar_normaliza_posicao(self, time_sp):
        id_j = main.jogadores.criar("Matheusinho", "lateral direito", "11/06/1989", time_sp)
        assert main.jogadores.buscar_por_id(id_j)["posicao"] == "Lateral Direito"

    @pytest.mark.parametrize("posicao", ["Libero", "Ponteiro", ""])
    def test_criar_posicao_invalida(self, time_sp, posicao):
        with pytest.raises(ValueError, match="Posição inválida"):
            main.jogadores.criar("Teste", posicao, "01/01/2000", time_sp)

    @pytest.mark.parametrize("data", ["2000-01-01", "01-01-2000", "Janeiro 2000"])
    def test_criar_data_invalida(self, time_sp, data):
        with pytest.raises(ValueError, match="Data inválida"):
            main.jogadores.criar("Teste", "Goleiro", data, time_sp)

    def test_buscar_inclui_nome_do_time(self, jogador):
        assert main.jogadores.buscar_por_id(jogador)["nome_time"] == "Corinthians"

    def test_listar_por_time_e_posicao(self, time_sp, time_rj):
        main.jogadores.criar("Hugo", "Goleiro",  "31/01/1999", time_sp)
        main.jogadores.criar("Rossi",   "Goleiro",  "21/08/1995", time_rj)
        main.jogadores.criar("Yuri",   "Atacante", "11/08/1996", time_sp)
        assert len(main.jogadores.listar(id_time=time_sp)) == 2
        assert len(main.jogadores.listar(posicao="goleiro")) == 2

    def test_deletar_com_scout_vinculado(self, scout, jogador):
        assert main.jogadores.deletar(jogador) is False


# =============================================================================
# PARTIDAS
# =============================================================================

class TestPartidas:

    def test_criar_e_buscar(self, partida):
        p = main.partidas.buscar_por_id(partida)
        assert p["nome_mandante"] == "Corinthians"
        assert p["gols_mandante"] == 2

    def test_criar_mesmo_time_levanta_erro(self, time_sp):
        with pytest.raises(ValueError, match="mesmo"):
            main.partidas.criar(time_sp, time_sp, "10/03/2026", "Amistoso")

    @pytest.mark.parametrize("gols_m,gols_v", [(-1, 0), (0, -1)])
    def test_criar_gols_negativos(self, time_sp, time_rj, gols_m, gols_v):
        with pytest.raises(ValueError, match="negativos"):
            main.partidas.criar(time_sp, time_rj, "10/03/2026", "Amistoso", gols_m, gols_v)

    def test_listar_por_time_mandante_e_visitante(self, time_sp, time_rj):
        outro = main.times.criar("Vasco", "RJ", 1898)
        main.partidas.criar(time_sp, time_rj, "01/03/2026", "Brasileirão")
        main.partidas.criar(time_rj, time_sp, "05/03/2026", "Brasileirão")
        main.partidas.criar(time_rj, outro,   "08/03/2026", "Brasileirão")
        assert len(main.partidas.listar(id_time=time_sp)) == 2

    def test_atualizar_placar(self, partida):
        main.partidas.atualizar(partida, gols_mandante=3, gols_visitante=0)
        p = main.partidas.buscar_por_id(partida)
        assert p["gols_mandante"] == 3 and p["gols_visitante"] == 0

    def test_deletar_com_scout_vinculado(self, scout, partida):
        assert main.partidas.deletar(partida) is False


# =============================================================================
# SCOUT
# =============================================================================

class TestScout:

    def test_criar_e_buscar(self, scout):
        s = main.scout.buscar_por_id(scout)
        assert s["nome_jogador"] == "Hugo"
        assert s["gols"] == 1

    def test_criar_duplicado_retorna_none(self, scout, partida, jogador):
        assert main.scout.criar(partida, jogador) is None

    @pytest.mark.parametrize("kwargs,erro", [
        ({"passes_tentados": 10, "passes_certos": 15}, "passes_certos"),
        ({"minutos_jogados": 200},                     "minutos_jogados"),
        ({"minutos_jogados": -5},                      "minutos_jogados"),
        ({"cartao_amarelo": 3},                        "cartao_amarelo"),
        ({"cartao_vermelho": 2},                       "cartao_vermelho"),
        ({"titular": 5},                               "titular"),
        ({"gols": -1},                                 "gols"),
    ])
    def test_criar_campo_invalido(self, partida, jogador, kwargs, erro):
        with pytest.raises(ValueError, match=erro):
            main.scout.criar(partida, jogador, **kwargs)

    def test_atualizar(self, scout):
        main.scout.atualizar(scout, gols=2, assistencias=1)
        s = main.scout.buscar_por_id(scout)
        assert s["gols"] == 2 and s["assistencias"] == 1

    def test_atualizar_passes_inconsistentes_levanta_erro(self, scout):
        # scout base: tentados=40, certos=35 — tentar setar certos=50 sem mudar tentados
        with pytest.raises(ValueError, match="passes_certos"):
            main.scout.atualizar(scout, passes_certos=50)

    def test_deletar(self, scout):
        assert main.scout.deletar(scout) is True
        assert main.scout.buscar_por_id(scout) is None


# =============================================================================
# INTEGRIDADE REFERENCIAL
# =============================================================================

class TestIntegridade:

    def test_fluxo_completo(self):
        """Ciclo de vida completo: criar tudo → remover na ordem correta."""
        id_t1 = main.times.criar("Atlético Mineiro", "MG", 1908)
        id_t2 = main.times.criar("Cruzeiro", "MG", 1921)
        id_j  = main.jogadores.criar("Hulk", "Atacante", "25/07/1986", id_t1)
        id_p  = main.partidas.criar(id_t1, id_t2, "20/03/2026", "Brasileirão")
        id_s  = main.scout.criar(id_p, id_j, minutos_jogados=85, gols=1)

        assert main.scout.deletar(id_s)     is True
        assert main.partidas.deletar(id_p)  is True
        assert main.jogadores.deletar(id_j) is True
        assert main.times.deletar(id_t1)    is True
        assert main.times.deletar(id_t2)    is True