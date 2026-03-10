"""
CRUD para o banco de dados de futebol usando SQLite3.

Tabelas:
    - Times
    - Jogadores
    - Partidas
    - Scout_Desempenho

Autor: Heitor Hernandes
Data:  10/03/2026
"""

import sqlite3
from datetime import datetime

# Caminho do banco de dados
DB_PATH = "futebol.db"

# Posições válidas no futebol
POSICOES_VALIDAS = [
    "Goleiro", "Zagueiro", "Lateral Direito", "Lateral Esquerdo",
    "Volante", "Meia", "Ponta Direita", "Ponta Esquerda", "Atacante"
]


# =============================================================================
# CONEXÃO
# =============================================================================

def conectar():
    # Abre e retorna uma conexão com o banco de dados.
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def inicializar_banco():
    # Cria as tabelas no banco se ainda não existirem.
    schema = """
    CREATE TABLE IF NOT EXISTS Times (
        id_time      INTEGER PRIMARY KEY AUTOINCREMENT,
        nome         TEXT    NOT NULL,
        estado       TEXT    NOT NULL CHECK (LENGTH(estado) = 2),
        ano_fundacao INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS Jogadores (
        id_jogador      INTEGER PRIMARY KEY AUTOINCREMENT,
        nome            TEXT    NOT NULL,
        posicao         TEXT    NOT NULL,
        data_nascimento TEXT    NOT NULL CHECK (data_nascimento LIKE '____-__-__'),
        id_time         INTEGER NOT NULL,
        FOREIGN KEY (id_time) REFERENCES Times(id_time)
            ON UPDATE CASCADE ON DELETE RESTRICT
    );

    CREATE TABLE IF NOT EXISTS Partidas (
        id_partida        INTEGER PRIMARY KEY AUTOINCREMENT,
        id_time_mandante  INTEGER NOT NULL,
        id_time_visitante INTEGER NOT NULL,
        data_partida      TEXT    NOT NULL CHECK (data_partida LIKE '____-__-__'),
        campeonato        TEXT    NOT NULL,
        gols_mandante     INTEGER NOT NULL DEFAULT 0,
        gols_visitante    INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY (id_time_mandante)  REFERENCES Times(id_time)
            ON UPDATE CASCADE ON DELETE RESTRICT,
        FOREIGN KEY (id_time_visitante) REFERENCES Times(id_time)
            ON UPDATE CASCADE ON DELETE RESTRICT,
        CHECK (id_time_mandante <> id_time_visitante)
    );

    CREATE TABLE IF NOT EXISTS Scout_Desempenho (
        id_scout         INTEGER PRIMARY KEY AUTOINCREMENT,
        id_partida       INTEGER NOT NULL,
        id_jogador       INTEGER NOT NULL,
        titular          INTEGER NOT NULL DEFAULT 1  CHECK (titular IN (0, 1)),
        minutos_jogados  INTEGER NOT NULL DEFAULT 0,
        gols             INTEGER NOT NULL DEFAULT 0,
        assistencias     INTEGER NOT NULL DEFAULT 0,
        passes_tentados  INTEGER NOT NULL DEFAULT 0,
        passes_certos    INTEGER NOT NULL DEFAULT 0,
        desarmes         INTEGER NOT NULL DEFAULT 0,
        faltas_cometidas INTEGER NOT NULL DEFAULT 0,
        cartao_amarelo   INTEGER NOT NULL DEFAULT 0  CHECK (cartao_amarelo  BETWEEN 0 AND 2),
        cartao_vermelho  INTEGER NOT NULL DEFAULT 0  CHECK (cartao_vermelho IN (0, 1)),
        FOREIGN KEY (id_partida) REFERENCES Partidas(id_partida)
            ON UPDATE CASCADE ON DELETE RESTRICT,
        FOREIGN KEY (id_jogador) REFERENCES Jogadores(id_jogador)
            ON UPDATE CASCADE ON DELETE RESTRICT,
        UNIQUE (id_partida, id_jogador),
        CHECK (passes_certos <= passes_tentados)
    );

    CREATE INDEX IF NOT EXISTS idx_jogador_time  ON Jogadores(id_time);
    CREATE INDEX IF NOT EXISTS idx_scout_partida ON Scout_Desempenho(id_partida);
    CREATE INDEX IF NOT EXISTS idx_scout_jogador ON Scout_Desempenho(id_jogador);
    """
    with conectar() as conn:
        conn.executescript(schema)
    print("Banco inicializado com sucesso.")
    


# =============================================================================
# FUNÇÕES DE NORMALIZAÇÃO
# =============================================================================

def normalizar_estado(estado: str) -> str:
    return estado.strip().upper()


def normalizar_posicao(posicao: str) -> str:
      return posicao.strip().title()


def normalizar_data(data: str) -> str:
    # Converte a data do formato DD/MM/AAAA para YYYY-MM-DD (padrão do banco).
    try:
        return datetime.strptime(data.strip(), "%d/%m/%Y").strftime("%Y-%m-%d")
    except ValueError:
        raise ValueError(
            f"Data inválida: '{data}'. Use o formato DD/MM/AAAA, ex: 17/08/1996."
        )
    


# =============================================================================
# FUNÇÕES DE VALIDAÇÃO
# =============================================================================

def validar_estado(estado: str):
    if len(estado) != 2 or not estado.isalpha():
        raise ValueError(
            f"Estado inválido: '{estado}'. Informe a sigla do estado com 2 letras, ex: 'SP'."
        )


def validar_ano_fundacao(ano: int):
    ano_atual = datetime.now().year
    if not (1863 <= ano <= ano_atual):
        raise ValueError(
            f"Ano de fundação inválido: {ano}. Coloque um ano válido entre 1863 e {ano_atual}."
        )


def validar_posicao(posicao: str):
    if posicao not in POSICOES_VALIDAS:
        raise ValueError(
            f"Posição inválida: '{posicao}'. Posições aceitas: {POSICOES_VALIDAS}"
        )


def validar_gols(gols_mandante: int, gols_visitante: int):
    if gols_mandante < 0 or gols_visitante < 0:
        raise ValueError("Os gols não podem ser negativos.")

# =============================================================================
# CRUD - TIMES
# =============================================================================

class CRUDTimes:
    

    def criar(self, nome: str, estado: str, ano_fundacao: int) -> int:
        """
        Cadastra um novo time no banco.
        Retorna o ID do time criado.
        """
        estado = normalizar_estado(estado)
        validar_estado(estado)
        validar_ano_fundacao(ano_fundacao)

        with conectar() as conn:
            cursor = conn.execute(
                "INSERT INTO Times (nome, estado, ano_fundacao) VALUES (?, ?, ?)",
                (nome.strip(), estado, ano_fundacao)
            )
            print(f"[Times] Time '{nome}' cadastrado com ID {cursor.lastrowid}.")
            return cursor.lastrowid

    def buscar_por_id(self, id_time: int) -> dict | None:
        """
        Busca um time pelo ID.
        Retorna um dicionário com os dados ou None se não encontrado.
        """
        with conectar() as conn:
            row = conn.execute(
                "SELECT * FROM Times WHERE id_time = ?", (id_time,)
            ).fetchone()

        if row:
            return dict(row)

        print(f"[Times] Nenhum time encontrado com ID {id_time}.")
        return None

    def listar(self, estado: str = None) -> list[dict]:
        """
        Lista todos os times cadastrados.
        Se informado, filtra pelo estado.
        """
        with conectar() as conn:
            if estado:
                rows = conn.execute(
                    "SELECT * FROM Times WHERE estado = ? ORDER BY nome",
                    (normalizar_estado(estado),)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM Times ORDER BY nome"
                ).fetchall()

        return [dict(r) for r in rows]

    def atualizar(self, id_time: int, nome: str = None,
                  estado: str = None, ano_fundacao: int = None) -> bool:
        """
        Atualiza os dados de um time.
        Só altera os campos que forem informados.
        Retorna True se o time foi encontrado e atualizado.
        """
        campos, valores = [], []

        if nome is not None:
            campos.append("nome = ?")
            valores.append(nome.strip())

        if estado is not None:
            estado = normalizar_estado(estado)
            validar_estado(estado)
            campos.append("estado = ?")
            valores.append(estado)

        if ano_fundacao is not None:
            validar_ano_fundacao(ano_fundacao)
            campos.append("ano_fundacao = ?")
            valores.append(ano_fundacao)

        if not campos:
            print("[Times] Nenhum campo informado para atualizar.")
            return False

        valores.append(id_time)
        sql = f"UPDATE Times SET {', '.join(campos)} WHERE id_time = ?"

        with conectar() as conn:
            cursor = conn.execute(sql, valores)
            atualizado = cursor.rowcount > 0

        if atualizado:
            print(f"[Times] Time ID {id_time} atualizado.")
        else:
            print(f"[Times] Nenhum time encontrado com ID {id_time}.")

        return atualizado

    def deletar(self, id_time: int) -> bool:
        """
        Remove um time do banco.
        Não é possível remover um time que tenha jogadores ou partidas cadastradas.
        Retorna True se o time foi removido.
        """
        try:
            with conectar() as conn:
                cursor = conn.execute(
                    "DELETE FROM Times WHERE id_time = ?", (id_time,)
                )
                deletado = cursor.rowcount > 0

            if deletado:
                print(f"[Times] Time ID {id_time} removido.")
            else:
                print(f"[Times] Nenhum time encontrado com ID {id_time}.")

            return deletado

        except sqlite3.IntegrityError:
            print(
                f"[Times] Não foi possível remover o time ID {id_time}. "
                "Existem jogadores ou partidas vinculados a ele."
            )
            return False
        
# =============================================================================
# CRUD - JOGADORES
# =============================================================================

class CRUDJogadores:
    """Operações CRUD para a tabela Jogadores."""

    def criar(self, nome: str, posicao: str,
              data_nascimento: str, id_time: int) -> int:
        """
        Cadastra um novo jogador no banco.
        Retorna o ID do jogador criado.
        """
        posicao         = normalizar_posicao(posicao)
        data_nascimento = normalizar_data(data_nascimento)
        validar_posicao(posicao)

        with conectar() as conn:
            cursor = conn.execute(
                """INSERT INTO Jogadores (nome, posicao, data_nascimento, id_time)
                   VALUES (?, ?, ?, ?)""",
                (nome.strip(), posicao, data_nascimento, id_time)
            )
            print(f"[Jogadores] '{nome}' cadastrado com ID {cursor.lastrowid}.")
            return cursor.lastrowid

    def buscar_por_id(self, id_jogador: int) -> dict | None:
        """
        Busca um jogador pelo ID, incluindo o nome do time.
        Retorna um dicionário com os dados ou None se não encontrado.
        """
        with conectar() as conn:
            row = conn.execute(
                """SELECT j.*, t.nome AS nome_time
                   FROM Jogadores j
                   JOIN Times t ON t.id_time = j.id_time
                   WHERE j.id_jogador = ?""",
                (id_jogador,)
            ).fetchone()

        if row:
            return dict(row)

        print(f"[Jogadores] Nenhum jogador encontrado com ID {id_jogador}.")
        return None

    def listar(self, id_time: int = None, posicao: str = None) -> list[dict]:
        """
        Lista jogadores com filtros opcionais por time e/ou posição.
        Inclui o nome do time no resultado.
        """
        query = """SELECT j.*, t.nome AS nome_time
                   FROM Jogadores j
                   JOIN Times t ON t.id_time = j.id_time"""

        filtros, valores = [], []

        if id_time is not None:
            filtros.append("j.id_time = ?")
            valores.append(id_time)

        if posicao is not None:
            filtros.append("j.posicao = ?")
            valores.append(normalizar_posicao(posicao))

        if filtros:
            query += " WHERE " + " AND ".join(filtros)

        query += " ORDER BY j.nome"

        with conectar() as conn:
            rows = conn.execute(query, valores).fetchall()

        return [dict(r) for r in rows]

    def atualizar(self, id_jogador: int, nome: str = None, posicao: str = None,
                  data_nascimento: str = None, id_time: int = None) -> bool:
        """
        Atualiza os dados de um jogador.
        Só altera os campos que forem informados.
        Retorna True se o jogador foi encontrado e atualizado.
        """
        campos, valores = [], []

        if nome is not None:
            campos.append("nome = ?")
            valores.append(nome.strip())

        if posicao is not None:
            posicao = normalizar_posicao(posicao)
            validar_posicao(posicao)
            campos.append("posicao = ?")
            valores.append(posicao)

        if data_nascimento is not None:
            campos.append("data_nascimento = ?")
            valores.append(normalizar_data(data_nascimento))

        if id_time is not None:
            campos.append("id_time = ?")
            valores.append(id_time)

        if not campos:
            print("[Jogadores] Nenhum campo informado para atualizar.")
            return False

        valores.append(id_jogador)
        sql = f"UPDATE Jogadores SET {', '.join(campos)} WHERE id_jogador = ?"

        with conectar() as conn:
            cursor = conn.execute(sql, valores)
            atualizado = cursor.rowcount > 0

        if atualizado:
            print(f"[Jogadores] Jogador ID {id_jogador} atualizado.")
        else:
            print(f"[Jogadores] Nenhum jogador encontrado com ID {id_jogador}.")

        return atualizado

    def deletar(self, id_jogador: int) -> bool:
        """
        Remove um jogador do banco.
        Não é possível remover um jogador com scouts registrados.
        Retorna True se o jogador foi removido.
        """
        try:
            with conectar() as conn:
                cursor = conn.execute(
                    "DELETE FROM Jogadores WHERE id_jogador = ?", (id_jogador,)
                )
                deletado = cursor.rowcount > 0

            if deletado:
                print(f"[Jogadores] Jogador ID {id_jogador} removido.")
            else:
                print(f"[Jogadores] Nenhum jogador encontrado com ID {id_jogador}.")

            return deletado

        except sqlite3.IntegrityError:
            print(
                f"[Jogadores] Não foi possível remover o jogador ID {id_jogador}. "
                "Existem scouts vinculados a ele."
            )
            return False

# =============================================================================
# CRUD - PARTIDAS
# =============================================================================

class CRUDPartidas:
    """Operações CRUD para a tabela Partidas."""

    def criar(self, id_time_mandante: int, id_time_visitante: int,
              data_partida: str, campeonato: str,
              gols_mandante: int = 0, gols_visitante: int = 0) -> int:
        """
        Registra uma nova partida.
        Retorna o ID da partida criada.
        """
        if id_time_mandante == id_time_visitante:
            raise ValueError("O time mandante e o visitante não podem ser o mesmo.")

        validar_gols(gols_mandante, gols_visitante)
        data_partida = normalizar_data(data_partida)

        with conectar() as conn:
            cursor = conn.execute(
                """INSERT INTO Partidas
                       (id_time_mandante, id_time_visitante, data_partida,
                        campeonato, gols_mandante, gols_visitante)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (id_time_mandante, id_time_visitante, data_partida,
                 campeonato.strip(), gols_mandante, gols_visitante)
            )
            print(f"[Partidas] Partida registrada com ID {cursor.lastrowid}.")
            return cursor.lastrowid

    def buscar_por_id(self, id_partida: int) -> dict | None:
        """
        Busca uma partida pelo ID, incluindo os nomes dos times.
        Retorna um dicionário com os dados ou None se não encontrada.
        """
        with conectar() as conn:
            row = conn.execute(
                """SELECT p.*,
                          tm.nome AS nome_mandante,
                          tv.nome AS nome_visitante
                   FROM Partidas p
                   JOIN Times tm ON tm.id_time = p.id_time_mandante
                   JOIN Times tv ON tv.id_time = p.id_time_visitante
                   WHERE p.id_partida = ?""",
                (id_partida,)
            ).fetchone()

        if row:
            return dict(row)

        print(f"[Partidas] Nenhuma partida encontrada com ID {id_partida}.")
        return None

    def listar(self, campeonato: str = None, id_time: int = None) -> list[dict]:
        """
        Lista partidas com filtros opcionais.
        Se id_time for informado, retorna partidas em que o time participou
        como mandante ou visitante.
        """
        query = """SELECT p.*,
                          tm.nome AS nome_mandante,
                          tv.nome AS nome_visitante
                   FROM Partidas p
                   JOIN Times tm ON tm.id_time = p.id_time_mandante
                   JOIN Times tv ON tv.id_time = p.id_time_visitante"""

        filtros, valores = [], []

        if campeonato is not None:
            filtros.append("p.campeonato = ?")
            valores.append(campeonato.strip())

        if id_time is not None:
            filtros.append("(p.id_time_mandante = ? OR p.id_time_visitante = ?)")
            valores.extend([id_time, id_time])

        if filtros:
            query += " WHERE " + " AND ".join(filtros)

        query += " ORDER BY p.data_partida DESC"

        with conectar() as conn:
            rows = conn.execute(query, valores).fetchall()

        return [dict(r) for r in rows]

    def atualizar(self, id_partida: int, gols_mandante: int = None,
                  gols_visitante: int = None, campeonato: str = None,
                  data_partida: str = None) -> bool:
        """
        Atualiza os dados de uma partida.
        Só altera os campos que forem informados.
        Retorna True se a partida foi encontrada e atualizada.
        """
        campos, valores = [], []

        if gols_mandante is not None:
            if gols_mandante < 0:
                raise ValueError("Os gols do mandante não podem ser negativos.")
            campos.append("gols_mandante = ?")
            valores.append(gols_mandante)

        if gols_visitante is not None:
            if gols_visitante < 0:
                raise ValueError("Os gols do visitante não podem ser negativos.")
            campos.append("gols_visitante = ?")
            valores.append(gols_visitante)

        if campeonato is not None:
            campos.append("campeonato = ?")
            valores.append(campeonato.strip())

        if data_partida is not None:
            campos.append("data_partida = ?")
            valores.append(normalizar_data(data_partida))

        if not campos:
            print("[Partidas] Nenhum campo informado para atualizar.")
            return False

        valores.append(id_partida)
        sql = f"UPDATE Partidas SET {', '.join(campos)} WHERE id_partida = ?"

        with conectar() as conn:
            cursor = conn.execute(sql, valores)
            atualizado = cursor.rowcount > 0

        if atualizado:
            print(f"[Partidas] Partida ID {id_partida} atualizada.")
        else:
            print(f"[Partidas] Nenhuma partida encontrada com ID {id_partida}.")

        return atualizado

    def deletar(self, id_partida: int) -> bool:
        """
        Remove uma partida do banco.
        Não é possível remover uma partida que tenha scouts registrados.
        Retorna True se a partida foi removida.
        """
        try:
            with conectar() as conn:
                cursor = conn.execute(
                    "DELETE FROM Partidas WHERE id_partida = ?", (id_partida,)
                )
                deletado = cursor.rowcount > 0

            if deletado:
                print(f"[Partidas] Partida ID {id_partida} removida.")
            else:
                print(f"[Partidas] Nenhuma partida encontrada com ID {id_partida}.")

            return deletado

        except sqlite3.IntegrityError:
            print(
                f"[Partidas] Não foi possível remover a partida ID {id_partida}. "
                "Existem scouts vinculados a ela."
            )
            return False

# =============================================================================
# CRUD - SCOUT_DESEMPENHO
# =============================================================================

class CRUDScout:
    """Operações CRUD para a tabela Scout_Desempenho."""

    def criar(self, id_partida: int, id_jogador: int, titular: int = 1,
              minutos_jogados: int = 0, gols: int = 0, assistencias: int = 0,
              passes_tentados: int = 0, passes_certos: int = 0,
              desarmes: int = 0, faltas_cometidas: int = 0,
              cartao_amarelo: int = 0, cartao_vermelho: int = 0) -> int|None:
        """
        Registra o desempenho de um jogador em uma partida.
        Retorna o ID do scout criado.
        """
        # Validações antes de salvar
        if titular not in (0, 1):
            raise ValueError("O campo titular deve ser 0 (reserva) ou 1 (titular).")
        if cartao_amarelo not in (0, 1, 2):
            raise ValueError("cartao_amarelo deve ser 0, 1 ou 2.")
        if cartao_vermelho not in (0, 1):
            raise ValueError("cartao_vermelho deve ser 0 ou 1.")
        if minutos_jogados < 0 or minutos_jogados > 150:
            raise ValueError("minutos_jogados deve ser entre 0 e 150.")
        if passes_certos > passes_tentados:
            raise ValueError("passes_certos não pode ser maior que passes_tentados.")
        
         # Verifica se os demais valores não são negativos
        campos_numericos = {
            "gols": gols, "assistencias": assistencias,
            "passes_tentados": passes_tentados, "passes_certos": passes_certos,
            "desarmes": desarmes, "faltas_cometidas": faltas_cometidas
        }
        for campo, valor in campos_numericos.items():
            if valor < 0:
                raise ValueError(f"O campo '{campo}' não pode ser negativo.")
        try:
            with conectar() as conn:   
                cursor = conn.execute(
                    """INSERT INTO Scout_Desempenho
                       (id_partida, id_jogador, titular, minutos_jogados, gols,
                        assistencias, passes_tentados, passes_certos, desarmes,
                        faltas_cometidas, cartao_amarelo, cartao_vermelho)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (id_partida, id_jogador, titular, minutos_jogados, gols,
                 assistencias, passes_tentados, passes_certos, desarmes,
                 faltas_cometidas, cartao_amarelo, cartao_vermelho)
                    ) 
                print(f"[Scout] Desempenho registrado com ID {cursor.lastrowid}.")
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            print(f"[Scout] Já existe um scout para o jogador ID {id_jogador} na partida ID {id_partida}.")
            return None

    def buscar_por_id(self, id_scout: int) -> dict | None:
        """
        Busca um scout pelo ID, incluindo nome do jogador e times da partida.
        Retorna um dicionário com os dados ou None se não encontrado.
        """
        with conectar() as conn:
            row = conn.execute(
                """SELECT s.*,
                          j.nome  AS nome_jogador,
                          tm.nome AS nome_mandante,
                          tv.nome AS nome_visitante,
                          p.data_partida,
                          p.campeonato
                   FROM Scout_Desempenho s
                   JOIN Jogadores j  ON j.id_jogador = s.id_jogador
                   JOIN Partidas  p  ON p.id_partida = s.id_partida
                   JOIN Times     tm ON tm.id_time   = p.id_time_mandante
                   JOIN Times     tv ON tv.id_time   = p.id_time_visitante
                   WHERE s.id_scout = ?""",
                (id_scout,)
            ).fetchone()

        if row:
            return dict(row)

        print(f"[Scout] Nenhum scout encontrado com ID {id_scout}.")
        return None

    def listar(self, id_partida: int = None, id_jogador: int = None) -> list[dict]:
        """
        Lista scouts com filtros opcionais por partida e/ou jogador.
        Inclui nome do jogador e dos times no resultado.
        """
        query = """SELECT s.*,
                          j.nome  AS nome_jogador,
                          tm.nome AS nome_mandante,
                          tv.nome AS nome_visitante
                   FROM Scout_Desempenho s
                   JOIN Jogadores j  ON j.id_jogador = s.id_jogador
                   JOIN Partidas  p  ON p.id_partida = s.id_partida
                   JOIN Times     tm ON tm.id_time   = p.id_time_mandante
                   JOIN Times     tv ON tv.id_time   = p.id_time_visitante"""

        filtros, valores = [], []

        if id_partida is not None:
            filtros.append("s.id_partida = ?")
            valores.append(id_partida)

        if id_jogador is not None:
            filtros.append("s.id_jogador = ?")
            valores.append(id_jogador)

        if filtros:
            query += " WHERE " + " AND ".join(filtros)

        with conectar() as conn:
            rows = conn.execute(query, valores).fetchall()

        return [dict(r) for r in rows]

    def atualizar(self, id_scout: int, gols: int = None, assistencias: int = None,
                  passes_tentados: int = None, passes_certos: int = None,
                  desarmes: int = None, faltas_cometidas: int = None,
                  minutos_jogados: int = None, cartao_amarelo: int = None,
                  cartao_vermelho: int = None, titular: int = None) -> bool:
        """
        Atualiza os dados de um scout.
        Só altera os campos que forem informados.
        Retorna True se o scout foi encontrado e atualizado.
        """
        campos, valores = [], []

        if gols is not None:
            campos.append("gols = ?")
            valores.append(gols)

        if assistencias is not None:
            campos.append("assistencias = ?")
            valores.append(assistencias)

        if minutos_jogados is not None:
            if not (0 <= minutos_jogados <= 150):
                raise ValueError("minutos_jogados deve ser entre 0 e 150.")
            campos.append("minutos_jogados = ?")
            valores.append(minutos_jogados)

        if passes_tentados is not None:
            campos.append("passes_tentados = ?")
            valores.append(passes_tentados)

        if passes_certos is not None:
            campos.append("passes_certos = ?")
            valores.append(passes_certos)

        if desarmes is not None:
            campos.append("desarmes = ?")
            valores.append(desarmes)

        if faltas_cometidas is not None:
            campos.append("faltas_cometidas = ?")
            valores.append(faltas_cometidas)

        if cartao_amarelo is not None:
            if cartao_amarelo not in (0, 1, 2):
                raise ValueError("cartao_amarelo deve ser 0, 1 ou 2.")
            campos.append("cartao_amarelo = ?")
            valores.append(cartao_amarelo)

        if cartao_vermelho is not None:
            if cartao_vermelho not in (0, 1):
                raise ValueError("cartao_vermelho deve ser 0 ou 1.")
            campos.append("cartao_vermelho = ?")
            valores.append(cartao_vermelho)

        if titular is not None:
            if titular not in (0, 1):
                raise ValueError("titular deve ser 0 ou 1.")
            campos.append("titular = ?")
            valores.append(titular)

        if not campos:
            print("[Scout] Nenhum campo informado para atualizar.")
            return False

        # Valida passes considerando os valores atuais do banco se necessário
        if passes_certos is not None or passes_tentados is not None:
            atual = self.buscar_por_id(id_scout)
            if atual:
                if passes_certos  is not None:
                    novos_certos = passes_certos
                else:
                    novos_certos = atual["passes_certos"]
                if passes_tentados is not None:
                    novos_tentados = passes_tentados
                else:
                    novos_tentados = atual["passes_tentados"]
                if novos_certos > novos_tentados:
                    raise ValueError("passes_certos não pode ser maior que passes_tentados.")

        valores.append(id_scout)
        sql = f"UPDATE Scout_Desempenho SET {', '.join(campos)} WHERE id_scout = ?"

        with conectar() as conn:
            cursor = conn.execute(sql, valores)
            atualizado = cursor.rowcount > 0

        if atualizado:
            print(f"[Scout] Scout ID {id_scout} atualizado.")
        else:
            print(f"[Scout] Nenhum scout encontrado com ID {id_scout}.")

        return atualizado

    def deletar(self, id_scout: int) -> bool:
        """
        Remove um scout do banco.
        Retorna True se o scout foi removido.
        """
        with conectar() as conn:
            cursor = conn.execute(
                "DELETE FROM Scout_Desempenho WHERE id_scout = ?", (id_scout,)
            )
            deletado = cursor.rowcount > 0

        if deletado:
            print(f"[Scout] Scout ID {id_scout} removido.")
        else:
            print(f"[Scout] Nenhum scout encontrado com ID {id_scout}.")

        return deletado

# =============================================================================
# INSTÂNCIAS PRONTAS PARA USO
# =============================================================================

times     = CRUDTimes()
jogadores = CRUDJogadores()
partidas  = CRUDPartidas()
scout     = CRUDScout()