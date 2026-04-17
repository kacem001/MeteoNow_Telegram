import os
import logging
import sqlite3
import requests
import datetime
import re
from dataclasses import dataclass
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Put BOT_TOKEN in .env file")

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

DB_PATH = "main_weather_bot.db"
geocode_cache: Dict[str, Any] = {}
pending_action: Dict[int, str] = {}
recent_button_hits: Dict[str, float] = {}

TRANSLATIONS = {
    "en": {
        "welcome": "Hello {name}! I'm a weather bot. Send your location (use the button) or type a city name.\nUse /help for commands.",
        "help": "Commands:\n/start - start\n/help - this help\n/settings - open settings\n/now - weather now\n/forecast - choose forecast length\n/forecast3 - forecast for 3 days\n/forecast5 - forecast for 5 days\n/forecast7 - forecast for 7 days\n/units - units menu\n/daily - daily alert menu\n",
        "searching_place": "Searching for location...",
        "place_not_found": "Location not found. Try another name or share your location.",
        "location_saved": "Location saved: {name}\nUse /now to get current weather.",
        "no_location": "You don't have a saved location yet. Send your location or type a city name.",
        "fetching_weather": "Fetching weather...",
        "fetch_failed": "Failed to fetch weather. Try again later.",
        "daily_enabled": "Daily alert enabled.",
        "daily_disabled": "Daily alert disabled.",
        "ask_hour": "Send an hour (0-23) for daily alert (e.g. 8). You may send formats like '8', '08', '8:00'.",
        "hour_set": "Daily alert set to {h}:00 and enabled.",
        "invalid_hour": "Please send a valid hour between 0 and 23.",
        "settings_title": "⚙️ Settings",
        "settings_items": "🌍 Language\n📍 Location\n🌡️ Units\n⏰ Daily Alert",
        "units_current": "Current units: {units}",
        "units_set": "Units set to {units}.",
        "lang_set": "Language set to {lang}.",
        "toggle_confirm": "Toggled: {state}",
        "refresh_now": "Refresh now",
        "forecast_days": "Forecast ({days} days):",
        "weather_prefix_daily_notice": "⏰ Morning weather notice:",
        "choose_lang": "Choose language:",
        "choose_units": "Choose units:",
        "choose_forecast": "Choose forecast length:",
        "settings_updated": "Settings updated.",
    },
    "ar": {
        "welcome": "مرحبا {name}! أنا بوت الطقس. أرسل موقعك (باستخدام الزر) أو اكتب اسم المدينة.\nاستخدم /help للأوامر.",
        "help": "الأوامر:\n/start - البداية\n/help - مساعدة\n/settings - الإعدادات\n/now - الطقس الآن\n/forecast - اختيار مدة التوقع\n/forecast3 - توقع 3 أيام\n/forecast5 - توقع 5 أيام\n/forecast7 - توقع 7 أيام\n/units - قائمة الوحدات\n/daily - قائمة التنبيه اليومي\n",
        "searching_place": "أبحث عن المكان...",
        "place_not_found": "لم أجد المكان. جرّب اسمًا آخر أو شارك موقعك.",
        "location_saved": "تم حفظ الموقع: {name}\nاستخدم /now للحصول على الطقس الآن.",
        "no_location": "لم تحدد موقعًا بعد. أرسل موقعك أو اكتب اسم مدينة.",
        "fetching_weather": "أجلب بيانات الطقس...",
        "fetch_failed": "تعذر جلب الطقس. حاول لاحقًا.",
        "daily_enabled": "تم تفعيل التنبيه اليومي.",
        "daily_disabled": "تم إيقاف التنبيه اليومي.",
        "ask_hour": "أرسل رقم الساعة (0-23) لوقت التنبيه (مثال: 8). يمكنك إرسال '8' أو '8:00'.",
        "hour_set": "تم تعيين التنبيه اليومي إلى {h}:00 وتم التفعيل.",
        "invalid_hour": "أرسل رقمًا صحيحًا بين 0 و 23.",
        "settings_title": "⚙️ الإعدادات",
        "settings_items": "🌍 اللغة\n📍 الموقع\n🌡️ الوحدات\n⏰ التنبيه اليومي",
        "units_current": "الوحدة الحالية: {units}",
        "units_set": "تم تغيير الوحدات إلى {units}.",
        "lang_set": "تم تغيير اللغة إلى {lang}.",
        "toggle_confirm": "تم التغيير: {state}",
        "refresh_now": "تحديث الآن",
        "forecast_days": "توقع ({days} أيام):",
        "weather_prefix_daily_notice": "⏰ إشعار الطقس الصباحي:",
        "choose_lang": "اختر اللغة:",
        "choose_units": "اختر الوحدات:",
        "choose_forecast": "اختر مدة التوقع:",
        "settings_updated": "تم تحديث الإعدادات.",
    },
    "fr": {
        "welcome": "Bonjour {name}! Je suis un bot météo. Envoyez votre position (bouton) ou tapez le nom d'une ville.\nUtilisez /help pour la liste des commandes.",
        "help": "Commandes:\n/start - démarrer\n/help - aide\n/settings - paramètres\n/now - météo maintenant\n/forecast - choisir la durée\n/forecast3 - prévision 3 jours\n/forecast5 - prévision 5 jours\n/forecast7 - prévision 7 jours\n/units - menu unités\n/daily - menu alerte quotidienne\n",
        "searching_place": "Recherche du lieu...",
        "place_not_found": "Lieu introuvable. Essayez un autre nom ou partagez votre position.",
        "location_saved": "Position sauvegardée: {name}\nUtilisez /now pour la météo.",
        "no_location": "Vous n'avez pas de position enregistrée. Envoyez votre position ou tapez le nom d'une ville.",
        "fetching_weather": "Récupération météo...",
        "fetch_failed": "Impossible de récupérer la météo. Réessayez plus tard.",
        "daily_enabled": "Alerte quotidienne activée.",
        "daily_disabled": "Alerte quotidienne désactivée.",
        "ask_hour": "Envoyez une heure (0-23) pour l'alerte quotidienne (ex: 8). Vous pouvez envoyer '8' ou '8:00'.",
        "hour_set": "Alerte quotidienne réglée à {h}:00 et activée.",
        "invalid_hour": "Veuillez envoyer une heure valide entre 0 et 23.",
        "settings_title": "⚙️ Paramètres",
        "settings_items": "🌍 Langue\n📍 Position\n🌡️ Unités\n⏰ Alerte quotidienne",
        "units_current": "Unités actuelles: {units}",
        "units_set": "Unités définies sur {units}.",
        "lang_set": "Langue définie sur {lang}.",
        "toggle_confirm": "Basculé: {state}",
        "refresh_now": "Rafraîchir maintenant",
        "forecast_days": "Prévisions ({days} jours):",
        "weather_prefix_daily_notice": "⏰ Alerte météo matinale:",
        "choose_lang": "Choisissez la langue:",
        "choose_units": "Choisissez les unités:",
        "choose_forecast": "Choisissez la durée:",
        "settings_updated": "Paramètres mis à jour.",
    }
}

def t(chat_id: int, key: str, **kwargs):
    lang = get_user_pref(chat_id).get("language", "en")
    text = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, "")
    return text.format(**kwargs)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        chat_id INTEGER PRIMARY KEY,
        latitude REAL,
        longitude REAL,
        location_name TEXT,
        units TEXT DEFAULT 'metric',
        daily_enabled INTEGER DEFAULT 0,
        daily_hour INTEGER DEFAULT 8,
        language TEXT DEFAULT 'en'
    )
    """)
    conn.commit()
    conn.close()

init_db()

def save_user(chat_id: int, loc: Optional[dict] = None, units: Optional[str] = None,
            daily: Optional[int] = None, daily_hour: Optional[int] = None, language: Optional[str] = None):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO users (chat_id) VALUES (?)", (chat_id,))
        if loc:
            c.execute("UPDATE users SET latitude=?, longitude=?, location_name=? WHERE chat_id=?",
                      (loc["lat"], loc["lon"], loc["name"], chat_id))
        if units:
            c.execute("UPDATE users SET units=? WHERE chat_id=?", (units, chat_id))
        if daily is not None:
            c.execute("UPDATE users SET daily_enabled=? WHERE chat_id=?", (int(bool(daily)), chat_id))
        if daily_hour is not None:
            c.execute("UPDATE users SET daily_hour=? WHERE chat_id=?", (int(daily_hour), chat_id))
        if language:
            c.execute("UPDATE users SET language=? WHERE chat_id=?", (language, chat_id))
        conn.commit()
    except Exception as e:
        logger.error(f"Error saving user data: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def get_user_pref(chat_id: int):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT latitude, longitude, location_name, units, daily_enabled, daily_hour, language FROM users WHERE chat_id=?", (chat_id,))
        row = c.fetchone()
        if not row:
            return {"latitude": None, "longitude": None, "location_name": None, "units": "metric", "daily_enabled": False, "daily_hour": 8, "language":"en"}
        lat, lon, name, units, daily_enabled, daily_hour, language = row
        return {
            "latitude": lat,
            "longitude": lon,
            "location_name": name,
            "units": units,
            "daily_enabled": bool(daily_enabled),
            "daily_hour": int(daily_hour) if daily_hour is not None else 8,
            "language": language or "en",
        }
    except Exception as e:
        logger.error(f"Error getting user preferences: {e}")
        return {"latitude": None, "longitude": None, "location_name": None, "units": "metric", "daily_enabled": False, "daily_hour": 8, "language":"en"}
    finally:
        if conn:
            conn.close()

@dataclass
class Location:
    lat: float
    lon: float
    name: str

def geocode_place(query: str, accept_language: str = "en") -> Optional[Location]:
    key = f"{query}__{accept_language}"
    if key in geocode_cache:
        v = geocode_cache[key]
        return Location(lat=v["lat"], lon=v["lon"], name=v["name"])
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": query, "format": "json", "limit": 1}
    headers = {"User-Agent": "TelegramWeatherBot/1.0", "Accept-Language": accept_language}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        if not data:
            return None
        item = data[0]
        loc = {"lat": float(item["lat"]), "lon": float(item["lon"]), "name": item.get("display_name", query)}
        geocode_cache[key] = loc
        return Location(lat=loc["lat"], lon=loc["lon"], name=loc["name"])
    except Exception:
        logger.exception("geocode failed")
        return None

def fetch_weather(lat: float, lon: float, units: str = "metric", days: int = 3) -> Optional[dict]:
    temp_unit = "fahrenheit" if units == "imperial" else "celsius"
    wind_unit = "mph" if units == "imperial" else "kmh"
    pressure_unit = "hpa"
    precip_unit = "inch" if units == "imperial" else "mm"
    daily_vars = "temperature_2m_max,temperature_2m_min,weathercode,precipitation_sum,sunrise,sunset"
    current_vars = "temperature_2m,relative_humidity_2m,precipitation,weathercode,windspeed_10m,pressure_msl"
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": current_vars,
        "daily": daily_vars,
        "timezone": "auto",
        "temperature_unit": temp_unit,
        "windspeed_unit": wind_unit,
        "precipitation_unit": precip_unit,
        "forecast_days": days,
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        logger.exception("weather fetch failed")
        return None

WEATHER_CODES = {
    0: "☀️ Clear",
    1: "🌤 Mostly clear",
    2: "⛅ Partly cloudy",
    3: "☁️ Overcast",
    45: "🌫 Fog",
    48: "🌫 Rime fog",
    51: "🌦 Light drizzle",
    53: "🌧 Moderate drizzle",
    55: "🌧 Dense drizzle",
    56: "🌧 Freezing drizzle: light",
    57: "🌧 Freezing drizzle: dense",
    61: "🌦 Rain: slight",
    63: "🌧 Rain: moderate",
    65: "🌧 Heavy rain",
    66: "🌧 Freezing rain: light",
    67: "🌧 Freezing rain: heavy",
    71: "🌨 Snow: slight",
    73: "🌨 Snow: moderate",
    75: "❄️ Snow heavy",
    77: "❄️ Snow grains",
    80: "🌦 Rain showers: slight",
    81: "🌧 Rain showers: moderate",
    82: "🌧 Rain showers: violent",
    85: "🌨 Snow showers: slight",
    86: "🌨 Snow showers: heavy",
    95: "⛈ Thunderstorm",
    96: "⛈ Thunderstorm with hail",
    99: "⛈ Violent storm",
}

def describe_weather_code(code: int):
    return WEATHER_CODES.get(code, "🌈 Weather")

def format_current_and_forecast(data: dict, loc_name: str, units: str, days: int = 3, lang: str = "en"):
    lines = []
    current = data.get("current", {})
    daily = data.get("daily", {})
    timezone = data.get("timezone", "UTC")
    unit_symbol = "F" if units == "imperial" else "C"
    wind_unit = "mph" if units == "imperial" else "km/h"
    precip_unit = "in" if units == "imperial" else "mm"
    
    # Extract city name from location (first part before comma)
    city_name = loc_name.split(",")[0].strip() if "," in loc_name else loc_name
    
    if current:
        temp = current.get("temperature_2m")
        wind = current.get("windspeed_10m")
        wc = current.get("weathercode")
        humidity = current.get("relative_humidity_2m")
        pressure = current.get("pressure_msl")
        precip = current.get("precipitation")
        
        # Header with location
        lines.append(f"╔═══════════════════════════")
        lines.append(f"║ 📍 <b>{city_name}</b>")
        lines.append(f"║ 🕐 {timezone.split('/')[-1].replace('_', ' ')}")
        lines.append(f"╚═══════════════════════════")
        lines.append("")
        
        # Current weather - main info
        lines.append(f"<b>🌡 {temp}°{unit_symbol}</b>  {describe_weather_code(wc)}")
        lines.append("")
        
        # Details in compact format
        details = []
        details.append(f"💨 {wind} {wind_unit}")
        if humidity is not None:
            details.append(f"💧 {humidity}%")
        if pressure is not None:
            details.append(f"🌪 {int(pressure)} hPa")
        if precip is not None and precip > 0:
            details.append(f"☔ {precip} {precip_unit}")
        lines.append(" │ ".join(details))
        lines.append("")
    
    dates = daily.get("time", [])
    tmax = daily.get("temperature_2m_max", [])
    tmin = daily.get("temperature_2m_min", [])
    codes = daily.get("weathercode", [])
    precip_sum = daily.get("precipitation_sum", [])
    sunrise = daily.get("sunrise", [])
    sunset = daily.get("sunset", [])
    
    if dates:
        lines.append("─────────────────────────")
        header = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get("forecast_days", "📅 <b>{days}-Day Forecast</b>").format(days=days)
        lines.append(header)
        lines.append("─────────────────────────")
        
        for i, d in enumerate(dates):
            if i >= days:
                break
            
            # Format date as weekday
            date_obj = datetime.datetime.strptime(d, "%Y-%m-%d")
            day_name = date_obj.strftime("%a, %b %d")
            
            # Temperature range
            temp_range = f"{int(tmin[i])}° ─ {int(tmax[i])}°"
            
            # Condition
            condition = describe_weather_code(codes[i])
            
            lines.append(f"<b>{day_name}</b>")
            lines.append(f"  {condition}")
            temp_line = f"  🌡 {temp_range}"
            
            # Add precipitation if present
            if precip_sum and i < len(precip_sum) and precip_sum[i] > 0:
                temp_line += f"  │  ☔ {precip_sum[i]}{precip_unit}"
            
            lines.append(temp_line)
            
            # Add sunrise/sunset for today only
            if i == 0 and sunrise and sunset:
                try:
                    sr_time = sunrise[0].split("T")[1][:5] if "T" in sunrise[0] else sunrise[0][-5:]
                    ss_time = sunset[0].split("T")[1][:5] if "T" in sunset[0] else sunset[0][-5:]
                    
                    if lang == "en":
                        lines.append(f"  🌅 Sunrise: {sr_time}  │  🌇 Sunset: {ss_time}")
                    elif lang == "ar":
                        lines.append(f"  🌅 الشروق: {sr_time}  │  🌇 الغروب: {ss_time}")
                    else:  # fr
                        lines.append(f"  🌅 Lever: {sr_time}  │  🌇 Coucher: {ss_time}")
                except Exception:
                    pass
            
            if i < days - 1:
                lines.append("")
    
    return "\n".join(lines)

def build_settings_keyboard(chat_id: int):
    prefs = get_user_pref(chat_id)
    lang = prefs.get("language", "en")
    units = prefs.get("units", "metric")
    daily_enabled = prefs.get("daily_enabled", False)
    daily_hour = prefs.get("daily_hour", 8)
    
    units_display = "°C" if units == "metric" else "°F"
    units_text = f"🌡️ Units: {units_display}"
    
    if daily_enabled:
        daily_text = f"⏰ Daily: ON ({daily_hour}:00)"
    else:
        daily_text = "⏰ Daily: OFF"
    
    kb = [
        [InlineKeyboardButton("🌍 " + ("Language" if lang=="en" else "اللغة" if lang=="ar" else "Langue"), callback_data="set_lang")],
        [InlineKeyboardButton(units_text, callback_data="set_units")],
        [InlineKeyboardButton(daily_text, callback_data="set_daily")],
    ]
    return InlineKeyboardMarkup(kb)

def rate_limit_key(chat_id: int, action: str):
    return f"{chat_id}:{action}"

def throttle(chat_id: int, action: str, interval: float = 0.7) -> bool:
    key = rate_limit_key(chat_id, action)
    now = datetime.datetime.now(datetime.timezone.utc).timestamp()
    last = recent_button_hits.get(key, 0)
    if now - last < interval:
        return False
    recent_button_hits[key] = now
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    name = user.first_name or ""
    prefs = get_user_pref(chat.id)
    lang = prefs.get("language", "en")
    msg = TRANSLATIONS.get(lang, TRANSLATIONS["en"])["welcome"].format(name=name)
    keyboard = [[KeyboardButton("Share location 📍", request_location=True)]]
    await context.bot.send_message(chat_id=chat.id, text=msg, reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(t(update.effective_chat.id, "help"))

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = t(chat_id, "settings_title")
    await update.message.reply_text(text, reply_markup=build_settings_keyboard(chat_id))

async def setlocation_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    keyboard = [[KeyboardButton("Share location 📍", request_location=True)]]
    msg = t(chat_id, "place_not_found") if chat_id in pending_action else "Please share your location using the button below, or type a city name."
    await update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))
    pending_action[chat_id] = "set_location"

async def handle_location_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    loc_obj = update.message.location
    if not loc_obj:
        await update.message.reply_text("No location received.")
        return
    name = f"Lat {loc_obj.latitude:.4f}, Lon {loc_obj.longitude:.4f}"
    loc = {"lat": loc_obj.latitude, "lon": loc_obj.longitude, "name": name}
    save_user(chat_id, loc=loc)
    pending_action.pop(chat_id, None)
    await update.message.reply_text(t(chat_id, "location_saved", name=name), reply_markup=ReplyKeyboardRemove())

def parse_hour_from_text(text: str) -> Optional[int]:
    text = text.strip()
    m = re.search(r"\b([0-1]?\d|2[0-3])\b", text)
    if m:
        try:
            val = int(m.group(1))
            if 0 <= val <= 23:
                return val
        except Exception:
            return None
    return None

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text.strip()
    prefs = get_user_pref(chat_id)
    user_lang = prefs.get("language", "en")
    if pending_action.get(chat_id) == "set_hour":
        h = parse_hour_from_text(text)
        if h is None:
            await update.message.reply_text(t(chat_id, "invalid_hour"))
            return
        save_user(chat_id, daily_hour=h, daily=1)
        if context.job_queue:
            jobs = context.job_queue.get_jobs_by_name(str(chat_id))
            for j in jobs:
                j.schedule_removal()
            context.job_queue.run_daily(send_daily_weather, time=datetime.time(h, 0), chat_id=chat_id, name=str(chat_id))
        pending_action.pop(chat_id, None)
        await update.message.reply_text(t(chat_id, "hour_set", h=h), reply_markup=ReplyKeyboardRemove())
        await update.message.reply_text(t(chat_id, "settings_title"), reply_markup=build_settings_keyboard(chat_id))
        return
    if pending_action.get(chat_id) == "set_location":
        await update.message.reply_text(t(chat_id, "searching_place"))
        loc = geocode_place(text, accept_language=user_lang)
        if not loc:
            await update.message.reply_text(t(chat_id, "place_not_found"))
            return
        save_user(chat_id, loc={"lat": loc.lat, "lon": loc.lon, "name": loc.name})
        pending_action.pop(chat_id, None)
        await update.message.reply_text(t(chat_id, "location_saved", name=loc.name), reply_markup=ReplyKeyboardRemove())
        return
    if text.startswith("/"):
        return
    await update.message.reply_text(t(chat_id, "searching_place"))
    loc = geocode_place(text, accept_language=user_lang)
    if not loc:
        await update.message.reply_text(t(chat_id, "place_not_found"))
        return
    save_user(chat_id, loc={"lat": loc.lat, "lon": loc.lon, "name": loc.name})
    await update.message.reply_text(t(chat_id, "location_saved", name=loc.name))

async def now_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    prefs = get_user_pref(chat_id)
    if not prefs.get("latitude"):
        await update.message.reply_text(t(chat_id, "no_location"))
        return
    await update.message.reply_text(t(chat_id, "fetching_weather"))
    data = fetch_weather(prefs["latitude"], prefs["longitude"], units=prefs["units"], days=3)
    if not data:
        await update.message.reply_text(t(chat_id, "fetch_failed"))
        return
    txt = format_current_and_forecast(data, prefs["location_name"] or "Your Location", units=prefs["units"], days=3, lang=prefs["language"])
    lang = prefs.get("language", "en")
    refresh_text = "🔄 Refresh" if lang == "en" else "🔄 تحديث" if lang == "ar" else "🔄 Actualiser"
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(refresh_text, callback_data="refresh_now")]])
    await update.message.reply_html(txt, reply_markup=kb)

async def forecast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(t(chat_id, "choose_forecast"), reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("3", callback_data="fc_3"), InlineKeyboardButton("5", callback_data="fc_5")],
        [InlineKeyboardButton("7", callback_data="fc_7")]
    ]))

async def forecastX_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cmd = update.message.text.strip().lower()
    days = 3 if cmd.endswith("3") else 5 if cmd.endswith("5") else 7
    chat_id = update.effective_chat.id
    prefs = get_user_pref(chat_id)
    if not prefs.get("latitude"):
        await update.message.reply_text(t(chat_id, "no_location"))
        return
    await update.message.reply_text(t(chat_id, "fetching_weather"))
    data = fetch_weather(prefs["latitude"], prefs["longitude"], units=prefs["units"], days=days)
    if not data:
        await update.message.reply_text(t(chat_id, "fetch_failed"))
        return
    txt = format_current_and_forecast(data, prefs["location_name"] or "Your Location", units=prefs["units"], days=days, lang=prefs["language"])
    await update.message.reply_html(txt)

async def units_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    prefs = get_user_pref(chat_id)
    current = prefs["units"]
    await update.message.reply_text(t(chat_id, "choose_units"), reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("°C (Metric)", callback_data="units_metric"), InlineKeyboardButton("°F (Imperial)", callback_data="units_imperial")]
    ]))

async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    prefs = get_user_pref(chat_id)
    enabled = prefs["daily_enabled"]
    await update.message.reply_text(t(chat_id, "daily_enabled") if enabled else t(chat_id, "daily_disabled"), reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("Toggle 🔁", callback_data="toggle_daily")],
        [InlineKeyboardButton("Set hour ⏰", callback_data="set_daily_hour")]
    ]))

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    chat_id = query.message.chat_id
    if not throttle(chat_id, data):
        return
    prefs = get_user_pref(chat_id)
    if data.startswith("fc_"):
        days = int(data.split("_")[1])
        if not prefs.get("latitude"):
            await query.edit_message_text(t(chat_id, "no_location"))
            return
        await query.edit_message_text("Fetching...")
        dataw = fetch_weather(prefs["latitude"], prefs["longitude"], units=prefs["units"], days=days)
        if not dataw:
            await query.message.reply_text(t(chat_id, "fetch_failed"))
            return
        txt = format_current_and_forecast(dataw, prefs["location_name"] or "Your Location", units=prefs["units"], days=days, lang=prefs["language"])
        await query.message.reply_html(txt)
        return
    if data.startswith("units_"):
        sel = data.split("_")[1]
        units = "metric" if sel == "metric" else "imperial"
        save_user(chat_id, units=units)
        try:
            await query.edit_message_text(t(chat_id, "settings_title"), reply_markup=build_settings_keyboard(chat_id))
        except Exception:
            pass
        return
    if data == "set_lang":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("English 🇬🇧", callback_data="lang_en"), InlineKeyboardButton("العربية 🇩🇿", callback_data="lang_ar")],
            [InlineKeyboardButton("Français 🇫🇷", callback_data="lang_fr")],
            [InlineKeyboardButton("« Back" if prefs.get("language")=="en" else "« رجوع" if prefs.get("language")=="ar" else "« Retour", callback_data="back_to_settings")]
        ])
        await query.edit_message_text(t(chat_id, "choose_lang"), reply_markup=kb)
        return
    if data.startswith("lang_"):
        new_lang = data.split("_")[1]
        save_user(chat_id, language=new_lang)
        try:
            await query.edit_message_text(t(chat_id, "settings_title"), reply_markup=build_settings_keyboard(chat_id))
        except Exception:
            pass
        return

    if data == "set_units":
        current = prefs["units"]
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("°C (Metric)" + (" ✓" if current == "metric" else ""), callback_data="units_metric"), 
             InlineKeyboardButton("°F (Imperial)" + (" ✓" if current == "imperial" else ""), callback_data="units_imperial")],
            [InlineKeyboardButton("« Back" if prefs.get("language")=="en" else "« رجوع" if prefs.get("language")=="ar" else "« Retour", callback_data="back_to_settings")]
        ])
        await query.edit_message_text(t(chat_id, "choose_units"), reply_markup=kb)
        return
    if data == "set_daily":
        enabled = prefs["daily_enabled"]
        hour = prefs.get("daily_hour", 8)
        lang = prefs.get("language", "en")
        status = f"Status: {'ON' if enabled else 'OFF'}" + (f" at {hour}:00" if enabled else "")
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"Toggle: {'ON' if enabled else 'OFF'} 🔁", callback_data="toggle_daily")],
            [InlineKeyboardButton("Set hour ⏰", callback_data="set_daily_hour")],
            [InlineKeyboardButton("« Back" if lang=="en" else "« رجوع" if lang=="ar" else "« Retour", callback_data="back_to_settings")]
        ])
        await query.edit_message_text(f"⏰ Daily Alert\n\n{status}", reply_markup=kb)
        return
    if data == "toggle_daily":
        enabled = not prefs["daily_enabled"]
        save_user(chat_id, daily=1 if enabled else 0)
        if context.job_queue:
            jobs = context.job_queue.get_jobs_by_name(str(chat_id))
            for j in jobs:
                j.schedule_removal()
            if enabled:
                h = prefs.get("daily_hour", 8)
                context.job_queue.run_daily(send_daily_weather, time=datetime.time(h, 0), chat_id=chat_id, name=str(chat_id))
        prefs = get_user_pref(chat_id)
        hour = prefs.get("daily_hour", 8)
        lang = prefs.get("language", "en")
        status = f"Status: {'ON' if enabled else 'OFF'}" + (f" at {hour}:00" if enabled else "")
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"Toggle: {'ON' if enabled else 'OFF'} 🔁", callback_data="toggle_daily")],
            [InlineKeyboardButton("Set hour ⏰", callback_data="set_daily_hour")],
            [InlineKeyboardButton("« Back" if lang=="en" else "« رجوع" if lang=="ar" else "« Retour", callback_data="back_to_settings")]
        ])
        try:
            await query.edit_message_text(f"⏰ Daily Alert\n\n{status}", reply_markup=kb)
        except Exception:
            pass
        return
    if data == "set_daily_hour":
        pending_action[chat_id] = "set_hour"
        try:
            await query.edit_message_text(t(chat_id, "ask_hour"), reply_markup=None)
        except Exception:
            pass
        return
    if data == "back_to_settings":
        try:
            await query.edit_message_text(t(chat_id, "settings_title"), reply_markup=build_settings_keyboard(chat_id))
        except Exception:
            pass
        return
    if data == "refresh_now":
        prefs = get_user_pref(chat_id)
        if not prefs.get("latitude"):
            await query.answer(t(chat_id, "no_location"), show_alert=True)
            return
        await query.answer("🔄 Refreshing...")
        dataw = fetch_weather(prefs["latitude"], prefs["longitude"], units=prefs["units"], days=3)
        if not dataw:
            await query.answer(t(chat_id, "fetch_failed"), show_alert=True)
            return
        txt = format_current_and_forecast(dataw, prefs["location_name"] or "Your Location", units=prefs["units"], days=3, lang=prefs["language"])
        lang = prefs.get("language", "en")
        refresh_text = "🔄 Refresh" if lang == "en" else "🔄 تحديث" if lang == "ar" else "🔄 Actualiser"
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(refresh_text, callback_data="refresh_now")]])
        try:
            await query.edit_message_text(txt, parse_mode="HTML", reply_markup=kb)
        except Exception:
            pass
        return

async def send_daily_weather(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id
    prefs = get_user_pref(chat_id)
    if not prefs or not prefs.get("latitude"):
        return
    data = fetch_weather(prefs["latitude"], prefs["longitude"], units=prefs["units"], days=3)
    if not data:
        await context.bot.send_message(chat_id=chat_id, text=t(chat_id, "fetch_failed"))
        return
    header = t(chat_id, "weather_prefix_daily_notice")
    txt = format_current_and_forecast(data, prefs["location_name"] or "Your Location", units=prefs["units"], days=3, lang=prefs["language"])
    await context.bot.send_message(chat_id=chat_id, text=header)
    await context.bot.send_message(chat_id=chat_id, text=txt, parse_mode="HTML")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

def reschedule_jobs_on_start(application: Application):
    if not application.job_queue:
        logger.warning("Job queue is not available, skipping job scheduling")
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT chat_id, daily_enabled, daily_hour FROM users WHERE daily_enabled=1")
    rows = c.fetchall()
    conn.close()
    for chat_id, enabled, hour in rows:
        try:
            h = int(hour) if hour is not None else 8
            application.job_queue.run_daily(send_daily_weather, time=datetime.time(h, 0), chat_id=int(chat_id), name=str(chat_id))
        except Exception:
            logger.exception("Failed to schedule job for user %s", chat_id)

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    # Job queue is automatically initialized in recent versions
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CommandHandler("now", now_command))
    application.add_handler(CommandHandler("forecast", forecast_command))
    application.add_handler(CommandHandler("forecast3", forecastX_command))
    application.add_handler(CommandHandler("forecast5", forecastX_command))
    application.add_handler(CommandHandler("forecast7", forecastX_command))
    application.add_handler(CommandHandler("units", units_command))
    application.add_handler(CommandHandler("daily", daily_command))
    application.add_handler(MessageHandler(filters.LOCATION, handle_location_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(CallbackQueryHandler(callback_handler))
    application.add_error_handler(error_handler)
    reschedule_jobs_on_start(application)
    application.run_polling()

if __name__ == "__main__":
    main()