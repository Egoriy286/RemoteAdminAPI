from flask import Flask, request, jsonify, send_file
import bot
import json
import os
import zipfile

app = Flask(__name__)

# Путь к JSON файлу
json_file_path = 'data.json'

# Путь к директории logs
logs_directory = 'logs'

# Загрузка данных из JSON файла при запуске приложения
with open(json_file_path, 'r') as file:
    initial_data = json.load(file)

# Эндпоинт для получения текущих данных
@app.route('/get_data', methods=['GET'])
def get_data():
    return jsonify(initial_data)

# Эндпоинт для изменения данных через POST запрос
@app.route('/update_data', methods=['POST'])
def update_data():
    # Получаем данные из запроса
    updated_data = request.get_json()

    # Обновляем данные в переменной initial_data
    initial_data.update(updated_data)

    # Сохраняем обновленные данные в JSON файл
    with open(json_file_path, 'w') as file:
        json.dump(initial_data, file, indent=4)
    bot.config()
    # Возвращаем обновленные данные в ответе
    return jsonify(initial_data)

@app.route('/status', methods=['GET'])
def status():
    return jsonify({'status': True})

def zip_logs(directory):
    zip_filename = 'logs.zip'
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for root, _, files in os.walk(directory):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), directory))

    return zip_filename

@app.route('/archive_logs', methods=['GET'])
def archive_logs():
    temp_zip_file = 'logs.zip'

    if os.path.exists(temp_zip_file):
        os.remove(temp_zip_file)
    zip_logs(logs_directory)

    return send_file(temp_zip_file, as_attachment=True)

def run_api():
    app.run(debug=False, host="0.0.0.0", port=5000)

if __name__ == '__main__':
    run_api()
