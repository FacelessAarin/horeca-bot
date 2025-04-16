from telethon import TelegramClient, events
from telethon.tl.types import PeerChannel
from telethon.errors import ChatAdminRequiredError

# 🔐 Авторизация (получается на https://my.telegram.org)
api_id = 17134534
api_hash = 'dd0e321c20c70dcd3cf02c37e5e4bd0f'
session_name = 'session_name'

# Создаем клиент
client = TelegramClient(session_name, api_id, api_hash)

# Каналы-доноры
DONOR_CHANNEL_IDS = [1154390431, 1856710191, 1921683930, 2084414005, 1344709112, 1268637091]
DONOR_CHANNELS = [PeerChannel(cid) for cid in DONOR_CHANNEL_IDS]

# Словарь: профессия -> (ID целевого канала, список ключевых слов)
TARGET_KEYWORDS = {
    'официант': (2289621358, ['официант', 'раннер', 'ранер', 'кейтеринг', 'старший официант',
                                 'помощник официанта', 'помощники официанта', 'старшие официанты']),
    'бармен': (2511495952, ['бармен', 'барледи', 'старший бармен', 'старшего бармена', 'ст. бармен',
                               'помощник бармена', 'барбэк', 'барбек', 'бармен заготовщик',
                               'барменеджер', 'бар-менеджер', 'шеф бармен', 'шеф-бармен', 'баршеф',
                               'бармен-официант']),
    'повар': (2595981035, ['повар', 'пиццайло', 'шаурмист', 'мангальщик', 'сушист', 'пекарь', 'пекари', 'кассир']),
    'бариста': (2687781555, ['бариста', 'помощник бариста', 'старший бариста', 'бариста официант',
                                'бариста-официант', 'бариста кассир', 'бариста-кассир', 'старшие бариста']),
    'админ': (2355992608, ['админ', 'администратор', 'хостес', 'менеджер'])
}

# Конвертируем в словарь: channel_id -> keywords
TARGET_CHANNELS_KEYWORDS = {
    cid: keywords for (_, (cid, keywords)) in TARGET_KEYWORDS.items()
}

# Канал для логирования всех сообщений, отправленных по ключевым словам
LOG_CHANNEL = PeerChannel(2498119483)

# Специальный канал для "бармен без опыта"
SPECIAL_CHANNEL = PeerChannel(2160325613)

PROFESSION_KEYWORDS = ['бармен', 'барбэк', 'барбек', 'старший бармен', 'бар']
EXPERIENCE_KEYWORDS = [
    'без опыта', 'опыт не важен', 'опыт не нужен', 'опыт  не требуется'
    'минимальный опыт', 'рассмотрим без опыта', 'начинающий', 'можно без опыта'
    'опыт не проблема', 'опыт работы барменом не требуется', 'опыт работы барменом не нужен'
    'опыт работы барменом не важен', 'опыт барменом не требуется', 'опыт барменом не нужен'

]

def matches_special_case(text):
    text_lower = text.lower()
    has_profession = any(p in text_lower for p in PROFESSION_KEYWORDS)
    has_experience = any(e in text_lower for e in EXPERIENCE_KEYWORDS)
    return has_profession and has_experience

# Обработка сообщений
@client.on(events.NewMessage(chats=DONOR_CHANNELS))
async def handler(event):
    message = event.message

    if not message.text and not message.media:
        return

    text_lower = (message.text or '').lower()
    sent_to_log = False

    for target_channel_id, keywords in TARGET_CHANNELS_KEYWORDS.items():
        # Проверка на "кассир" и "бариста"
        if 'кассир' in text_lower and 'бариста' in text_lower:
            if target_channel_id == 2671760244:  # Канал для бариста
                try:
                    await client.send_message(PeerChannel(target_channel_id), message)
                    print(f"Отправлено в канал бариста: {target_channel_id}")

                    if not sent_to_log:
                        await client.send_message(LOG_CHANNEL, message)
                        print(f"Дублировано в лог: {LOG_CHANNEL.channel_id}")
                        sent_to_log = True
                except ChatAdminRequiredError:
                    print(f"Нет прав админа для канала {target_channel_id}")
                except Exception as e:
                    print(f"Ошибка при отправке в канал бариста: {e}")

        # Если текст содержит ключевые слова для текущего канала
        elif any(keyword in text_lower for keyword in keywords):
            try:
                await client.send_message(PeerChannel(target_channel_id), message)
                print(f"Отправлено в: {target_channel_id}")

                if not sent_to_log:
                    await client.send_message(LOG_CHANNEL, message)
                    print(f"Дублировано в лог: {LOG_CHANNEL.channel_id}")
                    sent_to_log = True

            except ChatAdminRequiredError:
                print(f"Нет прав админа для канала {target_channel_id}")
            except Exception as e:
                print(f"Ошибка при отправке в {target_channel_id}: {e}")

    if message.text and matches_special_case(message.text):
        try:
            await client.send_message(SPECIAL_CHANNEL, message)
            print(f"Спец-отправка: бармен без опыта → {SPECIAL_CHANNEL.channel_id}")
        except Exception as e:
            print(f"Ошибка при отправке в спец-канал: {e}")

# Запуск
client.start()
client.run_until_disconnected()
