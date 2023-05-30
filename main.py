import asyncio
import json

import uvicorn
import telegram

from config import TELEGRAM_CHATID, TELEGRAM_TOKEN

"""
This chat
 ├ id: -1001862099073
 ├ title: Acapulco prueba
 └ type: supergroup
 """
bot = telegram.Bot(
    token=TELEGRAM_TOKEN
)


def send_telegram_message(mesage_dict):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(python_telegram_bot(mesage_dict))


async def python_telegram_bot(mensage_dict):
    pretty_json = json.dumps(mensage_dict, indent=2)
    await bot.send_message(
        chat_id=TELEGRAM_CHATID,
        # , reply_markup=keyboard
        text=f'```\n{pretty_json}\n```',
        parse_mode='Markdown'
    )


async def python_telegram_file_bot(document, filename):
    await bot.send_document(
        chat_id=TELEGRAM_CHATID,
        document=document,
        filename=filename,
    )


if __name__ == '__main__':
    uvicorn.run(
        "app:app",
        host='0.0.0.0',
        port=8010,
        reload=True
    )
