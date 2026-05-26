import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "geheimnis_123_cloud"
UPLOAD_BASE = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024 * 1024  # Erlaubt bis zu 20GB Uploads

# Datenbank-Initialisierung
def init_db():
    conn = sqlite3.connect('cloud.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT UNIQUE, 
                  password TEXT, 
                  limit_mb INTEGER DEFAULT 20480, 
                  role TEXT DEFAULT 'user')''')
    try:
        admin_pass = generate_password_hash('admin123')
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ('admin', admin_pass, 'admin'))
    except: pass 
    conn.commit()
    conn.close()

def get_user_folder(username):
    path = os.path.join(UPLOAD_BASE, username)
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def get_dir_size(path):
    total = 0
    if os.path.exists(path):
        for entry in os.scandir(path):
            if entry.is_file(): total += entry.stat().st_size
    return total / (1024 * 1024) # MB

# --- ROUTEN ---

@app.route('/')
def index():
    if 'user' not in session: return redirect(url_for('login'))
    user_path = get_user_folder(session['user'])
    files = os.listdir(user_path)
    
    conn = sqlite3.connect('cloud.db')
    u = conn.execute("SELECT limit_mb, role FROM users WHERE username=?", (session['user'],)).fetchone()
    conn.close()
    
    used_mb = get_dir_size(user_path)
    used_gb = round(used_mb / 1024, 2)
    limit_gb = u[0] / 1024
    return render_template('dashboard.html', files=files, used=used_gb, limit=limit_gb, role=u[1])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_in = request.form['username']
        pass_in = request.form['password']
        conn = sqlite3.connect('cloud.db')
        user = conn.execute("SELECT * FROM users WHERE username=?", (user_in,)).fetchone()
        conn.close()
        if user and check_password_hash(user[2], pass_in):
            session['user'] = user[1]
            session['role'] = user[4]
            return redirect(url_for('index'))
        flash("Ungültige Logindaten")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = request.form['username']
        pw = generate_password_hash(request.form['password'])
        try:
            conn = sqlite3.connect('cloud.db')
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (user, pw))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except: flash("Nutzername bereits vergeben!")
    return render_template('register.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'user' not in session: return redirect(url_for('login'))
    file = request.files['file']
    if not file: return redirect(url_for('index'))
    
    user_path = get_user_folder(session['user'])
    conn = sqlite3.connect('cloud.db')
    limit_mb = conn.execute("SELECT limit_mb FROM users WHERE username=?", (session['user'],)).fetchone()[0]
    conn.close()
    
    if get_dir_size(user_path) < limit_mb:
        file.save(os.path.join(user_path, secure_filename(file.filename)))
    else:
        flash("Speicherlimit erreicht!")
    return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_file(filename):
    if 'user' not in session: return redirect(url_for('login'))
    user_path = get_user_folder(session['user'])
    return send_from_directory(user_path, filename, as_attachment=True)

@app.route('/delete/<filename>')
def delete_file(filename):
    if 'user' not in session: return redirect(url_for('login'))
    user_path = get_user_folder(session['user'])
    file_path = os.path.join(user_path, secure_filename(filename))
    if os.path.exists(file_path):
        os.remove(file_path)
        flash(f"{filename} gelöscht.")
    return redirect(url_for('index'))

@app.route('/admin')
def admin_panel():
    if session.get('role') != 'admin': return redirect(url_for('index'))
    conn = sqlite3.connect('cloud.db')
    users = conn.execute("SELECT id, username, limit_mb, role FROM users").fetchall()
    conn.close()
    return render_template('admin.html', users=users)

@app.route('/admin/update', methods=['POST'])
def update_limit():
    if session.get('role') != 'admin': return redirect(url_for('index'))
    user_id = request.form['user_id']
    new_gb = int(request.form['limit_gb'])
    conn = sqlite3.connect('cloud.db')
    conn.execute("UPDATE users SET limit_mb=? WHERE id=?", (new_gb * 1024, user_id))
    conn.commit()
    conn.close()
    flash("Limit aktualisiert.")
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete/<int:user_id>')
def delete_user(user_id):
    if session.get('role') != 'admin': return redirect(url_for('index'))
    conn = sqlite3.connect('cloud.db')
    conn.execute("DELETE FROM users WHERE id=? AND role != 'admin'", (user_id,))
    conn.commit()
    conn.close()
    flash("Benutzer gelöscht.")
    return redirect(url_for('admin_panel'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)