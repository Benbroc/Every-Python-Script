import customtkinter as ctk
import threading
import time
import pyperclip
from groq import Groq

# ==========================================
# KONFIGURATION
# ==========================================
GROQ_API_KEY = "YOUR KEY"  # <--- HIER DEINEN KEY EINTRAGEN
client = Groq(api_key=GROQ_API_KEY)

MODELS = {
    "Llama 3.3": "llama-3.3-70b-versatile",
    "Llama 3.1": "llama-3.1-8b-instant",
}

class SteamAIApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Llama 3 Versions")
        self.geometry("1100x850")
        self.configure(fg_color="#171a21") 

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Chat-Bereich
        self.chat_canvas = ctk.CTkScrollableFrame(
            self, fg_color="#171a21", corner_radius=0,
            scrollbar_button_color="#3a3f47", scrollbar_button_hover_color="#66c0f4"
        )
        self.chat_canvas.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

        # Untere Leiste
        self.bottom_bar = ctk.CTkFrame(self, fg_color="#171a21", height=100, corner_radius=0)
        self.bottom_bar.grid(row=1, column=0, sticky="ew")

        # Eingabefeld (links)
        self.entry = ctk.CTkEntry(
            self.bottom_bar, placeholder_text="Nachricht schreiben...",
            fg_color="#212429", border_width=0, height=50, corner_radius=25
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(20, 10), pady=25)
        self.entry.bind("<Return>", lambda e: self.send_action())

        # KI Auswahl Dropdown (rechts)
        self.model_var = ctk.StringVar(value="Llama 3.3")
        self.model_menu = ctk.CTkOptionMenu(
            self.bottom_bar, values=list(MODELS.keys()), variable=self.model_var,
            fg_color="#3a3f47", button_color="#3a3f47", button_hover_color="#4e545e", 
            width=160, height=45, corner_radius=20
        )
        self.model_menu.pack(side="left", padx=10, pady=25)

        # Senden Button
        self.send_btn = ctk.CTkButton(
            self.bottom_bar, text="➤", width=65, height=50, corner_radius=25,
            fg_color="#3d4450", hover_color="#66c0f4", command=self.send_action
        )
        self.send_btn.pack(side="right", padx=(10, 20), pady=25)

    def copy_code(self, code_text, button):
        pyperclip.copy(code_text)
        button.configure(text="Kopiert!", fg_color="#4CAF50")
        self.after(2000, lambda: button.configure(text="Kopieren", fg_color="#3a3f47"))

    def add_bubble(self, sender, text, is_user=False):
        # Sicherer Split
        marker = chr(96)*3
        parts = text.split(marker)
        is_code = False

        for i, part in enumerate(parts):
            if i > 0: is_code = not is_code
            clean_part = part.strip()
            if not clean_part: continue

            container = ctk.CTkFrame(self.chat_canvas, fg_color="transparent")
            container.pack(anchor="w", padx=15, pady=8, fill="x")

            if is_code:
                # --- CODE BLOCK ---
                # Fix für den TclError: Wir nutzen einfaches Padding
                box = ctk.CTkFrame(container, fg_color="#121418", corner_radius=15, border_width=1, border_color="#333842")
                box.pack(anchor="w", padx=52, fill="x")
                
                h = ctk.CTkFrame(box, fg_color="transparent", height=30)
                h.pack(fill="x", padx=15, pady=5)
                
                cp = ctk.CTkButton(h, text="Kopieren", width=80, height=26, fg_color="#3a3f47", 
                                   corner_radius=12, command=lambda c=clean_part: self.copy_code(c, cp))
                cp.pack(side="right")

                # Hier war der Fehler: pady wurde falsch interpretiert. Jetzt gefixt.
                code_disp = ctk.CTkLabel(box, text=clean_part, font=("Consolas", 12), justify="left", 
                                        text_color="#A9B7C6")
                code_disp.pack(anchor="w", padx=20, pady=15)
            else:
                # --- TEXT BUBBLE ---
                header_frame = ctk.CTkFrame(container, fg_color="transparent")
                header_frame.pack(anchor="w", fill="x")

                # Avatar
                av_col = "#66c0f4" if is_user else "#3a3f47"
                av = ctk.CTkCanvas(header_frame, width=36, height=36, bg="#171a21", highlightthickness=0)
                av.pack(side="left", anchor="n", padx=(0, 15))
                av.create_oval(2, 2, 34, 34, fill=av_col, outline="")
                av.create_text(18, 18, text=sender[0].upper(), fill="white", font=("Arial", 12, "bold"))

                side = ctk.CTkFrame(header_frame, fg_color="transparent")
                side.pack(side="left", fill="both", expand=True)
                
                ctk.CTkLabel(side, text=f"{sender}  {time.strftime('%H:%M')}", 
                            font=("Arial", 12, "bold"), text_color="#66c0f4" if is_user else "#ebebeb").pack(anchor="w")

                bubble = ctk.CTkFrame(side, fg_color="#22252b" if is_user else "#2e3138", corner_radius=25)
                bubble.pack(anchor="w", pady=(4, 0))
                
                display_text = clean_part.replace("**", "").replace("*", "")
                msg_lbl = ctk.CTkLabel(bubble, text=display_text, wraplength=700, justify="left", 
                                      text_color="#d1d1d1", font=("Arial", 13))
                msg_lbl.pack(padx=20, pady=12)

        self.after(50, lambda: self.chat_canvas._parent_canvas.yview_moveto(1.0))

    def send_action(self):
        msg = self.entry.get().strip()
        if not msg: return
        self.entry.delete(0, 'end')
        self.add_bubble("User", msg, is_user=True)
        threading.Thread(target=self._query_groq, args=(msg,), daemon=True).start()

    def _query_groq(self, user_msg):
        indicator = []
        def show():
            f = ctk.CTkFrame(self.chat_canvas, fg_color="transparent")
            f.pack(anchor="w", padx=70, pady=5)
            ctk.CTkLabel(f, text="... schreibt", font=("Arial", 11, "italic"), text_color="#8f98a0").pack()
            indicator.append(f)
        self.after(0, show)

        try:
            res = client.chat.completions.create(
                messages=[{"role": "user", "content": user_msg}], 
                model=MODELS[self.model_var.get()]
            )
            ans = res.choices[0].message.content
            self.after(0, lambda: indicator[0].destroy() if indicator else None)
            self.after(0, lambda: self.add_bubble(self.model_var.get(), ans))
        except Exception as e:
            self.after(0, lambda: indicator[0].destroy() if indicator else None)
            self.after(0, lambda m=str(e): self.add_bubble("System", f"Fehler: {m}"))

if __name__ == "__main__":
    app = SteamAIApp()
    app.mainloop()