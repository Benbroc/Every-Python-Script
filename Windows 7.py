import sys
import os

os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --no-sandbox"

try:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QMdiArea, QMdiSubWindow, 
                                 QPushButton, QWidget, QVBoxLayout, QHBoxLayout, 
                                 QFrame, QFileSystemModel, QTreeView, QTextEdit, 
                                 QLineEdit, QGridLayout, QLabel, QStackedWidget)
    from PyQt5.QtWebEngineWidgets import QWebEngineView
    from PyQt5.QtCore import QUrl, Qt, QDir, QTimer, QTime, QPoint, QSize
    from PyQt5.QtGui import QPainter, QPen, QImage, QColor
except ImportError:
    print("Fehler: Bitte installiere: pip install PyQt5 PyQtWebEngine")
    sys.exit()

# ==========================================
# APPS
# ==========================================

class Calculator(QWidget):
    def __init__(self):
        super().__init__()
        l = QVBoxLayout(self)
        self.d = QLineEdit(); self.d.setReadOnly(True); self.d.setAlignment(Qt.AlignRight)
        self.d.setStyleSheet("font-size: 20px; height: 40px; background: #eee; color: black;")
        l.addWidget(self.d)
        g = QGridLayout(); l.addLayout(g)
        btns = ['7','8','9','/','4','5','6','*','1','2','3','-','0','C','=','+']
        r, c = 0, 0
        for b in btns:
            btn = QPushButton(b); btn.setFixedSize(45, 45)
            btn.clicked.connect(self.calc)
            g.addWidget(btn, r, c); c+=1
            if c > 3: c, r = 0, r+1
    def calc(self):
        t = self.sender().text()
        if t == '=':
            try: self.d.setText(str(eval(self.d.text())))
            except: self.d.setText("Error")
        elif t == 'C': self.d.clear()
        else: self.d.setText(self.d.text() + t)

class PaintWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.image = QImage(QSize(2000, 2000), QImage.Format_RGB32)
        self.image.fill(Qt.white)
        self.drawing = False
        self.last_point = QPoint()
    def paintEvent(self, event):
        p = QPainter(self); p.drawImage(self.rect(), self.image, self.image.rect())
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton: self.drawing = True; self.last_point = event.pos()
    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.LeftButton) and self.drawing:
            p = QPainter(self.image)
            p.setPen(QPen(Qt.black, 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            p.drawLine(self.last_point, event.pos()); self.last_point = event.pos(); self.update()

class BootScreen(QWidget):
    def __init__(self, on_finished):
        super().__init__()
        self.setStyleSheet("background-color: #000000;") 
        layout = QVBoxLayout(self)
        self.label = QLabel("Windows 7")
        self.label.setStyleSheet("color: white; font-size: 45pt; font-family: 'Segoe UI Light'; background: transparent;")
        layout.addWidget(self.label, alignment=Qt.AlignCenter)
        QTimer.singleShot(2500, on_finished)

class LoginScreen(QWidget):
    def __init__(self, on_success):
        super().__init__()
        self.on_success = on_success
        self.setStyleSheet("""
            QWidget {
                background: qradialgradient(cx:0.5, cy:0.5, radius:1.5, fx:0.5, fy:0.5, 
                stop:0 #2b83c3, stop:1 #0a4675);
            }
        """)
        
        l = QVBoxLayout(self)
        self.panel = QFrame(); self.panel.setFixedSize(320, 380)
        # Glas-Optik für das Login-Panel
        self.panel.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 25); 
                border-radius: 15px; 
                border: 1px solid rgba(255,255,255,40);
            }
            QLabel { background: transparent; border: none; color: white; }
        """)
        pl = QVBoxLayout(self.panel)
        pl.setContentsMargins(30, 30, 30, 30)
        
        avatar = QLabel("👤"); avatar.setStyleSheet("font-size: 70pt;")
        pl.addWidget(avatar, alignment=Qt.AlignCenter)
        
        name = QLabel("Administrator"); name.setStyleSheet("font-size: 18pt; font-weight: bold;")
        pl.addWidget(name, alignment=Qt.AlignCenter)
        
        self.pw = QLineEdit(); self.pw.setPlaceholderText("Passwort (1234)"); self.pw.setEchoMode(QLineEdit.Password)
        self.pw.setStyleSheet("""
            QLineEdit {
                padding: 10px; background: white; border-radius: 5px; color: black; font-size: 11pt;
            }
        """)
        self.pw.returnPressed.connect(self.check)
        pl.addWidget(self.pw)
        
        btn = QPushButton("Anmelden"); btn.setStyleSheet("""
            QPushButton {
                background: #4a9eff; color: white; padding: 10px; border-radius: 5px; font-weight: bold;
            }
            QPushButton:hover { background: #6db1ff; }
        """)
        btn.clicked.connect(self.check)
        pl.addWidget(btn)
        
        l.addWidget(self.panel, alignment=Qt.AlignCenter)

    def check(self):
        if self.pw.text() == "1234": self.on_success()
        else: self.pw.clear(); self.pw.setPlaceholderText("Falsch!")

class DesktopView(QWidget):
    def __init__(self, parent_window):
        super().__init__()
        self.layout = QVBoxLayout(self); self.layout.setContentsMargins(0, 0, 0, 0); self.layout.setSpacing(0)
        
        self.mdi = QMdiArea()
        self.mdi.setStyleSheet("""
            QMdiArea {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0a5b91, stop:0.5 #1c83c2, stop:1 #0a5b91);
                border: none;
            }
        """)
        self.layout.addWidget(self.mdi)
        
        self.init_taskbar()
        self.init_start_menu()

    def init_taskbar(self):
        self.taskbar = QFrame(); self.taskbar.setFixedHeight(45)
        self.taskbar.setStyleSheet("background: rgba(20, 60, 100, 220); border-top: 1px solid rgba(255,255,255,50);")
        tl = QHBoxLayout(self.taskbar); tl.setContentsMargins(10, 0, 10, 0)
        
        sb = QPushButton("Start"); sb.setFixedSize(60, 36)
        sb.setStyleSheet("background: qradialgradient(cx:0.5, cy:0.5, radius:0.8, stop:0 #55ff55, stop:1 #008800); border-radius: 18px; color: white; font-weight: bold; border: 2px solid white;")
        sb.clicked.connect(self.toggle_start)
        tl.addWidget(sb); tl.addStretch()
        
        self.clock = QLabel(); self.clock.setStyleSheet("color: white; font-weight: bold; font-family: 'Segoe UI'; font-size: 11pt;")
        tl.addWidget(self.clock)
        t = QTimer(self); t.timeout.connect(self.upd_time); t.start(1000); self.upd_time()
        
        self.layout.addWidget(self.taskbar)

    def upd_time(self): self.clock.setText(QTime.currentTime().toString("HH:mm:ss"))

    def init_start_menu(self):
        self.start_menu = QFrame(self); self.start_menu.setFixedSize(280, 420)
        self.start_menu.setStyleSheet("""
            QFrame { background: #f0f0f0; border: 2px solid #2b5797; border-top-left-radius: 12px; }
            QPushButton { text-align: left; padding: 10px; border: none; color: black; }
            QPushButton:hover { background: #3498db; color: white; }
        """)
        sl = QVBoxLayout(self.start_menu)
        apps = [("🌐 Browser", self.open_browser), ("📂 Explorer", self.open_explorer), 
                ("🧮 Calculator", self.open_calc), ("🎨 Paint", self.open_paint), ("📝 Notepad", self.open_note)]
        for n, f in apps:
            b = QPushButton(n); b.clicked.connect(f); b.clicked.connect(self.start_menu.hide)
            sl.addWidget(b)
        sl.addStretch()
        exit_b = QPushButton("🔴 Shut down"); exit_b.clicked.connect(QApplication.instance().quit)
        sl.addWidget(exit_b)
        self.start_menu.hide()

    def toggle_start(self):
        if self.start_menu.isVisible(): self.start_menu.hide()
        else:
            self.start_menu.move(0, self.height() - 45 - self.start_menu.height())
            self.start_menu.show(); self.start_menu.raise_()

    def add_sub(self, w, t, width=800, height=600):
        sub = QMdiSubWindow(); sub.setWidget(w); sub.setWindowTitle(t)
        sub.resize(width, height); sub.setStyleSheet("border: 5px solid #3c7fb1;")
        self.mdi.addSubWindow(sub); sub.show()

    def open_browser(self):
        b = QWebEngineView(); b.setUrl(QUrl("https://www.google.com"))
        self.add_sub(b, "Internet Explorer", 1000, 700)
    def open_explorer(self):
        m = QFileSystemModel(); m.setRootPath(QDir.rootPath())
        t = QTreeView(); t.setModel(m); t.setRootIndex(m.index(QDir.rootPath()))
        self.add_sub(t, "Explorer")
    def open_calc(self): self.add_sub(Calculator(), "Rechner", 260, 350)
    def open_paint(self): self.add_sub(PaintWidget(), "Paint", 800, 600)
    def open_note(self): self.add_sub(QTextEdit(), "Notepad", 500, 400)

class Win7System(QMainWindow):
    def __init__(self):
        super().__init__()
        self.showFullScreen()
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        self.boot = BootScreen(self.go_login)
        self.stack.addWidget(self.boot)
        
    def go_login(self):
        self.login = LoginScreen(self.go_desktop)
        self.stack.addWidget(self.login); self.stack.setCurrentWidget(self.login)
        
    def go_desktop(self):
        self.desktop = DesktopView(self)
        self.stack.addWidget(self.desktop); self.stack.setCurrentWidget(self.desktop)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_F11:
            if self.isFullScreen(): self.showNormal()
            else: self.showFullScreen()
        elif e.key() == Qt.Key_Escape: self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    sys_win = Win7System()
    sys_win.show()
    sys.exit(app.exec_())
