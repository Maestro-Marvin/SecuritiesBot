import telebot
import requests
import json
import sqlite3
import schedule
import time
import threading

bot_token = '6092258309:AAHzHQt34QQfYc7kUw2fWrf22DbIOhiqeeY'
api_key = 'ELRC0MAFS54BPPDR'
bot = telebot.TeleBot(bot_token)

# Создание базы данных
conn = sqlite3.connect('stocks.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS stocks
             (id INTEGER PRIMARY KEY,
             code TEXT NOT NULL,
             price REAL,
             user_id INTEGER NOT NULL)''')

# Обработка команды /help
@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.from_user.id, "Привет, я умею мониторить ценные бумаги на бирже!\n"
                    "Список команд:\n"
                    "/add <stock_code> добавляет ценную бумагу с заданным кодом в избранное\n"
                    "/remove <stock_code> удаляет ценную бумагу с заданным кодом из избранных\n"
                    "/list выводит список добавленных пользователем ценных бумаг с их ценами\n"
                    "/set_periodicity period бот будет мониторить акции раз в period минут"
                    "и сообщит если цена снизится, по умолчанию period = 10\n"
                    "Коды ценных бумаг можно узнать тут https://finance.yahoo.com/lookup")

# Обработка команды /add
@bot.message_handler(commands=['add'])
def add_stock(message):
    stock_code = message.text[5:]
    
    # Запрос информации о ценной бумаге через API
    response = requests.get('https://www.alphavantage.co/query',
                        params={'function': 'GLOBAL_QUOTE', 'symbol': stock_code, 'apikey': api_key})
    successful = True
    if response.status_code == 200:
        data = json.loads(response.text)
        try:
            stock_price = data['Global Quote']['05. price']
        except:
            successful = False
    if not successful:
        bot.reply_to(message, "Не удалось добавить ценную бумагу! Некорректный код ценной бумаги!")
        return
    # Добавление информации о ценной бумаге в БД
    user_id = message.chat.id
    c.execute(f"INSERT INTO stocks (code, price, user_id) VALUES ('{stock_code}', {stock_price}, {user_id})")
    conn.commit()
    bot.reply_to(message, f"{stock_code} успешно добавлена в список избранных!")

# Обработка команды /list
@bot.message_handler(commands=['list'])
def list_stocks(message):
    user_id = message.chat.id
    c.execute(f"SELECT code, price FROM stocks WHERE user_id={user_id}")
    stocks = c.fetchall()
    output = "Список избранных ценных бумаг:\n"
    for stock in stocks:
        output += f"{stock[0]} - {stock[1]}$\n"
    bot.reply_to(message, output)

# Обработка команды /set_periodicity
@bot.message_handler(commands=['set_periodicity'])
def set_periodicity(message):
    global periodicity
    user_id = message.chat.id
    try:
        periodicity = int(message.text[17:])
    except:
        bot.send_message(user_id, "неправильный ввод, укажите наутральное число минут")
    schedule.every(periodicity).minutes.do(monitor_stocks)


# Обработка команды /remove
@bot.message_handler(commands=['remove'])
def remove_stock(message):
    stock_code = message.text[8:]
    user_id = message.chat.id
    c.execute(f"DELETE FROM stocks WHERE user_id='{user_id}' AND code='{stock_code}'")
    conn.commit()
    bot.reply_to(message, f"{stock_code} успешно удален из списка избранных!")

# Функция мониторинга изменения цены ценной бумаги
def monitor_stocks():
    c.execute(f"SELECT id, code, price, user_id FROM stocks")
    stocks = c.fetchall()
    for stock in stocks:
        stock_id = stock[0]
        stock_code = stock[1]
        stock_price = stock[2]
        user_id = stock[3]
        
        # Запрос информации о ценной бумаге через API
        response = requests.get('https://www.alphavantage.co/query',
                        params={'function': 'GLOBAL_QUOTE', 'symbol': stock_code, 'apikey': api_key})
        if response.status_code == 200:
            data = json.loads(response.text)
            new_price = float(data['Global Quote']['05. price'])
            # Сравнение начальной цены с текущей ценой
            if new_price < stock_price:
                bot.send_message(user_id, f"Цена {stock_code} снизилась c {stock_price}$ до {new_price}$")
                c.execute(f"UPDATE stocks SET price = {new_price} WHERE id={stock_id}")
                conn.commit()
        else:
            bot.send_message(user_id, f"{stock_code} - ценная бумага была удалена с биржи!")
            c.execute(f"DELETE FROM stocks WHERE user_id='{user_id}' AND code='{stock_code}'")
            conn.commit()
    bot.send_message(user_id, "Мониторинг ценных бумаг завершен")


def polling_function():
    bot.polling()
    
# Функция polling_function бесконечная, поэтому чтобы выполнять периодически 
# monitor_stocks, мы запускаем её в другом потоке
polling_thread = threading.Thread(target=polling_function)
polling_thread.start()

# Расписание запуска функции мониторинга
periodicity = 10
schedule.every(periodicity).minutes.do(monitor_stocks)

while True:
    schedule.run_pending()
    time.sleep(1)
