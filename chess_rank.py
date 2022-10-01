import sys, os
from PySide6 import QtWidgets
from data.data_manager import DataManager
from gui.wid_main import MainWidget

if __name__ == "__main__":
    # For dev
    root_folder = os.path.dirname(os.path.abspath(__file__))
    # For release
    # root_folder = ""
    
    chess_data = DataManager(root_folder)
    chess_data.LoadData()

    # Spawn application
    app = QtWidgets.QApplication([])

    widget = MainWidget(chess_data)
    widget.resize(1000, 600)
    widget.show()

    sys.exit(app.exec())
