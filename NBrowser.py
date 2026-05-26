import sys
import os

# --- STABILITÄTS-FLAGS (WICHTIG GEGEN CRASHES) ---
os.environ["QTWEBENGINE_DISABLE_GPU"] = "1"
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--no-sandbox --disable-gpu --remote-debugging-port=9222"

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from PyQt6.QtWebEngineWidgets import *
from PyQt6.QtWebEngineCore import *

class GlowBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Fenster-Setup (Rahmenlos)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.resize(1200, 800)
        self.drag_pos = None

        # Hauptlayout
        self.container = QWidget()
        self.setCentralWidget(self.container)
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # --- 1. TOP HEADER (Tabs & Steuerung) ---
        self.header = QWidget()
        self.header.setFixedHeight(34)
        self.header.setObjectName("Header")
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(5, 0, 0, 0)
        header_layout.setSpacing(0)

        self.tabs = QTabBar()
        self.tabs.setExpanding(False)
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.tabBarClicked.connect(self.switch_tab)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        
        self.add_btn = QPushButton("+")
        self.add_btn.setFixedSize(28, 28)
        self.add_btn.clicked.connect(lambda: self.add_new_tab())

        # Fenster-Buttons (Min, Max, Close)
        self.controls = QWidget()
        controls_layout = QHBoxLayout(self.controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(0)
        
        self.btn_min = self.create_win_btn("-", self.showMinimized)
        self.btn_max = self.create_win_btn("□", self.toggle_max)
        self.btn_close = self.create_win_btn("×", self.close, is_red=True)
        
        controls_layout.addWidget(self.btn_min)
        controls_layout.addWidget(self.btn_max)
        controls_layout.addWidget(self.btn_close)

        header_layout.addWidget(self.tabs)
        header_layout.addWidget(self.add_btn)
        header_layout.addStretch()
        header_layout.addWidget(self.controls)

        # --- 2. NAVIGATION (URL & Zahnrad) ---
        self.nav_bar = QWidget()
        self.nav_bar.setFixedHeight(40)
        nav_layout = QHBoxLayout(self.nav_bar)
        nav_layout.setContentsMargins(10, 5, 10, 5)
        nav_layout.setSpacing(10)
        
        self.btn_back = QPushButton("‹")
        self.btn_back.setFixedSize(30, 30)
        self.btn_back.clicked.connect(self.go_back)
        
        self.url_bar = QLineEdit()
        self.url_bar.setFixedHeight(28)
        self.url_bar.returnPressed.connect(self.navigate)
        
        self.btn_settings = QPushButton("⚙")
        self.btn_settings.setFixedSize(30, 30)
        self.btn_settings.clicked.connect(self.open_settings)
        
        nav_layout.addWidget(self.btn_back)
        nav_layout.addWidget(self.url_bar)
        nav_layout.addWidget(self.btn_settings)

        # --- 3. INHALT ---
        self.browser_stack = QStackedWidget()

        self.main_layout.addWidget(self.header)
        self.main_layout.addWidget(self.nav_bar)
        self.main_layout.addWidget(self.browser_stack)

        self.apply_styles()
        self.add_new_tab(QUrl("https://www.google.com"), "Google")

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget { background-color: #0d0d0d; color: #eee; font-family: 'Segoe UI'; font-size: 12px; }
            #Header { background-color: #000; border-bottom: 1px solid #1a1a1a; }
            
            QTabBar::tab {
                background: #1a1a1a;
                padding: 5px 15px;
                margin-top: 4px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                min-width: 130px;
                color: #888;
            }
            QTabBar::tab:selected { 
                background: #0d0d0d; 
                color: #00ffcc; 
                border-bottom: 2px solid #00ffcc; 
            }
            
            QLineEdit {
                background-color: #1a1a1a;
                border: 1px solid #333;
                border-radius: 14px;
                padding: 0 12px;
                color: #00ffcc;
                font-family: 'Consolas', monospace;
            }
            
            QPushButton { border: none; background: transparent; font-size: 16px; color: white; }
            QPushButton:hover { background-color: #252525; border-radius: 4px; }
            #CloseBtn:hover { background-color: #c42b1c; border-radius: 0; }
        """)

    def create_win_btn(self, text, slot, is_red=False):
        btn = QPushButton(text)
        btn.setFixedSize(45, 34)
        btn.clicked.connect(slot)
        if is_red: btn.setObjectName("CloseBtn")
        return btn

    def add_new_tab(self, qurl=None, label="Laden..."):
        browser = QWebEngineView()
        
        # Sicherheitseinstellungen für interne Seiten
        s = browser.settings()
        s.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
        
        if not qurl: qurl = QUrl("https://www.google.com")
        
        idx = self.browser_stack.addWidget(browser)
        tab_idx = self.tabs.addTab(label)
        self.tabs.setTabData(tab_idx, idx)
        
        self.tabs.setCurrentIndex(tab_idx)
        self.browser_stack.setCurrentIndex(idx)
        browser.setUrl(qurl)
        
        browser.titleChanged.connect(lambda title: self.update_tab_title(browser, title))
        browser.urlChanged.connect(lambda q: self.url_bar.setText(q.toString()) if self.browser_stack.currentWidget() == browser else None)

    def update_tab_title(self, browser, title):
        for i in range(self.tabs.count()):
            if self.browser_stack.widget(self.tabs.tabData(i)) == browser:
                self.tabs.setTabText(i, title[:15])
                break

    def open_settings(self):
        if self.browser_stack.currentWidget():
            # qtwebengine://settings ist die korrekte interne URL für Qt
            self.browser_stack.currentWidget().setUrl(QUrl("qtwebengine://settings"))

    def switch_tab(self, i):
        stack_idx = self.tabs.tabData(i)
        if stack_idx is not None:
            self.browser_stack.setCurrentIndex(stack_idx)
            self.url_bar.setText(self.browser_stack.currentWidget().url().toString())

    def close_tab(self, i):
        if self.tabs.count() > 1:
            stack_idx = self.tabs.tabData(i)
            widget = self.browser_stack.widget(stack_idx)
            self.browser_stack.removeWidget(widget)
            widget.deleteLater()
            self.tabs.removeTab(i)
        else: self.close()

    def navigate(self):
        txt = self.url_bar.text()
        url = QUrl(txt) if "." in txt else QUrl(f"https://www.google.com/search?q={txt}")
        if not url.scheme(): url.setScheme("http")
        if self.browser_stack.currentWidget():
            self.browser_stack.currentWidget().setUrl(url)

    def go_back(self):
        if self.browser_stack.currentWidget(): self.browser_stack.currentWidget().back()

    def toggle_max(self):
        if self.isMaximized(): self.showNormal()
        else: self.showMaximized()

    # Fenster bewegen
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self.header.underMouse():
            self.drag_pos = e.globalPosition().toPoint()
    def mouseMoveEvent(self, e):
        if self.drag_pos:
            delta = e.globalPosition().toPoint() - self.drag_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.drag_pos = e.globalPosition().toPoint()
    def mouseReleaseEvent(self, e): self.drag_pos = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = GlowBrowser()
    w.show()
    sys.exit(app.exec())