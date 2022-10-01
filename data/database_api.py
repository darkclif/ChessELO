from data.chess_structs import ChessGame, ChessPlayer, RichChessGame, GameDetails, GameResult, DatabaseInfo
from data.database_creator import ChessDatabaseConnector
from helpers.elo import EloCalculator


class ChessDataAPI:
    GAME_UPDATE_MODE_CHECK = 0
    GAME_UPDATE_MODE_SIMPLE = 1

    def __init__(self, db_path: str) -> None:
        self.conn = ChessDatabaseConnector.GetOrCreateDatabase(db_path)

    def __del__(self):
        print("Database destructor called.")
        # self.conn.close()

    ########################
    # API
    ########################
    # Info
    def GetInfo(self)-> DatabaseInfo:
        cur = self.conn.cursor()
        res = cur.execute('''SELECT elo_calc_date FROM CH_INFO''')
        for r in res.fetchall():
            return DatabaseInfo(*r)

    def UpdateEloTimestamp(self, timestamp):
        cur = self.conn.cursor()
        res = cur.execute('''UPDATE CH_INFO SET elo_calc_date = ?''', (timestamp,))
        self.conn.commit()

    # Players
    def AddPlayer(self, full_name: str, nick: str)-> int:
        cur = self.conn.cursor()
        data = (full_name, nick, int(1500))
        query = '''
            INSERT INTO 
                CH_PLAYERS 
            SELECT 
                (SELECT IFNULL(MAX(id), 0) + 1 FROM CH_PLAYERS), ?, ?, ?
        '''

        cur.execute(query, data)
        self.conn.commit()

    def UpdatePlayer(self, id: int, full_name: str, nick: str)-> int:
        cur = self.conn.cursor()
        data = (full_name, nick, id)
        cur.execute('''UPDATE CH_PLAYERS SET full_name = ?, nick = ? WHERE id = ?''', data)
        self.conn.commit()

    def DeletePlayer(self, id: int):
        if self.__CanDeletePlayer(id):
            cur = self.conn.cursor()
            cur.execute('''DELETE FROM CH_PLAYERS WHERE id = ?''', (id,))
            self.conn.commit()

    def GetPlayers(self, start: int=0, end: int=0)-> int:
        cur = self.conn.cursor()
        if start + end == 0:
            res = cur.execute('''SELECT id, full_name, nick, elo FROM CH_PLAYERS ORDER BY id ASC''')
        else:
            data = (start, end)
            res = cur.execute('''SELECT id, full_name, nick, elo FROM CH_PLAYERS WHERE id >= ? AND id <= ? ORDER BY id ASC''', data)
        
        for r in res.fetchall():
            yield ChessPlayer(*r) 

    def GetPlayersDisplay(self):
        cur = self.conn.cursor()
        res = cur.execute('''SELECT full_name, nick, id FROM CH_PLAYERS ORDER BY id ASC''')
        for r in res.fetchall():
            full_name, nick, id = r
            full_name = full_name.split(' ')
            yield ("{} '{}' {}".format(full_name[0], nick, ' '.join(full_name[1:])), id)

    def GetPlayersId(self):
        cur = self.conn.cursor()
        res = cur.execute('''SELECT id FROM CH_PLAYERS''')
        for r in res.fetchall():
            yield r[0]

    def GetPlayersElo(self):
        cur = self.conn.cursor()
        res = cur.execute('''SELECT id, elo FROM CH_PLAYERS''')
        for r in res.fetchall():
            yield r

    def GetPlayersCount(self)-> int:
        cur = self.conn.cursor()
        res = cur.execute('''SELECT COUNT(*) FROM CH_PLAYERS''')
        return res.fetchone()

    # Games
    def AddGame(self, game: ChessGame)-> int:
        cur = self.conn.cursor()
        data = (
            # game.id,
            game.player_1_id,
            game.player_2_id,
            game.date,
            game.result,
            game.pgn
        )
        
        cur.execute('''
            INSERT INTO 
                CH_GAMES (
                    id, 
                    player_1_id, 
                    player_2_id, 
                    date, 
                    result, 
                    pgn
                )
            VALUES 
                (
                    (SELECT IFNULL(MAX(id), 0) + 1 FROM CH_GAMES), 
                    ?,
                    ?,
                    ?,
                    ?,
                    ?
                )
        ''', data)
        self.conn.commit()

    def GetGames(self, start_date: int=0, end_date: int=0)-> int:
        cur = self.conn.cursor()
        if start_date + end_date== 0:
            res = cur.execute('''
                SELECT 
                    id, 
                    date,
                    player_1_id,
                    player_2_id,
                    result, 
                    pgn 
                FROM 
                    CH_GAMES
                ORDER BY date DESC
            ''')
        else:
            data = (start_date, end_date)
            res = cur.execute('''
                SELECT 
                    id, 
                    date,
                    player_1_id,
                    player_2_id,
                    result, 
                    pgn 
                FROM 
                    CH_GAMES 
                WHERE 
                    date >= ? AND date <= ? 
                ORDER BY date DESC''', data)
        
        for r in res.fetchall():
            yield ChessGame(*r) 

    def GetRichGames(self, start_date: int=0, end_date: int=0):
        cur = self.conn.cursor()
        data = ()
        filter = ''
        if start_date != 0 or end_date != 0:
            filter = 'WHERE date >= ? AND date <= ?'
            data = (start_date, end_date)

        res = cur.execute('''
            SELECT 
                id,
                player_1_id, player_1_full_name, player_1_nick, player_1_elo, player_1_change, 
                player_2_id, player_2_full_name, player_2_nick, player_2_elo, player_2_change, 
                date,
                result,
                pgn,
                archived
            FROM 
                CHV_GAMES_RICH
            {}
            ORDER BY date DESC
        '''.format(filter), data)

        for r in res.fetchall():
            yield RichChessGame(
                id=r[0], 

                player_1_id=r[1], 
                player_1_full_name=r[2],
                player_1_nick=r[3],
                player_1_elo=r[4],
                player_1_change=r[5], 
                
                player_2_id=r[6], 
                player_2_full_name=r[7],
                player_2_nick=r[8],
                player_2_elo=r[9], 
                player_2_change=r[10], 
                
                date=r[11], 
                result=r[12],
                pgn=r[13],
                archived=bool(r[14])
            )

    def GetAllArchivedGamesAscending(self):
        elo_calc_date = self.GetInfo().elo_calc_date

        cur = self.conn.cursor()
        res = cur.execute('''
            SELECT 
                id, 
                date,
                player_1_id,
                player_2_id,
                result, 
                pgn 
            FROM 
                CH_GAMES
            WHERE
                date <= ?
            ORDER BY date ASC
        ''', (elo_calc_date,))
        for r in res.fetchall():
            yield ChessGame(*r)

    def GetAllNotArchivedGamesAscending(self, timestamp):
        elo_calc_date = self.GetInfo().elo_calc_date

        cur = self.conn.cursor()
        res = cur.execute('''
            SELECT 
                id, 
                date,
                player_1_id,
                player_2_id,
                result, 
                pgn 
            FROM 
                CH_GAMES
            WHERE
                date > ? AND date <= ? 
            ORDER BY date ASC
        ''', (elo_calc_date,timestamp))
        for r in res.fetchall():
            yield ChessGame(*r)

    def UpdateGame(self, game, recalc: bool):
        self.__UpdateGame(game)

        if recalc:
            self.RecalculateArchivedElo()

    def __UpdateGame(self, game: RichChessGame):
        cur = self.conn.cursor()
        data = (
            game.player_1_id, 
            game.player_2_id, 
            game.date,
            game.result,
            game.pgn,
            game.id,
        )

        cur.execute('''
            UPDATE 
                CH_GAMES 
            SET 
                player_1_id = ?, 
                player_2_id = ?, 
                date = ?,
                result = ?,
                pgn = ?
            WHERE 
                id = ?
        ''', data)
        self.conn.commit()

    def DeleteGame(self, id: int, recalc: bool)-> bool:
        cur = self.conn.cursor()
        cur.execute('''DELETE FROM CH_GAMES WHERE id = ?''', (id,))
        self.conn.commit()

        if recalc:
            self.RecalculateArchivedElo()

    # Game details
    def DeleteAllGameDetails(self):
        cur = self.conn.cursor()
        cur.execute('''DELETE FROM CH_GAMES_DETAILS''')
        self.conn.commit()

    def AddGameDetails(self, gdetails: GameDetails):
        cur = self.conn.cursor()
        data = (
            gdetails.id,
            gdetails.player_1_elo,
            gdetails.player_2_elo,
            gdetails.player_1_change,
            gdetails.player_2_change,
        )
        
        cur.execute('''
            INSERT INTO 
                CH_GAMES_DETAILS (
                    id, 
                    player_1_elo,
                    player_2_elo,
                    player_1_change,
                    player_2_change
                )
            VALUES 
                (?, ?, ?, ?, ?)
        ''', data)
        self.conn.commit()

    # Elo
    def RecalculateEloIterate(self, timestamp):
        EloCalculator.RecalculateEloIterate(self, timestamp)

    def RecalculateArchivedElo(self):
        # Update ELO of the players
        EloCalculator.RecalculateArchivedElo(self)

    def UpdatePlayerElo(self, id: int, elo: int):
        cur = self.conn.cursor()
        cur.execute('''UPDATE CH_PLAYERS SET elo = ? WHERE id = ?''', (elo, id))
        self.conn.commit()

    ########################
    # Private
    ########################
    def __PlayerExists(self, name: str)-> bool:
        pass

    def __CanDeletePlayer(self, id: str)-> bool:
        cur = self.conn.cursor()
        res = cur.execute('''SELECT COUNT(*) FROM CH_GAMES WHERE player_1_id == ? OR player_2_id == ?''', (id,id))
        return (0 == res.fetchone()[0])

    def __GetNextPlayerID(self)-> int:
        cur = self.conn.cursor()
        res = cur.execute('''SELECT IFNULL(MAX(id), 0) + 1 FROM CH_PLAYERS''')
        r = res.fetchone()

        return (r[0] + 1)
