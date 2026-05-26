import logging
from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit

# Flask-Setup
app = Flask(__name__)
app.config['SECRET_KEY'] = 'discord_clone_2026'
# Wir erzwingen den threading-Modus, um Treiber-Konflikte (eventlet/gevent) zu vermeiden
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Logs minimieren
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Speicher (Wird beim Server-Neustart geleert)
users = {}          # { sid: nickname }
pending_fas = {}    # { ziel_name: [liste_von_sendern] }
friends = {}        # { name: [liste_von_freunden] }

# --- DAS DESIGN (HTML & CSS) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Discord Python Pro</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        :root {
            --bg-sidebar: #1e1f22;
            --bg-channels: #2b2d31;
            --bg-chat: #313338;
            --discord-blue: #5865f2;
            --text-main: #dbdee1;
            --text-muted: #949ba4;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background: var(--bg-chat); color: var(--text-main); display: flex; height: 100vh; overflow: hidden; }

        /* Links: Server-Leiste */
        #activity-bar { width: 72px; background: var(--bg-sidebar); display: flex; flex-direction: column; align-items: center; padding-top: 12px; gap: 8px; flex-shrink: 0; }
        .circle-icon { width: 48px; height: 48px; background: #35363c; border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: 0.2s; color: white; }
        .circle-icon:hover { border-radius: 15px; background: var(--discord-blue); }
        .circle-icon.active { border-radius: 15px; background: var(--discord-blue); }

        /* Mitte: Sidebar */
        #sidebar { width: 240px; background: var(--bg-channels); display: flex; flex-direction: column; flex-shrink: 0; }
        .sidebar-header { height: 48px; padding: 0 16px; display: flex; align-items: center; font-weight: bold; border-bottom: 1px solid #232428; }
        .sidebar-list { flex: 1; padding: 10px; overflow-y: auto; }
        .user-item { padding: 8px; border-radius: 4px; cursor: pointer; display: flex; align-items: center; gap: 10px; margin-bottom: 2px; }
        .user-item:hover { background: #35373c; }
        .avatar { width: 32px; height: 32px; background: #4e5058; border-radius: 50%; }

        /* Rechts: Hauptbereich */
        #main { flex: 1; display: flex; flex-direction: column; }
        #top-nav { height: 48px; padding: 0 16px; display: flex; align-items: center; border-bottom: 1px solid #232428; gap: 20px; background: var(--bg-chat); }
        .nav-link { cursor: pointer; color: var(--text-muted); font-weight: bold; font-size: 0.9em; }
        .nav-link.active { color: white; background: #3f4147; padding: 4px 10px; border-radius: 4px; }

        #chat-window { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 15px; }
        .message { display: flex; gap: 15px; }
        .msg-user { font-weight: bold; color: white; margin-right: 5px; }
        .msg-text { color: var(--text-main); font-size: 0.95em; }

        #input-area { padding: 0 20px 24px; }
        #input-wrap { background: #383a40; border-radius: 8px; padding: 10px 15px; }
        input { background: transparent; border: none; color: white; width: 100%; outline: none; font-size: 1em; }

        /* Popups */
        #overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); display: none; z-index: 10; }
        #modal { position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: #111214; padding: 30px; border-radius: 8px; display: none; z-index: 11; width: 300px; text-align: center; }
        button { background: var(--discord-blue); color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; width: 100%; margin-top: 20px; font-weight: bold; }

        /* Freunde View */
        #friends-view { flex: 1; padding: 20px; display: none; overflow-y: auto; }
        .fa-card { background: #2b2d31; padding: 15px; border-radius: 8px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
        .accept-btn { background: #248046; width: auto; margin: 0; padding: 5px 15px; }
    </style>
</head>
<body>

<div id="overlay" onclick="closeModal()"></div>
<div id="modal">
    <div class="avatar" style="width:70px; height:70px; margin: 0 auto 15px;"></div>
    <h3 id="modal-name">User</h3>
    <button onclick="sendFA()">Freundschaftsanfrage senden</button>
</div>

<div id="activity-bar">
    <div class="circle-icon active" onclick="switchMainTab('chat')">H</div>
    <div class="circle-icon" onclick="switchMainTab('friends')">F</div>
</div>

<div id="sidebar">
    <div class="sidebar-header">Mitglieder</div>
    <div class="sidebar-list" id="user-list"></div>
</div>

<div id="main">
    <div id="top-nav">
        <span style="color:white; font-weight:bold;"># global-chat</span>
        <div style="width:1px; height:20px; background:#444;"></div>
        <div id="nav-chat-btn" class="nav-link active" onclick="switchMainTab('chat')">Chat</div>
        <div id="nav-friends-btn" class="nav-link" onclick="switchMainTab('friends')">Freunde & DMs</div>
    </div>

    <div id="chat-view" style="display:flex; flex-direction:column; flex:1;">
        <div id="chat-window"></div>
        <div id="input-area">
            <div id="input-wrap">
                <input type="text" id="msg-input" placeholder="Nachricht an #global-chat">
            </div>
        </div>
    </div>

    <div id="friends-view">
        <h2 style="margin-bottom:20px;">Anfragen</h2>
        <div id="fa-list"></div>
        <h2 style="margin-top:40px; margin-bottom:20px;">Deine Freunde</h2>
        <div id="friends-list"></div>
    </div>
</div>

<script>
    const socket = io();
    let myName = prompt("Dein Name:") || "User" + Math.floor(Math.random()*100);
    let selectedUser = "";

    socket.emit('join', {name: myName});

    function switchMainTab(tab) {
        document.getElementById('chat-view').style.display = (tab === 'chat') ? 'flex' : 'none';
        document.getElementById('friends-view').style.display = (tab === 'friends') ? 'block' : 'none';
        document.getElementById('nav-chat-btn').classList.toggle('active', tab === 'chat');
        document.getElementById('nav-friends-btn').classList.toggle('active', tab === 'friends');
        if(tab === 'friends') socket.emit('request_social_data');
    }

    function openProfile(name) {
        if(name === myName) return;
        selectedUser = name;
        document.getElementById('modal-name').innerText = name;
        document.getElementById('modal').style.display = 'block';
        document.getElementById('overlay').style.display = 'block';
    }

    function closeModal() {
        document.getElementById('modal').style.display = 'none';
        document.getElementById('overlay').style.display = 'none';
    }

    function sendFA() {
        socket.emit('send_fa', {target: selectedUser});
        closeModal();
        alert("Anfrage gesendet!");
    }

    socket.on('update_users', (data) => {
        const list = document.getElementById('user-list');
        list.innerHTML = "";
        data.users.forEach(u => {
            const div = document.createElement('div');
            div.className = 'user-item';
            div.innerHTML = `<div class="avatar"></div><span>${u}</span>`;
            div.onclick = () => openProfile(u);
            list.appendChild(div);
        });
    });

    socket.on('new_msg', (data) => {
        const win = document.getElementById('chat-window');
        win.innerHTML += `<div class="message"><div class="avatar"></div><div><span class="msg-user">${data.author}</span><div class="msg-text">${data.content}</div></div></div>`;
        win.scrollTop = win.scrollHeight;
    });

    socket.on('social_data', (data) => {
        const faList = document.getElementById('fa-list');
        faList.innerHTML = data.pending.length ? "" : "<p style='color:gray'>Keine Anfragen</p>";
        data.pending.forEach(sender => {
            faList.innerHTML += `<div class="fa-card"><span>Anfrage von <b>${sender}</b></span><button class="accept-btn" onclick="socket.emit('accept_fa', {name:'${sender}'})">Annehmen</button></div>`;
        });

        const frList = document.getElementById('friends-list');
        frList.innerHTML = data.friends.length ? "" : "<p style='color:gray'>Noch keine Freunde</p>";
        data.friends.forEach(f => {
            frList.innerHTML += `<div class="user-item"><div class="avatar"></div><span>${f}</span></div>`;
        });
    });

    document.getElementById('msg-input').onkeypress = (e) => {
        if(e.key === 'Enter' && e.target.value) {
            socket.emit('message', {msg: e.target.value});
            e.target.value = "";
        }
    };
</script>
</body>
</html>
"""

# --- SERVER LOGIK ---

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@socketio.on('join')
def on_join(data):
    name = data.get('name', 'Gast')
    users[request.sid] = name
    if name not in friends: friends[name] = []
    if name not in pending_fas: pending_fas[name] = []
    emit('update_users', {'users': list(users.values())}, broadcast=True)

@socketio.on('send_fa')
def on_fa(data):
    sender = users[request.sid]
    target = data['target']
    if sender != target:
        if sender not in pending_fas.get(target, []):
            pending_fas.setdefault(target, []).append(sender)

@socketio.on('request_social_data')
def on_social():
    me = users[request.sid]
    emit('social_data', {
        'friends': friends.get(me, []),
        'pending': pending_fas.get(me, [])
    })

@socketio.on('accept_fa')
def on_accept(data):
    me = users[request.sid]
    new_friend = data['name']
    if new_friend in pending_fas[me]:
        friends.setdefault(me, []).append(new_friend)
        friends.setdefault(new_friend, []).append(me)
        pending_fas[me].remove(new_friend)
    on_social()

@socketio.on('message')
def on_msg(data):
    sender = users[request.sid]
    emit('new_msg', {'author': sender, 'content': data['msg']}, broadcast=True)

@socketio.on('disconnect')
def on_disc():
    if request.sid in users:
        users.pop(request.sid)
        emit('update_users', {'users': list(users.values())}, broadcast=True)

if __name__ == '__main__':
    # Startet den Server
    socketio.run(app, host='127.0.0.1', port=5000, debug=True)