import sys
from PySide6.QtWidgets import QApplication
from .ui.windows import CompanionApp

def main():
    app=QApplication(sys.argv); app.setApplicationName("Crystal Companion"); app.setQuitOnLastWindowClosed(False)
    controller=CompanionApp(app)
    sys.exit(app.exec())
if __name__ == "__main__": main()
