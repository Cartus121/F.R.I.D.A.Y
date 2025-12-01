"""
Translations for F.R.I.D.A.Y.
Supports English and Russian
"""

TRANSLATIONS = {
    "en": {
        # Window
        "app_title": "{ai_name} - AI Assistant",
        "app_name": "{ai_name}",
        "subtitle": "AI Voice Assistant",
        
        # Status
        "sleeping": "Standing by",
        "listening": "Listening",
        "waiting_wake": "Awaiting command",
        "processing": "Processing...",
        "ready": "Online",
        "offline": "Offline",
        
        # Chat
        "welcome": "Systems online. {ai_name} ready.",
        "wake_hint": "Say '{wake_word}' when you need me.",
        "mic_off": "Voice input disabled",
        "mic_on": "Voice input active. Say '{wake_word}' when you need me.",
        "mic_unavailable": "Voice input unavailable",
        "voice_active": "Voice recognition active. Standing by for your command.",
        "voice_unavailable": "Voice systems offline. Text input available.",
        
        # Input
        "placeholder": "Type a command or use voice...",
        "send": "Send",
        "mic": "🎤",
        
        # Settings
        "settings_title": "⚙️ {ai_name} Settings",
        "api_key_label": "OpenAI API Key (required):",
        "weather_key_label": "OpenWeather API Key (optional):",
        "language_label": "Language:",
        "voice_label": "Voice:",
        "wake_word_label": "Wake Word:",
        "api_help": "Get your API key at:\nhttps://platform.openai.com/api-keys",
        "weather_help": "Get weather API key at:\nhttps://openweathermap.org/api",
        "save": "Save",
        "cancel": "Cancel",
        "invalid_key": "⚠️ Invalid API key format",
        "settings_saved": "Configuration updated.",
        
        # Voice options
        "voice_friday": "F.R.I.D.A.Y. (Irish Female)",
        
        # Reminders & Timers
        "reminder": "Reminder",
        "reminder_alert": "⏰ Reminder: {message}",
        "timer_set": "Timer set for {duration}.",
        "timer_done": "⏰ Time's up.",
        "timer_cancelled": "Timer cancelled.",
        
        # Responses
        "wake_response": "Yes? What do you need?",
        "goodbye": "Standing by. Say '{wake_word}' when you need me.",
        "thanks_response": "Of course.",
        "understood": "Understood.",
        "right_away": "Right away.",
        "consider_it_done": "Consider it done.",
        "working_on_it": "Working on it.",
        "online_ready": "{ai_name} online. Say '{wake_word}' when you need me.",
        
        # System tray
        "tray_show": "Show {ai_name}",
        "tray_settings": "Settings",
        "tray_quit": "Quit",
        "tray_listening": "Listening...",
        "tray_standby": "Standing by",
        
        # Errors
        "error_api": "I'm having trouble connecting to my systems.",
        "error_weather": "Weather data unavailable.",
        "error_generic": "Something went wrong. I'll look into it.",
        
        # Calculations & Conversions
        "calc_result": "That's {result}.",
        "conversion_result": "{value} {from_unit} is {result} {to_unit}.",
    },
    
    "ru": {
        # Window
        "app_title": "{ai_name} - ИИ Ассистент",
        "app_name": "{ai_name}",
        "subtitle": "Умный Голосовой Помощник",
        
        # Status
        "sleeping": "Режим ожидания",
        "listening": "Слушаю",
        "waiting_wake": "Ожидаю команду",
        "processing": "Обрабатываю...",
        "ready": "В сети",
        "offline": "Не в сети",
        
        # Chat
        "welcome": "Системы в сети. {ai_name} готов к работе.",
        "wake_hint": "Скажите '{wake_word}' когда понадоблюсь.",
        "mic_off": "Голосовой ввод отключен",
        "mic_on": "Голосовой ввод активен. Скажите '{wake_word}' когда понадоблюсь.",
        "mic_unavailable": "Голосовой ввод недоступен",
        "voice_active": "Голосовое управление активно. Ожидаю вашу команду.",
        "voice_unavailable": "Голосовые системы недоступны. Используйте текстовый ввод.",
        
        # Input
        "placeholder": "Введите команду или используйте голос...",
        "send": "Отпр.",
        "mic": "🎤",
        
        # Settings
        "settings_title": "⚙️ Настройки {ai_name}",
        "api_key_label": "API Ключ OpenAI (обязательно):",
        "weather_key_label": "API Ключ OpenWeather (опционально):",
        "language_label": "Язык:",
        "voice_label": "Голос:",
        "wake_word_label": "Слово активации:",
        "api_help": "Получить API ключ:\nhttps://platform.openai.com/api-keys",
        "weather_help": "Получить ключ погоды:\nhttps://openweathermap.org/api",
        "save": "Сохранить",
        "cancel": "Отмена",
        "invalid_key": "⚠️ Неверный формат API ключа",
        "settings_saved": "Настройки обновлены.",
        
        # Voice options
        "voice_friday": "Ф.Р.А.Й.Д.Э.Й. (Ирландский женский)",
        
        # Reminders & Timers
        "reminder": "Напоминание",
        "reminder_alert": "⏰ Напоминание: {message}",
        "timer_set": "Таймер установлен на {duration}.",
        "timer_done": "⏰ Время вышло.",
        "timer_cancelled": "Таймер отменен.",
        
        # Responses
        "wake_response": "Да? Что вам нужно?",
        "goodbye": "Режим ожидания. Скажите '{wake_word}' когда понадоблюсь.",
        "thanks_response": "Конечно.",
        "understood": "Понятно.",
        "right_away": "Сейчас сделаю.",
        "consider_it_done": "Считайте, что сделано.",
        "working_on_it": "Работаю над этим.",
        "online_ready": "{ai_name} в сети. Скажите '{wake_word}' когда понадоблюсь.",
        
        # System tray
        "tray_show": "Показать {ai_name}",
        "tray_settings": "Настройки",
        "tray_quit": "Выход",
        "tray_listening": "Слушаю...",
        "tray_standby": "Режим ожидания",
        
        # Errors
        "error_api": "Проблемы с подключением к системам.",
        "error_weather": "Данные о погоде недоступны.",
        "error_generic": "Что-то пошло не так. Разберусь.",
        
        # Calculations & Conversions
        "calc_result": "Это {result}.",
        "conversion_result": "{value} {from_unit} это {result} {to_unit}.",
    }
}


def get_text(key: str, lang: str = "en", **kwargs) -> str:
    """Get translated text with placeholder support"""
    translations = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    text = translations.get(key, TRANSLATIONS["en"].get(key, key))
    
    # Get AI name from settings (avoid circular imports)
    ai_name = "F.R.I.D.A.Y."
    wake_word = "friday"
    try:
        from settings import load_settings, AI_NAMES
        settings = load_settings()
        voice = settings.get("voice", "F.R.I.D.A.Y. (Irish Female)")
        ai_name = AI_NAMES.get(voice, settings.get("ai_name", "F.R.I.D.A.Y."))
        wake_word = settings.get("wake_word", "friday")
    except Exception:
        pass
    
    # Set default values for common placeholders
    defaults = {
        "wake_word": wake_word,
        "ai_name": ai_name,
    }
    
    # Merge defaults with provided kwargs
    for k, v in defaults.items():
        if k not in kwargs:
            kwargs[k] = v
    
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, ValueError):
            pass
    
    return text


def get_language() -> str:
    """Get current language from settings"""
    try:
        from settings import load_settings
        settings = load_settings()
        lang = settings.get("language", "en")
        if lang == "auto":
            return "en"  # Default to English for auto
        return lang
    except:
        return "en"
