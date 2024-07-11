import threading
from api import run_api
from bot import start_bot

def main():
    # Запускаем API в отдельном потоке
    api_thread = threading.Thread(target=run_api)
    api_thread.start()

    # Запускаем бота в основном потоке
    start_bot()

    # Ждем завершения работы потока с API (не обязательно, в зависимости от логики вашего приложения)
    api_thread.join()

if __name__ == "__main__":
    main()
