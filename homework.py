import logging
import requests
import os
import time

from telegram import Bot
from dotenv import load_dotenv

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
    """Отправка сообщения в телеграм"""
    text = message
    try:
        bot.send_message(TELEGRAM_CHAT_ID, text)
    except Exception:
        logging.error('Cбой при отправке сообщения в Telegram')
        raise Exception('Cбой при отправке сообщения в Telegram')


def get_api_answer(current_timestamp):
    """ Проверка ответа сервера """
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except ValueError:
        logging.error('Нет ответа api')
        raise ValueError

    if response.status_code == requests.codes.ok:
        return response.json()
    else:
        logging.error(f'Ошибка соединения {response.status_code}')
        raise TypeError


def check_response(response):
    """Проверка API на корректность """
    if type(response) != dict:
        raise TypeError('Не словарь')
    try:
        homeworks = response['homeworks']
    except IndexError:
        logging.error('Нет ключа homework')
        raise IndexError('Нет ключа homework')
    else:
        if type(homeworks) != list:
            raise TypeError('Домашки пришли не в виде списка')
        else:
            return homeworks[0]


def parse_status(homework):
    """ Определение статуса работы """
    if 'homework_name' not in homework:
        raise KeyError('homework_name отсутствует в homework')
    homework_name = homework['homework_name']
    homework_status = homework['status']
    verdict = HOMEWORK_STATUSES[homework_status]
    if homework_status in HOMEWORK_STATUSES:
        message = (f'Изменился статус проверки работы '
                   f'"{homework_name}". {verdict}')
        return message
    else:
        raise Exception('Статус работы не определен')


def check_tokens():
    """ Проверка всех необходимых токенов """
    if all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
        logging.info('Проверка токенов')
        return True
    else:
        logging.critical('Отсутствие токенов!')


def main():
    """ Основная функция программы """
    current_date = int(time.time()) - (604800 * 3)
    bot = Bot(token=TELEGRAM_TOKEN)
    logging.basicConfig(
        level=logging.INFO,
        filename='main.log',
        filemode='w',
        format='%(asctime)s, %(levelname)s, %(message)s'
    )
    while True:
        try:
            check_tokens()
            api_answer = get_api_answer(current_date)
            check_api = check_response(api_answer)
            message = parse_status(check_api)
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.info('Отправлена иноформация о ошибке')
            send_message(bot, message)
            time.sleep(RETRY_TIME)
        else:
            logging.info('Отправка иноформации по домашней работе')
            send_message(bot, message)


if __name__ == '__main__':
    main()
