# 🌤️ Telegram Weather Bot

A professional, feature-rich Telegram bot that provides real-time weather information with a beautiful interface. Supports multiple languages, daily alerts, and customizable units.

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## ✨ Features

- **🌍 Multi-Language Support**: English, Arabic, and French
- **📍 Location-Based Weather**: Share your location or search by city name
- **🌡️ Dual Unit System**: Switch between Celsius (Metric) and Fahrenheit (Imperial)
- **📅 Extended Forecasts**: Get 3, 5, or 7-day weather forecasts
- **⏰ Daily Alerts**: Automatic morning weather notifications at your chosen time
- **🔄 Real-Time Updates**: Refresh button for instant weather updates
- **📊 Comprehensive Data**: Temperature, humidity, pressure, wind speed, precipitation, sunrise/sunset
- **💾 User Preferences**: Saves location, language, units, and alert settings
- **🎨 Professional UI**: Clean, modern interface with intuitive buttons

## 📸 Screenshots

The bot displays weather in a beautifully formatted layout:
```
╔═══════════════════════════
║ 📍 Annaba
║ 🕐 Algiers
╚═══════════════════════════

🌡 12.8°C  ⛅ Partly cloudy

💨 8.2 km/h │ 💧 61% │ 🌪 1018 hPa

─────────────────────────
Forecast (3 days):
─────────────────────────
Fri, Nov 28
  🌦 Rain showers: slight
  🌡 10° ─ 14°  │  ☔ 5.1mm
  🌅 Sunrise: 07:20  │  🌇 Sunset: 17:13
```

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- A Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Internet connection

### Step 1: Install Python

Download and install Python from [python.org](https://www.python.org/downloads/)

**Windows**: Make sure to check "Add Python to PATH" during installation

**Linux/Mac**: Python is usually pre-installed. Check with:
```bash
python3 --version
```

### Step 2: Get Your Bot Token

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Copy the **Bot Token** (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Step 3: Setup the Bot

1. **Extract the files** to a folder (e.g., `WeatherBot`)

2. **Install required packages**:

   **Windows (PowerShell)**:
   ```powershell
   pip install python-telegram-bot requests python-dotenv
   ```

   **Linux/Mac (Terminal)**:
   ```bash
   pip3 install python-telegram-bot requests python-dotenv
   ```

3. **Create a `.env` file** in the same folder as `main.py`:

   Create a new file named `.env` (exactly, with the dot at the beginning) and add:
   ```
   BOT_TOKEN=your_bot_token_here
   ```
   
   Replace `your_bot_token_here` with the token you got from BotFather.

   **Example**:
   ```
   BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   ```

## ▶️ Running the Bot

### Windows

1. Open PowerShell in the bot folder
2. Run:
   ```powershell
   python main.py
   ```

### Linux/Mac

1. Open Terminal in the bot folder
2. Run:
   ```bash
   python3 main.py
   ```

### Success!

If everything is set up correctly, you'll see:
```
INFO - Application started
```

The bot is now running! Keep the terminal/PowerShell window open.

## 📱 Using the Bot

### Basic Commands

| Command | Description |
|---------|-------------|
| `/start` | Start the bot and get welcome message |
| `/help` | Show all available commands |
| `/now` | Get current weather |
| `/forecast` | Choose forecast length (3/5/7 days) |
| `/forecast3` | Get 3-day forecast |
| `/forecast5` | Get 5-day forecast |
| `/forecast7` | Get 7-day forecast |
| `/settings` | Open settings menu |
| `/units` | Change temperature units |
| `/daily` | Configure daily weather alerts |

### Setting Up Your Location

**Option 1: Share Location**
1. Send `/start`
2. Click "Share location 📍" button
3. Allow Telegram to access your location

**Option 2: Type City Name**
- Just type any city name (e.g., "London", "Paris", "New York")
- The bot will save it automatically

### Configuring Settings

Send `/settings` to access:

- **🌍 Language**: Choose English, Arabic (العربية), or French (Français)
- **🌡️ Units**: Switch between °C (Metric) and °F (Imperial)
- **⏰ Daily Alert**: 
  - Toggle ON/OFF
  - Set your preferred notification time (0-23 hour format)

### Daily Weather Alerts

1. Send `/daily` or go to Settings
2. Toggle daily alerts ON
3. Click "Set hour ⏰"
4. Send your preferred hour (e.g., "8" for 8:00 AM)
5. You'll receive automatic weather updates every morning!

## 🗂️ File Structure

```
WeatherBot/
├── main.py                 # Main bot code
├── .env                    # Your bot token (create this)
├── README.md              # This file
└── main_weather_bot.db    # Database (auto-created)
```

## 🔧 Troubleshooting

### "ModuleNotFoundError: No module named 'telegram'"
**Solution**: Install the required packages:
```bash
pip install python-telegram-bot requests python-dotenv
```

### "RuntimeError: Put BOT_TOKEN in .env file"
**Solution**: 
- Make sure `.env` file exists in the same folder as `main.py`
- Check that it contains: `BOT_TOKEN=your_actual_token`
- No spaces around the `=` sign

### Bot doesn't respond
**Solution**:
- Make sure the Python script is running (check terminal/PowerShell)
- Verify your bot token is correct
- Check your internet connection

### "Failed to fetch weather"
**Solution**:
- Check your internet connection
- The weather API (Open-Meteo) might be temporarily down
- Try again in a few moments

### Database locked error
**Solution**:
- Close any other instances of the bot
- Delete `main_weather_bot.db` file (your settings will reset)
- Restart the bot

## 🌐 APIs Used

- **Weather Data**: [Open-Meteo](https://open-meteo.com/) - Free weather API
- **Geocoding**: [Nominatim/OpenStreetMap](https://nominatim.openstreetmap.org/) - Free geocoding service
- **Telegram Bot API**: For bot functionality

## 📊 Technical Details

- **Language**: Python 3.8+
- **Framework**: python-telegram-bot
- **Database**: SQLite3
- **Weather API**: Open-Meteo (no API key required)
- **Storage**: Local SQLite database for user preferences

## 🔐 Privacy & Data

The bot stores locally:
- User's chat ID (Telegram identifier)
- Last saved location (coordinates and name)
- Preferred language, units, and alert settings

**No personal data** (name, phone, etc.) is collected or stored.

## 📝 Customization

### Customizing Welcome Messages and Text

You can customize all bot messages by editing the `TRANSLATIONS` dictionary in `main.py`:

**English** - Starting at **line 29**:
```python
"en": {
    "welcome": "Hello {name}! I'm a weather bot. ...",  # Line 29
    "help": "Commands:\n/start - start\n...",
    ...
}
```

**Arabic** - Starting at **line 57**:
```python
"ar": {
    "welcome": "مرحبا {name}! أنا بوت الطقس. ...",  # Line 57
    "help": "الأوامر:\n/start - البداية\n...",
    ...
}
```

**French** - Starting at **line 85**:
```python
"fr": {
    "welcome": "Bonjour {name}! Je suis un bot météo. ...",  # Line 85
    "help": "Commandes:\n/start - démarrer\n...",
    ...
}
```

Simply edit the text inside the quotes to customize any message!

### Adding More Languages

To add a new language, copy one of the existing language blocks and translate all messages:
```python
TRANSLATIONS = {
    "en": { ... },
    "ar": { ... },
    "fr": { ... },
    "es": {  # Add Spanish
        "welcome": "¡Hola {name}! Soy un bot del tiempo. ...",
        "help": "Comandos:\n/start - iniciar\n...",
        # ... translate all other messages
    }
}
```

Then add the new language button in the settings (around line 600):
```python
[InlineKeyboardButton("Español 🇪🇸", callback_data="lang_es")]
```

### Changing Default Settings

Modify the default values in `get_user_pref()` function (around line 170):
```python
return {
    "units": "metric",      # Change to "imperial" for Fahrenheit
    "daily_hour": 8,        # Change default alert time
    "language": "en",       # Change default language
    ...
}
```

## 🆘 Support

For issues or questions:
1. Check the Troubleshooting section above
2. Ensure all prerequisites are met
3. Verify your `.env` file is configured correctly

## 📄 License

This project is provided as-is for personal or commercial use.

## 🎯 Future Features

Potential enhancements you could add:
- Air quality index
- UV index
- Weather alerts/warnings
- Multiple saved locations
- Weather maps
- Historical weather data
- Admin panel for managing users

## 👨‍💻 About

Professional Telegram Weather Bot with modern UI/UX design, built with Python and the python-telegram-bot library.

---

**Enjoy your weather bot! ☀️🌧️❄️**

For any customization or additional features, the code is well-commented and easy to modify.
