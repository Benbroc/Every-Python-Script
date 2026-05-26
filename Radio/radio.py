import threading
import time
import os
import socket
from flask import Flask, Response, render_template_string, jsonify
import tkinter as tk
from tkinter import filedialog
from mutagen.mp3 import MP3

app = Flask(__name__)

class RadioEngine:
    def __init__(self):
        self.queue = []      # Kommende Songs
        self.history = []    # Gespielte Songs
        self.active_path = None
        self.current_song_name = "Studio Standby"
        self.start_time = 0
        self.song_duration = 0
        self.is_playing = False
        self.version_id = 0

    def get_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except: return "127.0.0.1"

radio = RadioEngine()

# --- WEB SERVER ---

@app.route('/')
def index():
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="de">
        <head>
            <meta charset="UTF-8">
            <title>Elite Radio</title>
            <style>
                body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 20px; display: flex; flex-direction: column; align-items: center; }
                .container { max-width: 800px; width: 100%; display: grid; grid-template-columns: 1fr 1.5fr 1fr; gap: 20px; margin-top: 40px; }
                
                /* Player Central Card */
                .player-card { background: #1e293b; padding: 30px; border-radius: 24px; text-align: center; box-shadow: 0 20px 50px rgba(0,0,0,0.4); border: 1px solid #334155; grid-column: 2; }
                .live-badge { background: #f43f5e; color: white; font-size: 0.7rem; font-weight: bold; padding: 4px 12px; border-radius: 99px; display: inline-block; margin-bottom: 15px; animation: pulse 2s infinite; }
                @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
                h1 { font-size: 1.2rem; margin: 15px 0; color: #38bdf8; min-height: 50px; }
                audio { width: 100%; border-radius: 12px; }

                /* List Panels (History & Queue) */
                .list-panel { background: #1e293b; border-radius: 20px; padding: 20px; border: 1px solid #334155; height: 400px; overflow-y: auto; }
                h2 { font-size: 0.9rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; border-bottom: 1px solid #334155; padding-bottom: 10px; margin-top: 0; }
                .song-item { padding: 10px 0; border-bottom: 1px solid #1e293b; font-size: 0.85rem; color: #cbd5e1; }
                .song-item.dim { opacity: 0.5; font-style: italic; }
                
                @media (max-width: 768px) { .container { grid-template-columns: 1fr; } .player-card { grid-column: 1; order: 1; } .list-panel { order: 2; height: 200px; } }
            </style>
        </head>
        <body>
            <div class="container">
                <!-- HISTORY -->
                <div class="list-panel">
                    <h2>Verlauf</h2>
                    <div id="history-list"></div>
                </div>

                <!-- MAIN PLAYER -->
                <div class="player-card">
                    <div class="live-badge">● LIVE</div>
                    <h1 id="track-display">Warte auf Stream...</h1>
                    <audio id="audio-player" controls autoplay></audio>
                </div>

                <!-- QUEUE -->
                <div class="list-panel">
                    <h2>Warteschlange</h2>
                    <div id="queue-list"></div>
                </div>
            </div>

            <script>
                let currentVersion = -1;
                const player = document.getElementById('audio-player');
                const title = document.getElementById('track-display');
                const qList = document.getElementById('queue-list');
                const hList = document.getElementById('history-list');

                async function updateStatus() {
                    try {
                        const r = await fetch('/status');
                        const data = await r.json();
                        
                        // Listen immer aktualisieren
                        qList.innerHTML = data.queue.map(s => `<div class="song-item">🎵 ${s}</div>`).join('');
                        hList.innerHTML = data.history.map(s => `<div class="song-item dim">✓ ${s}</div>`).reverse().join('');

                        // Bei Songwechsel Stream neu laden
                        if (data.version !== currentVersion) {
                            currentVersion = data.version;
                            title.innerText = data.track;
                            const timestamp = new Date().getTime();
                            player.src = "/stream?v=" + timestamp; 
                            player.load();
                            player.play().catch(e => {});
                        }
                    } catch (e) {}
                }

                setInterval(updateStatus, 2000);
            </script>
        </body>
        </html>
    ''')

@app.route('/status')
def get_status():
    return jsonify(
        track=radio.current_song_name, 
        version=radio.version_id,
        queue=[os.path.basename(p) for p in radio.queue],
        history=[os.path.basename(p) for p in radio.history]
    )

@app.route('/stream')
def stream():
    def generate():
        my_v = radio.version_id
        while True:
            if radio.version_id != my_v: break
            if radio.active_path:
                try:
                    with open(radio.active_path, "rb") as f:
                        ratio = os.path.getsize(radio.active_path) / radio.song_duration
                        f.seek(max(0, int((time.time() - radio.start_time) * ratio)))
                        while radio.is_playing and radio.version_id == my_v:
                            data = f.read(8192)
                            if not data: break
                            yield data
                            time.sleep(0.04)
                except: pass
            time.sleep(0.5)
    return Response(generate(), mimetype="audio/mpeg")

# --- GUI ---
class RadioGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Padio Elite")
        self.root.geometry("500x650")
        self.root.configure(bg="#0f172a")

        tk.Label(root, text="STUDIO CONSOLE", font=("Arial Black", 20), bg="#0f172a", fg="#38bdf8").pack(pady=20)
        
        self.info = tk.Label(root, text=f"IP: http://{radio.get_ip()}:5000", bg="#1e293b", fg="#10b981", font=("Consolas", 11), pady=10)
        self.info.pack(fill=tk.X, padx=40)

        # Queue View
        tk.Label(root, text="Nächste Songs:", bg="#0f172a", fg="#64748b").pack(anchor="w", padx=40, pady=(10,0))
        self.lb = tk.Listbox(root, bg="#1e293b", fg="white", font=("Arial", 11), borderwidth=0, highlightthickness=0)
        self.lb.pack(fill=tk.BOTH, expand=True, padx=40, pady=10)

        btn_frame = tk.Frame(root, bg="#0f172a")
        btn_frame.pack(pady=20)

        tk.Button(btn_frame, text="✚ DATEIEN", command=self.add, bg="#334155", fg="white", bd=0, padx=25, pady=10).grid(row=0, column=0, padx=10)
        tk.Button(btn_frame, text="▶ NEXT", command=self.play_next, bg="#38bdf8", fg="#0f172a", bd=0, padx=25, pady=10, font="bold").grid(row=0, column=1, padx=10)

        threading.Thread(target=self.auto_worker, daemon=True).start()

    def add(self):
        for f in filedialog.askopenfilenames(filetypes=[("Audio", "*.mp3")]):
            radio.queue.append(f)
            self.lb.insert(tk.END, f" 🎵 {os.path.basename(f)}")

    def play_next(self):
        # Alten Song in die History verschieben
        if radio.active_path:
            radio.history.append(radio.active_path)
            if len(radio.history) > 10: radio.history.pop(0) # Nur letzte 10 behalten

        if radio.queue:
            path = radio.queue.pop(0)
            self.lb.delete(0)
            radio.song_duration = MP3(path).info.length
            radio.active_path = path
            radio.current_song_name = os.path.basename(path)
            radio.start_time = time.time()
            radio.is_playing = True
            radio.version_id += 1
        else:
            radio.is_playing = False
            radio.active_path = None
            radio.current_song_name = "Ende der Playlist"
            radio.version_id += 1

    def auto_worker(self):
        while True:
            if radio.is_playing and radio.active_path:
                if (time.time() - radio.start_time) >= (radio.song_duration - 0.5):
                    self.root.after(0, self.play_next)
            time.sleep(0.5)

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, threaded=True, use_reloader=False), daemon=True).start()
    root = tk.Tk()
    gui = RadioGUI(root)
    root.mainloop()