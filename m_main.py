import sqlite3
import sys

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow

from main_n import MyWidget


class IP(QMainWindow, MyWidget):

    def __init__(self):
        super().__init__()
        uic.loadUi('design.ui', self)

        self.setWindowTitle('phortate')

        self.original_image = None
        self.conn = sqlite3.connect('transformation_history.db')
        self.create_table()

        self.action_2.triggered.connect(self.open)
        self.action_3.triggered.connect(self.export)
        self.action_4.triggered.connect(self.undo)
        self.rotate.clicked.connect(self.rotate_run)

        self.rotation = 0
        self.rot = 90

        self.brightness.valueChanged.connect(self.change_brightness)
        self.brightness.setMinimum(-100)
        self.brightness.setMaximum(100)
        self.brightness.setValue(0)

    def undo(self): #функция отменить
        last_transformation = self.get_last_transformation()
        if last_transformation:
            if last_transformation['rotation'] is not None:
                inverse_rotation = -last_transformation['rotation']
                self.rot = inverse_rotation
                self.rotate_run()
                self.rot = 90
            if last_transformation['brightness'] is not None:
                inverse_brightness = -last_transformation['brightness']
                self.change_brightness(inverse_brightness // 20)
            if last_transformation['sharpness'] is not None:
                inverse_sharpness = -last_transformation['sharpness']
                self.update_sharpness(inverse_sharpness)
            self.remove_last_transformation()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = IP()
    ex.show()
    sys.exit(app.exec_())