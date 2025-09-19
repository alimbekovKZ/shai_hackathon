# JIRA MCP Server

JIRA MCP (Model Context Protocol) Server для автоматизации создания и управления задачами в JIRA. Поддерживает Atlassian Document Format (ADF), назначение исполнителей и интеграцию с AI системами.

## 🌟 Особенности

- ✅ **Создание задач JIRA** с богатым форматированием (ADF)
- ✅ **Назначение исполнителей** по email или имени
- ✅ **Поиск пользователей** в проекте
- ✅ **Получение информации** о существующих задачах
- ✅ **Автоматическое форматирование** списков и текста
- ✅ **HTTP и MCP** протоколы
- ✅ **Совместимость с JIRA Cloud**

## 📋 Доступные инструменты MCP

### 1. `create_jira_issue`
Создает новую задачу в JIRA с расширенными возможностями.

**Параметры:**
- `summary` (обязательный) - Название задачи
- `description` (обязательный) - Описание с поддержкой списков (`•`, `-`, `*`)
- `issue_type` (опциональный) - Тип задачи (Task, Bug, Story). По умолчанию: "Task"
- `assignee` (опциональный) - Email или имя исполнителя

**Пример:**
```json
{
  "name": "create_jira_issue",
  "arguments": {
    "summary": "Внедрить новую функцию аутентификации",
    "description": "Задачи для реализации:\n• Настроить OAuth 2.0\n• Создать страницу входа\n• Добавить тесты",
    "issue_type": "Task",
    "assignee": "developer@company.com"
  }
}
```

### 2. `assign_jira_issue`
Назначает исполнителя для существующей задачи.

**Параметры:**
- `issue_key` (обязательный) - Ключ задачи (например, PROJ-123)
- `assignee` (обязательный) - Email или имя исполнителя

### 3. `get_jira_issue`
Получает подробную информацию о задаче.

**Параметры:**
- `issue_key` (обязательный) - Ключ задачи JIRA

### 4. `get_project_users`
Возвращает список пользователей, которые могут быть назначены исполнителями в проекте.

**Параметры:** Не требуются

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка окружения

Создайте файл `.env`:
```env
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_USERNAME=your-email@domain.com
JIRA_API_TOKEN=your_api_token
JIRA_PROJECT_KEY=YOUR-PROJECT
```

**Как получить API токен JIRA:**
1. Перейдите в [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Нажмите "Create API token"
3. Скопируйте токен в переменную `JIRA_API_TOKEN`

### 3. Запуск сервера

```bash
python jira_shai.py
```

Сервер запустится на `http://localhost:8000`

## 🔧 Версии серверов

Проект содержит несколько версий MCP серверов:

| Файл | Описание | Особенности |
|------|----------|-------------|
| `jira_shai.py` | **Основная версия** | ADF поддержка, назначение исполнителей, поиск пользователей |
| `jira_test.py` | Версия с ADF | Только создание и получение задач |
| `jira_mcp_openai.py` | OpenAI совместимая | Расширенная совместимость |
| `jira_http_server.py` | HTTP тестовый сервер | Для отладки и мониторинга |

**Рекомендуется использовать `jira_shai.py`** как наиболее полную версию.

## 📡 API Endpoints

### HTTP REST API
```bash
# Проверка состояния
GET /health

# Список инструментов
GET /tools

# MCP JSON-RPC endpoint
POST /mcp
```

### MCP Protocol
Сервер поддерживает стандартный MCP протокол:
- `initialize` - Инициализация соединения
- `tools/list` - Получение списка доступных инструментов
- `tools/call` - Вызов инструмента

## 🎨 Atlassian Document Format (ADF)

Сервер автоматически конвертирует текст в ADF формат:

**Входной текст:**
```
Задачи для выполнения:
• Создать модель данных
• Настроить API endpoints
• Написать тесты

Дополнительные заметки:
- Использовать PostgreSQL
- Добавить индексы
```

**Результат в JIRA:** Корректно отформатированные списки с буллетами и структурированным текстом.

## 🧪 Тестирование

### Проверка конфигурации
```bash
python -c "
from jira_shai import JIRAConfig
config = JIRAConfig()
print('✅ Конфигурация валидна' if config.is_valid() else '❌ Ошибка конфигурации')
"
```

### Тест создания задачи
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "create_jira_issue",
      "arguments": {
        "summary": "Тестовая задача",
        "description": "Проверка работы API"
      }
    }
  }'
```

### Мониторинг сервера
Откройте `http://localhost:8000` в браузере для просмотра статуса и документации.

## 🔍 Устранение неполадок

### Ошибки аутентификации
```bash
# Проверьте учетные данные
curl -u "your-email@domain.com:your_api_token" \
  https://your-domain.atlassian.net/rest/api/3/myself
```

### Ошибки создания задач
1. **Проверьте права доступа** - убедитесь, что пользователь может создавать задачи в проекте
2. **Валидируйте тип задач** - убедитесь, что указанный `issue_type` существует в проекте
3. **Проверьте проект** - убедитесь, что `JIRA_PROJECT_KEY` корректен

### Проблемы с назначением исполнителей
1. **Проверьте пользователей** - используйте `get_project_users` для просмотра доступных пользователей
2. **Формат email** - убедитесь, что email точно соответствует зарегистрированному в JIRA
3. **Права проекта** - пользователь должен иметь доступ к проекту

## 📊 Логирование

Сервер ведет подробные логи:
```bash
# Просмотр логов в реальном времени
tail -f *.log

# Уровни логирования
INFO - Основные операции
DEBUG - Подробная отладочная информация  
ERROR - Ошибки выполнения
WARNING - Предупреждения
```

## 🔐 Безопасность

- **API токены** хранятся только в переменных окружения
- **Логи** не содержат чувствительной информации
- **HTTPS** обязателен для production окружения
- **Валидация входных данных** на всех endpoints

## 🚀 Production развертывание

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "jira_shai.py"]
```

### systemd service
```ini
[Unit]
Description=JIRA MCP Server
After=network.target

[Service]
Type=simple
User=jira-mcp
WorkingDirectory=/opt/jira-mcp
Environment=PYTHONPATH=/opt/jira-mcp
ExecStart=/usr/bin/python3 jira_shai.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## 📈 Мониторинг

Сервер предоставляет метрики через `/health` endpoint:
- Статус подключения к JIRA
- Количество обработанных запросов
- Время последнего запроса
- Информация о версии и конфигурации

## 🤝 Интеграция с AI системами

Сервер оптимизирован для работы с AI системами:
- **Структурированные ответы** в JSON формате
- **Подробные описания ошибок** для обработки AI
- **Контекстные подсказки** в схемах инструментов
- **Поддержка batch операций**

## 📚 Примеры использования

См. файлы `example_*.py` для подробных примеров интеграции с различными AI системами и фреймворками.
