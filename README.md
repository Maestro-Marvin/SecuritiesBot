# SecuritiesBot
## Идея
В проекте реализован телеграм бот, написанный на питоне, с помощью библиотеки telebot.
Бот позволяет добалять пользователю ценные бумаги (акции, облигации) в избранное и далее
следит за их ценой на бирже и сообщает пользователю если она снизится.

## Реализация
Вся информация о избранных ценных бумагах польхователей хранится в базе данных, взаимодействие
с ней реализовано с помощью библиотеки sqlite3. Программа узнаёт цены акций, с помощью
api запросов к бирже, реализовано с помощью библиотеки requests. Возвращаемые в результате 
запроса данные парсятся с помощью json. Поскольку мониторинг акций должен происходить 
периодично в фоновом режиме, то функция реагирующая на ввод пользователя bot.polling 
запускается в другом потоке, реализовано с помощью библиотеки threading, периодичность
с помощью schedule

## Как пользоваться
Вся информация о функциональности бота выводится после команды /help
Поскольку корпоративные акции и облигации хранятся на бирже не по полному
названию компании, а в сокращённом виде - так называемые ticker symbol, то пользователю
требуется сначала узнать на сайте биржи эту последовательность
