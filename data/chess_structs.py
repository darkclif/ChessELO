from PySide6 import QtCore


class DatabaseInfo:
    def __init__(self, calc_date: int):
        self.elo_calc_date = calc_date


class GameSide:
    WHITE = 0
    BLACK = 1


class GameResult:
    WHITE_WIN = 0
    BLACK_WIN = 1
    DRAW = 2
    _SIZE = 3

    @staticmethod
    def getEloResult(r: int, side: int)-> float:
        if r == GameResult.DRAW:
            return 0.5
        if r == GameResult.WHITE_WIN and side == GameSide.WHITE:
            return 1.0
        if r == GameResult.BLACK_WIN and side == GameSide.BLACK:
            return 1.0
        return 0.0

    @staticmethod
    def getOpposite(r: int):
        if r != 2:
            return abs(r - 1)
        return 2

    @staticmethod
    def getString(r: int):
        map_str = {
            0: '1-0', 1: '0-1', 2: '½-½'
        }
        return map_str[r]
    
    @staticmethod
    def getComboData():
        arr = []
        for i in range(GameResult._SIZE):
            arr.append((GameResult.getString(i), i))
        return arr


class ChessGamesDifference:
    NO_SIGNIFICANT_DIFF = 0
    SIGNIFICANT_DIFF = 1
    SIGNIFICANT_DIFF_TIME = 1 << 1
    _SIZE = 2

    @staticmethod
    def GetDiffInfo(single_flag):
        info_map = {
            ChessGamesDifference.SIGNIFICANT_DIFF: 'You tried to modify the result or players of the game that is already taken into account during ELO calculation.',
            ChessGamesDifference.SIGNIFICANT_DIFF_TIME: 'You tried to modify date of the game that is already taken into account during ELO calculation.'
        }
        return info_map[single_flag]

    @staticmethod
    def GetDiffInfoList(flag):
        arr = []
        for i in range(ChessGamesDifference._SIZE):
            if flag & (1 << i):
                arr.append(ChessGamesDifference.GetDiffInfo(1 << i))
        return arr


class ChessGame:
    def __init__(self, 
        id, 
        date: str, 
        p1: int, 
        p2: int, 
        result: int,
        pgn: str
    ) -> None:
        self.id = id
        self.date = date
        self.player_1_id = p1
        self.player_2_id = p2
        self.result = result
        self.pgn = pgn 

    @staticmethod
    def GetBlankGame():
        return ChessGame(
            None,
            QtCore.QDateTime.currentSecsSinceEpoch(),
            None,
            None,
            GameResult.DRAW,
            ''
        )

    def CheckDiffImportance(self, other, elo_timestamp: int)-> ChessGamesDifference:
        # Check if this game was already taken into acocunt during ELO calculations
        flag = ChessGamesDifference.NO_SIGNIFICANT_DIFF

        if (self.date != other.date and (self.date <= elo_timestamp or other.date <= elo_timestamp)):
            flag |= ChessGamesDifference.SIGNIFICANT_DIFF_TIME
        elif (self.date == other.date and self.date <= elo_timestamp):
            # The date was not changed but some other important data could have been
            if (
                self.player_1_id != other.player_1_id 
                or self.player_2_id != other.player_2_id 
                or self.result != other.result
            ):
                flag |= ChessGamesDifference.SIGNIFICANT_DIFF

        return flag

    def GetQtDate(self):
        return QtCore.QDateTime.fromSecsSinceEpoch(self.date)

    def GetFormatedDate(self):
        return self.GetQtDate().toString()

    def getData(self):
        yield self.id
        yield self.GetQtDate().toString()
        yield self.player_1_id
        yield self.player_1_id
        yield GameResult.getString(self.result)

    @staticmethod
    def getHeaders():
        yield 'ID'
        yield 'Date'
        yield 'WhiteID'
        yield 'BlackID'
        yield 'Result'


class RichChessGame(ChessGame):
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            self.__dict__[key] = value

    def GetChessGame(self)-> ChessGame:
        return ChessGame(
            self.id,
            self.date,
            self.player_1_id,
            self.player_2_id,
            self.result,
            self.pgn
        )

    def GetPlayerDisplayName(self, player: int):
        p_fullname = None
        p_nick = None
        if player == GameSide.WHITE:
            p_fullname = self.player_1_full_name
            p_nick = self.player_1_nick
        if player == GameSide.BLACK:
            p_fullname = self.player_2_full_name
            p_nick = self.player_2_nick
        if not p_fullname or not p_nick:
            return "[Invalid]"

        p_fullname = p_fullname.split(' ')
        return "{} '{}' {}".format(p_fullname[0], p_nick, ' '.join(p_fullname[1:]))

    def GetPlayerEloChange(self, player: int):
        if player == GameSide.WHITE:
            if self.player_1_elo is None or self.player_1_change is None:
                return '-'
            else:
                return "{0}({1:+d})".format(self.player_1_elo, self.player_1_change)
        if player == GameSide.BLACK:
            if self.player_2_elo is None or self.player_2_change is None:
                return '-'
            else:
                return "{0}({1:+d})".format(self.player_2_elo, self.player_2_change)

        return "[Invalid]"

    def GetFormatedResult(self):
        return GameResult.getString(self.result)


class GameDetails:
    def __init__(self, id, player_1_elo, player_2_elo, player_1_change, player_2_change):
        self.id = id
        self.player_1_elo = player_1_elo 
        self.player_2_elo = player_2_elo 
        self.player_1_change = player_1_change
        self.player_2_change = player_2_change


class ChessPlayer:
    def __init__(self, id: int, full_name: str, nick: str, elo: int) -> None:
        self.id = id
        self.full_name = full_name
        self.nick = nick
        self.elo = elo

    def getData(self):
        yield self.id
        yield self.full_name
        yield self.nick
        yield self.elo

    @staticmethod
    def getHeaders():
        yield 'ID'
        yield 'Full Name'
        yield 'Nick'
        yield 'Elo'