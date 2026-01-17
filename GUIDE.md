# 📚 Study Bot - Complete Setup Guide

A Telegram bot that helps students study by generating AI summaries of lectures and coding challenges.

---

## 🎯 What Does This Bot Do?

| You Upload | Your Friend Gets |
|------------|------------------|
| 📄 **PDF Lecture** | AI Summary + Original PDF |
| 💻 **Code File** | Coding Challenge + Solution File |

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Get Your API Keys

1. **Telegram Bot Token**
   - Open Telegram and message [@BotFather](https://t.me/BotFather)
   - Send `/newbot` and follow the prompts
   - Copy the token (looks like `123456789:ABCdef...`)

2. **Groq API Key** (FREE)
   - Go to [console.groq.com](https://console.groq.com)
   - Sign up and create an API key

3. **Telegram User IDs**
   - Message [@userinfobot](https://t.me/userinfobot) on Telegram
   - It will reply with your ID (a number like `409070322`)
   - Get your friend's ID the same way

---

### Step 2: Configure the Bot

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your values:
   ```
   TELEGRAM_TOKEN=your_bot_token_here
   GROQ_API_KEY=your_groq_key_here
   ADMIN_ID=your_telegram_id
   FRIEND_ID=friends_telegram_id
   ```

---

### Step 3: Install & Run

```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot
python study_bot.py
```

---

### Step 4: Your Friend Must Start the Bot

⚠️ **Important:** Before you can send materials to your friend, they MUST:
1. Open the bot in Telegram (search for your bot's name)
2. Press **Start** or send `/start`

---

## ☁️ Deploy to Cloud (Run 24/7)

### Using Railway (Recommended)

1. Push code to GitHub
2. Sign up at [railway.app](https://railway.app) with GitHub
3. Create new project → Deploy from GitHub
4. Add environment variables in Railway's **Variables** tab:
   - `TELEGRAM_TOKEN`
   - `GROQ_API_KEY`
   - `ADMIN_ID`
   - `FRIEND_ID`
5. Deploy!

---

## 📁 Supported File Types

| Type | Extensions |
|------|------------|
| PDF | `.pdf` |
| Python | `.py` |
| Java | `.java` |
| C/C++ | `.c`, `.cpp` |
| JavaScript | `.js`, `.ts` |
| Others | `.cs`, `.go`, `.rb`, `.php` |

---

## ❓ Troubleshooting

| Error | Solution |
|-------|----------|
| "Chat not found" | Friend needs to `/start` the bot first |
| "API key not set" | Check your `.env` file or Railway variables |
| "Model decommissioned" | Update the `MODEL` variable in `study_bot.py` |

---

## 📜 License

MIT - Feel free to use and modify!
