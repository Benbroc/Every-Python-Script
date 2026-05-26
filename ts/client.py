import socket
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, simpledialog

class TS3Client:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("TS3 Python Pro")
        self.root.geometry("900x550")
        self.root.configure(bg="#2b2b2b")

        # Nickname via Pop-up
        self.nickname = simpledialog.askstring("Login", "Dein Name:", parent=self.root) or "Gast"

        self._setup_style()
        self._build_ui()
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect()

    def _setup_style(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", background="#333333", foreground="white", fieldbackground="#333333", borderwidth=0)
        style.map("Treeview", background=[('selected', '#4a90e2')])

    def _build_ui(self):
        # Paned Window (Splitter)
        self.pw = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        self.pw.pack(fill=tk.BOTH, expand=True)

        # Links: User & Channel Liste
        self.left_panel = tk.Frame(self.pw, bg="#333333")
        self.tree = ttk.Treeview(self.left_panel, show="tree")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        self.server_node = self.tree.insert("", "end", text=" 🌐 Mein Server", open=True)
        self.pw.add(self.left_panel, weight=1)

        # Rechts: Chat
        self.right_panel = tk.Frame(self.pw, bg="#2b2b2b")
        self.chat_area = scrolledtext.ScrolledText(self.right_panel, bg="#1e1e1e", fg="#dcdcdc", font=("Consolas", 10), state='disabled')
        self.chat_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Input
        self.entry = tk.Entry(self.right_panel, bg="#3c3c3c", fg="white", insertbackground="white", borderwidth=5, relief=tk.FLAT)
        self.entry.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.entry.bind("<Return>", self.send_msg)
        
        self.pw.add(self.right_panel, weight=3)

    def connect(self):
        try:
            self.socket.connect(('127.0.0.1', 65432))
            self.socket.send(self.nickname.encode('utf-8'))
            threading.Thread(target=self.receive, daemon=True).start()
            self.write_chat(f"SYSTEM: Verbunden als {self.nickname}. Nutze /msg Name Text für DMs.")
        except:
            self.write_chat("SYSTEM: Server nicht erreichbar.")

    def send_msg(self, event=None):
        msg = self.entry.get()
        if msg:
            self.socket.send(msg.encode('utf-8'))
            if not msg.startswith("/msg "): # Normale Nachricht lokal anzeigen
                self.write_chat(f"Du: {msg}")
            self.entry.delete(0, tk.END)

    def receive(self):
        while True:
            try:
                data = self.socket.recv(1024).decode('utf-8')
                if not data: break
                
                # Wenn SYSTEM-Nachricht über User-Liste kommt (simuliert)
                if "ist beigetreten" in data or "verlassen" in data:
                    # Hier könnte man die Treeview-Logik einbauen
                    pass
                
                self.write_chat(data)
            except:
                break

    def write_chat(self, text):
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, text + "\n")
        self.chat_area.config(state='disabled')
        self.chat_area.yview(tk.END)

if __name__ == "__main__":
    TS3Client().root.mainloop()