import logging
from logging.handlers import TimedRotatingFileHandler
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram import F
import asyncio
import openai
import time, os
import json

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

json_file_path = 'data.json'

with open(json_file_path, 'r') as file:
    data = json.load(file)

# Конфигурация
API_TOKEN = data['api_token_telegram']
MODEL = data['model']
SECRET_KEY = data['secretkey_model']
HOST = data['host']
client = None
bot = None
dp = None
def config():
    global API_TOKEN, MODEL, SECRET_KEY, HOST, client, bot, dp
    with open(json_file_path, 'r') as file:
        data = json.load(file)

    # Конфигурация
    API_TOKEN = data['api_token_telegram']
    MODEL = data['model']
    SECRET_KEY = data['secretkey_model']
    HOST = data['host']

    try:
        client = openai.AsyncOpenAI(
            api_key=SECRET_KEY,
            base_url=HOST,
        )
        bot = Bot(token=API_TOKEN)
        dp = Dispatcher()
    except(Exception):
        logging.warning("Data not load. Check data.json!!!")
        pass
config()
LOG_DIR = 'logs'

user_history = {}

os.makedirs(LOG_DIR, exist_ok=True)

txt_handler = TimedRotatingFileHandler(
    filename=os.path.join(LOG_DIR, 'bot_log.txt'),
    when='midnight',
    interval=1,
    backupCount=7,
    encoding='utf-8'
)
txt_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
txt_handler.suffix = '%Y-%m-%d'

csv_handler = TimedRotatingFileHandler(
    filename=os.path.join(LOG_DIR, 'bot_log.csv'),
    when='midnight',
    interval=1,
    backupCount=7,
    encoding='utf-8'
)
csv_handler.setFormatter(logging.Formatter('%(asctime)s, %(message)s'))
csv_handler.suffix = '%Y-%m-%d'

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(txt_handler)
logger.addHandler(csv_handler)


def clear(user_id):
    if user_id in user_history:
        del user_history[user_id]
    logger.info(f"User {user_id}, maximum_tokens, MAX_TOKENS")

@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    user_id = message.from_user.id

    # Стираем историю сообщений пользователя
    if user_id in user_history:
        del user_history[user_id]

    logger.info(f"User {user_id}, started a new session, NEW_SESSION")

    await message.reply(f"Привет я ИИ {data['name']}! Отправь мне сообщение, и я отвечу на него.")

@dp.message(F.text)
async def echo(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_history:
        user_history[user_id] = []

    # Добавляем текущее сообщение пользователя в историю
    user_history[user_id].append({"role": "user", "content": message.text})

    logger.info(f"{user_id}, Hide, ANSWER")

    # Формируем историю сообщений для отправки в модель
    history = user_history[user_id]


    try:
        # Отправляем запрос к модели
        timer = time.time()
        chat_response = await client.chat.completions.create(
            model=MODEL,
            messages=history,
            temperature=0,
        )
        elapsed_time = time.time() - timer
        logger.info(f"{user_id}, {elapsed_time}, TIME")
        logger.info(f"{user_id}, {chat_response.usage.total_tokens}, TOTAL_TOKENS")
        response_text = chat_response.choices[0].message.content
        logger.info(f"{user_id}, Hide, RESPONSE")
        if (chat_response.usage.total_tokens > int(data['max_tokens'])):
            clear(user_id)

        # Добавляем ответ модели в историю
        user_history[user_id].append({"role": "assistant", "content": response_text})
    except(Exception):
        response_text="Error"
        pass


    await message.answer(response_text)


@dp.message(F.text, Command("policy"))
def POLICY(message: types.Message):
    return message.answer(POLICY)



def start_bot():
    while(True):
        try:
            print("start")

            asyncio.run(dp.start_polling(bot))
        except(Exception):
            config()
            print("No valid data")
            time.sleep(5)

if __name__ == "__main__":
    start_bot()

# Политика конфиденциальности
POLICY = """
Мы уважаем вашу конфиденциальность и строго соблюдаем все нормы защиты данных. Мы собираем и используем только те данные, которые необходимы для предоставления наших услуг. Все данные хранятся в безопасности и ни при каких обстоятельствах не будут переданы третьим лицам без вашего согласия.
"""

print(POLICY)