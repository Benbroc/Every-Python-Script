import sys
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView

class FullscreenBrowser(QMainWindow):
    def __init__(self):
        super().__init__()

        # Web-Ansicht erstellen
        self.browser = QWebEngineView()
        
        # Die Ziel-URL setzen
        self.browser.setUrl(QUrl("http://voltix.giize.com:5000"))
        
        # Den Browser als zentrales Element des Fensters setzen
        self.setCentralWidget(self.browser)
        
        # In den Vollbildmodus wechseln
        self.showFullScreen()

        # Beenden mit der ESC-Taste ermöglichen
        self.browser.installEventFilter(self)

    def keyPressEvent(self, event):
        # Wenn man ESC drückt, schließt sich das Programm
        if event.key() == 0x01000000: # Code für die Escape-Taste
            self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # App-Name (optional)
    app.setApplicationName("Voltix Browser")
    
    window = FullscreenBrowser()
    
    sys.exit(app.exec())