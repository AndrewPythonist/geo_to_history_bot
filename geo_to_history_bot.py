from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import InputMediaPhoto, error, KeyboardButton, ReplyKeyboardMarkup
from config import TOKEN, TOKEN_TEST
import requests
from time import sleep
from geopy import distance
import random


global COORDS, SKIP
COORDS = {} # словарь с последними координатами которые отправили пользователи
SKIP = {} #  сколько фото пропускать от текущей точки для поиска в запросе


def get_photos(latitude, longitude, distance=1000, limit=10, skip=0):
	'''
		посылаем запрос на pastvu api, с параметрами широты, долготы, максимальным расстроянием от точки, количество фотографий и сколько фото пропускать от точки

		возвращает список со словарями о фото, пример:
		{'cid': 449459,
		 'dir': 'nw',
		 'file': 't/t/m/ttmrs80811yfro4md7.jpeg',
		 'geo': [37.82287, -122.474985],
		 's': 5,
		 'title': 'View of the Marin Tower of the Golden Gate Bridge under construction',
		 'year': 1934}
	'''

	url = f'https://pastvu.com/api2?method=photo.giveNearestPhotos&params={{"geo":{[latitude, longitude]},"distance":{distance},"limit":{limit}, "skip":{skip}}}'
	req = requests.get(url)

	result = req.json()['result']['photos']

	return result

def send_photo(photo_url):
	# функция чтобы отправить одну фотограффию, принимает на вход юрл фото

	context.bot.sendPhoto(
						chat_id = chat_id,
						photo = photo_url
						)

def photos_to_InputMediaPhotos(update, context, photos):
	'''
		преобразует список photos в список из объектов типа InputMediaPhoto чтобы потом передать их в send_media_group
	'''

	media = []

	for photo in photos:
		photo_url = f"https://pastvu.com/_p/d/{photo['file']}"

		caption = f"{photo['year']}, {photo['title']}"

		distance_between_points = int(distance.geodesic((COORDS[update.effective_message.chat_id][0], COORDS[update.effective_message.chat_id][1]), (photo['geo'][0], photo['geo'][1])).km)

		if distance_between_points > 2:
			caption += "\n\nрасстояние от фото до вашей точки: {distance_between_points} км."
		
		media.append(InputMediaPhoto(media=photo_url, caption=caption))

	return media

def send_photos(update, context, photos):
	'''
		отправяет группу фото в одном сообщении, если одно или нексолько url фотограффий не подходят телеграмму, то мы обрабатываем ошибку:
		отсылаем по одному фото в другой чат и смотрим где всплывает ошибка, а где нет.

		* на будущее добавить с помощью sendChatAction событие что бот загружает фото, т.к. нужно некоторое время на загрузку
	'''

	if len(photos) >= 1:

		media = photos_to_InputMediaPhotos(update, context, photos)
		
		try:
			a = context.bot.send_media_group(
										chat_id = update.effective_message.chat_id,
										media = media
										)

		except error.BadRequest:
			fit_photos = []

			for photo in photos:
				try:
					context.bot.sendPhoto(
								chat_id = 824963451,
								photo = f"https://pastvu.com/_p/d/{photo['file']}"
								)

					fit_photos.append(photo)
				except:
					context.bot.send_message(
							chat_id = 824963451,
							text = f"Error url: https://pastvu.com/_p/d/{photo['file']}"
							)

			send_photos(update, context, fit_photos)
	else:
		context.bot.send_message(
							chat_id = update.effective_message.chat_id,
							text = "К сожалению по фашему запросу ничего не нашлось:("
							)

def start(update, context):
	text = "­Отправьте мне свою геолокацию и я вам покажу как выглядело это место в прошлом."
	chat_id = update.effective_message.chat_id

	context.bot.send_message(
							chat_id = chat_id,
							text = text,
							reply_markup = get_keyboard()
							)

def any_message(update, context):
	'''
		обработчик команды /start и любого текстового сообщения
	'''

	chat_id = update.effective_message.chat_id

	if update.effective_message.text == "Еще фото":

		if chat_id in COORDS.keys():
			SKIP[chat_id] += 10

			photos = get_photos(COORDS[chat_id][0], COORDS[chat_id][1], distance=1000000, limit=10, skip = SKIP[chat_id])
			send_photos(update, context, photos)
		else:
			context.bot.send_message(
								chat_id = chat_id,
								text = "Для начала отправь свою геопозицию:)"
								)
	else:
		context.bot.send_message(
								chat_id = chat_id,
								text = "Отправь мне свою геолокацию и я покажу как выглядело это место в прошлом."
								)

def get_keyboard():

	keyboard = [
				[KeyboardButton("Отправить геолокацию", request_location=True)],
				[KeyboardButton("Еще фото")]
				]

	return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_location(update, context):
	'''
		функция-обработчик, когда пользователь отсылает геолокацию
	'''

	chat_id = update.effective_message.chat_id
	# print('\n\n', update)

	latitude = update.message.location.latitude # широта
	longitude = update.message.location.longitude # долгота

	COORDS[chat_id] = [latitude, longitude]
	SKIP[chat_id] = 0

	photos = get_photos(latitude, longitude, distance=1000000, limit=10, skip = SKIP[chat_id])
	# print(photos, '\n\n')

	send_photos(update, context, photos)

def test_message(update, context):

	for _ in range(10):

		latitude = random.triangular(-90,90)
		longitude = random.triangular(-180,180)

		context.bot.send_message(
								chat_id = update.effective_message.chat_id,
								text = f'{latitude}, {longitude}'
								)

		photos = get_photos(latitude, longitude, distance=1000000)

		send_photos(update, context, photos)

		sleep(1)


def main():
	print("Бот запущен. Нажмите ctrl + C чтобы его выключить")

	updater = Updater(token=TOKEN, use_context=True)

	start_handler = CommandHandler('start', start)
	test_handler = CommandHandler('test', test_message)
	message_handler = MessageHandler(Filters.text, any_message)
	location_handler = MessageHandler(Filters.location, get_location)

	updater.dispatcher.add_handler(start_handler)
	updater.dispatcher.add_handler(message_handler)
	updater.dispatcher.add_handler(test_handler)
	updater.dispatcher.add_handler(location_handler)

	updater.start_polling()
	updater.idle()


if __name__ == '__main__':
	main()