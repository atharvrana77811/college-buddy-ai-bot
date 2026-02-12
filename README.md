# College Buddy AI 🤖

College Buddy AI is a Telegram bot designed for engineering students who want curated AI news, project ideas, and skill guidance — directly inside Telegram.

It eliminates random browsing and delivers structured updates daily.

---

## 🚀 Features

- 📰 Latest AI & Tech News (Google News RSS integration)
- 🤖 Branch-based career guidance (CSE, AIML, Robotics, ECE)
- 🎯 Project ideas for students
- 🧠 Skill-of-the-day suggestions
- 📊 Clean inline button UI (Telegram InlineKeyboard)
- ⏰ Automated daily digest (APScheduler)

---

## 🛠 Tech Stack

- Python 3.10
- python-telegram-bot
- feedparser (RSS parsing)
- APScheduler
- Railway (Deployment)
- GitHub (CI/CD)

---

## ⚙️ Architecture

1. User interacts via Telegram UI.
2. Bot fetches real-time RSS feeds.
3. Content filtered by category.
4. Scheduled job pushes daily digest.
5. Deployed as a live cloud service.

---

## 📦 Installation (Local Setup)

```bash
git clone https://github.com/yourusername/college-buddy-ai-bot.git
cd college-buddy-ai-bot
pip install -r requirements.txt

