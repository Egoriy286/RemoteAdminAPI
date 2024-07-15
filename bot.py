import logging
from logging.handlers import TimedRotatingFileHandler
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram import F
import asyncio
import openai
import time, os
import json
json_file_path = 'data.json'

# Политика конфиденциальности
POLICY = """
Мы уважаем вашу конфиденциальность и строго соблюдаем все нормы защиты данных. Мы собираем и используем только те данные, которые необходимы для предоставления наших услуг. Все данные хранятся в безопасности и ни при каких обстоятельствах не будут переданы третьим лицам без вашего согласия.
"""

# Конфигурация
API_TOKEN = None
MODEL = None
SECRET_KEY = None
MAX_TOKENS = None
NAME = None
HOST = None
client = None
bot = None
dp = None

def config():
    global API_TOKEN, NAME, MODEL, SECRET_KEY, HOST, client, bot, dp, MAX_TOKENS
    with open(json_file_path, 'r') as file:
        data = json.load(file)

    # Конфигурация
    API_TOKEN = data['api_token_telegram']
    MODEL = data['model']
    SECRET_KEY = data['secretkey_model']
    MAX_TOKENS = data['max_tokens']
    HOST = data['host']
    NAME = data['name']
    file.close()
    try:
        client = openai.AsyncOpenAI(
            api_key=SECRET_KEY,
            base_url=HOST,
        )
        bot = Bot(token=API_TOKEN)
        dp = Dispatcher()
        logging.warning("data: client, bot, dp successful load")
    except(Exception):
        logging.critical("Dispatcher bad check api. Check data.json!!!")
        pass
config()
LOG_DIR = 'logs'

user_history = {}

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

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

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
def clear(user_id):
    if user_id in user_history:
        del user_history[user_id]
    logger.info(f"User {user_id}, maximum_tokens, MAX_TOKENS")

@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    global NAME
    user_id = message.from_user.id

    # Стираем историю сообщений пользователя
    if user_id in user_history:
        del user_history[user_id]

    logger.info(f"{user_id}, user start, NEW_SESSION")

    await message.reply(f"Привет я ИИ {NAME}! Отправь мне сообщение, и я отвечу на него.")

@dp.message(F.text)
async def echo(message: types.Message):
    global MAX_TOKENS, MODEL
    user_id = message.from_user.id
    if user_id not in user_history:
        user_history[user_id] = []

    # Добавляем текущее сообщение пользователя в историю
    user_history[user_id].append({"role": "user", "content": message.text})

    logger.info(f"{user_id}, Hide, ANSWER")

    # Формируем историю сообщений для отправки в модель
    history = user_history[user_id]


    try:
        temp = {'status_model': True}
        with open("temp.json", 'w') as file:
            json.dump(temp, file, indent=4)
        file.close()
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
        if (chat_response.usage.total_tokens > int(MAX_TOKENS)):
            clear(user_id)

        # Добавляем ответ модели в историю
        user_history[user_id].append({"role": "assistant", "content": response_text})
    except(Exception):
        temp = {'status_model': False}
        with open("temp.json", 'w') as file:
            json.dump(temp, file, indent=4)
        file.close()
        response_text = None
        logger.critical("Connection to model bad!!!")
        pass

    await message.answer(response_text)

@dp.message(F.text, Command("policy"))
def POLICY(message: types.Message):
    return message.answer(POLICY)



def start_bot():

    while (True):
        try:
            logger.warning("bot successful start")
            asyncio.run(dp.start_polling(bot))
        except(Exception):
            config()
            logger.critical("bot not start please check")
            time.sleep(8)

if __name__ == "__main__":
    start_bot()