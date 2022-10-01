from PySide6 import QtWidgets
import traceback

def SpawnModal(title: str, text: str, buttons):
    msgBox = QtWidgets.QMessageBox()
    msgBox.setIcon(QtWidgets.QMessageBox.Information)
    msgBox.setText(text)
    msgBox.setWindowTitle(title)
    msgBox.setStandardButtons(buttons)
    return msgBox.exec()

def ShowModalException():
    tb = traceback.format_exc()
    SpawnModal("Error", "Error occured: {}".format(tb), QtWidgets.QMessageBox.Ok)