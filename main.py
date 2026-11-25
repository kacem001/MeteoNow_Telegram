import os
import logging
import sqlite3
import requests
import datetime
import re
from dataclasses import dataclass
from typing import Optional, Dict, Any, Tuple
from dotenv import load_dotenv
from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Put BOT_TOKEN in .env file")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

DB_PATH = "main_weather_bot.db"
geocode_cache: Dict[str, Any] = {}
pending_action: Dict[int, str] = {}
recent_button_hits: Dict[str, float] = {}

TRANSLATIONS = {
    "en": {
        "welcome": (
            "👋 Hello <b>{name}</b>! I'm your personal weather assistant.\n\n"
            "📍 <b>Quick Start:</b>\n"
            "• Type any <b>city name</b> (e.g. <i>Algiers, Paris</i>)\n"
            "• Or paste <b>coordinates</b> (e.g. <code>36.75, 3.04</code>)\n"
            "• Or tap <b>📍 Share Location</b> below for GPS"
        ),
        "help": (
            "📖 <b>Help & Commands</b>\n\n"
            "🌤 /now — Current weather & forecast\n"
            "📅 /forecast — Interactive 3, 5, or 7-day forecast\n"
            "📍 /location — Change location (GPS, city, or lat/lon)\n"
            "⚙️ /settings — Language, units, daily & severe alerts\n"
            "❓ /help — Show this guide\n\n"
            "💡 <i>Tip: You can type a city name or paste coordinates anytime!</i>"
        ),
        "btn_share_loc": "📍 Share Location",
        "btn_now": "🌤 Weather Now",
        "btn_forecast": "📅 Forecast",
        "btn_settings": "⚙️ Settings",
        "btn_help": "❓ Help",
        "btn_refresh": "🔄 Refresh",
        "btn_hourly": "🕒 Today Hourly",
        "btn_home": "🏠 Home",
        "btn_back": "« Back",
        "searching_place": "🔍 Searching for location...",
        "place_not_found": "❌ Location not found. Try another city name, coordinates (lat, lon), or share your GPS location.",
        "location_saved": "✅ Location saved: <b>{name}</b>",
        "ask_location": "📍 Tap the button below to share your GPS location, type a city name, or enter coordinates (e.g. <code>36.7538, 3.0588</code>):",
        "no_location": "📍 You haven't set a location yet. Type a city name, paste coordinates, or tap Share Location.",
        "fetching_weather": "⏳ Fetching weather...",
        "fetch_failed": "⚠️ Failed to fetch weather. Please try again shortly.",
        "ask_hour": "⏰ Send the hour (0–23) for your daily weather report (e.g. <code>8</code> or <code>08:00</code>):",
        "hour_set": "✅ Daily report set to <b>{h}:00</b> and enabled.",
        "invalid_hour": "⚠️ Please send a valid hour between 0 and 23.",
        "settings_title": "⚙️ <b>Bot Settings</b>\nCustomize your weather experience:",
        "choose_lang": "🌍 Choose your language:",
        "choose_units": "🌡️ Choose measurement units:",
        "choose_forecast": "📅 Select forecast duration:",
        "forecast_days": "📅 <b>{days}-Day Forecast</b>",
        "hourly_title": "🕒 <b>Next 12 Hours</b>",
        "weather_prefix_daily_notice": "⏰ <b>Daily Morning Weather Report</b>",
        "severe_alert_title": "🚨 <b>Real-Time Weather Alert</b> for <b>{city}</b>:",
        "feels_like": "Feels like",
        "uv_index": "UV",
        "sunrise": "Sunrise",
        "sunset": "Sunset",
    },
    "ar": {
        "welcome": (
            "👋 مرحباً <b>{name}</b>! أنا مساعدك الشخصي للطقس.\n\n"
            "📍 <b>للبدء السريع:</b>\n"
            "• اكتب اسم أي <b>مدينة</b> (مثل: <i>الجزائر، عنابة</i>)\n"
            "• أو ألصق <b>الإحداثيات</b> (مثل: <code>36.75, 3.04</code>)\n"
            "• أو اضغط على <b>📍 مشاركة الموقع</b> بالأسفل"
        ),
        "help": (
            "📖 <b>المساعدة والأوامر</b>\n\n"
            "🌤 /now — الطقس الحالي والتوقعات\n"
            "📅 /forecast — توقعات 3 أو 5 أو 7 أيام\n"
            "📍 /location — تغيير الموقع (GPS، مدينة، أو إحداثيات)\n"
            "⚙️ /settings — اللغة، الوحدات، والتنبيهات الفورية\n"
            "❓ /help — عرض هذه القائمة\n\n"
            "💡 <i>تلميح: يمكنك كتابة اسم أي مدينة أو إحداثيات في أي وقت!</i>"
        ),
        "btn_share_loc": "📍 مشاركة الموقع",
        "btn_now": "🌤 الطقس الآن",
        "btn_forecast": "📅 التوقعات",
        "btn_settings": "⚙️ الإعدادات",
        "btn_help": "❓ مساعدة",
        "btn_refresh": "🔄 تحديث",
        "btn_hourly": "🕒 توقعات الساعات",
        "btn_home": "🏠 الرئيسية",
        "btn_back": "« رجوع",
        "searching_place": "🔍 جاري البحث عن الموقع...",
        "place_not_found": "❌ لم يتم العثور على الموقع. جرّب اسم مدينة آخر أو الإحداثيات.",
        "location_saved": "✅ تم حفظ الموقع: <b>{name}</b>",
        "ask_location": "📍 اضغط على الزر بالأسفل لمشاركة موقعك، أو اكتب اسم مدينة، أو أدخل الإحداثيات (مثل <code>36.7538, 3.0588</code>):",
        "no_location": "📍 لم تحدد موقعاً بعد. اكتب اسم مدينة أو شارك موقعك.",
        "fetching_weather": "⏳ جاري جلب بيانات الطقس...",
        "fetch_failed": "⚠️ تعذر جلب الطقس. حاول مرة أخرى لاحقاً.",
        "ask_hour": "⏰ أرسل رقم الساعة (0–23) للتنبيه اليومي (مثال: <code>8</code> أو <code>08:00</code>):",
        "hour_set": "✅ تم ضبط التنبيه اليومي على الساعة <b>{h}:00</b> وتفعيله.",
        "invalid_hour": "⚠️ يرجى إرسال رقم صحيح بين 0 و 23.",
        "settings_title": "⚙️ <b>إعدادات البوت</b>\nخصص تجربتك:",
        "choose_lang": "🌍 اختر اللغة:",
        "choose_units": "🌡️ اختر وحدات القياس:",
        "choose_forecast": "📅 اختر مدة التوقعات:",
        "forecast_days": "📅 <b>توقعات {days} أيام</b>",
        "hourly_title": "🕒 <b>الـ 12 ساعة القادمة</b>",
        "weather_prefix_daily_notice": "⏰ <b>تقرير الطقس الصباحي</b>",
        "severe_alert_title": "🚨 <b>تنبيه طقس فوري</b> في <b>{city}</b>:",
        "feels_like": "الإحساس",
        "uv_index": "الأشعة",
        "sunrise": "الشروق",
        "sunset": "الغروب",
    },
    "fr": {
        "welcome": (
            "👋 Bonjour <b>{name}</b> ! Je suis votre assistant météo.\n\n"
            "📍 <b>Démarrage rapide :</b>\n"
            "• Tapez le nom d'une <b>ville</b> (ex. <i>Alger, Paris</i>)\n"
            "• Ou collez des <b>coordonnées</b> (ex. <code>36.75, 3.04</code>)\n"
            "• Ou appuyez sur <b>📍 Partager ma position</b> ci-dessous"
        ),
        "help": (
            "📖 <b>Aide & Commandes</b>\n\n"
            "🌤 /now — Météo actuelle et prévisions\n"
            "📅 /forecast — Prévisions sur 3, 5 ou 7 jours\n"
            "📍 /location — Changer de lieu (GPS, ville ou lat/lon)\n"
            "⚙️ /settings — Langue, unités, alertes quotidiennes & météo\n"
            "❓ /help — Afficher ce guide\n\n"
            "💡 <i>Astuce : Tapez une ville ou des coordonnées à tout moment !</i>"
        ),
        "btn_share_loc": "📍 Partager ma position",
        "btn_now": "🌤 Météo Actuelle",
        "btn_forecast": "📅 Prévisions",
        "btn_settings": "⚙️ Paramètres",
        "btn_help": "❓ Aide",
        "btn_refresh": "🔄 Actualiser",
        "btn_hourly": "🕒 Heure par heure",
        "btn_home": "🏠 Accueil",
        "btn_back": "« Retour",
        "searching_place": "🔍 Recherche du lieu...",
        "place_not_found": "❌ Lieu introuvable. Essayez une autre ville ou des coordonnées.",
        "location_saved": "✅ Position enregistrée : <b>{name}</b>",
        "ask_location": "📍 Appuyez sur le bouton ci-dessous pour partager votre GPS, tapez une ville ou entrez des coordonnées (ex. <code>36.7538, 3.0588</code>) :",
        "no_location": "📍 Aucune position enregistrée. Tapez une ville ou partagez votre position.",
        "fetching_weather": "⏳ Récupération de la météo...",
        "fetch_failed": "⚠️ Impossible de récupérer la météo. Réessayez plus tard.",
        "ask_hour": "⏰ Envoyez l'heure (0–23) pour l'alerte quotidienne (ex. <code>8</code> ou <code>08:00</code>) :",
        "hour_set": "✅ Alerte quotidienne réglée à <b>{h}:00</b> et activée.",
        "invalid_hour": "⚠️ Veuillez envoyer une heure valide entre 0 et 23.",
        "settings_title": "⚙️ <b>Paramètres</b>\nPersonnalisez votre expérience :",
        "choose_lang": "🌍 Choisissez votre langue :",
        "choose_units": "🌡️ Choisissez les unités :",
        "choose_forecast": "📅 Choisissez la durée :",
        "forecast_days": "📅 <b>Prévisions ({days} jours)</b>",
        "hourly_title": "🕒 <b>Prochaines 12 heures</b>",
        "weather_prefix_daily_notice": "⏰ <b>Bulletin météo matinal</b>",
        "severe_alert_title": "🚨 <b>Alerte météo en temps réel</b> pour <b>{city}</b> :",
        "feels_like": "Ressenti",
        "uv_index": "UV",
        "sunrise": "Lever",
        "sunset": "Coucher",
    },
}


def t(chat_id: int, key: str, **kwargs) -> str:
    lang = get_user_pref(chat_id).get("language", "en")
    text = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, "")
    return text.format(**kwargs) if kwargs else text


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
        language TEXT DEFAULT 'en',
        alerts_enabled INTEGER DEFAULT 1,
        last_alert_sig TEXT DEFAULT ''
    )
    """)
    existing_cols = {row[1] for row in c.execute("PRAGMA table_info(users)").fetchall()}
    if "alerts_enabled" not in existing_cols:
        c.execute("ALTER TABLE users ADD COLUMN alerts_enabled INTEGER DEFAULT 1")
    if "last_alert_sig" not in existing_cols:
        c.execute("ALTER TABLE users ADD COLUMN last_alert_sig TEXT DEFAULT ''")
    conn.commit()
    conn.close()


init_db()


def user_exists(chat_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT 1 FROM users WHERE chat_id=?", (chat_id,))
    exists = c.fetchone() is not None
    conn.close()
    return exists


def save_user(
    chat_id: int,
    loc: Optional[dict] = None,
    units: Optional[str] = None,
    daily: Optional[int] = None,
    daily_hour: Optional[int] = None,
    language: Optional[str] = None,
    alerts_enabled: Optional[int] = None,
    last_alert_sig: Optional[str] = None,
):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO users (chat_id) VALUES (?)", (chat_id,))
        if loc:
            c.execute(
                "UPDATE users SET latitude=?, longitude=?, location_name=?, last_alert_sig='' WHERE chat_id=?",
                (loc["lat"], loc["lon"], loc["name"], chat_id),
            )
        if units:
            c.execute("UPDATE users SET units=? WHERE chat_id=?", (units, chat_id))
        if daily is not None:
            c.execute("UPDATE users SET daily_enabled=? WHERE chat_id=?", (int(bool(daily)), chat_id))
        if daily_hour is not None:
            c.execute("UPDATE users SET daily_hour=? WHERE chat_id=?", (int(daily_hour), chat_id))
        if language:
            c.execute("UPDATE users SET language=? WHERE chat_id=?", (language, chat_id))
        if alerts_enabled is not None:
            c.execute("UPDATE users SET alerts_enabled=? WHERE chat_id=?", (int(bool(alerts_enabled)), chat_id))
        if last_alert_sig is not None:
            c.execute("UPDATE users SET last_alert_sig=? WHERE chat_id=?", (last_alert_sig, chat_id))
        conn.commit()
    except Exception as e:
        logger.error(f"Error saving user data: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


def get_user_pref(chat_id: int) -> Dict[str, Any]:
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "SELECT latitude, longitude, location_name, units, daily_enabled, daily_hour, language, alerts_enabled, last_alert_sig FROM users WHERE chat_id=?",
            (chat_id,),
        )
        row = c.fetchone()
        if not row:
            return {
                "latitude": None,
                "longitude": None,
                "location_name": None,
                "units": "metric",
                "daily_enabled": False,
                "daily_hour": 8,
                "language": "en",
                "alerts_enabled": True,
                "last_alert_sig": "",
            }
        lat, lon, name, units, daily_enabled, daily_hour, language, alerts_enabled, last_alert_sig = row
        return {
            "latitude": lat,
            "longitude": lon,
            "location_name": name,
            "units": units or "metric",
            "daily_enabled": bool(daily_enabled),
            "daily_hour": int(daily_hour) if daily_hour is not None else 8,
            "language": language or "en",
            "alerts_enabled": bool(alerts_enabled) if alerts_enabled is not None else True,
            "last_alert_sig": last_alert_sig or "",
        }
    except Exception as e:
        logger.error(f"Error getting user preferences: {e}")
        return {
            "latitude": None,
            "longitude": None,
            "location_name": None,
            "units": "metric",
            "daily_enabled": False,
            "daily_hour": 8,
            "language": "en",
            "alerts_enabled": True,
            "last_alert_sig": "",
        }
    finally:
        if conn:
            conn.close()


@dataclass
class Location:
    lat: float
    lon: float
    name: str


def parse_coordinates(text: str) -> Optional[Tuple[float, float]]:
    match = re.match(r"^\s*(-?\d{1,2}(?:\.\d+)?)\s*[,;\s]\s*(-?\d{1,3}(?:\.\d+)?)\s*$", text)
    if not match:
        return None
    lat, lon = float(match.group(1)), float(match.group(2))
    if -90 <= lat <= 90 and -180 <= lon <= 180:
        return lat, lon
    return None


def reverse_geocode(lat: float, lon: float, accept_language: str = "en") -> str:
    key = f"rev:{lat:.3f},{lon:.3f}__{accept_language}"
    if key in geocode_cache:
        return geocode_cache[key]
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {"lat": lat, "lon": lon, "format": "json", "zoom": 10}
    headers = {"User-Agent": "TelegramWeatherBot/2.0", "Accept-Language": accept_language}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=8)
        r.raise_for_status()
        data = r.json()
        addr = data.get("address", {})
        city = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("state")
        country = addr.get("country")
        if city and country:
            name = f"{city}, {country}"
        else:
            name = data.get("display_name", f"{lat:.4f}, {lon:.4f}")
        geocode_cache[key] = name
        return name
    except Exception:
        return f"{lat:.4f}, {lon:.4f}"


def geocode_place(query: str, accept_language: str = "en") -> Optional[Location]:
    coords = parse_coordinates(query)
    if coords:
        lat, lon = coords
        name = reverse_geocode(lat, lon, accept_language)
        return Location(lat=lat, lon=lon, name=name)

    key = f"{query.lower()}__{accept_language}"
    if key in geocode_cache:
        v = geocode_cache[key]
        return Location(lat=v["lat"], lon=v["lon"], name=v["name"])

    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": query, "format": "json", "limit": 1}
    headers = {"User-Agent": "TelegramWeatherBot/2.0", "Accept-Language": accept_language}
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
    precip_unit = "inch" if units == "imperial" else "mm"
    daily_vars = "temperature_2m_max,temperature_2m_min,weathercode,precipitation_sum,sunrise,sunset,uv_index_max"
    current_vars = "temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,weathercode,windspeed_10m,pressure_msl"
    hourly_vars = "temperature_2m,weathercode,precipitation_probability"
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": current_vars,
        "hourly": hourly_vars,
        "daily": daily_vars,
        "timezone": "auto",
        "temperature_unit": temp_unit,
        "windspeed_unit": wind_unit,
        "precipitation_unit": precip_unit,
        "forecast_days": max(days, 1),
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        logger.exception("weather fetch failed")
        return None


WEATHER_CODES = {
    0: ("☀️ Clear", "☀️ صافٍ", "☀️ Dégagé"),
    1: ("🌤 Mostly clear", "🌤 صافٍ غالباً", "🌤 Plutôt dégagé"),
    2: ("⛅ Partly cloudy", "⛅ غائم جزئياً", "⛅ Partiellement nuageux"),
    3: ("☁️ Overcast", "☁️ غائم", "☁️ Couvert"),
    45: ("🌫 Fog", "🌫 ضباب", "🌫 Brouillard"),
    48: ("🌫 Rime fog", "🌫 ضباب متجمد", "🌫 Brouillard givrant"),
    51: ("🌦 Light drizzle", "🌦 رذاذ خفيف", "🌦 Bruine légère"),
    53: ("🌧 Moderate drizzle", "🌧 رذاذ معتدل", "🌧 Bruine modérée"),
    55: ("🌧 Dense drizzle", "🌧 رذاذ كثيف", "🌧 Bruine dense"),
    61: ("🌦 Slight rain", "🌦 مطر خفيف", "🌦 Pluie légère"),
    63: ("🌧 Moderate rain", "🌧 مطر معتدل", "🌧 Pluie modérée"),
    65: ("🌧 Heavy rain", "🌧 مطر غزير", "🌧 Forte pluie"),
    71: ("🌨 Slight snow", "🌨 ثلوج خفيفة", "🌨 Neige légère"),
    73: ("🌨 Moderate snow", "🌨 ثلوج معتدلة", "🌨 Neige modérée"),
    75: ("❄️ Heavy snow", "❄️ ثلوج كثيفة", "❄️ Fortes chutes de neige"),
    80: ("🌦 Rain showers", "🌦 زخات مطر", "🌦 Averses"),
    81: ("🌧 Moderate showers", "🌧 زخات مطر معتدلة", "🌧 Averses modérées"),
    82: ("🌧 Violent showers", "🌧 زخات مطر عنيفة", "🌧 Averses violentes"),
    95: ("⛈ Thunderstorm", "⛈ عاصفة رعدية", "⛈ Orage"),
    96: ("⛈ Thunderstorm & hail", "⛈ عاصفة رعدية وبَرَد", "⛈ Orage et grêle"),
    99: ("⛈ Severe thunderstorm", "⛈ عاصفة رعدية شديدة", "⛈ Orage violent"),
}


def describe_weather_code(code: int, lang: str = "en") -> str:
    idx = 1 if lang == "ar" else 2 if lang == "fr" else 0
    entry = WEATHER_CODES.get(code)
    return entry[idx] if entry else "🌈 Weather"


def format_current_and_forecast(data: dict, loc_name: str, units: str, days: int = 3, lang: str = "en") -> str:
    lines = []
    current = data.get("current", {})
    daily = data.get("daily", {})
    timezone = data.get("timezone", "UTC")
    unit_symbol = "F" if units == "imperial" else "C"
    wind_unit = "mph" if units == "imperial" else "km/h"
    precip_unit = "in" if units == "imperial" else "mm"
    tr = TRANSLATIONS.get(lang, TRANSLATIONS["en"])

    city_name = loc_name.split(",")[0].strip() if "," in loc_name else loc_name

    if current:
        temp = current.get("temperature_2m")
        feels = current.get("apparent_temperature")
        wind = current.get("windspeed_10m")
        wc = current.get("weathercode")
        humidity = current.get("relative_humidity_2m")
        pressure = current.get("pressure_msl")
        precip = current.get("precipitation")

        lines.append(f"📍 <b>{city_name}</b>  •  🕐 {timezone.split('/')[-1].replace('_', ' ')}")
        lines.append("━━━━━━━━━━━━━━━━━━━━━")
        lines.append(f"<b>🌡 {temp}°{unit_symbol}</b>  {describe_weather_code(wc, lang)}")
        if feels is not None:
            lines.append(f"🤒 {tr['feels_like']}: <b>{feels}°{unit_symbol}</b>")
        lines.append("")

        details = [f"💨 {wind} {wind_unit}"]
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
    uv_max = daily.get("uv_index_max", [])

    if dates:
        lines.append("─────────────────────")
        lines.append(tr["forecast_days"].format(days=days))
        lines.append("─────────────────────")

        for i, d in enumerate(dates[:days]):
            date_obj = datetime.datetime.strptime(d, "%Y-%m-%d")
            day_name = date_obj.strftime("%a, %b %d")
            temp_range = f"{int(tmin[i])}° ─ {int(tmax[i])}°"
            condition = describe_weather_code(codes[i], lang)

            lines.append(f"<b>{day_name}</b> • {condition}")
            temp_line = f"  🌡 {temp_range}"
            if precip_sum and i < len(precip_sum) and precip_sum[i] > 0:
                temp_line += f"  │  ☔ {precip_sum[i]}{precip_unit}"
            if i == 0 and uv_max and uv_max[0] is not None:
                temp_line += f"  │  ☀️ {tr['uv_index']}: {uv_max[0]}"
            lines.append(temp_line)

            if i == 0 and sunrise and sunset:
                try:
                    sr_time = sunrise[0].split("T")[1][:5]
                    ss_time = sunset[0].split("T")[1][:5]
                    lines.append(f"  🌅 {tr['sunrise']}: {sr_time}  │  🌇 {tr['sunset']}: {ss_time}")
                except Exception:
                    pass

            if i < min(days, len(dates)) - 1:
                lines.append("")

    return "\n".join(lines)


def format_hourly_forecast(data: dict, loc_name: str, units: str, lang: str = "en") -> str:
    tr = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    unit_symbol = "F" if units == "imperial" else "C"
    city_name = loc_name.split(",")[0].strip() if "," in loc_name else loc_name
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    codes = hourly.get("weathercode", [])
    probs = hourly.get("precipitation_probability", [])

    current_time_str = data.get("current", {}).get("time", "")
    start_idx = 0
    if current_time_str and times:
        prefix = current_time_str[:13]
        for idx, tm in enumerate(times):
            if tm.startswith(prefix):
                start_idx = idx
                break

    lines = [f"📍 <b>{city_name}</b> — {tr['hourly_title']}", "━━━━━━━━━━━━━━━━━━━━━"]
    for i in range(start_idx, min(start_idx + 12, len(times))):
        hour_str = times[i].split("T")[1][:5]
        cond = describe_weather_code(codes[i], lang)
        prob_str = f"  💧{probs[i]}%" if i < len(probs) and probs[i] is not None else ""
        lines.append(f"<code>{hour_str}</code>  <b>{temps[i]}°{unit_symbol}</b>  {cond}{prob_str}")

    return "\n".join(lines)


def build_home_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(t(chat_id, "btn_now"), callback_data="quick_now"),
            InlineKeyboardButton(t(chat_id, "btn_forecast"), callback_data="quick_fc"),
        ],
        [
            InlineKeyboardButton(t(chat_id, "btn_share_loc"), callback_data="prompt_location"),
        ],
        [
            InlineKeyboardButton(t(chat_id, "btn_settings"), callback_data="back_to_settings"),
            InlineKeyboardButton(t(chat_id, "btn_help"), callback_data="show_help"),
        ],
    ])


def build_weather_keyboard(chat_id: int, active_days: int = 3) -> InlineKeyboardMarkup:
    lang = get_user_pref(chat_id).get("language", "en")
    tr = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    day_buttons = []
    for d in (3, 5, 7):
        label = f"• {d}d •" if d == active_days else f"{d}d"
        day_buttons.append(InlineKeyboardButton(label, callback_data=f"fc_{d}"))
    return InlineKeyboardMarkup([
        day_buttons,
        [
            InlineKeyboardButton(tr["btn_hourly"], callback_data="view_hourly"),
            InlineKeyboardButton(tr["btn_refresh"], callback_data=f"refresh_{active_days}"),
        ],
        [
            InlineKeyboardButton(tr["btn_home"], callback_data="back_home"),
        ],
    ])


def build_settings_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    prefs = get_user_pref(chat_id)
    lang = prefs.get("language", "en")
    units = prefs.get("units", "metric")
    daily_enabled = prefs.get("daily_enabled", False)
    daily_hour = prefs.get("daily_hour", 8)
    alerts_enabled = prefs.get("alerts_enabled", True)

    units_display = "°C" if units == "metric" else "°F"
    daily_text = f"⏰ Daily: ON ({daily_hour}:00)" if daily_enabled else "⏰ Daily: OFF"
    alerts_text = f"🚨 Severe Alerts: {'ON' if alerts_enabled else 'OFF'}"

    kb = [
        [InlineKeyboardButton("🌍 " + ("Language" if lang == "en" else "اللغة" if lang == "ar" else "Langue"), callback_data="set_lang")],
        [InlineKeyboardButton(f"🌡️ Units: {units_display}", callback_data="set_units")],
        [InlineKeyboardButton(daily_text, callback_data="set_daily")],
        [InlineKeyboardButton(alerts_text, callback_data="toggle_alerts")],
        [InlineKeyboardButton("📍 Change Location", callback_data="prompt_location")],
        [InlineKeyboardButton(t(chat_id, "btn_home"), callback_data="back_home")],
    ]
    return InlineKeyboardMarkup(kb)


def compact_location_keyboard(chat_id: int) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[KeyboardButton(t(chat_id, "btn_share_loc"), request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def throttle(chat_id: int, action: str, interval: float = 0.6) -> bool:
    key = f"{chat_id}:{action}"
    now = datetime.datetime.now(datetime.timezone.utc).timestamp()
    if now - recent_button_hits.get(key, 0) < interval:
        return False
    recent_button_hits[key] = now
    return True


async def send_weather_card(target, chat_id: int, days: int = 3, edit: bool = False):
    prefs = get_user_pref(chat_id)
    if not prefs.get("latitude"):
        msg = t(chat_id, "no_location")
        if edit:
            await target.edit_message_text(msg, reply_markup=build_home_keyboard(chat_id))
        else:
            await target.reply_text(msg, reply_markup=compact_location_keyboard(chat_id))
        return

    data = fetch_weather(prefs["latitude"], prefs["longitude"], units=prefs["units"], days=days)
    if not data:
        err = t(chat_id, "fetch_failed")
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(t(chat_id, "btn_home"), callback_data="back_home")]])
        if edit:
            await target.edit_message_text(err, reply_markup=kb)
        else:
            await target.reply_text(err, reply_markup=kb)
        return

    txt = format_current_and_forecast(
        data, prefs["location_name"] or "Your Location", units=prefs["units"], days=days, lang=prefs["language"]
    )
    kb = build_weather_keyboard(chat_id, active_days=days)
    if edit:
        await target.edit_message_text(txt, parse_mode="HTML", reply_markup=kb)
    else:
        await target.reply_html(txt, reply_markup=kb)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    name = user.first_name or "there"

    if not user_exists(chat.id):
        tg_lang = (user.language_code or "en")[:2].lower()
        detected = tg_lang if tg_lang in ("en", "ar", "fr") else "en"
        save_user(chat.id, language=detected)

    await update.message.reply_html(
        t(chat.id, "welcome", name=name),
        reply_markup=build_home_keyboard(chat.id),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(t(update.effective_chat.id, "btn_now"), callback_data="quick_now"),
            InlineKeyboardButton(t(update.effective_chat.id, "btn_home"), callback_data="back_home"),
        ]
    ])
    await update.message.reply_html(t(update.effective_chat.id, "help"), reply_markup=kb)


async def location_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    pending_action[chat_id] = "set_location"
    await update.message.reply_html(
        t(chat_id, "ask_location"),
        reply_markup=compact_location_keyboard(chat_id),
    )


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_html(t(chat_id, "settings_title"), reply_markup=build_settings_keyboard(chat_id))


async def handle_location_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    loc_obj = update.message.location
    if not loc_obj:
        return
    lang = get_user_pref(chat_id).get("language", "en")
    resolved_name = reverse_geocode(loc_obj.latitude, loc_obj.longitude, accept_language=lang)
    loc = {"lat": loc_obj.latitude, "lon": loc_obj.longitude, "name": resolved_name}
    save_user(chat_id, loc=loc)
    pending_action.pop(chat_id, None)

    await update.message.reply_html(
        t(chat_id, "location_saved", name=resolved_name),
        reply_markup=ReplyKeyboardRemove(),
    )
    await send_weather_card(update.message, chat_id, days=3, edit=False)


def parse_hour_from_text(text: str) -> Optional[int]:
    m = re.search(r"\b([0-1]?\d|2[0-3])\b", text.strip())
    if m:
        val = int(m.group(1))
        if 0 <= val <= 23:
            return val
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
            for j in context.job_queue.get_jobs_by_name(str(chat_id)):
                j.schedule_removal()
            context.job_queue.run_daily(
                send_daily_weather, time=datetime.time(h, 0), chat_id=chat_id, name=str(chat_id)
            )
        pending_action.pop(chat_id, None)
        await update.message.reply_html(t(chat_id, "hour_set", h=h), reply_markup=ReplyKeyboardRemove())
        await update.message.reply_html(t(chat_id, "settings_title"), reply_markup=build_settings_keyboard(chat_id))
        return

    if text.startswith("/"):
        return

    status_msg = await update.message.reply_text(t(chat_id, "searching_place"))
    loc = geocode_place(text, accept_language=user_lang)
    if not loc:
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(t(chat_id, "btn_home"), callback_data="back_home")]])
        await status_msg.edit_text(t(chat_id, "place_not_found"), reply_markup=kb)
        return

    save_user(chat_id, loc={"lat": loc.lat, "lon": loc.lon, "name": loc.name})
    pending_action.pop(chat_id, None)
    await status_msg.edit_text(t(chat_id, "location_saved", name=loc.name), parse_mode="HTML")
    await send_weather_card(update.message, chat_id, days=3, edit=False)


async def now_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_weather_card(update.message, update.effective_chat.id, days=3, edit=False)


async def forecast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        t(chat_id, "choose_forecast"),
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("3 Days", callback_data="fc_new_3"),
                InlineKeyboardButton("5 Days", callback_data="fc_new_5"),
                InlineKeyboardButton("7 Days", callback_data="fc_new_7"),
            ],
            [InlineKeyboardButton(t(chat_id, "btn_home"), callback_data="back_home")],
        ]),
    )


async def forecastX_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cmd = update.message.text.strip().lower()
    days = 3 if cmd.endswith("3") else 5 if cmd.endswith("5") else 7
    await send_weather_card(update.message, update.effective_chat.id, days=days, edit=False)


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    chat_id = query.message.chat_id
    if not throttle(chat_id, data):
        return
    prefs = get_user_pref(chat_id)

    if data == "show_help":
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(t(chat_id, "btn_home"), callback_data="back_home")]])
        await query.edit_message_text(t(chat_id, "help"), parse_mode="HTML", reply_markup=kb)
        return

    if data == "back_home":
        name = query.from_user.first_name or "there"
        await query.edit_message_text(
            t(chat_id, "welcome", name=name),
            parse_mode="HTML",
            reply_markup=build_home_keyboard(chat_id),
        )
        return

    if data == "quick_now":
        await send_weather_card(query, chat_id, days=3, edit=True)
        return

    if data == "quick_fc":
        await query.edit_message_text(
            t(chat_id, "choose_forecast"),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("3 Days", callback_data="fc_3"),
                    InlineKeyboardButton("5 Days", callback_data="fc_5"),
                    InlineKeyboardButton("7 Days", callback_data="fc_7"),
                ],
                [InlineKeyboardButton(t(chat_id, "btn_home"), callback_data="back_home")],
            ]),
        )
        return

    if data.startswith("fc_new_"):
        days = int(data.split("_")[2])
        await send_weather_card(query, chat_id, days=days, edit=True)
        return

    if data.startswith("fc_"):
        days = int(data.split("_")[1])
        await send_weather_card(query, chat_id, days=days, edit=True)
        return

    if data.startswith("refresh_"):
        days = int(data.split("_")[1])
        await send_weather_card(query, chat_id, days=days, edit=True)
        return

    if data == "view_hourly":
        if not prefs.get("latitude"):
            await query.edit_message_text(t(chat_id, "no_location"), reply_markup=build_home_keyboard(chat_id))
            return
        dataw = fetch_weather(prefs["latitude"], prefs["longitude"], units=prefs["units"], days=1)
        if not dataw:
            await query.edit_message_text(t(chat_id, "fetch_failed"), reply_markup=build_home_keyboard(chat_id))
            return
        txt = format_hourly_forecast(dataw, prefs["location_name"] or "Your Location", prefs["units"], prefs["language"])
        kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(t(chat_id, "btn_back"), callback_data="fc_3"),
                InlineKeyboardButton(t(chat_id, "btn_home"), callback_data="back_home"),
            ]
        ])
        await query.edit_message_text(txt, parse_mode="HTML", reply_markup=kb)
        return

    if data == "prompt_location":
        pending_action[chat_id] = "set_location"
        await query.message.reply_html(t(chat_id, "ask_location"), reply_markup=compact_location_keyboard(chat_id))
        return

    if data == "toggle_alerts":
        new_state = not prefs.get("alerts_enabled", True)
        save_user(chat_id, alerts_enabled=1 if new_state else 0)
        await query.edit_message_text(
            t(chat_id, "settings_title"), parse_mode="HTML", reply_markup=build_settings_keyboard(chat_id)
        )
        return

    if data.startswith("units_"):
        units = "metric" if data == "units_metric" else "imperial"
        save_user(chat_id, units=units)
        await query.edit_message_text(
            t(chat_id, "settings_title"), parse_mode="HTML", reply_markup=build_settings_keyboard(chat_id)
        )
        return

    if data == "set_lang":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("English 🇬🇧", callback_data="lang_en"), InlineKeyboardButton("العربية 🇩🇿", callback_data="lang_ar")],
            [InlineKeyboardButton("Français 🇫🇷", callback_data="lang_fr")],
            [
                InlineKeyboardButton(t(chat_id, "btn_back"), callback_data="back_to_settings"),
                InlineKeyboardButton(t(chat_id, "btn_home"), callback_data="back_home"),
            ],
        ])
        await query.edit_message_text(t(chat_id, "choose_lang"), reply_markup=kb)
        return

    if data.startswith("lang_"):
        save_user(chat_id, language=data.split("_")[1])
        await query.edit_message_text(
            t(chat_id, "settings_title"), parse_mode="HTML", reply_markup=build_settings_keyboard(chat_id)
        )
        return

    if data == "set_units":
        current = prefs["units"]
        kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("°C (Metric)" + (" ✓" if current == "metric" else ""), callback_data="units_metric"),
                InlineKeyboardButton("°F (Imperial)" + (" ✓" if current == "imperial" else ""), callback_data="units_imperial"),
            ],
            [
                InlineKeyboardButton(t(chat_id, "btn_back"), callback_data="back_to_settings"),
                InlineKeyboardButton(t(chat_id, "btn_home"), callback_data="back_home"),
            ],
        ])
        await query.edit_message_text(t(chat_id, "choose_units"), reply_markup=kb)
        return

    if data == "set_daily":
        enabled = prefs["daily_enabled"]
        hour = prefs.get("daily_hour", 8)
        status = f"Status: <b>{'ON' if enabled else 'OFF'}</b>" + (f" at {hour}:00" if enabled else "")
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"Toggle: {'ON' if enabled else 'OFF'} 🔁", callback_data="toggle_daily")],
            [InlineKeyboardButton("Set hour ⏰", callback_data="set_daily_hour")],
            [
                InlineKeyboardButton(t(chat_id, "btn_back"), callback_data="back_to_settings"),
                InlineKeyboardButton(t(chat_id, "btn_home"), callback_data="back_home"),
            ],
        ])
        await query.edit_message_text(f"⏰ <b>Daily Alert</b>\n\n{status}", parse_mode="HTML", reply_markup=kb)
        return

    if data == "toggle_daily":
        enabled = not prefs["daily_enabled"]
        save_user(chat_id, daily=1 if enabled else 0)
        if context.job_queue:
            for j in context.job_queue.get_jobs_by_name(str(chat_id)):
                j.schedule_removal()
            if enabled:
                h = prefs.get("daily_hour", 8)
                context.job_queue.run_daily(
                    send_daily_weather, time=datetime.time(h, 0), chat_id=chat_id, name=str(chat_id)
                )
        hour = prefs.get("daily_hour", 8)
        status = f"Status: <b>{'ON' if enabled else 'OFF'}</b>" + (f" at {hour}:00" if enabled else "")
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"Toggle: {'ON' if enabled else 'OFF'} 🔁", callback_data="toggle_daily")],
            [InlineKeyboardButton("Set hour ⏰", callback_data="set_daily_hour")],
            [
                InlineKeyboardButton(t(chat_id, "btn_back"), callback_data="back_to_settings"),
                InlineKeyboardButton(t(chat_id, "btn_home"), callback_data="back_home"),
            ],
        ])
        await query.edit_message_text(f"⏰ <b>Daily Alert</b>\n\n{status}", parse_mode="HTML", reply_markup=kb)
        return

    if data == "set_daily_hour":
        pending_action[chat_id] = "set_hour"
        await query.edit_message_text(t(chat_id, "ask_hour"), parse_mode="HTML")
        return

    if data == "back_to_settings":
        await query.edit_message_text(
            t(chat_id, "settings_title"), parse_mode="HTML", reply_markup=build_settings_keyboard(chat_id)
        )
        return


async def send_daily_weather(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    prefs = get_user_pref(chat_id)
    if not prefs or not prefs.get("latitude"):
        return
    data = fetch_weather(prefs["latitude"], prefs["longitude"], units=prefs["units"], days=3)
    if not data:
        return
    header = t(chat_id, "weather_prefix_daily_notice")
    txt = format_current_and_forecast(
        data, prefs["location_name"] or "Your Location", units=prefs["units"], days=3, lang=prefs["language"]
    )
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"{header}\n\n{txt}",
        parse_mode="HTML",
        reply_markup=build_weather_keyboard(chat_id, 3),
    )


def evaluate_severe_weather(data: dict, units: str, lang: str) -> Optional[Tuple[str, str]]:
    current = data.get("current", {})
    if not current:
        return None
    wc = current.get("weathercode", 0)
    temp = current.get("temperature_2m", 20)
    wind = current.get("windspeed_10m", 0)

    temp_c = (temp - 32) * 5 / 9 if units == "imperial" else temp
    wind_kmh = wind * 1.60934 if units == "imperial" else wind

    warnings = []
    sig_parts = []

    if wc in (65, 67, 75, 82, 86, 95, 96, 99):
        warnings.append(describe_weather_code(wc, lang))
        sig_parts.append(f"wc:{wc}")
    if wind_kmh >= 60:
        msg = f"💨 Strong winds ({wind} {'mph' if units == 'imperial' else 'km/h'})"
        warnings.append(msg)
        sig_parts.append("wind_high")
    if temp_c >= 40:
        msg = f"🔥 Extreme heat ({temp}°{'F' if units == 'imperial' else 'C'})"
        warnings.append(msg)
        sig_parts.append("heat_high")
    elif temp_c <= -5:
        msg = f"🥶 Freezing cold ({temp}°{'F' if units == 'imperial' else 'C'})"
        warnings.append(msg)
        sig_parts.append("cold_low")

    if not warnings:
        return None
    return "|".join(sig_parts), "\n".join(f"• {w}" for w in warnings)


async def check_severe_weather_alerts(context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT chat_id, latitude, longitude, location_name, units, language, last_alert_sig FROM users WHERE alerts_enabled=1 AND latitude IS NOT NULL"
    )
    rows = c.fetchall()
    conn.close()

    for chat_id, lat, lon, loc_name, units, lang, last_sig in rows:
        data = fetch_weather(lat, lon, units=units or "metric", days=1)
        if not data:
            continue
        res = evaluate_severe_weather(data, units or "metric", lang or "en")
        if not res:
            if last_sig:
                save_user(chat_id, last_alert_sig="")
            continue

        sig, body = res
        if sig != last_sig:
            save_user(chat_id, last_alert_sig=sig)
            city = (loc_name or "Your Location").split(",")[0].strip()
            title = TRANSLATIONS.get(lang or "en", TRANSLATIONS["en"])["severe_alert_title"].format(city=city)
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"{title}\n\n{body}",
                    parse_mode="HTML",
                    reply_markup=build_weather_keyboard(chat_id, 3),
                )
            except Exception as e:
                logger.warning(f"Failed to send alert to {chat_id}: {e}")


async def post_init(application: Application):
    await application.bot.set_my_commands([
        BotCommand("start", "Start & quick menu"),
        BotCommand("now", "Current weather"),
        BotCommand("forecast", "3, 5, or 7-day forecast"),
        BotCommand("location", "Set location (GPS, city, lat/lon)"),
        BotCommand("settings", "Language, units & alerts"),
        BotCommand("help", "Help & instructions"),
    ])

    if application.job_queue:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT chat_id, daily_enabled, daily_hour FROM users WHERE daily_enabled=1")
        rows = c.fetchall()
        conn.close()
        for chat_id, _, hour in rows:
            try:
                h = int(hour) if hour is not None else 8
                application.job_queue.run_daily(
                    send_daily_weather, time=datetime.time(h, 0), chat_id=int(chat_id), name=str(chat_id)
                )
            except Exception:
                logger.exception("Failed to schedule job for user %s", chat_id)

        application.job_queue.run_repeating(check_severe_weather_alerts, interval=7200, first=60)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)


def main():
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("location", location_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CommandHandler("now", now_command))
    application.add_handler(CommandHandler("forecast", forecast_command))
    application.add_handler(CommandHandler("forecast3", forecastX_command))
    application.add_handler(CommandHandler("forecast5", forecastX_command))
    application.add_handler(CommandHandler("forecast7", forecastX_command))
    application.add_handler(MessageHandler(filters.LOCATION, handle_location_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(CallbackQueryHandler(callback_handler))
    application.add_error_handler(error_handler)
    application.run_polling()


if __name__ == "__main__":
    main()