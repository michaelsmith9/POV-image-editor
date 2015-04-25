"""
ENGG2800 POV Software
Distribution Version 1
Development version 1.05

"""


import controller
from controller import Controller
from PyQt4 import QtGui
import sys


def main():
    """
    Initialises the Controller.
    """
    app = QtGui.QApplication(sys.argv)
    ex = Controller()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
