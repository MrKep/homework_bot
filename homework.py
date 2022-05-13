
"""Бот для контроля домашней работы."""

import logging
import os
import time

import requests
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправка сообщения в телеграм."""
    text = message
    try:
        logging.info('Отправляем сообщение в Telegram')
        bot.send_message(TELEGRAM_CHAT_ID, text)
    except Exception:
        raise Exception('Cбой при отправке сообщения в Telegram')
    else:
        logging.info('Сообщение отправлено')


def get_api_answer(current_timestamp):
    """Проверка ответа сервера."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except ValueError:
        raise ValueError

    if response.status_code == requests.codes.ok:
        return response.json()
    else:
        raise TypeError


def check_response(response):
    """Проверка API на корректность."""
    if not isinstance(response, dict):
        raise TypeError('Не словарь')
    try:
        homeworks = response['homeworks']
    except IndexError:
        raise IndexError('Нет ключа homework')
    else:
        if not isinstance(homeworks, list):
            raise TypeError('Домашки пришли не в виде списка')
        else:
            return homeworks[0]


def parse_status(homework):
    """Определение статуса работы."""
    print(homework)
    if 'homework_name' not in homework:
        raise KeyError('homework_name отсутствует в homework')
    if 'status' not in homework:
        raise KeyError('status отсутствует в homework')
    homework_name = homework['homework_name']
    homework_status = homework['status']
    verdict = HOMEWORK_STATUSES[homework_status]
    if homework_status in HOMEWORK_STATUSES:
        message = (f'Изменился статус проверки работы '
                   f'"{homework_name}". {verdict}')
        return message
    else:
        raise KeyError('Статус работы не определен')


def check_tokens():
    """Проверка всех необходимых токенов."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная функция программы."""
    current_date = int(time.time()) - (604800 * 3)
    bot = Bot(token=TELEGRAM_TOKEN)
    message = ''
    while True:
        try:
            check_tokens()
            api_answer = get_api_answer(current_date)
            check_api = check_response(api_answer)
            if message != parse_status(check_api):
                message = parse_status(check_api)
                send_message(bot, message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.info('Отправлена иноформация о ошибке')
            send_message(bot, message)
            time.sleep(RETRY_TIME)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        filename='main.log',
        filemode='w',
        format='%(asctime)s, %(levelname)s, %(message)s'
    )
    main()
