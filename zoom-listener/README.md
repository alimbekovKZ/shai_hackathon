# Zoom Meeting Recorder

Автоматизированная система записи встреч Zoom с поддержкой транскрипции и API управления. Используется для записи аудио встреч и последующей обработки через AI pipeline.

## 🌟 Особенности

- ✅ **Автоматическое подключение** к встречам Zoom
- ✅ **Запись аудио** в реальном времени (формат WAV, 32kHz)
- ✅ **FastAPI сервер** для управления записями
- ✅ **CLI интерфейс** для запуска ботов
- ✅ **Deepgram интеграция** для транскрипции в реальном времени
- ✅ **Множественные встречи** одновременно
- ✅ **Безопасное завершение** с сохранением данных

## 🏗️ Архитектура

```
zoom-listener/
├── api.py                 # FastAPI сервер для HTTP API
├── cli.py                 # Командная строка для запуска ботов
├── meeting_bot.py         # Основной класс MeetingBot
├── deepgram_transcriber.py # Интеграция с Deepgram
├── main.py               # Простой запуск без параметров
├── test_api.py           # Тесты API
└── requirements.txt      # Python зависимости
```

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка Zoom SDK

**Скачайте Zoom Meeting SDK:**
1. Зарегистрируйтесь на [Zoom Marketplace](https://marketplace.zoom.us/)
2. Создайте Meeting SDK App
3. Скачайте SDK для Linux
4. Установите в систему:

```bash
# Установка системных зависимостей
sudo apt-get install libasound2-dev python3-gi python3-gi-cairo gir1.2-gtk-3.0

# Настройка переменных окружения
export LD_LIBRARY_PATH=/path/to/zoom/sdk/lib:$LD_LIBRARY_PATH
```

### 3. Конфигурация

Создайте файл `.env`:
```env
# Zoom App Credentials
ZOOM_APP_CLIENT_ID=your_zoom_client_id
ZOOM_APP_CLIENT_SECRET=your_zoom_client_secret

# Опциональные настройки
DEEPGRAM_API_KEY=your_deepgram_key  # Для транскрипции
RECORD_VIDEO=false                  # Запись видео (экспериментально)
```

### 4. Запуск API сервера

```bash
python api.py
```

Сервер будет доступен на `http://localhost:8000`

## 📡 API Endpoints

### Запуск записи
```http
GET /start?meeting_id={id}&meeting_password={password}
```

**Пример:**
```bash
curl "http://localhost:8000/start?meeting_id=86096318216&meeting_password=your_password"
```

**Ответ:**
```json
{
  "status": "success",
  "message": "Meeting 86096318216 recording started successfully",
  "meeting_id": "86096318216"
}
```

### Получение записи
```http
GET /record/{meeting_id}
```

Возвращает WAV файл записи или JSON с путем к файлу.

### Статус встречи
```http
GET /status/{meeting_id}
```

**Ответ:**
```json
{
  "meeting_id": "86096318216",
  "is_running": true,
  "has_recording": true,
  "latest_recording": "sample_program/out/audio/meeting_recording_86096318216.wav"
}
```

### Остановка записи
```http
POST /stop/{meeting_id}
```

## 🖥️ CLI Использование

### Запуск бота напрямую
```bash
python cli.py --meeting_id "86096318216" --meeting_password "your_password"
```

### Запуск с использованием переменных окружения
```bash
export MEETING_ID="86096318216"
export MEETING_PWD="your_password"
python main.py
```

## 🤖 MeetingBot класс

Основной класс для управления встречами Zoom:

```python
from meeting_bot import MeetingBot

# Создание и запуск бота
bot = MeetingBot(
    meeting_number="86096318216",
    password="your_password", 
    display_name="AI Recording Bot"
)

try:
    bot.init()           # Инициализация SDK
    # bot автоматически подключится к встрече
finally:
    bot.cleanup()        # Обязательная очистка ресурсов
```

### Основные методы

| Метод | Описание |
|-------|----------|
| `init()` | Инициализация Zoom SDK и сервисов |
| `join_meeting()` | Подключение к встрече |
| `start_raw_recording()` | Начало записи аудио |
| `stop_raw_recording()` | Остановка записи |
| `leave()` | Покидание встречи |
| `cleanup()` | Очистка ресурсов SDK |

## 🎵 Обработка аудио

### Формат записи
- **Формат:** WAV (Linear PCM)
- **Частота дискретизации:** 32,000 Hz
- **Каналы:** Моно
- **Битность:** 16 бит

### Структура файлов
```
sample_program/out/audio/
├── meeting_recording_86096318216.wav    # Основная запись
├── audio.wav                           # Резервная копия
└── *.pcm                              # Временные PCM файлы
```

### Непрерывная запись
Система поддерживает `AudioFileWriter` для thread-safe записи:

```python
recorder = AudioFileWriter(
    output_path="recording.wav",
    sample_rate=32000,
    channels=1, 
    sample_width=2
)

recorder.start_recording()
# ... запись данных ...
recorder.stop_recording()
```

## 🗣️ Транскрипция (Deepgram)

### Настройка Deepgram
```python
from deepgram_transcriber import DeepgramTranscriber

transcriber = DeepgramTranscriber()
# Отправка аудио данных для транскрипции в реальном времени
transcriber.send(audio_data)
```

### Конфигурация
- **Модель:** nova-2-conversationalai
- **Язык:** en-GB (настраивается)
- **Пунктуация:** Включена
- **Промежуточные результаты:** Включены

## 🧪 Тестирование

### Автоматические тесты
```bash
python test_api.py
```

### Ручное тестирование
```bash
# Проверка состояния API
curl http://localhost:8000/

# Тест запуска записи
curl "http://localhost:8000/start?meeting_id=test&meeting_password=test"

# Проверка статуса
curl http://localhost:8000/status/test
```

## 🔧 Расширенная конфигурация

### Настройки записи
```python
# В meeting_bot.py
class MeetingBot:
    def __init__(self, ...):
        self.use_audio_recording = True      # Запись аудио
        self.use_video_recording = False     # Запись видео (экспериментально)
```

### Обработка сигналов
Система корректно обрабатывает SIGINT/SIGTERM для безопасного завершения:

```python
import signal

def signal_handler(signum, frame):
    print(f"Получен сигнал {signum}, завершение...")
    bot.cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
```

## 🐛 Устранение неполадок

### Проблемы с Zoom SDK
```bash
# Проверка SDK
python -c "import zoom_meeting_sdk as zoom; print('SDK OK')"

# Проверка библиотек
ldd /path/to/zoom/sdk/lib/libzoomsdk.so

# Установка недостающих зависимостей
sudo apt-get install libgstreamer1.0-0 libgstreamer-plugins-base1.0-0
```

### Ошибки аутентификации
1. **Проверьте учетные данные** в .env файле
2. **Проверьте права приложения** в Zoom Marketplace
3. **Обновите JWT токен** если истек срок действия

### Проблемы с аудио
```bash
# Проверка аудио устройств
pactl list short sources

# Проверка прав доступа
ls -la /dev/snd/

# Тест записи
arecord -f cd -t wav -d 5 test.wav
```

### Проблемы с памятью
```bash
# Мониторинг использования памяти
ps aux | grep python
top -p $(pgrep -f meeting_bot)

# Очистка временных файлов
rm -f sample_program/out/audio/*.pcm
```

## 📊 Мониторинг и логирование

### Структура логов
```python
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('zoom_recorder.log'),
        logging.StreamHandler()
    ]
)
```

### Метрики производительности
- Время подключения к встрече
- Качество аудио записи
- Использование CPU/памяти
- Статус транскрипции

## 🔐 Безопасность

### Защита учетных данных
- API ключи только в переменных окружения
- Автоматическое удаление временных файлов
- Шифрование записей (опционально)

### Сетевая безопасность
```python
# Настройка CORS для API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Ограничить домены
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```
