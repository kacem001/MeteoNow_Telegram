<div align="center">

# 🌤️ MeteoNow

**A fast, multilingual Telegram weather assistant with real-time severe weather alerts, interactive forecasts, and scheduled daily briefings.**

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![python-telegram-bot](https://img.shields.io/badge/python--telegram--bot-20%2B-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://docs.python-telegram-bot.org/)
[![Open-Meteo API](https://img.shields.io/badge/API-Open--Meteo-orange?style=for-the-badge)](https://open-meteo.com/)
[![SQLite](https://img.shields.io/badge/Database-SQLite3-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

</div>

---

## 📖 Overview

**MeteoNow** is an asynchronous, full-featured Telegram bot designed for frictionless weather tracking. Built with `python-telegram-bot` and powered by the **Open-Meteo** and **Nominatim (OpenStreetMap)** APIs, it delivers accurate current conditions, 12-hour breakdowns, multi-day forecasts, automated morning reports, and background severe weather monitoring—all without requiring paid third-party weather API keys.

---

## ✨ Key Features

- **📍 Flexible Location Input**
  - **GPS Sharing**: Compact, non-intrusive reply keyboard with automatic reverse geocoding into readable city names.
  - **City Search**: Instant global city lookup with smart caching.
  - **Raw Coordinates**: Direct support for pasting `latitude, longitude` pairs (e.g., `36.7538, 3.0588`).
- **⚡ Seamless Inline UI**
  - Interactive forecast cards that update **in place** (`3d`, `5d`, `7d` switchers, `🕒 Today Hourly`, `🔄 Refresh`, and quick `🏠 Home` navigation).
  - Native Telegram `/` command menu integration alongside button-driven navigation.
- **🚨 Real-Time Severe Weather Watcher**
  - Background job running every 2 hours to monitor subscribed users' locations for thunderstorms, heavy rain/snow, gale-force winds ($\ge 60\text{ km/h}$), extreme heat ($\ge 40^\circ\text{C}$), or freezing temperatures ($\le -5^\circ\text{C}$), with deduplication to prevent notification spam.
- **⏰ Scheduled Daily Briefings**
  - Customizable morning weather notifications delivered automatically at the user's preferred hour (`00:00`–`23:00`).
- **🌍 Automatic Multi-Language Support**
  - Auto-detects the user's Telegram client locale on `/start` and supports seamless switching between **English**, **Arabic (العربية)**, and **French (Français)**.
- **🌡️ Dual Measurement Systems**
  - Instant toggling between **Metric** (`°C`, `km/h`, `mm`) and **Imperial** (`°F`, `mph`, `in`).

---

## 📸 Preview

```text
📍 Algiers  •  🕐 Algiers
━━━━━━━━━━━━━━━━━━━━━
🌡 21.4°C  ⛅ Partly cloudy
🤒 Feels like: 20.8°C

💨 11.5 km/h │ 💧 58% │ 🌪 1019 hPa

─────────────────────
📅 3-Day Forecast
─────────────────────
Thu, Nov 26 • ☀️ Clear
  🌡 14° ─ 23°  │  ☀️ UV: 4.2
  🌅 Sunrise: 07:38  │  🌇 Sunset: 17:32

Fri, Nov 27 • 🌦 Slight rain
  🌡 13° ─ 19°  │  ☔ 3.4mm

Sat, Nov 28 • ⛅ Partly cloudy
  🌡 12° ─ 20°

[ • 3d • ]  [  5d  ]  [  7d  ]
[ 🕒 Today Hourly ] [ 🔄 Refresh ]
[            🏠 Home            ]
```

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Language** | Python 3.9+ | Core application logic |
| **Bot Framework** | `python-telegram-bot` (v20+ `JobQueue`) | Async Telegram API handling & scheduled tasks |
| **Weather Data** | [Open-Meteo API](https://open-meteo.com/) | Current, hourly, and 7-day forecast data |
| **Geocoding** | [Nominatim (OSM)](https://nominatim.openstreetmap.org/) | Forward & reverse geocoding |
| **Persistence** | SQLite3 | Lightweight user preferences & alert state storage |

---

## 🚀 Getting Started

### 1. Prerequisites

- Python **3.9** or higher
- A Telegram Bot Token obtained from [@BotFather](https://t.me/BotFather)

### 2. Installation

Clone the repository and navigate into the project directory:

```bash
git clone https://github.com/yourusername/MeteoNow.git
cd MeteoNow
```

Create a virtual environment (recommended) and install dependencies:

```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate         # Windows

pip install "python-telegram-bot[job-queue]" requests python-dotenv
```

> **Note:** Installing `python-telegram-bot[job-queue]` ensures `APScheduler` is installed for daily reports and background severe weather alerts.

### 3. Configuration

Create a `.env` file in the root directory:

```env
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

*(Optional)* Configure your bot profile in [@BotFather](https://t.me/BotFather):
- **Name:** `MeteoNow`
- **About:** `Real-time weather forecasts, hourly breakdowns, daily morning briefings, and severe weather alerts in English, Français & العربية.`

### 4. Run the Bot

```bash
python main.py
```

---

## 💬 Bot Commands

| Command | Description |
| :--- | :--- |
| `/start` | Launch the bot, auto-detect language, and open the main menu |
| `/now` | View current weather and 3-day forecast |
| `/forecast` | Open interactive forecast duration selector (`3`, `5`, or `7` days) |
| `/forecast3` | Quick 3-day weather forecast |
| `/forecast5` | Quick 5-day weather forecast |
| `/forecast7` | Quick 7-day weather forecast |
| `/location` | Set location via GPS button, city name, or `lat, lon` coordinates |
| `/settings` | Configure language, units (`°C`/`°F`), daily briefings, and severe alerts |
| `/help` | Display usage instructions and available commands |

---

## 🗂️ Project Structure

```text
MeteoNow/
├── main.py                  # Core bot handlers, API clients, formatters & background jobs
├── .env                     # Environment variables (excluded from Git)
├── .gitignore               # Ignores .env, __pycache__, and local SQLite database
├── main_weather_bot.db      # SQLite database (auto-generated on first run)
└── README.md                # Project documentation
```

---

## 🗺️ Roadmap

- [ ] **MeteoNow Web Dashboard**: Companion web app sharing the user backend to manage alerts and view interactive radar maps.
- [ ] **Multi-Location Bookmarks**: Save and switch between multiple favorite cities (e.g., *Home*, *Work*, *Travel*).
- [ ] **Air Quality Index (AQI)**: Real-time air pollution and pollen metrics via Open-Meteo Air Quality API.
- [ ] **Docker Support**: Official `Dockerfile` and `docker-compose.yml` for one-command cloud deployment.

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.
