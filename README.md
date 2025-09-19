# AI-Powered Meeting Assistant (Shai Hackathon)

Комплексное решение для автоматизации обработки встреч с интеграцией JIRA, Zoom и AI. Система автоматически записывает встречи Zoom, обрабатывает их с помощью AI и создает задачи в JIRA на основе обсуждений.

Демо: https://v0-jira-zoom-ai.vercel.app/


## 🏗️ Архитектура проекта

```
shai_hackathon/
├── JIRA/                          # JIRA MCP Server для интеграции
│   ├── jira_shai.py              # Основной сервер с поддержкой ADF и назначения исполнителей
│   ├── jira_mcp_*.py             # Различные версии MCP серверов
│   ├── jira_http_server.py       # HTTP сервер для тестирования JIRA API
│   └── requirements.txt          # Зависимости Python
├── zoom-listener/                 # Zoom Meeting Recorder
│   ├── api.py                    # FastAPI сервер для управления записью
│   ├── meeting_bot.py            # Основной класс для записи встреч
│   ├── cli.py                    # CLI интерфейс
│   └── requirements.txt          # Зависимости Python
├── jira-zoom-ai-helper/          # Веб-интерфейс
│   ├── app/                      # Next.js приложение
│   ├── components/               # React компоненты
│   └── package.json              # Зависимости Node.js
└── README.md                     # Этот файл
```

## 🚀 Компоненты системы

### 1. JIRA MCP Server (`/JIRA`)
- **Назначение**: Сервер для интеграции с JIRA через MCP протокол
- **Функции**: 
  - Создание задач в JIRA с поддержкой ADF формата
  - Назначение исполнителей
  - Получение информации о задачах
  - Поиск пользователей проекта
- **Технологии**: Python, FastAPI, MCP Protocol

### 2. Zoom Meeting Recorder (`/zoom-listener`)
- **Назначение**: Запись аудио из встреч Zoom
- **Функции**:
  - Автоматическое подключение к встречам Zoom
  - Запись аудио в реальном времени
  - API для управления записью
  - Сохранение записей в формате WAV
- **Технологии**: Python, Zoom SDK, FastAPI

### 3. Web Interface (`/jira-zoom-ai-helper`)
- **Назначение**: Пользовательский интерфейс для обработки встреч
- **Функции**:
  - Ввод ссылки на Zoom встречу
  - Запуск обработки через AI workflow
  - Отображение результатов
- **Технологии**: Next.js, React, TypeScript, Tailwind CSS

## 🔧 Быстрый старт

### Предварительные требования
- Python 3.8+
- Node.js 18+
- Docker (опционально)
- Zoom App credentials
- JIRA credentials
- Deepgram API key (для транскрипции)

### 1. Настройка окружения

Создайте файл `.env` в корне проекта:
```env
# Zoom настройки
ZOOM_APP_CLIENT_ID=your_zoom_client_id
ZOOM_APP_CLIENT_SECRET=your_zoom_client_secret

# JIRA настройки
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_USERNAME=your-email@domain.com
JIRA_API_TOKEN=your_jira_api_token
JIRA_PROJECT_KEY=YOUR-PROJECT

# Deepgram настройки
DEEPGRAM_API_KEY=your_deepgram_api_key
```

### 2. Запуск JIRA MCP Server

```bash
cd JIRA
pip install -r requirements.txt
python jira_shai.py
```

Сервер будет доступен на `http://localhost:8000`

### 3. Запуск Zoom Recorder

```bash
cd zoom-listener
pip install -r requirements.txt
python api.py
```

API будет доступен на `http://localhost:8000`

### 4. Запуск Web Interface

```bash
cd jira-zoom-ai-helper
npm install
npm run dev
```

Интерфейс будет доступен на `http://localhost:3000`

## 📊 Workflow обработки встреч

1. **Ввод данных**: Пользователь вводит ссылку на Zoom встречу в веб-интерфейсе
2. **Запись**: Система автоматически подключается к встрече и записывает аудио
3. **Обработка AI**: Запись обрабатывается через AI workflow (Deepgram + LLM)
4. **Создание задач**: На основе анализа автоматически создаются задачи в JIRA
5. **Результат**: Пользователь получает ссылки на созданные задачи

## 🔗 API Endpoints

### JIRA MCP Server
- `POST /mcp` - MCP JSON-RPC endpoint
- `GET /health` - Проверка состояния
- `GET /tools` - Список доступных инструментов

### Zoom Recorder API
- `GET /start?meeting_id={id}&meeting_password={password}` - Начать запись
- `GET /record/{meeting_id}` - Получить файл записи
- `GET /status/{meeting_id}` - Статус записи
- `POST /stop/{meeting_id}` - Остановить запись

## 🛠️ Разработка

### Структура веток
- `main` - стабильная версия
- `develop` - разработка новых функций
- `feature/*` - отдельные функции

### Тестирование
```bash
# JIRA MCP Server
cd JIRA
python -m pytest

# Zoom Recorder
cd zoom-listener
python test_api.py
```

## 📝 Конфигурация

### JIRA MCP Server
Поддерживает следующие инструменты:
- `create_jira_issue` - Создание задач
- `assign_jira_issue` - Назначение исполнителей
- `get_jira_issue` - Получение информации о задачах
- `get_project_users` - Список пользователей проекта

### Zoom Meeting Bot
Автоматически:
- Подключается к встрече
- Записывает аудио всех участников
- Сохраняет записи с временными метками
- Поддерживает множественные встречи

## 🔒 Безопасность

- Все API ключи хранятся в переменных окружения
- JIRA токены используют OAuth 2.0
- Аудио записи удаляются после обработки
- Логи не содержат чувствительной информации

## 🐛 Устранение неполадок

### Проблемы с Zoom SDK
```bash
# Проверьте права доступа
sudo apt-get install libasound2-dev
export LD_LIBRARY_PATH=/path/to/zoom/sdk/lib

# Проверьте конфигурацию
python -c "import zoom_meeting_sdk as zoom; print('SDK OK')"
```

### Проблемы с JIRA
```bash
# Тест подключения
curl -X GET "http://localhost:8000/health"

# Проверка конфигурации
python -c "from JIRA.jira_shai import JIRAConfig; print(JIRAConfig().is_valid())"
```

## 📄 Лицензия

MIT License - см. LICENSE файл для деталей.

## 👥 Команда

Проект разработан в рамках Shai Hackathon командой DSML для автоматизации рабочих процессов с помощью AI.

## 🔗 Полезные ссылки

- [Zoom Meeting SDK Documentation](https://developers.zoom.us/docs/meeting-sdk/)
- [JIRA REST API](https://developer.atlassian.com/server/jira/platform/rest-apis/)
- [MCP Protocol Specification](https://spec.modelcontextprotocol.io/)
- [Next.js Documentation](https://nextjs.org/docs)
