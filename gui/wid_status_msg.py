from PySide6 import QtCore, QtWidgets, QtGui
from enum import IntEnum


class EMsgColor(IntEnum):
    ERROR   = 0 
    WARNING = 1 
    NORMAL  = 2
    _SIZE   = 3


class GlobalStatusMessage(QtWidgets.QWidget):
    ''' Singleton for storing reference to status message widget. '''
    instance = None
    
    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)

        # Set palletes for handling text colors
        self.palettes = [QtGui.QPalette() for _ in range(EMsgColor._SIZE) ]
        self.palettes[EMsgColor.ERROR].setColor(QtGui.QPalette.WindowText, QtGui.QColor(255, 100, 100, 255))
        self.palettes[EMsgColor.WARNING].setColor(QtGui.QPalette.WindowText, QtGui.QColor(250, 155, 50, 255))
        self.palettes[EMsgColor.NORMAL].setColor(QtGui.QPalette.WindowText, QtGui.QColor(0, 0, 0, 255))

        # Label
        main_layout = QtWidgets.QHBoxLayout()
        self.wid_status = QtWidgets.QLabel("", self)
        self.wid_status.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(self.wid_status)

        self.setLayout(main_layout)
        GlobalStatusMessage.instance = self

    @staticmethod
    def SetMessage(msg: str, color: EMsgColor = EMsgColor.NORMAL)-> None:
        self = GlobalStatusMessage.instance
        self.wid_status.setText(msg)
        self.wid_status.setPalette(self.palettes[color])
