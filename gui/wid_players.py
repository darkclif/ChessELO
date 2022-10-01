from PySide6 import QtWidgets
from data.data_manager import DataManager
from data.chess_structs import ChessGame, ChessPlayer
from gui.edit.wid_edit_player import PlayerEditDialog
from helpers.gui import ShowModalException, SpawnModal


class PlayersWidget(QtWidgets.QWidget):
    ''' Widgets that shows players '''
    
    def __init__(self, db_manager: DataManager, parent: QtWidgets.QWidget):
        super().__init__(parent)
        self.db_manager = db_manager

        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.setLayout(self.main_layout)

        # Datasheet
        self.table_widget = QtWidgets.QTableWidget(self)
        self.table_widget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        # self.table_widget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.table_widget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_widget.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.table_widget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        headers = list(ChessPlayer.getHeaders())
        self.table_widget.setColumnCount(len(headers))
        self.table_widget.setHorizontalHeaderLabels(headers)

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

        new_btn.clicked.connect(self.__OnNewPlayer)
        delete_btn.clicked.connect(self.__OnDeletePlayer)
        edit_btn.clicked.connect(self.__OnEditPlayer)

        # Bottom
        showgames_btn = QtWidgets.QPushButton("Show games (S)", buttons_widget)

        showgames_btn.clicked.connect(self.__OnShowPlayerGame)

        # Add all to widget
        buttons_layout.addWidget(new_btn)
        buttons_layout.addWidget(delete_btn)
        buttons_layout.addWidget(edit_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(showgames_btn)

        return buttons_widget
    
    def __GetSelectedPlayerID(self):
        rows = self.table_widget.selectionModel().selectedRows()
        if len(rows):
            return int(rows[0].data())
        else:
            return None
    
    def __GetSelectedPlayerData(self):
        id = self.__GetSelectedPlayerID()
        if id:
            return next((p for p in self.player_data if p.id == id), None)
        
    def __OnNewPlayer(self):
        dialog = PlayerEditDialog(self.db_manager, self)
        if dialog.exec_():
            self.__RefreshTableData()

    def __OnDeletePlayer(self):
        id = self.__GetSelectedPlayerID()
        try:
            result = SpawnModal(
                "I have for you imporant question", 
                "Are you sure?", 
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel
            )
            if result == QtWidgets.QMessageBox.Yes:
                self.db_manager.GetDatabaseAPI().DeletePlayer(id)
                self.__RefreshTableData()
        except Exception as e:
            ShowModalException()

    def __OnEditPlayer(self):
        player = self.__GetSelectedPlayerData()
        if not player:
            SpawnModal('Error', 'Cannot find currently selected player.', QtWidgets.QMessageBox.Ok)
            return

        dialog = PlayerEditDialog(self.db_manager, self, player)
        if dialog.exec_():
            self.__RefreshTableData()

    def __OnShowPlayerGame(self):
        print("!!!")

    def RefreshData(self):
        self.__RefreshTableData()

    def __RefreshTableData(self):
        self.player_data = list(self.db_manager.GetDatabaseAPI().GetPlayers())
        self.table_widget.setRowCount(len(self.player_data))
        for i, player in enumerate(self.player_data):
            for j, data in enumerate(player.getData()):
                new_item = QtWidgets.QTableWidgetItem(str(data))
                self.table_widget.setItem(i, j, new_item)
        
        # self.table_widget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        # self.table_widget.resizeColumnsToContents()
        # self.table_widget.horizontalHeader().setStretchLastSection(True)
    