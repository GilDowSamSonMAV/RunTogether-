# Study Bot - Telegram Bot for Students

A Telegram bot that helps students study by:
- 📚 Generating AI summaries of PDF lectures
- 💻 Creating coding challenges from code files

## Setup

1. Create a `.env` file with your credentials:
```
TELEGRAM_TOKEN=your_bot_token
GROQ_API_KEY=your_groq_key
ADMIN_ID=your_telegram_id
FRIEND_ID=friends_telegram_id
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run:
```bash
python study_bot.py
```

## Deploy to Railway

1. Push to GitHub
2. Connect Railway to your repo
3. Add environment variables in Railway dashboard
4. Deploy!
