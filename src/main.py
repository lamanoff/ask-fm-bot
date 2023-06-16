from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.deep_linking import get_start_link
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.deep_linking import decode_payload
from aiogram.dispatcher import FSMContext
from aiogram.types import ChatMemberUpdated, ContentType, InlineKeyboardButton, InlineKeyboardMarkup
import logging
import db
import time
import re
import os


API_TOKEN = os.environ['API_TOKEN']

answer_regexp = re.compile("answer_(.*)")
logging.basicConfig(level=logging.DEBUG)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

channels_to_subscribe = []
channel_links = []


class Stage(StatesGroup):
    send_message_to = State()


async def check_subscription(user_id):
    result = True
    for channel in channels_to_subscribe:
        chat_member = await bot.get_chat_member(channel, user_id)
        result = result and chat_member['status'] != 'left'
    return result


@dp.message_handler(commands=['start'], state=['*', Stage.send_message_to])
async def start(message: types.Message, state: FSMContext):
    is_subscribed = await check_subscription(message.from_user.id)
    inline_kb = InlineKeyboardMarkup()
    if not is_subscribed:
        for channel_link in channel_links:
            inline_btn = InlineKeyboardButton('Channel', url=channel_link)
            inline_kb.add(inline_btn)
        await message.answer('Please subscribe to the channels to use the bot.', reply_markup=inline_kb)
        return
    args = message.get_args()
    payload = decode_payload(args)
    if payload:
        async with state.proxy() as data:
            data['user-id'] = payload
        await Stage.send_message_to.set()
        start_text = """Send an anonymous message to this person who posted this link.

Write here everything you think about him in one message and in a few moments he will receive it, but he will not know who it is from.

👀 You can send text, voice message, photo or video."""
        await message.reply(start_text)
        db.add_user(message.from_user.id, message.from_user.username, time.time())
        return
    link = await get_start_link(message.from_user.id, encode=True)
    content = f"""❗️INSTRUCTIONS FOR USE:
1. Copy this link: {link}

2. Paste it into the profile description or insta-story, AS IN THE SCREENSHOT

3. We are waiting for anonymous questions :)

P.S. the link is personal, by clicking on it, the person will send a message to YOU"""
    with open('inst.jpg', 'rb') as photo:
        await message.answer_photo(caption=content, photo=photo)
    db.add_user(message.from_user.id, message.from_user.username, time.time())


@dp.my_chat_member_handler()
async def add_to_channel(update: ChatMemberUpdated):
    if update.new_chat_member.status == 'member':
        db.add_user(update.from_user.id, update.from_user.username, time.time())
    elif update.new_chat_member.status == 'kicked':
        db.delete_user(update.from_user.id)


@dp.message_handler(state=Stage.send_message_to, content_types=ContentType.ANY)
async def process_message(message: types.Message, state: FSMContext):
    is_subscribed = await check_subscription(message.from_user.id)
    inline_kb = InlineKeyboardMarkup()
    if not is_subscribed:
        for channel_link in channel_links:
            inline_btn = InlineKeyboardButton('Channel', url=channel_link)
            inline_kb.add(inline_btn)
        await message.answer('Please subscribe to the channels to use the bot.', reply_markup=inline_kb)
        return
    inline_btn = InlineKeyboardButton('Reply', callback_data=f'answer_{message.from_user.id}')
    inline_btn2 = InlineKeyboardButton('Share the reply on Instagram', url='https://www.instagram.com/')
    inline_kb = InlineKeyboardMarkup().add(inline_btn)
    inline_kb = inline_kb.add(inline_btn2)
    async with state.proxy() as data:
        if 'answer_user_id' in data:
            user_id = data['answer_user_id']
            await message.answer("Your response has been delivered.")
            await message.bot.send_message(user_id,
                                           'You got an answer. To ask a question to a person again, follow his link again.')
        else:
            user_id = data['user-id']
            await message.answer(
                "Your message has been sent. To ask a question to a person again, follow his link again.")
            await message.bot.send_message(user_id, 'You have received a new anonymous message.')
        if message.video:
            await message.bot.send_video(user_id, message.video.file_id, reply_markup=inline_kb)
            content = message.video.as_json()
        elif message.video_note:
            await message.bot.send_video_note(user_id, message.video_note.file_id, reply_markup=inline_kb)
            content = message.video_note.as_json()
        elif message.voice:
            await message.bot.send_voice(user_id, message.voice.file_id, reply_markup=inline_kb)
            content = message.voice.as_json()
        elif message.photo:
            await message.bot.send_photo(user_id, message.photo[-1].file_id, reply_markup=inline_kb)
            content = message.photo[-1].as_json()
        elif message.audio:
            await message.bot.send_audio(user_id, message.audio.file_id, reply_markup=inline_kb)
            content = message.audio.as_json()
        elif message.sticker:
            await message.bot.send_sticker(user_id, message.sticker.file_id, reply_markup=inline_kb)
            content = message.sticker.file_id
        elif message.document:
            await message.bot.send_document(user_id, message.document.file_id, reply_markup=inline_kb)
            content = message.document.as_json()
        else:
            await message.bot.send_message(user_id, message.text, reply_markup=inline_kb)
            content = message.text
    await state.finish()
    user_to = await bot.get_chat_member(user_id, user_id)
    if 'answer_user_id' in data:
        message_type = 'answer'
    else:
        message_type = 'question'
    db.add_message(message.from_user.id,
                   user_id, message.from_user.username,
                   user_to.user.username, content,
                   message_type, time.time())


@dp.callback_query_handler(lambda c: answer_regexp.match(c.data), state=['*', Stage.send_message_to])
async def process_callback_answer(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 'Enter your answer (voice, picture, video, text).')
    async with state.proxy() as data:
        data['answer_user_id'] = answer_regexp.match(callback_query.data).group(1)
    await Stage.send_message_to.set()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False)
