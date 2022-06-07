from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import InputMediaPhoto, error
from config import TOKEN, TOKEN_TEST
import requests
from time import sleep
from geopy import distance

def get_photos(latitude, longitude, distance=1000, limit=10):
	'''
	'''

	url = f'https://pastvu.com/api2?method=photo.giveNearestPhotos&params={{"geo":{[latitude, longitude]},"distance":{distance},"limit":{limit}}}'
	req = requests.get(url)

	result = req.json()['result']['photos']

	if result:
		return result
	else:
		return False

def any_message(update, context):

	text = "Отправьте мне свою геолокацию и я вам покажу как выглядело это место в прошлом."
	chat_id = update.effective_message.chat_id

	context.bot.send_message(
							chat_id = chat_id,
							text = text
							)

def get_location(update, context):

	chat_id = update.effective_message.chat_id
	print('\n\n', update)

	latitude = update.message.location.latitude # широта
	longitude = update.message.location.longitude # долгота

	photos = get_photos(latitude, longitude, distance=1000000)
	print(photos, '\n\n')



	try:

		media = [InputMediaPhoto(media=f"https://pastvu.com/_p/d/{photo['file']}?random=42", caption=f"{photo['year']}, {photo['title']}\n\nрасстояние места фото от вашей точки: {int(distance.geodesic((latitude, longitude), (photo['geo'][0], photo['geo'][1])).m)} м.") for photo in photos]

		context.bot.send_media_group(
									chat_id = chat_id,
									media = media
									
									)
	except error.BadRequest as err:
		print('Error -', err)








def main():
	print("Бот запущен. Нажмите ctrl + C чтобы его выключить")

	updater = Updater(token=TOKEN_TEST, use_context=True)

	start_handler = CommandHandler('start', any_message)
	message_handler = MessageHandler(Filters.text, any_message)
	location_handler = MessageHandler(Filters.location, get_location)

	updater.dispatcher.add_handler(start_handler)
	updater.dispatcher.add_handler(message_handler)
	updater.dispatcher.add_handler(location_handler)

	updater.start_polling()
	updater.idle()


if __name__ == '__main__':
	main()