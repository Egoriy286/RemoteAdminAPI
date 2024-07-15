import threading
import time

from bot import start_bot
from flask import Flask, request, jsonify, send_file
import bot
import json
import os
import zipfile
import signal

app = Flask(__name__)

# Путь к JSON файлу
json_file_path = 'data.json'

# Путь к директории logs
logs_directory = 'logs'

# Загрузка данных из JSON файла при запуске приложения


# Эндпоинт для получения текущих данных
@app.route('/get_data', methods=['GET'])
def get_data():
    with open(json_file_path, 'r') as file:
        initial_data = json.load(file)
    file.close()
    return jsonify(initial_data)

# Эндпоинт для изменения данных через POST запрос
@app.route('/update_data', methods=['POST'])
def update_data():
    # Получаем данные из запроса
    updated_data = request.get_json()
    with open(json_file_path, 'r') as file:
        initial_data = json.load(file)
    file.close()
    # Обновляем данные в переменной initial_data
    initial_data.update(updated_data)

    # Сохраняем обновленные данные в JSON файл
    with open(json_file_path, 'w') as file:
        json.dump(initial_data, file, indent=4)
    time.sleep(2)
    bot.config()
    # Возвращаем обновленные данные в ответе
    return jsonify(initial_data)

@app.route('/status', methods=['GET'])
def status():

    return jsonify({'status': True})

@app.route('/status_model', methods=['GET'])
def status_model():
    with open("temp.json", 'r') as file:
        status_data = json.load(file)
    return jsonify(status_data)

def zip_logs(directory):
    zip_filename = 'logs.zip'
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for root, _, files in os.walk(directory):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), directory))
    zipf.close()
    return zip_filename

@app.route('/logs', methods=['GET'])
def archive_logs():
    temp_zip_file = 'logs.zip'

    if os.path.exists(temp_zip_file):
        os.remove(temp_zip_file)
    zip_logs(logs_directory)

    return send_file(temp_zip_file, as_attachment=True)

@app.route('/restart', methods=['POST'])
def restart():
    if request.method == 'POST':
        # Отправляем сигнал для перезагрузки процесса
        os.kill(os.getpid(), signal.SIGINT)
        return jsonify({"status": "restarting"}), 200

def run_api():
    app.logger.info("start-app")
    app.run(debug=False, host="0.0.0.0", port=5000)

def main():
    # Запускаем API в отдельном потоке
    api_thread = threading.Thread(target=run_api)

    api_thread.start()

    # Запускаем бота в основном потоке
    app.logger.info("start-bot")
    time.sleep(4)
    start_bot()

    # Ждем завершения работы потока с API (не обязательно, в зависимости от логики вашего приложения)
    api_thread.join()

if __name__ == "__main__":
    main()
