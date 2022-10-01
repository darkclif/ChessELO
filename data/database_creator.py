from pathlib import Path
import sqlite3


class ChessDatabaseConnector:
    @staticmethod
    def GetOrCreateDatabase(db_path):
        db_file = Path(db_path)
        conn = None

        if db_file.is_file():
            return sqlite3.connect(db_path)
        else:
            conn = sqlite3.connect(db_path)
            ChessDatabaseConnector.CreateDatabaseStructures(conn)
            return conn

    @staticmethod
    def CreateDatabaseStructures(conn: sqlite3.Connection):
        cur = conn.cursor()

        # Players
        cur.execute('''
            CREATE TABLE CH_PLAYERS(id, full_name, nick, elo)
        ''')

        # Games
        cur.execute('''
            CREATE TABLE CH_GAMES(id, player_1_id, player_2_id, date, result, pgn)
        ''')

        # Game details
        # Stores iterative information about the game
        cur.execute('''
            CREATE TABLE CH_GAMES_DETAILS(id, player_1_elo, player_2_elo, player_1_change, player_2_change)
        ''')

        # Game rich view
        cur.execute('''
            CREATE VIEW 
                CHV_GAMES_RICH 
            AS 
            SELECT
                CH_GAMES.id, 

                player_1_id, 
                PL1.full_name as player_1_full_name,
                PL1.nick as player_1_nick,
                player_1_elo,
                player_1_change, 

                player_2_id, 
                PL2.full_name as player_2_full_name,
                PL2.nick as player_2_nick,
                player_2_elo, 
                player_2_change, 

                date, 
                result,
                pgn,
                (CASE WHEN CH_GAMES.date <= INFO.elo_calc_date THEN 1 ELSE 0 END) as archived
            FROM
                CH_GAMES,
                (SELECT id, full_name, nick FROM CH_PLAYERS) AS PL1,
                (SELECT id, full_name, nick FROM CH_PLAYERS) AS PL2,
                (SELECT elo_calc_date FROM CH_INFO LIMIT 1) as INFO
            LEFT JOIN
                CH_GAMES_DETAILS
            ON
                CH_GAMES_DETAILS.id == CH_GAMES.id
            WHERE
                PL1.id == CH_GAMES.player_1_id
                AND PL2.id == CH_GAMES.player_2_id
        ''')


        # Database data
        # elo_calc_date - all games up to this date were calculated
        cur.executescript('''
            CREATE TABLE CH_INFO(elo_calc_date);
            INSERT INTO CH_INFO VALUES (0);
        ''')

        conn.commit()