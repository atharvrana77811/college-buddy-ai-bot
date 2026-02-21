from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackQueryHandler,
)
import feedparser
import logging
import random
import json
import os
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ---------- logging ----------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# ---------- env vars ----------
TOKEN = os.getenv("BOT_TOKEN")
SHEET_ID = os.getenv("SHEET_ID")
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON")

# ---------- Google Sheets tracking ----------
def get_sheet():
    creds_dict = json.loads(GOOGLE_CREDS_JSON)
    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID).sheet1

def track_user(user_id, username):
    try:
        sheet = get_sheet()
        records = sheet.get_all_records()
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        for i, row in enumerate(records, start=2):
            if str(row["user_id"]) == str(user_id):
                sheet.update_cell(i, 4, now)
                sheet.update_cell(i, 5, int(row["message_count"]) + 1)
                return
        sheet.append_row([str(user_id), username or "unknown", now, now, 1])
    except Exception as e:
        logging.error(f"Sheet tracking error: {e}")

# ---------- RSS feeds ----------
CATEGORY_FEEDS = {
    "ai": "https://news.google.com/rss/search?q=artificial+intelligence&hl=en-IN&gl=IN&ceid=IN:en",
    "robotics": "https://news.google.com/rss/search?q=robotics&hl=en-IN&gl=IN&ceid=IN:en",
    "startup": "https://news.google.com/rss/search?q=startup+technology&hl=en-IN&gl=IN&ceid=IN:en",
    "coding": "https://news.google.com/rss/search?q=programming+software+developer&hl=en-IN&gl=IN&ceid=IN:en",
}

# ---------- memory ----------
user_prefs = {}
seen_links = {k: set() for k in CATEGORY_FEEDS}
daily_jobs = {}

# ---------- YOUR ADMIN TELEGRAM ID ----------
ADMIN_ID = 7697683067  # <-- REPLACE THIS WITH YOUR TELEGRAM ID

# ---------- COMMAND HANDLERS ----------

def start(update, context):
    user = update.effective_user
    track_user(user.id, user.username)

    keyboard = [
        [InlineKeyboardButton("⚙️ Setup Branch", callback_data="setup")],
        [
            InlineKeyboardButton("🤖 AI News", callback_data="ai"),
            InlineKeyboardButton("🔧 Robotics", callback_data="robotics"),
        ],
        [
            InlineKeyboardButton("🚀 Startups", callback_data="startup"),
            InlineKeyboardButton("💻 Coding", callback_data="coding"),
        ],
        [InlineKeyboardButton("⏰ Daily AI Digest", callback_data="daily")],
        [
            InlineKeyboardButton("🎯 Project idea", callback_data="project"),
            InlineKeyboardButton("🧠 Skill for today", callback_data="skill"),
        ],
        [InlineKeyboardButton("ℹ️ About Bot", callback_data="about")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_message.reply_text(
        "👋 Welcome to *College Buddy AI* — your tech + career assistant.\n\n"
        "I give:\n"
        "• AI / Robotics / Startup / Coding news\n"
        "• Branch-based career angles\n"
        "• Project & learning ideas for students\n\n"
        "Tap a button below or use commands like:\n"
        "/setup, /ai, /robotics, /startup, /coding, /daily, /project, /skill.",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )


def stats(update, context):
    if update.effective_user.id != ADMIN_ID:
        return update.effective_message.reply_text("Not authorized.")
    try:
        sheet = get_sheet()
        records = sheet.get_all_records()
        total = len(records)
        update.effective_message.reply_text(
            f"📊 *Bot Stats*\n\nTotal unique users: {total}",
            parse_mode="Markdown"
        )
    except Exception as e:
        update.effective_message.reply_text(f"Error: {e}")


def setup(update, context):
    user_id = update.effective_user.id
    update.effective_message.reply_text(
        "Choose your branch:\n"
        "1. CSE\n"
        "2. AIML\n"
        "3. Robotics\n"
        "4. ECE\n\n"
        "Send just the number (1–4)."
    )
    user_prefs[user_id] = {"stage": "awaiting_branch"}


def echo(update, context):
    user = update.effective_user
    track_user(user.id, user.username)
    user_id = update.effective_user.id
    text = update.effective_message.text.strip()
    if user_id in user_prefs and user_prefs[user_id].get("stage") == "awaiting_branch":
        branches = {"1": "CSE", "2": "AIML", "3": "Robotics", "4": "ECE"}
        if text not in branches:
            return update.effective_message.reply_text("Invalid input. Send a number 1–4.")
        user_prefs[user_id] = {"branch": branches[text]}
        return update.effective_message.reply_text(f"Nice! I saved your branch as: {branches[text]} ✅")
    update.effective_message.reply_text(f"You said: {text}")

def news(update, context):
    text = (
        "📰 *Tech News for Students*\n\n"
        "1️⃣ AI model beats 98% of humans in reasoning.\n"
        "2️⃣ Google releases a new robotics breakthrough.\n"
        "3️⃣ MIT reveals an upgraded drone navigation system.\n\n"
        "💡 *Why it matters:*\n"
        "- AI + Robotics = fastest growing tech fields.\n"
        "- Learn Python, APIs, ML basics.\n"
        "- Great for internships and projects.\n"
    )
    update.effective_message.reply_text(text, parse_mode="Markdown")


def fetch_rss_entries(category: str, limit: int = 3):
    url = CATEGORY_FEEDS[category]
    feed = feedparser.parse(url)
    new_entries = []
    for entry in feed.entries:
        link = entry.link
        if link in seen_links[category]:
            continue
        new_entries.append(entry)
        seen_links[category].add(link)
        if len(new_entries) == limit:
            break
    if not new_entries:
        new_entries = feed.entries[:limit]
    return new_entries


def category_career_text(category: str, branch: str) -> str:
    base_texts = {
        "ai": "Follow these to spot where AI jobs & research are heading.",
        "robotics": "Good for understanding how AI meets hardware and control systems.",
        "startup": "Gives you ideas about products, markets and startup culture.",
        "coding": "Shows what tools, languages and frameworks are hot for devs.",
    }
    base = base_texts[category]
    if branch == "AIML" and category == "ai":
        extra = " Double down on ML, math, and building small model-based projects."
    elif branch == "Robotics" and category == "robotics":
        extra = " Learn ROS, sensors, and path planning—perfect project ideas here."
    elif branch == "CSE" and category in ("ai", "coding", "startup"):
        extra = " Use these as inspiration for software projects and hackathons."
    elif branch == "ECE" and category == "robotics":
        extra = " Focus on embedded systems + edge AI, strong niche combo."
    else:
        extra = ""
    return base + extra


def build_category_message(category: str, title: str, user_id: int) -> str:
    branch = user_prefs.get(user_id, {}).get("branch", "General")
    entries = fetch_rss_entries(category, limit=3)
    if not entries:
        return "Couldn't fetch news right now 🫠"
    msg = f"📰 *Latest {title} News*\n\n"
    for i, entry in enumerate(entries, start=1):
        msg += f"{i}. [{entry.title}]({entry.link})\n"
    msg += f"\n🎯 *Career angle for {branch} students:*\n"
    msg += category_career_text(category, branch)
    return msg


def send_category_news(update, context, category: str, title: str):
    user_id = update.effective_user.id
    msg = build_category_message(category, title, user_id)
    update.effective_message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=True)


def ai_news(update, context):
    send_category_news(update, context, category="ai", title="AI")

def robotics_news(update, context):
    send_category_news(update, context, category="robotics", title="Robotics")

def startup_news(update, context):
    send_category_news(update, context, category="startup", title="Startup / Tech Business")

def coding_news(update, context):
    send_category_news(update, context, category="coding", title="Coding / Dev")

def realnews(update, context):
    ai_news(update, context)


def daily(update, context):
    chat_id = update.effective_message.chat_id
    if chat_id in daily_jobs:
        daily_jobs[chat_id].schedule_removal()
    job = context.job_queue.run_repeating(
        daily_job, interval=24 * 60 * 60, first=0, context=chat_id, name=str(chat_id),
    )
    daily_jobs[chat_id] = job
    update.effective_message.reply_text(
        "✅ Daily AI digest activated.\n"
        "You'll get fresh AI news + career angle once a day around this time."
    )

def daily_job(context):
    chat_id = context.job.context
    msg = build_category_message("ai", "AI", chat_id)
    context.bot.send_message(
        chat_id=chat_id,
        text="⏰ *Your Daily AI Digest*\n\n" + msg,
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )


PROJECT_IDEAS = {
    "CSE": [
        "Build a Telegram bot that summarizes YouTube videos into notes.",
        "Create a web app that tracks your coding practice and suggests questions.",
        "Make a small API that recommends project ideas based on interests.",
    ],
    "AIML": [
        "Train a model to classify memes vs normal images.",
        "Build a movie recommendation system using basic ML.",
        "Create a chatbot that answers questions from your college notes.",
    ],
    "Robotics": [
        "Line-following robot with basic obstacle avoidance.",
        "Simulate a robotic arm in Python using simple kinematics.",
        "Make a small RC car that can be controlled via a phone app.",
    ],
    "ECE": [
        "IoT project: monitor room temperature and send alerts to Telegram.",
        "Build a simple home automation system with relays + microcontroller.",
        "Create a low-cost smart energy meter prototype.",
    ],
    "General": [
        "Make a personal finance tracker app for students.",
        "Build a 'habit streak' tracker bot on Telegram.",
        "Create a website that curates best free tech learning resources.",
    ],
}

def project_ideas(update, context):
    user_id = update.effective_user.id
    branch = user_prefs.get(user_id, {}).get("branch", "General")
    ideas = PROJECT_IDEAS.get(branch, PROJECT_IDEAS["General"])
    update.effective_message.reply_text(
        f"🎯 *Project idea for {branch} students:*\n\n{random.choice(ideas)}",
        parse_mode="Markdown",
    )


SKILLS = {
    "CSE": [
        "Learn basic git: clone, commit, push, pull.",
        "Get comfortable with Python lists, dicts, and list comprehensions.",
        "Read about REST APIs and try calling one from Python.",
    ],
    "AIML": [
        "Learn how train/test split works in ML.",
        "Implement linear regression from scratch in Python.",
        "Understand the difference between classification and regression.",
    ],
    "Robotics": [
        "Revise PID control basics and why it's used in robots.",
        "Learn what ROS (Robot Operating System) is and where it's used.",
        "Study different types of sensors: ultrasonic, IR, LiDAR.",
    ],
    "ECE": [
        "Revise Ohm's law + basic circuit analysis.",
        "Learn how ADC (Analog to Digital Converter) works.",
        "Study the basics of microcontrollers vs microprocessors.",
    ],
    "General": [
        "Spend 30 minutes today reading documentation instead of watching videos.",
        "Write a proper README for one of your projects.",
        "Clean up your GitHub: push at least one project there.",
    ],
}

def skill_of_the_day(update, context):
    user_id = update.effective_user.id
    branch = user_prefs.get(user_id, {}).get("branch", "General")
    skills = SKILLS.get(branch, SKILLS["General"])
    update.effective_message.reply_text(
        f"🧠 *Skill for today ({branch}):*\n\n{random.choice(skills)}",
        parse_mode="Markdown",
    )


def button_handler(update, context):
    query = update.callback_query
    data = query.data
    query.answer()

    if data == "setup":
        setup(update, context)
    elif data == "ai":
        ai_news(update, context)
    elif data == "robotics":
        robotics_news(update, context)
    elif data == "startup":
        startup_news(update, context)
    elif data == "coding":
        coding_news(update, context)
    elif data == "realnews":
        realnews(update, context)
    elif data == "daily":
        daily(update, context)
    elif data == "project":
        project_ideas(update, context)
    elif data == "skill":
        skill_of_the_day(update, context)
    elif data == "about":
        query.edit_message_text(
            "🤖 *About College Buddy AI*\n\n"
            "I share:\n"
            "• AI / Robotics / Startup / Coding news\n"
            "• Branch-based career guidance\n"
            "• Project ideas & skills to focus on\n\n"
            "Built by a B.Tech student who actually cares about learning and execution. 🔥",
            parse_mode="Markdown",
        )


def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("setup", setup))
    dp.add_handler(CommandHandler("news", news))
    dp.add_handler(CommandHandler("stats", stats))
    dp.add_handler(CommandHandler("ai", ai_news))
    dp.add_handler(CommandHandler("robotics", robotics_news))
    dp.add_handler(CommandHandler("startup", startup_news))
    dp.add_handler(CommandHandler("coding", coding_news))
    dp.add_handler(CommandHandler("realnews", realnews))
    dp.add_handler(CommandHandler("daily", daily))
    dp.add_handler(CommandHandler("project", project_ideas))
    dp.add_handler(CommandHandler("skill", skill_of_the_day))
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    logging.info("Bot started…")
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
