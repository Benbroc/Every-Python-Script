import threading
import os
import shutil
from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO, emit
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

elements = {}

@app.route('/')
def index():
    return render_template('kiosk.html')

@app.route('/static/uploads/<filename>')
def serve_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@socketio.on('connect')
def on_connect():
    emit('sync_all', elements)

def start_flask():
    socketio.run(app, host='0.0.0.0', port=5000)

threading.Thread(target=start_flask, daemon=True).start()

# --- TKINTER GUI (DARK MODE STYLE) ---
root = tk.Tk()
root.title("Kiosk Master Control")
root.configure(bg="#1e1e1e")

# Das Vorschaufeld (Canvas)
canvas = tk.Canvas(root, width=800, height=450, bg="#000", highlightthickness=0)
canvas.pack(pady=20, padx=20)

tk_images = {}

def on_drag(event):
    item = canvas.find_withtag("selected")
    if item:
        canvas.coords(item, event.x, event.y)
        tag = canvas.gettags(item)[0]
        elements[tag]["x"] = event.x
        elements[tag]["y"] = event.y
        socketio.emit('update_element', {"id": tag, "x": event.x, "y": event.y})

def on_click(event):
    canvas.dtag("all", "selected")
    item = canvas.find_closest(event.x, event.y)
    canvas.addtag_withtag("selected", item)

def add_text():
    content = entry.get() or "Test"
    obj_id = f"el_{len(elements)}"
    canvas.create_text(100, 100, text=content, fill="white", font=("Arial", 20, "bold"), tags=(obj_id,))
    elements[obj_id] = {"type": "text", "content": content, "x": 100, "y": 100}
    socketio.emit('new_element', {"id": obj_id, **elements[obj_id]})

def add_image():
    file_path = filedialog.askopenfilename()
    if file_path:
        filename = os.path.basename(file_path)
        shutil.copy(file_path, os.path.join(UPLOAD_FOLDER, filename))
        obj_id = f"img_{len(elements)}"
        img = Image.open(os.path.join(UPLOAD_FOLDER, filename))
        img.thumbnail((150, 150))
        tk_img = ImageTk.PhotoImage(img)
        tk_images[obj_id] = tk_img
        canvas.create_image(200, 200, image=tk_img, tags=(obj_id,))
        img_url = f"/static/uploads/{filename}"
        elements[obj_id] = {"type": "image", "content": img_url, "x": 200, "y": 200}
        socketio.emit('new_element', {"id": obj_id, **elements[obj_id]})

canvas.bind("<B1-Motion>", on_drag)
canvas.bind("<Button-1>", on_click)

# UI Elemente
frame = tk.Frame(root, bg="#1e1e1e")
frame.pack(pady=10)
entry = tk.Entry(frame, width=30, font=("Arial", 12))
entry.pack(side=tk.LEFT, padx=5)
tk.Button(frame, text="Text +", command=add_text, bg="#444", fg="white", padx=10).pack(side=tk.LEFT, padx=2)
tk.Button(frame, text="Bild +", command=add_image, bg="#28a745", fg="white", padx=10).pack(side=tk.LEFT, padx=2)

root.mainloop()