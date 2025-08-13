import os
import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

def handler(request):

    CHEKIBOT_API = os.getenv('CHEKIBOT_API')
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

    if not TELEGRAM_TOKEN or not CHEKIBOT_API:
        return{"statusCode": 500, "body": "Configuration error"}
    
    try:        

        bot = telegram.Bot(token=TELEGRAM_TOKEN)

    
        update = request.get_json()

        if "message" in update and "text" in update["message"]:
            chat_id = update["message"]["chat"]["id"]
            delivered_message = update["message"]["text"]

            payload = {'message': delivered_message}
            api_answer = requests.post(CHEKIBOT_API, json=payload, timeout=10)
            api_answer.raise_for_status()

            data_response = api_answer.json()
            response_text = data_response.get('response', " ")
            bot.send_message(chat_id=chat_id, text=response_text)

    except Exception as e:
        print(f"Error:{e}")

    return {"statusCode": 200, "body": "ok"}




