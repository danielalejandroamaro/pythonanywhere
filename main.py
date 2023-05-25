import asyncio
import json
import os

import uvicorn
import telegram

"""
This chat
 ├ id: -1001862099073
 ├ title: Acapulco prueba
 └ type: supergroup
 """
bot = telegram.Bot(
    token='6227916110:AAHAmel-za-Jq_Ip9gslGZXTHKQ8SMqdyIo'
)


def send_telegram_message(mesage_dict):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(python_telegram_bot(mesage_dict))


async def python_telegram_bot(mensage_dict):
    pretty_json = json.dumps(mensage_dict, indent=2)
    _id = -1001862099073
    await bot.send_message(
        chat_id=_id,
        # , reply_markup=keyboard
        text=f'```\n{pretty_json}\n```',
        parse_mode='Markdown'
    )


if __name__ == '__main__':
    uvicorn.run(
        "app:app",
        host='0.0.0.0',
        port=8010,
        reload=True
    )
