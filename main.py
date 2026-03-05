"""
CRUD para o banco de dados de futebol usando SQLite3.

Tabelas:
    - Times
    - Jogadores
    - Partidas
    - Scout_Desempenho

Autor: Heitor Hernandes
Data:  2026-03-05
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