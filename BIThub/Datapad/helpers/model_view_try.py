import sys
from PyQt5.QtCore import QDir
from PyQt5.QtWidgets import *

if __name__ == "__main__":

    app = QApplication([])
    splitter = QSplitter()

    model = QFileSystemModel()
    model.setRootPath(QDir.currentPath())
    tree = QTreeView(splitter)

    tree.setModel(model)

    tree.setRootIndex(model.index(QDir.currentPath()))

    list = QListView(splitter)
    list.setModel(model)
    list.setRootIndex(model.index(QDir.currentPath()))

    splitter.setWindowTitle("Two views onto the same file system model")
    splitter.show()
    sys.exit(app.exec())