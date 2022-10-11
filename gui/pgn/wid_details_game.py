from PySide6 import QtWidgets, QtCore, QtGui
from data.chess_structs import GameSide, RichChessGame
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtSvgWidgets import QSvgWidget
from data.data_manager import DataManager
from functools import partial
import chess.pgn
import io


class GameDetailsDialog(QtWidgets.QDialog):
    def __init__(self, db_manager: DataManager, parent: QtWidgets.QWidget, game: RichChessGame):
        super().__init__(parent)
        self.db_manager = db_manager
        self.game = game

        self.pgn_game = None
        self.curr_board = None
        self.moves = []
        self.current_move = 0
        self.error = None

        try:
            self.pgn_game = self.__LoadGamePGN()
            self.curr_board = self.pgn_game.board()
        except ValueError as e:
            self.error = str(e)

        if len(self.pgn_game.errors):
            self.error = ''.join(['>> {}\n'.format(str(e)) for e in self.pgn_game.errors])

        # Layout
        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.setWindowTitle("Game details")
        self.setLayout(self.main_layout)
        self.setModal(True)

        self.main_layout.addWidget(self.__CreateGameDataWidget())
        if not self.error:
            self.main_layout.addWidget(self.__CreateMoveWidget())
            self.main_layout.addWidget(self.__CreateSVGWidget())
            self.__RefreshSVG(1)
        else:
            self.main_layout.addWidget(self.__CreateErrorInfoWidget())

    # Create game data widget
    def __CreateErrorInfoWidget(self):
        widget = QtWidgets.QWidget(self)
        layout = QtWidgets.QHBoxLayout(widget)
        layout.addWidget(QtWidgets.QLabel("Error during loading PGN:\n {}".format(self.error), widget))
        return widget

    def __CreateGameDataWidget(self):
        widget = QtWidgets.QWidget(self)
        grid_layout = QtWidgets.QGridLayout(widget)
        
        data_layout = [
            ('ID', lambda rg: rg.id),
            ('Date', lambda rg: rg.GetFormatedDate()),
            ('White', lambda rg: rg.GetPlayerDisplayName(GameSide.WHITE)),
            ('ELO', lambda rg: rg.GetPlayerEloChange(GameSide.WHITE)),
            ('Black', lambda rg: rg.GetPlayerDisplayName(GameSide.BLACK)),
            ('ELO', lambda rg: rg.GetPlayerEloChange(GameSide.BLACK)),
            ('Result', lambda rg: rg.GetFormatedResult()),
            ('Archived', lambda rg: rg.archived),
        ]

        for i, entry in enumerate(data_layout):
            grid_layout.addWidget(QtWidgets.QLabel(entry[0], self), i, 1)
            wid = QtWidgets.QLineEdit(self)
            wid.setText(str(entry[1](self.game)))
            wid.setReadOnly(True)
            wid.setEnabled(False)
            grid_layout.addWidget(wid, i, 2)

        grid_layout.setRowStretch(7, 10)

        widget.setLayout(grid_layout)
        return widget

    def __CreateMoveWidget(self):
        widget = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout(widget)

        layout.addWidget(self.__CreateMoveGridWidget())
        layout.addWidget(self.__CreateMoveArrows())

        widget.setLayout(layout)
        return widget

    def __CreateMoveGridWidget(self):
        self.table_widget = QtWidgets.QTableWidget(self)
        # Prevent default table widget navigation
        self.table_widget.keyPressEvent = lambda *args, **kwargs: self.keyPressEvent(*args, **kwargs)
        self.table_widget.setColumnCount(2)
        self.table_widget.setHorizontalHeaderLabels(['White', 'Black'])
        self.table_widget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

        self.table_widget.setRowCount((len(list(self.pgn_game.mainline_moves())) + 1) / 2)

        board = self.pgn_game.board()
        row, col, cnt = 0, 0, 1
        for m in self.pgn_game.mainline_moves():
            self.moves.append(m)

            san = board.san_and_push(m)
            new_item = QtWidgets.QTableWidgetItem(san)
            new_item.setData(QtCore.Qt.UserRole, cnt)
            self.table_widget.setItem(row, col, new_item)

            row += col * 1
            col = (col + 1) % 2
            cnt += 1
       
        #self.table_widget.itemClicked.connect(self.__OnMoveSelected)
        self.table_widget.itemSelectionChanged.connect(self.__OnMoveSelected)
        return self.table_widget

    def __CreateMoveArrows(self):
        widget = QtWidgets.QWidget(self)
        layout = QtWidgets.QHBoxLayout(widget)
        layout.setContentsMargins(0,0,0,0)

        self.prev_button = QtWidgets.QPushButton("<", widget)
        self.next_button = QtWidgets.QPushButton(">", widget)

        self.prev_button.clicked.connect(partial(self.__OnChangeMove, -1))
        self.next_button.clicked.connect(partial(self.__OnChangeMove, 1))

        layout.addWidget(self.prev_button)
        layout.addWidget(self.next_button)
        widget.setLayout(layout)

        return widget

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Left:
            self.__OnChangeMove(-1)
            return
        elif event.key() == QtCore.Qt.Key_Right:
            self.__OnChangeMove(1)
            return
        super(GameDetailsDialog, self).keyPressEvent(event)

    def __OnChangeMove(self, delta):
        move_id = min(max(0, self.current_move + delta - 1), len(self.moves) - 1)
        row, col = move_id // 2, move_id % 2

        self.table_widget.clearSelection()
        self.table_widget.setRangeSelected(QtWidgets.QTableWidgetSelectionRange(row, col, row, col), True) 
        self.__AutoScroll()

    def __AutoScroll(self):
        items = self.table_widget.selectedItems()
        if len(items):
            self.table_widget.scrollToItem(items[0])

    def __CreateSVGWidget(self):
        self.svg_wid = QSvgWidget(self)
        return self.svg_wid

    def __LoadGamePGN(self):
        str_io = io.StringIO(self.game.pgn)
        pgn_game = chess.pgn.read_game(str_io)
        return pgn_game

    def __OnMoveSelected(self):
        items = self.table_widget.selectedItems()
        if len(items):
            move_id = items[0].data(QtCore.Qt.UserRole)
            
            if move_id:
                self.__RefreshSVG(move_id)

    def __RefreshSVG(self, move_id: int):
        while move_id > self.current_move:
            self.current_move += 1
            self.curr_board.push(self.moves[self.current_move - 1])

        while move_id < self.current_move:
            self.current_move -= 1
            self.curr_board.pop()

        # Refresh
        svg = chess.svg.board(self.curr_board)
        svg = bytearray(svg, encoding='utf-8')
        self.svg_wid.load(svg)

        self.current_move = move_id

