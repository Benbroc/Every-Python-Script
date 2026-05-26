import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'voltix_geheimer_schluessel_123'

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
DATA_FILE = 'updates.json'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_updates():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_all_updates(updates):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(updates, f, indent=4)

@app.route('/')
def home():
    all_updates = get_updates()
    # Nur die ersten 2 Updates an die Startseite senden
    newest_two = all_updates[:2]
    return render_template('index.html', updates=newest_two)
    
    if request.method == 'POST':
        title = request.form.get('title')
        text = request.form.get('text')
        file = request.files.get('photo')
        
        # Aktuelles Datum generieren
        current_date = datetime.now().strftime("%d.%m.%Y")
        
        filename = None
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        if title:
            updates = get_updates()
            updates.insert(0, {
                "title": title, 
                "text": text, 
                "image": filename,
                "date": current_date # Datum wird gespeichert
            })
            save_all_updates(updates)
            return redirect(url_for('admin'))

    return render_template('admin.html', updates=get_updates())

@app.route('/delete/<int:index>')
def delete_update(index):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    updates = get_updates()
    if 0 <= index < len(updates):
        update = updates[index]
        if update.get('image'):
            img_path = os.path.join(app.config['UPLOAD_FOLDER'], update['image'])
            if os.path.exists(img_path):
                os.remove(img_path)
        updates.pop(index)
        save_all_updates(updates)
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6001, debug=True)
