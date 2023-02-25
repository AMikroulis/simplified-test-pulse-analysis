from sys import executable, argv
from subprocess import check_output
from PyQt5.QtWidgets import QFileDialog, QApplication


def gui_fname(directory='./'):
    file = check_output([executable, __file__, directory])
    return file


if __name__ == "__main__":
    directory = argv[1]
    app = QApplication([directory])
    fname = QFileDialog.getExistingDirectory()
    print(fname.strip(), end='')