import os
import json
import traceback

from PySide6.QtWidgets import QLabel, QWidget
from PySide6 import QtGui
from data.chess_structs import RichChessGame

from data.database_api import ChessDataAPI

class DataManager:
    SQL_DB_PATH = "./database.db"

    def __init__(self, root_folder):
        self.main_widget = None

        # Path
        self.db_path = os.path.join(root_folder, DataManager.SQL_DB_PATH)

        # Data
        self.data = None
        self.loaded = False
        self.load_err = ''

    def SetRootWidget(self, main_widget)-> None:
        self.main_widget = main_widget
    
    def IsLoaded(self)-> bool:
        return self.loaded
    
    def GetDatabaseAPI(self):
        return self.data

    # Bootstrap
    def LoadData(self)-> None:
        try:
            self.data = ChessDataAPI(self.db_path)
            self.loaded = True
        except Exception as e:
            trc = traceback.format_exc()
            self.load_err = "Error during loading data: {}\n{}".format(str(e), trc)
    
    # Helpers / Wrappers around database API
    def GetEloTimestamp(self):
        api = self.GetDatabaseAPI()
        return api.GetInfo().elo_calc_date
