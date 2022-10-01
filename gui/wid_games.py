from PySide6 import QtWidgets
import PySide6.QtNfc
from data.data_manager import DataManager
from data.chess_structs import ChessGame, GameSide
from gui.edit.wid_edit_game import GameEditDialog
from gui.edit.wid_edit_player import PlayerEditDialog
from gui.pgn.wid_details_game import GameDetailsDialog
from helpers.gui import ShowModalException, SpawnModal


class GamesWidget(QtWidgets.QWidget):
    def __init__(self, db_manager: DataManager, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self.db_manager: DataManager = db_manager

        # Change behaviour
        self.selected_player = None

        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.setLayout(self.main_layout)

        # Datasheet
        self.table_widget = QtWidgets.QTableWidget(self)
        self.table_widget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        #self.table_widget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.table_widget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_widget.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.table_widget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        self.data_layout = [
            ('ID', lambda rg: rg.id),
            ('Date', lambda rg: rg.GetFormatedDate()),
            ('White', lambda rg: rg.GetPlayerDisplayName(GameSide.WHITE)),
            ('ELO', lambda rg: rg.GetPlayerEloChange(GameSide.WHITE)),
            ('Black', lambda rg: rg.GetPlayerDisplayName(GameSide.BLACK)),
            ('ELO', lambda rg: rg.GetPlayerEloChange(GameSide.BLACK)),
            ('Result', lambda rg: rg.GetFormatedResult()),
            ('Archived', lambda rg: rg.archived),
        ]
        #headers = list(ChessGame.getHeaders())
        self.table_widget.setColumnCount(len(self.data_layout))
        self.table_widget.setHorizontalHeaderLabels([t[0] for t in self.data_layout])

        self.__RefreshTableData()
        self.main_layout.addWidget(self.table_widget)
        
        # Buttons
        self.buttons_widget = self.__CreateButtonsWidget()
        self.main_layout.addWidget(self.buttons_widget)

    def __CreateButtonsWidget(self):
        buttons_widget = QtWidgets.QWidget(self)
        buttons_layout = QtWidgets.QVBoxLayout(buttons_widget)
        buttons_widget.setLayout(buttons_layout)

        # Top
        new_btn = QtWidgets.QPushButton("New (N)", buttons_widget)
        delete_btn = QtWidgets.QPushButton("Delete (D)", buttons_widget)
        edit_btn = QtWidgets.QPushButton("Edit (E)", buttons_widget)

        new_btn.clicked.connect(self.__OnNewGame)
        delete_btn.clicked.connect(self.__OnDeleteGame)
        edit_btn.clicked.connect(self.__OnEditGame)

        # Middle
        show_btn = QtWidgets.QPushButton("Show (S)", buttons_widget)
        show_btn.clicked.connect(self.__OnShowGame)

        # Bottom
        update_btn = QtWidgets.QPushButton("Update ELO (R)", buttons_widget)
        recalculate_btn = QtWidgets.QPushButton("Recalc ELO (T)", buttons_widget)
        
        update_btn.clicked.connect(self.__OnUpdateElo)
        recalculate_btn.clicked.connect(self.__OnRecalculateElo)

        # Add all to widget
        buttons_layout.addWidget(new_btn)
        buttons_layout.addWidget(delete_btn)
        buttons_layout.addWidget(edit_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(show_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(update_btn)
        buttons_layout.addWidget(recalculate_btn)

        return buttons_widget
    
    def __GetSelectedGameID(self):
        rows = self.table_widget.selectionModel().selectedRows()
        if len(rows):
            return int(rows[0].data())
        else:
            return None
    
    def __GetSelectedGameData(self):
        id = self.__GetSelectedGameID()
        if id:
            return next((p for p in self.rich_game_data if p.id == id), None)
        
    def __OnShowGame(self):
        game = self.__GetSelectedGameData()
        if not game:
            SpawnModal('Error', 'Cannot find currently selected game.', QtWidgets.QMessageBox.Ok)
            return

        dialog = GameDetailsDialog(self.db_manager, self, game)
        dialog.show()

    def __OnUpdateElo(self):
        selected_game = self.__GetSelectedGameData()
        self.db_manager.GetDatabaseAPI().RecalculateEloIterate(selected_game.date)
        self.__RefreshTableData()

    def __OnRecalculateElo(self):
        self.db_manager.GetDatabaseAPI().RecalculateArchivedElo()
        self.__RefreshTableData()

    def __OnNewGame(self):
        dialog = GameEditDialog(self.db_manager, self)
        if dialog.exec_():
            self.__RefreshTableData()

    def __OnDeleteGame(self):
        id = self.__GetSelectedGameID()
        try:
            result = SpawnModal(
                "I have for you imporant question", 
                "Are you sure?", 
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel
            )

            if result != QtWidgets.QMessageBox.Yes:
                return

            selected_game = self.__GetSelectedGameData()
            recalc = False
            if selected_game.date <= self.db_manager.GetEloTimestamp():
                recalc = True
                m = 'This game was taken into account during ELO calculation. Deleting this game will trigger recalculation, do you want to proceed?'
                r = SpawnModal('There is a problem...', m, QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                if r != QtWidgets.QMessageBox.Yes:
                    return

            self.db_manager.GetDatabaseAPI().DeleteGame(id, recalc)
            self.__RefreshTableData()
        except Exception as e:
            ShowModalException()

    def __OnEditGame(self):
        player = self.__GetSelectedGameData()
        if not player:
            SpawnModal('Error', 'Cannot find currently selected game.', QtWidgets.QMessageBox.Ok)
            return

        dialog = GameEditDialog(self.db_manager, self, player)
        if dialog.exec_():
            self.__RefreshTableData()

    def RefreshData(self):
        self.__RefreshTableData()
        
    def __RefreshTableData(self):
        self.rich_game_data = list(self.db_manager.GetDatabaseAPI().GetRichGames())
        self.table_widget.setRowCount(len(self.rich_game_data))

        for i, game in enumerate(self.rich_game_data):
            for j, data_layout in enumerate(self.data_layout):
                new_item = QtWidgets.QTableWidgetItem(str(data_layout[1](game)))
                self.table_widget.setItem(i, j, new_item)
        
        # self.table_widget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        # self.table_widget.resizeColumnsToContents()
        # self.table_widget.horizontalHeader().setStretchLastSection(True)
