import sqlite3
import os
from fastapi import FastAPI, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from itsdangerous import TimestampSigner
from passlib.context import CryptContext

app = FastAPI()
SECRET_KEY = "super_geheim_123"
signer = TimestampSigner(SECRET_KEY)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# WICHTIG: Erstellt die Tabelle, falls sie fehlt
def init_db():
    conn = sqlite3.connect("users.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            username TEXT UNIQUE, 
            password TEXT, 
            own_stream TEXT DEFAULT '',
            following TEXT DEFAULT ''
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_user_data(request: Request):
    session = request.cookies.get("session")
    if not session: return None
    try:
        uname = signer.unsign(session, max_age=3600).decode()
        conn = sqlite3.connect("users.db")
        conn.row_factory = sqlite3.Row
        user = conn.execute("SELECT * FROM users WHERE username = ?", (uname,)).fetchone()
        conn.close()
        return user
    except: return None

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    user = get_user_data(request)
    sidebar_html = ""
    if user and user["following"]:
        for f in user["following"].split(","):
            if f: sidebar_html += f'<div class="side-item" onclick="openStream(\'{f}\')">🟣 {f}</div>'

    return f"""
    <html>
        <head>
            <style>
                body {{ background: #0e0e10; color: white; font-family: sans-serif; margin: 0; display: flex; flex-direction: column; height: 100vh; }}
                nav {{ background: #18181b; padding: 10px 20px; display: flex; justify-content: space-between; border-bottom: 1px solid #333; }}
                .main-layout {{ display: flex; flex: 1; overflow: hidden; }}
                .sidebar {{ width: 200px; background: #1f1f23; border-right: 1px solid #333; }}
                .content {{ flex: 1; padding: 20px; }}
                .btn {{ background: #9146ff; border: none; color: white; padding: 8px 15px; border-radius: 4px; cursor: pointer; }}
                .side-item {{ padding: 10px; cursor: pointer; }}
                .side-item:hover {{ background: #26262c; }}
                .modal {{ display:none; position:fixed; top:50%; left:50%; transform:translate(-50%,-50%); background:#18181b; padding:30px; border:1px solid #9146ff; z-index:100; }}
            </style>
        </head>
        <body>
            <nav>
                <b onclick="location.href='/'" style="cursor:pointer; color:#9146ff;">PYTHON-TWITCH</b>
                <div>
                    {f'<span>{user["username"]}</span> <button class="btn" onclick="toggleModal(\'settings-modal\')">⚙️</button> <a href="/logout" style="color:grey; margin-left:10px;">Logout</a>' if user else '<button class="btn" onclick="toggleModal(\'reg-modal\')">Login</button>'}
                </div>
            </nav>
            <div class="main-layout">
                <div class="sidebar">{sidebar_html}</div>
                <div class="content" id="main-view">
                    <h2>Entdecken</h2>
                    <button class="btn" onclick="openStream('montanablack')">MontanaBlack</button>
                    <button class="btn" onclick="openStream('papaplatte')">Papaplatte</button>
                </div>
                <div id="chat-view" style="width:250px; background:#18181b; border-left:1px solid #333; display:none; flex-direction:column;">
                    <div id="chat-box" style="flex:1; padding:10px;"></div>
                    <input type="text" placeholder="Chatten..." onkeypress="sendMsg(event)" style="margin:10px; background:#000; color:#fff; border:1px solid #333; padding:5px;">
                </div>
            </div>

            <div id="reg-modal" class="modal">
                <form action="/auth" method="post">
                    <input type="text" name="username" placeholder="Nutzername" required><br><br>
                    <input type="password" name="password" placeholder="Passwort" required><br><br>
                    <button type="submit" class="btn">Login / Register</button>
                </form>
            </div>

            <script>
                const isLoggedIn = {"true" if user else "false"};
                function openStream(chan) {{
                    document.getElementById('main-view').innerHTML = `
                        <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                            <h3>${{chan}}</h3>
                            <button class="btn" onclick="followChan('${{chan}}')">💜 Folgen</button>
                        </div>
                        <iframe src="https://player.twitch.tv/?channel=${{chan}}&parent=localhost&parent=127.0.0.1" height="80%" width="100%" allowfullscreen></iframe>
                    `;
                    document.getElementById('chat-view').style.display = "flex";
                }}
                function sendMsg(e) {{
                    if(e.key === 'Enter') {{
                        if(!isLoggedIn) {{ alert("Logge dich ein!"); return; }}
                        document.getElementById('chat-box').innerHTML += `<p><b>Du:</b> ${{e.target.value}}</p>`;
                        e.target.value = "";
                    }}
                }}
                function followChan(chan) {{
                    if(!isLoggedIn) {{ alert("Logge dich ein!"); return; }}
                    window.location.href = "/follow?name=" + chan;
                }}
                function toggleModal(id) {{ 
                    const m = document.getElementById(id);
                    m.style.display = m.style.display === 'block' ? 'none' : 'block';
                }}
            </script>
        </body>
    </html>
    """

@app.post("/auth")
async def auth(username: str = Form(...), password: str = Form(...)):
    safe_pw = password[:71]
    conn = sqlite3.connect("users.db")
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    
    if user:
        try:
            if not pwd_context.verify(safe_pw, user[2]):
                return HTMLResponse("Falsches Passwort!")
        except: return HTMLResponse("Datenbank-Fehler. Bitte users.db löschen.")
    else:
        hash_pw = pwd_context.hash(safe_pw)
        conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hash_pw))
        conn.commit()
    
    conn.close()
    token = signer.sign(username.encode()).decode()
    resp = RedirectResponse(url="/", status_code=303)
    resp.set_cookie(key="session", value=token, httponly=True)
    return resp

@app.get("/follow")
async def follow(request: Request, name: str):
    user = get_user_data(request)
    if user:
        current = user["following"].split(",") if user["following"] else []
        if name not in current:
            current.append(name)
            conn = sqlite3.connect("users.db")
            conn.execute("UPDATE users SET following = ? WHERE id = ?", (",".join(current), user["id"]))
            conn.commit()
            conn.close()
    return RedirectResponse(url="/")

@app.get("/logout")
async def logout():
    resp = RedirectResponse(url="/")
    resp.delete_cookie("session")
    return resp

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)