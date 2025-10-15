import os
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
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

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        'Welcome to Word Chain Game! 🎮\n\n'
        'Commands:\n'
        '/join - Join the game\n'
        '/startgame - Start the game\n'
        '/rules - Show game rules\n'
        '/status - Show current game status'
    )

def join(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    player_name = update.effective_user.first_name
    
    if chat_id not in games:
        games[chat_id] = WordChainGame()
    
    game = games[chat_id]
    
    if game.started:
        update.message.reply_text("Game has already started! Wait for the next round.")
        return
    
    if game.add_player(player_name):
        update.message.reply_text(f"✅ {player_name} joined the game! Players: {', '.join(game.players)}")
    else:
        update.message.reply_text(f"⚠️ {player_name}, you're already in the game!")

def start_game(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    
    if chat_id not in games or len(games[chat_id].players) < 2:
        update.message.reply_text("Need at least 2 players to start! Use /join to join.")
        return
    
    game = games[chat_id]
    game.start_game()
    
    update.message.reply_text(
        f"🎮 Game Started! 🎮\n\n"
        f"Players: {', '.join(game.players)}\n"
        f"First word can be anything!\n"
        f"First player: {game.players[0]}\n\n"
        f"Type a word to begin!"
    )

def handle_message(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    player_name = update.effective_user.first_name
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

def show_rules(update: Update, context: CallbackContext):
    rules = """
📖 WORD CHAIN GAME RULES:

1. Players take turns saying words
2. Each new word must start with the last letter of the previous word
3. Words must be at least 2 letters long
4. No repeating words
5. If a player can't think of a word, they're out!

Example: apple → elephant → tiger → rabbit
    """
    update.message.reply_text(rules)

def show_status(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    
    if chat_id not in games:
        update.message.reply_text("No active game in this chat. Use /join to start!")
        return
    
    game = games[chat_id]
    
    if not game.started:
        status = f"🕐 Game not started\nPlayers: {', '.join(game.players)}\nUse /startgame to begin!"
    else:
        status = (
            f"🎮 Game in Progress!\n"
            f"Players: {', '.join(game.players)}\n"
            f"Current turn: {game.players[game.current_player]}\n"
            f"Last letter: {game.last_letter if game.last_letter else 'Any'}\n"
            f"Words used: {len(game.used_words)}"
        )
    
    update.message.reply_text(status)

def main():
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not TOKEN:
        logger.error("Please set TELEGRAM_BOT_TOKEN environment variable")
        return
    
    # Use Updater instead of Application for older versions
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher
    
    # Add handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("join", join))
    dispatcher.add_handler(CommandHandler("startgame", start_game))
    dispatcher.add_handler(CommandHandler("rules", show_rules))
    dispatcher.add_handler(CommandHandler("status", show_status))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    logger.info("Bot is starting...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
