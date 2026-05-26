import discord
from discord.ext import commands
import random
import json
import os

# ==================== CONFIGURATION ====================
TOKEN = ''  # Ersetze dies mit deinem echten Bot-Token
SLOTS_CHANNEL_ID_STR = "1506695102897066144"  # Deine Channel-ID
GOD_USER_ID = 1304491059853656165  # Diese ID hat unendlich Coins
START_COINS = 10
DATA_FILE = "bank.json"

# Die Liste der Emojis
SLOT_EMOJIS = ["🍒", "🍋", "🍇", "🍊", "💎", "7️⃣"]

# NUR diese Emojis geben noch einen Teilgewinn, wenn 2 davon nebeneinander/im Slot sind!
LUCKY_PAIRS = ["💎", "7️⃣"]
# =======================================================

try:
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix="!", intents=intents)

    user_bank = {}
    user_bets = {}

    # --- Daten-Verwaltung ---
    def load_data():
        global user_bank
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    data = json.load(f)
                    user_bank = {int(k): v for k, v in data.items()}
                print("💾 Kontostände geladen.")
            except Exception as e:
                print(f"❌ Fehler beim Laden: {e}")
        else:
            user_bank = {}

    def save_data():
        try:
            with open(DATA_FILE, "w") as f:
                json.dump(user_bank, f, indent=4)
        except Exception as e:
            print(f"❌ Fehler beim Speichern: {e}")

    def get_balance(user_id):
        if user_id == GOD_USER_ID:
            return 999999999
            
        if user_id not in user_bank:
            user_bank[user_id] = START_COINS
            save_data()
        return user_bank[user_id]

    def get_balance_label(user_id):
        if user_id == GOD_USER_ID:
            return "∞ Unendlich"
        return f"{get_balance(user_id)} Coins"

    def get_bet(user_id):
        if user_id not in user_bets:
            user_bets[user_id] = 1
        return user_bets[user_id]


    # --- Die GUI / Buttons für Discord ---
    class SlotsGUI(discord.ui.View):
        def __init__(self, player_id):
            super().__init__(timeout=None)
            self.player_id = player_id

        async def update_message(self, interaction: discord.Interaction, status_text="Wähle deinen Einsatz und drehe!"):
            balance_text = get_balance_label(self.player_id)
            bet = get_bet(self.player_id)
            
            embed = discord.Embed(title="🎰 MINI SLOTS GAME", color=0x9b59b6)
            embed.add_field(name="🪙 Dein Guthaben", value=f"**{balance_text}**", inline=True)
            embed.add_field(name="💵 Aktueller Einsatz", value=f"**{bet} Coin(s)**", inline=True)
            embed.add_field(name="Spielstatus", value=status_text, inline=False)
            
            await interaction.response.edit_message(embed=embed, view=self)

        @discord.ui.button(label="➖ Einsatz runter", style=discord.ButtonStyle.danger, row=0)
        async def minus_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.player_id:
                await interaction.response.send_message("❌ Das ist nicht dein Spiel!", ephemeral=True)
                return
            
            current_bet = get_bet(self.player_id)
            if current_bet > 1:
                user_bets[self.player_id] -= 1
                await self.update_message(interaction, "Einsatz verringert.")
            else:
                await interaction.response.send_message("❌ Minimaler Einsatz ist 1 Coin!", ephemeral=True)

        @discord.ui.button(label="➕ Einsatz hoch", style=discord.ButtonStyle.success, row=0)
        async def plus_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.player_id:
                await interaction.response.send_message("❌ Das ist nicht dein Spiel!", ephemeral=True)
                return
            
            current_bet = get_bet(self.player_id)
            balance = get_balance(self.player_id)
            
            if current_bet < balance:
                user_bets[self.player_id] += 1
                await self.update_message(interaction, "Einsatz erhöht.")
            else:
                await interaction.response.send_message("❌ Du kannst nicht mehr setzen, als du besitzt!", ephemeral=True)

        @discord.ui.button(label="🎰 SPIN! 🎰", style=discord.ButtonStyle.primary, row=1)
        async def spin_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.player_id:
                await interaction.response.send_message("❌ Das ist nicht dein Spiel!", ephemeral=True)
                return

            balance = get_balance(self.player_id)
            bet = get_bet(self.player_id)

            if balance <= 0 and self.player_id != GOD_USER_ID:
                user_bank[self.player_id] = START_COINS
                user_bets[self.player_id] = 1
                save_data()
                await self.update_message(interaction, "❌ Du warst pleite! Deine Coins wurden auf 10 zurückgesetzt.")
                return

            if balance < bet:
                user_bets[self.player_id] = balance
                bet = balance

            if self.player_id != GOD_USER_ID:
                user_bank[self.player_id] -= bet

            # Walzen drehen
            w1 = random.choice(SLOT_EMOJIS)
            w2 = random.choice(SLOT_EMOJIS)
            w3 = random.choice(SLOT_EMOJIS)
            
            walzen_display = f"┃ {w1} ┃ {w2} ┃ {w3} ┃"

            # --- NEUE GEWINNLOGIK (SELTENER) ---
            # 1. Hauptgewinn: Alle 3 absolut identisch
            if w1 == w2 == w3:
                gewinn = bet * 7  # Jackpot-Multiplikator leicht erhöht (von 5 auf 7), da es seltener ist!
                if self.player_id != GOD_USER_ID:
                    user_bank[self.player_id] += gewinn
                status = f"```\n{walzen_display}\n```\n🎉 **JACKPOT!** Alle drei passen! Du gewinnst **{gewinn} Coins**!"
            
            # 2. Teilgewinn: 2 gleiche Symbole, ABER nur wenn es Diamanten oder Siebener sind
            elif (w1 == w2 or w1 == w3) and w1 in LUCKY_PAIRS:
                gewinn = bet * 2
                if self.player_id != GOD_USER_ID:
                    user_bank[self.player_id] += gewinn
                status = f"```\n{walzen_display}\n```\n💵 **Teilgewinn!** Ein Paar Edel-Symbole ({w1})! Du erhältst **{gewinn} Coins**."
            elif (w2 == w3) and w2 in LUCKY_PAIRS:
                gewinn = bet * 2
                if self.player_id != GOD_USER_ID:
                    user_bank[self.player_id] += gewinn
                status = f"```\n{walzen_display}\n```\n💵 **Teilgewinn!** Ein Paar Edel-Symbole ({w2})! Du erhältst **{gewinn} Coins**."
            
            # 3. Niete
            else:
                status = f"```\n{walzen_display}\n```\n😭 **Kein Treffer.** Versuche es noch einmal!"

            if self.player_id != GOD_USER_ID:
                save_data()
            
            new_balance = get_balance(self.player_id)
            if user_bets[self.player_id] > new_balance and new_balance > 0:
                user_bets[self.player_id] = new_balance

            await self.update_message(interaction, status)


    # --- Bot Commands ---
    @bot.event
    async def on_ready():
        load_data()
        print(f'🤖 Bot ist online als {bot.user.name}!')
        print(f'🔒 Erlaubter Channel: {SLOTS_CHANNEL_ID_STR}')

    @bot.command()
    async def slots(ctx):
        if str(ctx.channel.id) != SLOTS_CHANNEL_ID_STR:
            return

        player_id = ctx.author.id
        balance_text = get_balance_label(player_id)
        bet = get_bet(player_id)

        embed = discord.Embed(title="🎰 MINI SLOTS GAME", color=0x9b59b6)
        embed.add_field(name="🪙 Dein Guthaben", value=f"**{balance_text}**", inline=True)
        embed.add_field(name="💵 Aktueller Einsatz", value=f"**{bet} Coin(s)**", inline=True)
        embed.add_field(name="Spielstatus", value="Wähle deinen Einsatz und drehe!", inline=False)

        view = SlotsGUI(player_id=player_id)
        await ctx.send(embed=embed, view=view)

    @bot.command()
    async def give(ctx, ziel_user: discord.Member = None, anzahl: int = None):
        if str(ctx.channel.id) != SLOTS_CHANNEL_ID_STR:
            return

        if ziel_user is None or anzahl is None:
            await ctx.send("❌ falsches Format! Nutzung: `!give @User Anzahl` (z.B. `!give @Benko 5`)")
            return

        if ziel_user.id == ctx.author.id:
            await ctx.send("❌ Du kannst dir nicht selbst Coins geben!")
            return

        if anzahl <= 0:
            await ctx.send("❌ Du musst mindestens 1 Coin vergeben!")
            return

        absender_id = ctx.author.id
        empfaenger_id = ziel_user.id

        if absender_id != GOD_USER_ID:
            aktuelles_guthaben = get_balance(absender_id)
            if aktuelles_guthaben < anzahl:
                await ctx.send(f"❌ Du hast nicht genug Coins! Dein Kontostand: {aktuelles_guthaben} Coins.")
                return
            user_bank[absender_id] -= anzahl
        
        get_balance(empfaenger_id)
        if empfaenger_id != GOD_USER_ID:
            user_bank[empfaenger_id] += anzahl

        save_data()

        guthaben_sender_text = get_balance_label(absender_id)
        guthaben_empfaenger_text = get_balance_label(empfaenger_id)

        embed = discord.Embed(title="💸 COIN-ÜBERWEISUNG", color=0x2ecc71)
        embed.description = f"**{ctx.author.name}** hat **{anzahl} Coin(s)** an **{ziel_user.name}** überwiesen!"
        embed.add_field(name=f"🪙 {ctx.author.name}", value=f"Neu: {guthaben_sender_text}")
        embed.add_field(name=f"🪙 {ziel_user.name}", value=f"Neu: {guthaben_empfaenger_text}")
        
        await ctx.send(embed=embed)

    bot.run(TOKEN)

except Exception as e:
    print(f"\n❌ BERATER-INFO: Das Skript ist abgestürzt!\nFehlermeldung: {e}\n")
    input("Drücke ENTER, um das Fenster zu schließen...")