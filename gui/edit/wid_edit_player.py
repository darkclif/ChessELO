from ast import Delete
from PySide6 import QtWidgets
from data.data_manager import DataManager
from data.chess_structs import ChessPlayer
from helpers.gui import ShowModalException, SpawnModal


class PlayerEditDialog(QtWidgets.QDialog):
    def __init__(self, db_manager: DataManager, parent: QtWidgets.QWidget, player: ChessPlayer = None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.player = player

        self.main_layout = QtWidgets.QGridLayout(self)
        self.setWindowTitle("Edit player" if player else "Create player")
        self.setLayout(self.main_layout)
        self.setModal(True)

        # Add data
        data_layout = [
            (False, 'id', 'ID', lambda p: p.id),
            (False, 'elo', 'ELO', lambda p: p.elo),
            (True, 'full_name', 'Full name', lambda p: p.full_name),
            (True, 'nick', 'Nick name', lambda p: p.nick),
        ]
        self.named_edits = {}
        for row, item in enumerate(data_layout):
            enabled, name, text, get_data = item

            # Label
            self.main_layout.addWidget(QtWidgets.QLabel(text, self), row, 1)
            
            # Edit
            text_edit = QtWidgets.QLineEdit(self)
            text_edit.setMaxLength(24)
            self.named_edits[name] = text_edit
            if not enabled:
                text_edit.setReadOnly(True)
                text_edit.setEnabled(False)
            if player:
                text_edit.setText(str(get_data(player)))
            self.main_layout.addWidget(text_edit, row, 2)

        # Add buttons
        accept_btn = QtWidgets.QPushButton("Accept (A)", self)
        cancel_btn = QtWidgets.QPushButton("Cancel (C)", self)

        accept_btn.clicked.connect(self.__ApplyChanges)
        cancel_btn.clicked.connect(self.__CancelChanges)

        self.main_layout.addWidget(accept_btn, len(data_layout), 1)
        self.main_layout.addWidget(cancel_btn, len(data_layout), 2)

    def __ApplyChanges(self):
        try:
            if self.player:
                data = (self.named_edits['full_name'].text(), self.named_edits['nick'].text())
                self.db_manager.GetDatabaseAPI().UpdatePlayer(self.player.id, *data)
            else:
                data = (self.named_edits['full_name'].text(), self.named_edits['nick'].text())
                self.db_manager.GetDatabaseAPI().AddPlayer(*data)
        except Exception as e:
            ShowModalException()

        self.accept()

    def __CancelChanges(self):
        self.close()