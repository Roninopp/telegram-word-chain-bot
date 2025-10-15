import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import random

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Game states
games = {}
user_scores = {}

class WordChainGame:
    def __init__(self):
        self.current_word = None
        self.required_length = 3
        self.players = []
        self.current_player_index = 0
        self.used_words = set()
    
    def start_game(self, first_word=None):
        if first_word:
            self.current_word = first_word.lower()
            self.required_length = len(first_word)
            self.used_words.add(first_word.lower())
        else:
            # Start with random 3-letter word
            self.current_word = random.choice(['cat', 'dog', 'sun', 'car', 'box'])
            self.required_length = 3
            self.used_words.add(self.current_word)
        
        return self.get_game_status()
    
    def next_turn(self, word):
        word = word.lower().strip()
        
        # Validate word
        if not word.isalpha():
            return False, "Please enter only letters!"
        
        if word in self.used_words:
            return False, "Word already used!"
        
        if len(word) != self.required_length:
            return False, f"Word must be {self.required_length} letters!"
        
        if not word.startswith(self.current_word[-1]):
            return False, f"Word must start with '{self.current_word[-1].upper()}'!"
        
        # Valid move
        self.used_words.add(word)
        self.current_word = word
        self.required_length = 3 if self.required_length == 4 else 4  # Alternate between 3 and 4
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        
        return True, self.get_game_status()
    
    def get_game_status(self):
        current_player = self.players[self.current_player_index] if self.players else "Someone"
        return (
            f"🎮 **Word Chain Game**\n\n"
            f"Current word: `{self.current_word.upper()}`\n"
            f"Next word: {self.required_length} letters starting with `{self.current_word[-1].upper()}`\n"
            f"Next player: {current_player}\n"
            f"Used words: {len(self.used_words)}"
        )
    
    def add_player(self, user_id, username):
        player = f"@{username}" if username else f"User_{user_id}"
        if player not in self.players:
            self.players.append(player)

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when command /start is issued."""
    user = update.effective_user
    await update.message.reply_text(
        f"Hi {user.first_name}! 👋\n\n"
        "I host games of word chain in Telegram groups!\n"
        "Add me to a group to start playing word chain games!\n\n"
        "**How to play:**\n"
        "• Use /newgame to start a word chain\n"
        "• Players take turns saying words\n"
        "• Each word must start with the last letter of previous word\n"
        "• Words alternate between 3 and 4 letters\n\n"
        "Add me to your group and type /newgame to start! 🎮"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message."""
    await update.message.reply_text(
        "**Word Chain Bot Help**\n\n"
        "Commands:\n"
        "/start - Welcome message\n"
        "/newgame - Start new word chain game\n"
        "/endgame - End current game\n"
        "/score - Show player scores\n\n"
        "Game Rules:\n"
        "• Words must be valid English words\n"
        "• Alternate between 3 and 4 letters\n"
        "• No repeating words\n"
        "• Must start with last letter of previous word"
    )

async def new_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start a new word chain game."""
    chat_id = update.effective_chat.id
    
    if chat_id in games:
        await update.message.reply_text("A game is already running! Use /endgame to stop it.")
        return
    
    games[chat_id] = WordChainGame()
    game = games[chat_id]
    
    # Add the user who started the game
    user = update.effective_user
    game.add_player(user.id, user.username)
    
    status = game.start_game()
    
    await update.message.reply_text(
        f"🎯 **New Word Chain Game Started!**\n\n"
        f"{status}\n\n"
        "Type a word to play! The game alternates between 3 and 4 letter words."
    )

async def end_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """End the current game."""
    chat_id = update.effective_chat.id
    
    if chat_id not in games:
        await update.message.reply_text("No game is currently running!")
        return
    
    game = games[chat_id]
    await update.message.reply_text(
        f"🏁 **Game Ended!**\n\n"
        f"Final word: `{game.current_word.upper()}`\n"
        f"Total words: {len(game.used_words)}\n"
        f"Players: {', '.join(game.players)}"
    )
    
    del games[chat_id]

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular messages as potential word moves."""
    chat_id = update.effective_chat.id
    
    if chat_id not in games:
        return
    
    game = games[chat_id]
    user = update.effective_user
    message_text = update.message.text.strip()
    
    # Add player if not already in game
    game.add_player(user.id, user.username)
    
    # Check if it's user's turn
    current_player = game.players[game.current_player_index]
    user_identifier = f"@{user.username}" if user.username else f"User_{user.id}"
    
    if current_player != user_identifier:
        await update.message.reply_text(f"Wait for your turn! It's {current_player}'s turn.")
        return
    
    # Process the word
    success, result = game.next_turn(message_text)
    
    if success:
        await update.message.reply_text(result)
    else:
        await update.message.reply_text(f"❌ Invalid word! {result}")

async def show_score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show player scores."""
    chat_id = update.effective_chat.id
    
    if chat_id not in games or not games[chat_id].players:
        await update.message.reply_text("No active game or players!")
        return
    
    game = games[chat_id]
    score_text = "**Player Scores:**\n" + "\n".join(game.players)
    await update.message.reply_text(score_text)

def main():
    """Start the bot."""
    # Get token from environment variable
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not TOKEN:
        logger.error("Please set TELEGRAM_BOT_TOKEN environment variable")
        return
    
    # Create application
    application = Application.builder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("newgame", new_game))
    application.add_handler(CommandHandler("endgame", end_game))
    application.add_handler(CommandHandler("score", show_score))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the Bot
    port = int(os.environ.get('PORT', 8443))
    
    if "KOYEB" in os.environ:
        # Running on Koyeb - use webhook
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=TOKEN,
            webhook_url=f"https://{os.environ.get('KOYEB_APP_NAME', 'your-app')}.koyeb.app/{TOKEN}"
        )
    else:
        # Running locally - use polling
        application.run_polling()

if __name__ == '__main__':
    main()
