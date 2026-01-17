# 📚 Study Bot - Complete Setup Guide

A Telegram bot that helps students study by generating AI summaries of lectures and coding challenges, with a **RAG-powered knowledge base** for answering questions.

---

## 🎯 What Does This Bot Do?

| Feature | Description |
|---------|-------------|
| 📄 **PDF Summaries** | Upload a lecture PDF → Get AI-generated summary with key concepts |
| 💻 **Code Challenges** | Upload code file → Get a coding challenge + solution |
| 🧠 **RAG Knowledge Base** | All uploads are indexed → Student can ask questions about any lecture |

---

## 🧠 What is RAG?

**RAG (Retrieval Augmented Generation)** makes the bot smarter by remembering all uploaded content:

1. **Indexing**: When you upload a PDF, it's split into chunks and stored as vectors
2. **Semantic Search**: When the student asks a question, the bot finds relevant chunks
3. **Context-Aware Answers**: The AI answers using the actual lecture content

**Example:**
- Admin uploads 5 lecture PDFs about Data Structures
- Student asks: "How does a binary search tree work?"
- Bot searches all lectures → Finds relevant sections → Gives answer based on the lectures

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Get Your API Keys

| Service | Where to Get | Purpose |
|---------|--------------|---------|
| **Telegram Bot** | [@BotFather](https://t.me/BotFather) | Bot token |
| **Groq API** | [console.groq.com](https://console.groq.com) | AI (free!) |
| **User IDs** | [@userinfobot](https://t.me/userinfobot) | Admin & Student IDs |

### Step 2: Configure

```bash
cp .env.example .env
# Edit .env with your values
```

### Step 3: Run Locally

```bash
pip install -r requirements.txt
python study_bot.py
```

### Step 4: Friend Must Start Bot

Your friend needs to message the bot and press **Start** before receiving materials.

---

## ☁️ Deploy to Railway (Run 24/7)

### Basic Deployment

1. Push to GitHub
2. Go to [railway.app](https://railway.app) → Sign in with GitHub
3. **New Project** → **Deploy from GitHub**
4. Add environment variables in **Variables** tab

### Enable RAG Knowledge Base

1. In Railway, click **"+ New"** → **"Database"** → **"PostgreSQL"**
2. Railway automatically adds `DATABASE_URL`
3. Redeploy - the bot will create tables automatically!

---

## 💬 How to Use RAG (For Students)

Once RAG is enabled, the student can **ask questions directly** to the bot:

```
Student: "What is the time complexity of quicksort?"
Bot: 📖 Based on your lectures: "Quicksort has an average time complexity of O(n log n)..."
```

The bot searches through all uploaded lecture materials and provides answers with context!

---

## 🔧 RAG Optimization Tips

| Optimization | Description |
|--------------|-------------|
| **Chunk Size** | Default 500 chars works well for lectures |
| **Overlap** | 50 char overlap prevents cutting concepts in half |
| **Top-K** | Returns 3 most relevant chunks (configurable) |
| **Embedding Model** | Uses `bge-small-en-v1.5` (384 dims, fast on CPU) |

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
| "Conflict: terminated by other getUpdates" | Stop local bot - Railway is running it |
| "Knowledge base not available" | Add PostgreSQL database in Railway |
| "API key not set" | Check Railway environment variables |

---

## 📜 License

MIT - Feel free to use and modify!
