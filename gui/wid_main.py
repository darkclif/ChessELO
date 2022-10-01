from PySide6 import QtWidgets

from data.data_manager import DataManager
from gui.wid_players import PlayersWidget
from gui.wid_games import GamesWidget
from gui.wid_status_msg import GlobalStatusMessage


class MainWidget(QtWidgets.QWidget):
    ''' Main widget for storing whole dynamic UI '''
    
    def __init__(self, db_manager: DataManager):
        super().__init__()
        self.change_response = []
        self.db_manager = db_manager
        self.db_manager.SetRootWidget(self)

        self.setWindowTitle("Chess ELO")
        self.main_layout = QtWidgets.QVBoxLayout(self)

        # Status message
        self.status_widget = GlobalStatusMessage(self)

        if not self.db_manager.IsLoaded():
            # Show error and stop.
            self.main_layout.addWidget(self.status_widget)
            self.status_widget.SetMessage(self.db_manager.load_err)
            self.setLayout(self.main_layout)
            return

        # If there is no error...
        self.root_tab = QtWidgets.QTabWidget(self)
        self.main_layout.addWidget(self.root_tab)

        players_tab = PlayersWidget(self.db_manager, self)
        games_tab = GamesWidget(self.db_manager, self)
        
        self.root_tab.addTab(players_tab, "Players")
        self.root_tab.addTab(games_tab, "Games")

        self.change_response = [players_tab, games_tab]
        self.root_tab.currentChanged.connect(self.OnTabChanged)

    def OnTabChanged(self, index: int):
        w = self.root_tab.currentWidget()
        if w in self.change_response:
            w.RefreshData()
