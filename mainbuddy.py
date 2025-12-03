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

# ---------- logging so you can see what's happening ----------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# ⚠️ PUT YOUR BOT TOKEN HERE (KEEP IT SECRET)
TOKEN = "8481127899:AAE...something"


# ---------- RSS feeds for different categories ----------
CATEGORY_FEEDS = {
    "ai": "https://news.google.com/rss/search?q=artificial+intelligence&hl=en-IN&gl=IN&ceid=IN:en",
    "robotics": "https://news.google.com/rss/search?q=robotics&hl=en-IN&gl=IN&ceid=IN:en",
    "startup": "https://news.google.com/rss/search?q=startup+technology&hl=en-IN&gl=IN&ceid=IN:en",
    "coding": "https://news.google.com/rss/search?q=programming+software+developer&hl=en-IN&gl=IN&ceid=IN:en",
}

# ---------- memory ----------
user_prefs = {}                              # stores user branch
seen_links = {k: set() for k in CATEGORY_FEEDS}  # per-category seen links

# chat_id -> job (for /daily)
daily_jobs = {}


# ---------- COMMAND HANDLERS ----------

def start(update, context):
    """Show welcome text + inline menu."""
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


def setup(update, context):
    """Ask user for their branch."""
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
    """Handle replies to setup + normal messages."""
    user_id = update.effective_user.id
    text = update.effective_message.text.strip()

    # ---------- STEP 1: user choosing branch ----------
    if user_id in user_prefs and user_prefs[user_id].get("stage") == "awaiting_branch":
        branches = {
            "1": "CSE",
            "2": "AIML",
            "3": "Robotics",
            "4": "ECE",
        }

        if text not in branches:
            return update.effective_message.reply_text(
                "Invalid input. Send a number 1–4."
            )

        user_prefs[user_id] = {"branch": branches[text]}
        return update.effective_message.reply_text(
            f"Nice! I saved your branch as: {branches[text]} ✅"
        )

    # ---------- default behaviour ----------
    update.effective_message.reply_text(f"You said: {text}")


def news(update, context):
    """Static sample news."""
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


# ---------- HELPERS ----------

def fetch_rss_entries(category: str, limit: int = 3):
    """
    Get up to `limit` unseen entries for the given category.
    Falls back to latest if nothing new.
    """
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
    """Return a career note based on category + branch."""
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
    """Build the text for category news, re-used by commands and /daily."""
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
    """Generic function for AI/Robotics/Startup/Coding commands & buttons."""
    user_id = update.effective_user.id
    msg = build_category_message(category, title, user_id)
    update.effective_message.reply_text(
        msg, parse_mode="Markdown", disable_web_page_preview=True
    )


# ---------- CATEGORY COMMANDS ----------

def ai_news(update, context):
    send_category_news(update, context, category="ai", title="AI")


def robotics_news(update, context):
    send_category_news(update, context, category="robotics", title="Robotics")


def startup_news(update, context):
    send_category_news(update, context, category="startup", title="Startup / Tech Business")


def coding_news(update, context):
    send_category_news(update, context, category="coding", title="Coding / Dev")


def realnews(update, context):
    """Alias to AI news for backward compatibility."""
    ai_news(update, context)


# ---------- DAILY DIGEST ----------

def daily(update, context):
    """Start (or restart) daily AI digest for this chat."""
    chat_id = update.effective_message.chat_id

    # cancel previous job if exists
    if chat_id in daily_jobs:
        daily_jobs[chat_id].schedule_removal()

    job = context.job_queue.run_repeating(
        daily_job,
        interval=24 * 60 * 60,  # every 24 hours
        first=0,                # send one immediately
        context=chat_id,
        name=str(chat_id),
    )
    daily_jobs[chat_id] = job

    update.effective_message.reply_text(
        "✅ Daily AI digest activated.\n"
        "You'll get fresh AI news + career angle once a day around this time."
    )


def daily_job(context):
    """JobQueue callback: send daily AI news to a chat."""
    chat_id = context.job.context
    # in private chats, chat_id == user_id
    user_id = chat_id

    msg = build_category_message("ai", "AI", user_id)
    context.bot.send_message(
        chat_id=chat_id,
        text="⏰ *Your Daily AI Digest*\n\n" + msg,
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )


# ---------- PROJECT IDEAS ----------

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
    """Give 1 project idea based on branch."""
    user_id = update.effective_user.id
    branch = user_prefs.get(user_id, {}).get("branch", "General")

    ideas = PROJECT_IDEAS.get(branch, PROJECT_IDEAS["General"])
    idea = random.choice(ideas)

    update.effective_message.reply_text(
        f"🎯 *Project idea for {branch} students:*\n\n{idea}",
        parse_mode="Markdown",
    )


# ---------- SKILL OF THE DAY ----------

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
        "Revise Ohm’s law + basic circuit analysis.",
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
    """Suggest 1 skill to work on today."""
    user_id = update.effective_user.id
    branch = user_prefs.get(user_id, {}).get("branch", "General")

    skills = SKILLS.get(branch, SKILLS["General"])
    skill = random.choice(skills)

    update.effective_message.reply_text(
        f"🧠 *Skill for today ({branch}):*\n\n{skill}",
        parse_mode="Markdown",
    )


# ---------- INLINE BUTTON HANDLER ----------

def button_handler(update, context):
    query = update.callback_query
    data = query.data
    query.answer()  # stop the 'loading...'

    # Use same update/context functions as commands
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


# ---------- MAIN ----------

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("setup", setup))
    dp.add_handler(CommandHandler("news", news))

    # category commands
    dp.add_handler(CommandHandler("ai", ai_news))
    dp.add_handler(CommandHandler("robotics", robotics_news))
    dp.add_handler(CommandHandler("startup", startup_news))
    dp.add_handler(CommandHandler("coding", coding_news))
    dp.add_handler(CommandHandler("realnews", realnews))

    # new feature commands
    dp.add_handler(CommandHandler("daily", daily))
    dp.add_handler(CommandHandler("project", project_ideas))
    dp.add_handler(CommandHandler("skill", skill_of_the_day))

    # inline button callbacks
    dp.add_handler(CallbackQueryHandler(button_handler))

    # fallback
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    logging.info("Bot started…")
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
