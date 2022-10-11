import copy
from PySide6 import QtWidgets, QtCore
from data.data_manager import DataManager
from data.chess_structs import ChessGame, ChessGamesDifference, GameResult
from data.database_api import ChessDataAPI
from helpers.gui import ShowModalException, SpawnModal


class GameEditNamedWidgets:
    def __init__(self):
        self.wid_id = None
        self.wid_date = None
        self.wid_white = None
        self.wid_black = None
        self.wid_result = None
        self.wid_pgn = None

class GameEditDialog(QtWidgets.QDialog):
    def __init__(self, db_manager: DataManager, parent: QtWidgets.QWidget, game: ChessGame = None):
        super().__init__(parent)
        self.db_manager = db_manager
        
        # Check if editing or creating new
        if game:
            self.prev_game = copy.copy(game)
            self.game = game
        else:
            self.prev_game = None
            self.game = ChessGame.GetBlankGame()

        self.cache_player_data = None

        # Layout
        self.main_layout = QtWidgets.QGridLayout(self)
        self.setWindowTitle("Edit game" if self.prev_game else "Create game")
        self.setLayout(self.main_layout)
        self.setModal(True)

        # Create layout
        self.edits = GameEditNamedWidgets()

        self.main_layout.addWidget(QtWidgets.QLabel('ID', self), 0, 1)
        self.edits.wid_id = QtWidgets.QLineEdit(self)        
        self.edits.wid_id.setReadOnly(True)
        self.edits.wid_id.setEnabled(False)
        self.main_layout.addWidget(self.edits.wid_id, 0, 2)

        self.main_layout.addWidget(QtWidgets.QLabel('Date', self), 1, 1)
        self.edits.wid_date = QtWidgets.QDateTimeEdit(QtCore.QDateTime.currentDateTime(), self)
        self.main_layout.addWidget(self.edits.wid_date, 1, 2)

        self.main_layout.addWidget(QtWidgets.QLabel('White', self), 2, 1)
        self.edits.wid_white = self.__CreatePlayersDropdown()
        self.main_layout.addWidget(self.edits.wid_white, 2, 2)

        self.main_layout.addWidget(QtWidgets.QLabel('Black', self), 3, 1)
        self.edits.wid_black = self.__CreatePlayersDropdown()
        self.main_layout.addWidget(self.edits.wid_black, 3, 2)

        self.main_layout.addWidget(QtWidgets.QLabel('Result', self), 4, 1)
        self.edits.wid_result = self.__CreateResultsDropdown()
        self.main_layout.addWidget(self.edits.wid_result, 4, 2)

        self.main_layout.addWidget(QtWidgets.QLabel('PGN', self), 5, 1)
        self.edits.wid_pgn = QtWidgets.QTextEdit(self)
        self.edits.wid_pgn.setAcceptRichText(False)
        self.main_layout.addWidget(self.edits.wid_pgn, 5, 2)

        self.__RefreshGameDataUI()

        # Add buttons
        accept_btn = QtWidgets.QPushButton("Accept (A)", self)
        cancel_btn = QtWidgets.QPushButton("Cancel (C)", self)

        accept_btn.clicked.connect(self.__ApplyChanges)
        cancel_btn.clicked.connect(self.__CancelChanges)

        self.main_layout.addWidget(accept_btn, 6, 1)
        self.main_layout.addWidget(cancel_btn, 6, 2)

    # Fill data with game data
    def __RefreshGameDataUI(self):
        self.edits.wid_id.setText("-" if not self.game.id else str(self.game.id))
        
        if self.game.player_1_id:
            index = self.edits.wid_white.findData(self.game.player_1_id)
            self.edits.wid_white.setCurrentIndex(index)

        if self.game.player_2_id:
            index = self.edits.wid_black.findData(self.game.player_2_id)
            self.edits.wid_black.setCurrentIndex(index)

        index = self.edits.wid_result.findData(self.game.result)
        self.edits.wid_result.setCurrentIndex(index)

        self.edits.wid_pgn.setPlainText(self.game.pgn)
        self.edits.wid_date.setDateTime(QtCore.QDateTime.fromSecsSinceEpoch(self.game.date))

    # Finish editing
    def __ApplyChanges(self):
        self.__UpdateGameStructure()
        r, m = self.__CheckGameCorrectness()
        if not r:
            SpawnModal('Error during applying changes to game', m, QtWidgets.QMessageBox.Ok)
            return
        
        try:
            # Update / Create
            if self.prev_game:
                cont, recalc = self.__CheckUpdateMode()
                if not cont:
                    return

                self.db_manager.GetDatabaseAPI().UpdateGame(self.game, recalc)
            else:
                self.db_manager.GetDatabaseAPI().AddGame(self.game)
        except Exception as e:
            ShowModalException()

        self.accept()

    def __CancelChanges(self):
        self.close()
    
    # Game finish editing handling
    def __CheckGameCorrectness(self):
        if self.game.player_1_id == self.game.player_2_id:
            return (False, 'Cannot create a game with two identical players.') 
        return (True, '')

    def __UpdateGameStructure(self):
        self.game.date = self.edits.wid_date.dateTime().toSecsSinceEpoch()
        self.game.player_1_id = self.edits.wid_white.currentData()
        self.game.player_2_id = self.edits.wid_black.currentData()
        self.game.result = self.edits.wid_result.currentData()
        self.game.pgn = self.edits.wid_pgn.toPlainText()

    def __CheckUpdateMode(self):
        # -> (continue, recalc)
        # recalc - if True, recalculate database up to elo_calc_date
        # continue - if False, abort operation
        flags = self.game.CheckDiffImportance(self.prev_game, self.db_manager.GetEloTimestamp())
        if flags != 0:
            m = 'Updating this game with current data will invalidate ELO rating due to reasons below, do you want to proceed?'
            problems = '\n'.join([' -{}'.format(m) for m in ChessGamesDifference.GetDiffInfoList(flags)])
            r = SpawnModal('There is a problem...', '{}\n{}'.format(m, problems), QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            
            if r == QtWidgets.QMessageBox.No:
                return (False, True)
            else:
                return (True, True)
        else:
            return (True, False)

    # Create GUI helpers
    def __CreatePlayersDropdown(self)-> QtWidgets.QComboBox:
        if not self.cache_player_data:
            self.cache_player_data = list(self.db_manager.GetDatabaseAPI().GetPlayersDisplay())
        
        combo_box = QtWidgets.QComboBox(self)
        for display_name, id in self.cache_player_data:
            combo_box.addItem(display_name, id)
        return combo_box
    
    def __CreateResultsDropdown(self)-> QtWidgets.QComboBox:
        combo_box = QtWidgets.QComboBox(self)
        for result_name, id in GameResult.getComboData():
            combo_box.addItem(result_name, id)
        return combo_box
    