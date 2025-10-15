import os
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Game state
games = {}

class WordChainGame:
    def __init__(self):
        self.players = []
        self.used_words = set()
        self.current_player = 0
        self.last_letter = None
        self.started = False

    def add_player(self, player_name):
        if player_name not in self.players:
            self.players.append(player_name)
            return True
        return False

    def start_game(self):
        self.started = True
        self.used_words.clear()
        self.current_player = 0
        self.last_letter = None

    def play_word(self, word):
        word = word.lower().strip()
        
        if len(word) < 2:
            return False, "Word must be at least 2 letters long!"
        
        if word in self.used_words:
            return False, f"'{word}' has already been used!"
        
        if self.last_letter and not word.startswith(self.last_letter):
            return False, f"Word must start with '{self.last_letter}'!"
        
        self.used_words.add(word)
        self.last_letter = word[-1] if word[-1] not in ['a', 'e', 'i', 'o', 'u'] else word[-2]
        self.current_player = (self.current_player + 1) % len(self.players)
        
        return True, f"✅ Valid word! Next player: {self.players[self.current_player]}"

def start(update, context):
    update.message.reply_text('Welcome to Word Chain Game! 🎮\n\nCommands:\n/join - Join game\n/startgame - Start game\n/rules - Show rules\n/status - Show status')

def join(update, context):
    chat_id = update.message.chat_id
    player_name = update.message.from_user.first_name
    
    if chat_id not in games:
        games[chat_id] = WordChainGame()
    
    game = games[chat_id]
    
    if game.started:
        update.message.reply_text("Game already started! Wait for next round.")
        return
    
    if game.add_player(player_name):
        update.message.reply_text(f"✅ {player_name} joined! Players: {', '.join(game.players)}")
    else:
        update.message.reply_text(f"⚠️ {player_name}, you're already in!")

def start_game(update, context):
    chat_id = update.message.chat_id
    
    if chat_id not in games or len(games[chat_id].players) < 2:
        update.message.reply_text("Need at least 2 players! Use /join")
        return
    
    game = games[chat_id]
    game.start_game()
    update.message.reply_text(f"🎮 Game Started!\nPlayers: {', '.join(game.players)}\nFirst player: {game.players[0]}\nType a word to begin!")

def handle_message(update, context):
    chat_id = update.message.chat_id
    player_name = update.message.from_user.first_name
    word = update.message.text
    
    if word.startswith('/'):
        return
    
    if chat_id not in games or not games[chat_id].started:
        return
    
    game = games[chat_id]
    
    if player_name != game.players[game.current_player]:
        update.message.reply_text(f"⚠️ It's {game.players[game.current_player]}'s turn!")
        return
    
    success, message = game.play_word(word)
    update.message.reply_text(message)

def show_rules(update, context):
    rules = "📖 RULES:\n1. Take turns saying words\n2. New word starts with last letter of previous word\n3. Minimum 2 letters\n4. No repeating words\nExample: apple → elephant → tiger"
    update.message.reply_text(rules)

def show_status(update, context):
    chat_id = update.message.chat_id
    
    if chat_id not in games:
        update.message.reply_text("No active game. Use /join")
        return
    
    game = games[chat_id]
    
    if not game.started:
        status = f"🕐 Game not started\nPlayers: {', '.join(game.players)}\nUse /startgame"
    else:
        status = f"🎮 Game running!\nPlayers: {', '.join(game.players)}\nCurrent: {game.players[game.current_player]}\nLast letter: {game.last_letter if game.last_letter else 'Any'}"
    
    update.message.reply_text(status)

def main():
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not TOKEN:
        logger.error("Please set TELEGRAM_BOT_TOKEN environment variable")
        return
    
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("join", join))
    dp.add_handler(CommandHandler("startgame", start_game))
    dp.add_handler(CommandHandler("rules", show_rules))
    dp.add_handler(CommandHandler("status", show_status))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    logger.info("Bot starting...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
