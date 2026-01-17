"""
Telegram Study Bot - Helps students study with AI-powered summaries and challenges.

Admin uploads PDF lectures or code files → Bot processes with Groq AI → 
Sends summaries/challenges to Student along with original files.

Now with RAG: Uploaded content is indexed for semantic search!
"""

import os
import io
import logging
from dotenv import load_dotenv
from groq import Groq
from PyPDF2 import PdfReader
from telegram import Update
from telegram.ext import (
    Application,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
)

# Load environment variables
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
FRIEND_ID = int(os.getenv("FRIEND_ID", "0"))

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configure Groq client
client = Groq(api_key=GROQ_API_KEY)
MODEL = "llama-3.3-70b-versatile"  # Current free model

# RAG availability flag
RAG_ENABLED = False

# Supported code file extensions
CODE_EXTENSIONS = {".py", ".java", ".c", ".cpp", ".js", ".ts", ".cs", ".go", ".rb", ".php"}

# ============================================================================
# AI PROMPTS
# ============================================================================

LECTURE_PROMPT = """You are a helpful study assistant. Analyze this lecture content and provide:

1. **📋 Executive Summary** - Exactly 3 bullet points capturing the main ideas
2. **🔑 Key Concepts** - Simple, clear explanations of important terms/concepts
3. **💻 Code Examples** - If any code is mentioned, highlight it with explanations
4. **❓ Kill Confirmation** - One multiple-choice question (A/B/C/D) to test understanding

Format your response clearly with the headers above. Be concise but thorough.

LECTURE CONTENT:
{content}
"""

CODE_CHALLENGE_PROMPT = """You are a coding instructor. Based on this code, create a learning challenge:

1. **🎯 Problem Description** - Describe what problem this code solves WITHOUT revealing the solution approach
2. **💡 Hints** - Provide exactly 2 helpful hints that guide without giving away the answer
3. **📝 Your Task** - Ask the student to write pseudo-code for solving this problem

Do NOT include the actual code or solution in your response. Make it educational and engaging.

CODE:
```
{content}
```
"""

RAG_QUESTION_PROMPT = """You are a helpful study assistant. Answer the student's question using the provided context from their lecture materials.

CONTEXT FROM LECTURES:
{context}

STUDENT'S QUESTION:
{question}

Provide a clear, helpful answer based on the lecture material. If the context doesn't contain enough information to answer, say so and provide what general knowledge you can.
"""

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def extract_pdf_text(file_bytes: bytes) -> str:
    """Extract text from PDF bytes using PyPDF2."""
    try:
        pdf_reader = PdfReader(io.BytesIO(file_bytes))
        text_parts = []
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        return "\n".join(text_parts)
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        raise ValueError(f"Could not extract text from PDF: {e}")


async def generate_ai_response(prompt: str) -> str:
    """Generate response using Groq API."""
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "user", "content": prompt}
            ],
            model=MODEL,
            temperature=0.7,
            max_tokens=2000,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        logger.error(f"Groq API error: {e}")
        raise ValueError(f"AI processing failed: {e}")


def get_file_extension(filename: str) -> str:
    """Get lowercase file extension."""
    return os.path.splitext(filename)[1].lower() if filename else ""


# ============================================================================
# HANDLERS
# ============================================================================

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Main handler for document uploads from Admin."""
    user_id = update.effective_user.id
    
    # Only process documents from Admin
    if user_id != ADMIN_ID:
        logger.info(f"Ignored document from non-admin user: {user_id}")
        return
    
    document = update.message.document
    file_name = document.file_name or "unknown"
    file_extension = get_file_extension(file_name)
    
    logger.info(f"Admin uploaded: {file_name} ({file_extension})")
    
    # Acknowledge receipt to Admin
    await update.message.reply_text(f"📥 Received: <b>{file_name}</b>\n⏳ Processing with AI...", parse_mode="HTML")
    
    try:
        if file_extension == ".pdf":
            await process_pdf(update, context, document, file_name)
        elif file_extension in CODE_EXTENSIONS:
            await process_code(update, context, document, file_name)
        else:
            await update.message.reply_text(
                f"⚠️ Unsupported file type: {file_extension}\n"
                f"Supported: PDF, {', '.join(CODE_EXTENSIONS)}"
            )
    except Exception as e:
        error_msg = f"❌ Error processing {file_name}: {str(e)}"
        logger.error(error_msg)
        await update.message.reply_text(error_msg)


async def process_pdf(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    document,
    file_name: str
) -> None:
    """Process PDF lecture files."""
    global RAG_ENABLED
    
    # Download PDF
    file = await context.bot.get_file(document.file_id)
    file_bytes = await file.download_as_bytearray()
    
    # Check file size (limit to 10MB for processing)
    if len(file_bytes) > 10 * 1024 * 1024:
        raise ValueError("PDF too large (>10MB). Please upload a smaller file.")
    
    # Extract text
    pdf_text = await extract_pdf_text(bytes(file_bytes))
    
    if not pdf_text.strip():
        raise ValueError("Could not extract any text from PDF. It may be scanned/image-based.")
    
    # Index in RAG knowledge base if available
    rag_status = ""
    if RAG_ENABLED:
        try:
            import rag_engine
            chunks_added = rag_engine.add_document(pdf_text, file_name)
            rag_status = f"\n📚 Indexed {chunks_added} chunks in knowledge base"
            logger.info(f"Added {chunks_added} chunks to RAG from {file_name}")
        except Exception as e:
            logger.error(f"RAG indexing failed: {e}")
            rag_status = "\n⚠️ Knowledge base indexing failed"
    
    # Truncate if too long (Groq has token limits)
    max_chars = 25000
    summary_text = pdf_text
    if len(pdf_text) > max_chars:
        summary_text = pdf_text[:max_chars] + "\n\n[... content truncated for processing ...]"
    
    # Generate AI summary
    prompt = LECTURE_PROMPT.format(content=summary_text)
    summary = await generate_ai_response(prompt)
    
    # Send summary to Student
    await context.bot.send_message(
        chat_id=FRIEND_ID,
        text=f"📚 <b>New Lecture Summary</b>\n📄 <i>{file_name}</i>\n\n{summary}",
        parse_mode="HTML"
    )
    
    # Send original PDF to Student (using file_id - no re-upload!)
    await context.bot.send_document(
        chat_id=FRIEND_ID,
        document=document.file_id,
        caption="📖 Original lecture material - study this when you're ready!"
    )
    
    # Confirm to Admin
    await update.message.reply_text(f"✅ Sent summary + PDF to your friend!{rag_status}")


async def process_code(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    document,
    file_name: str
) -> None:
    """Process code files to create challenges."""
    global RAG_ENABLED
    
    # Download code file
    file = await context.bot.get_file(document.file_id)
    file_bytes = await file.download_as_bytearray()
    
    # Decode content
    try:
        code_content = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        code_content = file_bytes.decode("latin-1")
    
    if not code_content.strip():
        raise ValueError("Code file is empty.")
    
    # Index in RAG knowledge base if available
    rag_status = ""
    if RAG_ENABLED:
        try:
            import rag_engine
            chunks_added = rag_engine.add_document(code_content, file_name)
            rag_status = f"\n📚 Indexed {chunks_added} chunks in knowledge base"
            logger.info(f"Added {chunks_added} chunks to RAG from {file_name}")
        except Exception as e:
            logger.error(f"RAG indexing failed: {e}")
            rag_status = "\n⚠️ Knowledge base indexing failed"
    
    # Truncate if too long
    max_chars = 15000
    if len(code_content) > max_chars:
        code_content = code_content[:max_chars] + "\n\n// ... truncated ..."
    
    # Generate AI challenge
    prompt = CODE_CHALLENGE_PROMPT.format(content=code_content)
    challenge = await generate_ai_response(prompt)
    
    # Send challenge to Student
    await context.bot.send_message(
        chat_id=FRIEND_ID,
        text=f"💻 <b>Coding Challenge</b>\n📄 <i>{file_name}</i>\n\n{challenge}",
        parse_mode="HTML"
    )
    
    # Send original code as "Solution" (using file_id - no re-upload!)
    await context.bot.send_document(
        chat_id=FRIEND_ID,
        document=document.file_id,
        caption="🔓 SOLUTION FILE - Only open after you've tried solving it!"
    )
    
    # Confirm to Admin
    await update.message.reply_text(f"✅ Sent challenge + solution file to your friend!{rag_status}")


async def handle_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text questions from the student using RAG."""
    global RAG_ENABLED
    
    user_id = update.effective_user.id
    
    # Only respond to the student
    if user_id != FRIEND_ID:
        # If it's the admin, just ignore text messages
        if user_id == ADMIN_ID:
            return
        await update.message.reply_text("Sorry, this bot is private.")
        return
    
    question = update.message.text
    
    if not question or len(question) < 3:
        return
    
    # Check if RAG is available
    if not RAG_ENABLED:
        await update.message.reply_text(
            "🤖 Knowledge base is not available yet.\n"
            "Ask your friend to upload some lecture PDFs first!"
        )
        return
    
    await update.message.reply_text("🔍 Searching lecture materials...")
    
    try:
        import rag_engine
        
        # Get relevant context
        context_str = rag_engine.get_context_string(question)
        
        if not context_str:
            await update.message.reply_text(
                "📭 No relevant content found in the knowledge base.\n"
                "Try rephrasing your question or ask your friend to upload more materials."
            )
            return
        
        # Generate answer with context
        prompt = RAG_QUESTION_PROMPT.format(context=context_str, question=question)
        answer = await generate_ai_response(prompt)
        
        await update.message.reply_text(
            f"📖 <b>Answer based on your lectures:</b>\n\n{answer}",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"RAG question error: {e}")
        await update.message.reply_text(f"❌ Error searching knowledge base: {str(e)}")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    global RAG_ENABLED
    user_id = update.effective_user.id
    
    rag_info = "\n\n🧠 <b>Knowledge Base:</b> " + ("Active ✅" if RAG_ENABLED else "Not configured")
    
    if user_id == ADMIN_ID:
        await update.message.reply_text(
            "👋 <b>Admin Mode Active</b>\n\n"
            "Upload files and I'll process them for your friend:\n"
            "• 📄 <b>PDF</b> → AI Summary + Original file\n"
            "• 💻 <b>Code</b> → Coding Challenge + Solution file\n\n"
            f"Friend ID configured: <code>{FRIEND_ID}</code>"
            f"{rag_info}",
            parse_mode="HTML"
        )
    elif user_id == FRIEND_ID:
        await update.message.reply_text(
            "👋 <b>Welcome, Student!</b>\n\n"
            "You'll receive study materials here automatically:\n"
            "• 📚 Lecture summaries with key concepts\n"
            "• 💻 Coding challenges to practice\n\n"
            "💡 <b>Ask me questions!</b> I can search through uploaded lectures."
            f"{rag_info}",
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text("Sorry, this bot is private.")


# ============================================================================
# MAIN
# ============================================================================

def main() -> None:
    """Start the bot."""
    global RAG_ENABLED
    
    # Validate configuration
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_TOKEN not set in .env")
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set in .env")
    if ADMIN_ID == 0:
        raise ValueError("ADMIN_ID not set in .env")
    if FRIEND_ID == 0:
        raise ValueError("FRIEND_ID not set in .env")
    
    # Initialize RAG if DATABASE_URL is available
    if DATABASE_URL:
        try:
            import rag_engine
            rag_engine.init_db()
            RAG_ENABLED = True
            logger.info("RAG knowledge base initialized successfully!")
        except Exception as e:
            logger.warning(f"RAG initialization failed: {e}. Running without knowledge base.")
            RAG_ENABLED = False
    else:
        logger.info("DATABASE_URL not set. Running without RAG knowledge base.")
    
    logger.info(f"Starting bot... Admin ID: {ADMIN_ID}, Friend ID: {FRIEND_ID}, RAG: {RAG_ENABLED}")
    
    # Build application
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question))
    
    # Start polling
    logger.info("Bot is running with Groq AI! Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
