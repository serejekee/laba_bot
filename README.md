# Телеграм Бот для автоматизии в лаборатории

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://t.me/OFFpolice2069)
[![aiogram](https://img.shields.io/badge/aiogram-%5E3.0.0-%234FC3F7)](https://docs.aiogram.dev/en/latest/)
[![Requests](https://img.shields.io/badge/requests-%5E2.28.1-%230577B5)](https://docs.python-requests.org/en/latest/)
[![aiohttp](https://img.shields.io/badge/aiohttp-%5E3.8.1-%23017ACC)](https://docs.aiohttp.org/en/stable/)
[![google-auth](https://img.shields.io/badge/google--auth-%5E2.6.0-%230F9D58)](https://googleapis.dev/python/google-auth/latest/)
[![google-auth-oauthlib](https://img.shields.io/badge/google--auth--oauthlib-%5E0.5.2-%23EA4335)](https://googleapis.dev/python/google-auth-oauthlib/latest/)
[![google-api-python-client](https://img.shields.io/badge/google--api--python--client-%5E2.83.0-%234285F4)](https://googleapis.dev/python/google-api-python-client/latest/)
[![openpyxl](https://img.shields.io/badge/openpyxl-%5E3.1.2-%23007396)](https://openpyxl.readthedocs.io/en/stable/)

## Обзор

Этот Python-скрипт реализует Telegram-бота с использованием современных версий библиотек:

[aiogram](https://docs.aiogram.dev/en/latest/) — для создания асинхронного Telegram-бота.  
[aiohttp](https://docs.aiohttp.org/en/stable/) — для асинхронных HTTP-запросов и работы с вебхуками.  
[google-auth](https://googleapis.dev/python/google-auth/latest/) — для аутентификации в сервисах Google.  
[google-auth-oauthlib](https://googleapis.dev/python/google-auth-oauthlib/latest/) — для OAuth 2.0 авторизации в Google API.  
[google-api-python-client](https://googleapis.dev/python/google-api-python-client/latest/) — для работы с API сервисов Google.  
[pandas](https://pandas.pydata.org/) — для обработки и анализа табличных данных.  
[openpyxl](https://openpyxl.readthedocs.io/en/stable/) — для работы с файлами Excel (.xlsx).  

Бот предоставляет удобный интерфейс для автоматизации процессов через Телеграм.

## Возможности

- Команда `/start` для запуска бота и получения инструкций.

## Инструкция по использованию бота
## 📜 Основные команды для пользователя

| Команда                   | Описание                               |
|---------------------------|----------------------------------------|
| `/start`                  | Запуск бота и отображение меню         |
| 📝 Оставить заявку        | Отправить заявку на рассмотрение       |
| 📤 Загрузить документ     | Загрузить документ в систему           |
| 🔍 Статус заявки          | Проверить статус своей заявки          |
| ❌ Закрыть                 | Закрывает текущее меню                 |
## 📜 Основные команды для продукт-менеджера
| Команда                   | Описание                               |
|---------------------------|----------------------------------------|
| `/start`                  | Запуск бота и отображение меню         |
| 🏢 Список компаний        | Просмотреть список компаний            |
| ➕ Зарегистрировать заявку | Добавить новую заявку от имени компании |
| ❌ Закрыть                 | Закрывает текущее меню                 |
## 📜 Основные команды для менеджера
| Команда                   | Описание                               |
|---------------------------|----------------------------------------|
| `/start`                  | Запуск бота и отображение меню         |
| 📋 Список заявок          | Просмотреть все поступившие заявки     |
| ✅ Принять заявку          | Одобрить заявку менеджером             |
| ❌ Закрыть                 | Закрывает текущее меню                 |
## 📜 Основные команды для инспектора
| Команда                   | Описание                               |
|---------------------------|----------------------------------------|
| `/start`                  | Запуск бота и отображение меню         |
| 📑 Выбор заявок           | Выбрать заявки для проверки инспектором |
| ✅ Одобрить                | Одобрить заявку после проверки         |
| 🚫 Отклонить              | Отклонить заявку после проверки        |
| ❌ Закрыть                 | Закрывает текущее меню                 |

## 📜 Команда /reg - регистрирует пользователя
## 📜 Команда /reg_p - регистрирует продукт-менеджера
## 📜 Команда /reg_m - регистрирует менеджера
## 📜 Команда /reg_i - регистрирует инспектора

## Установка

1. **Клонируйте репозиторий:**

   ```bash
   git clone https://github.com/serejekee/laba_bot
   cd bot

2. **Создайте .env:**

   ```bash
    BOT_TOKEN=BOT_TOKEN
    SPREADSHEET_ID=SPREADSHEET_ID
    DRIVE_ORDERS_ID=DRIVE_ORDERS_ID
    DRIVE_REPORT_ID=DRIVE_REPORT_ID

3. **Создайте credentials.json:**

- Перейдите на сайт: [google cloud console](https://console.cloud.google.com/welcome?hl=ru&project=gen-lang-client-0119176748)


4. **Разверните Телеграм API:**

   ```bash
   git clone https://github.com/tdlib/telegram-bot-api.git  

5. **Разверните проекта:**

   ```bash
   cd telegram-bot
   docker-compose up --build - 1 раз
   docker-compose up -d 

6. **Свертывание проекта:**

   ```bash
   cd telegram-bot
   docker-compose down
