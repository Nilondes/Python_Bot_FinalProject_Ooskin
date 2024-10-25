from dotenv import load_dotenv
import os, telebot, datetime, logging, psycopg2, re
from bot.functions import User, Ad, SearchCriteria, AdComments


load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('DATABASE_HOST'),
    database=os.getenv('DATABASE_DB'),
    user=os.getenv('DATABASE_USER'),
    password=os.getenv('DATABASE_PASSWORD'),
    port='5432'
)

bot_token = os.getenv('BOT_TOKEN')

users = User(conn)

ads = Ad(conn)

criteria = SearchCriteria(conn)

comments = AdComments(conn)

bot = telebot.TeleBot(bot_token)

sessions = {}


@bot.message_handler(commands=['start', 'back'])
def main(message):
    try:
        username = message.from_user.username
        chat_id = message.from_user.id
        users.create_user(chat_id, username)
        keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        start_menu = telebot.types.KeyboardButton("/back")
        keyboard.add(start_menu)
        if users.check_username(chat_id)[1]:
            bot.send_message(chat_id, text=f'Hello {username}'
                                           f'\n'
                                           f'\n'
                                           f'/pending_ads, /pending_comments', reply_markup=keyboard)
        else:
            bot.send_message(chat_id, text=f'Hello {username}'
                                       f'\n'
                                       f'\n'
                                       f'/create_ad, /search_criteria, /search_ads, /my_ads', reply_markup=keyboard)

    except Exception as e:
        bot.send_message(message.from_user.id, text='An error occurred')
        logging.error(f"Error occurred: {e}")


@bot.message_handler(commands=['create_ad'])
def create_ad(message):
    if not users.check_username(message.chat.id):
        return None
    try:
        bot.send_message(message.from_user.id, text='Please, enter ad name')
        bot.register_next_step_handler(message, create_ad_name)
    except Exception as e:
        bot.send_message(message.from_user.id, text='An error occurred')
        logging.error(f"Error occurred: {e}")


def create_ad_name(message):
    try:
        if message.text.startswith('/'):
            raise ValueError
        sessions[message.chat.id] = {'name': message.text}
        sessions[message.chat.id].update({'user': message.from_user.username})
        bot.send_message(message.from_user.id, text='Please, enter ad start date (use format YYYY-MM-DD)')
        bot.register_next_step_handler(message, create_ad_start_date)
    except ValueError:
        sessions[message.chat.id] = {}
        bot.send_message(message.from_user.id, text='Name cannot start with "/"')
    except Exception as e:
        sessions[message.chat.id] = {}
        bot.send_message(message.from_user.id, text='An error occurred')
        logging.error(f"Error occurred: {e}")


def create_ad_start_date(message):
    try:
        ad_start_date = datetime.datetime.strptime(message.text, '%Y-%m-%d').date()
    except ValueError as err:
        sessions[message.chat.id] = {}
        bot.send_message(message.from_user.id, text='The date has unknown format '
                                                    'Please, use YYYY-MM-DD.')
    except Exception as e:
        sessions[message.chat.id] = {}
        bot.send_message(message.from_user.id, text='An error occurred')
        logging.error(f"Error occurred: {e}")
    else:
        sessions[message.chat.id].update({'start_date': str(ad_start_date)})
        bot.send_message(message.from_user.id, text='Please, enter ad end date (use format YYYY-MM-DD)')
        bot.register_next_step_handler(message, create_ad_end_date)


def create_ad_end_date(message):
    try:
        ad_end_date = datetime.datetime.strptime(message.text, '%Y-%m-%d').date()
    except ValueError as err:
        sessions[message.chat.id] = {}
        bot.send_message(message.from_user.id, text='The date has unknown format '
                                                    'Please, use YYYY-MM-DD.')
    except Exception as e:
        sessions[message.chat.id] = {}
        bot.send_message(message.from_user.id, text='An error occurred')
        logging.error(f"Error occurred: {e}")
    else:
        if ad_end_date <= datetime.datetime.strptime(sessions[message.chat.id]['start_date'], '%Y-%m-%d').date():
            sessions[message.chat.id] = {}
            bot.send_message(message.from_user.id, text='The end date cannot be less than start')
            return None
        sessions[message.chat.id].update({'end_date': str(ad_end_date)})
        bot.send_message(message.from_user.id, text='Please, enter the price')
        bot.register_next_step_handler(message, create_ad_price)


def create_ad_price(message):
    try:
        ad_price = round(float(message.text), 2)
        if ad_price < 0.01:
            raise ValueError
        sessions[message.chat.id].update({'price': ad_price})
        bot.send_message(message.from_user.id, text='Please, enter description')
        bot.register_next_step_handler(message, create_ad_description)
    except ValueError:
        sessions[message.chat.id] = {}
        bot.send_message(message.from_user.id, text='The price should be decimal and more then 0.01')

    except Exception as e:
        sessions[message.chat.id] = {}
        bot.send_message(message.from_user.id, text='An error occurred')
        logging.error(f"Error occurred: {e}")


def create_ad_description(message):
    try:
        if message.text.startswith('/'):
            raise ValueError
        ad_description = message.text
        sessions[message.chat.id].update({'description': ad_description})
        bot.send_message(message.from_user.id, text='Please, enter ad location')
        bot.register_next_step_handler(message, create_ad_location)
    except ValueError:
        sessions[message.chat.id] = {}
        bot.send_message(message.from_user.id, text='Description cannot start with "/"')
    except Exception as e:
        sessions[message.chat.id] = {}
        bot.send_message(message.from_user.id, text='An error occurred')
        logging.error(f"Error occurred: {e}")


def create_ad_location(message):
    try:
        if message.text.startswith('/'):
            raise ValueError
        ad_location = message.text
        sessions[message.chat.id].update({'location': ad_location})
        bot.send_message(message.from_user.id, text='Please, enter phone in format "+7(123)456-78-90"')
        bot.register_next_step_handler(message, create_ad_phone)
    except ValueError:
        sessions[message.chat.id] = {}
        bot.send_message(message.from_user.id, text='Location cannot start with "/"')
    except Exception as e:
        sessions[message.chat.id] = {}
        bot.send_message(message.from_user.id, text='An error occurred')
        logging.error(f"Error occurred: {e}")


def create_ad_phone(message):
    try:
        ad_phone = message.text
        phone_pattern = r"^\+7\(\d{3}\)\d{3}-\d{2}-\d{2}$"
        if not re.match(phone_pattern, ad_phone):
            raise ValueError
        sessions[message.chat.id].update({'phone': ad_phone})
        ad_id = ads.create_ad(sessions[message.chat.id])
        sessions[message.chat.id] = {}
        bot.send_message(message.from_user.id, text=f'The ad id {ad_id} has been created')
    except ValueError:
        bot.send_message(message.from_user.id, text='The phone should have format "+7(123)456-78-90"')
    except Exception as e:
        bot.send_message(message.from_user.id, text='An error occurred')
        logging.error(f"Error occurred: {e}")


@bot.message_handler(commands=['pending_ads'])
def show_pending_ads(message):
    if not users.check_username(message.chat.id)[1]:
        return None
    try:
        pending_ads = ads.show_ads(is_approved=(False, ))
        if pending_ads:
            for ad in pending_ads:
                keyboard = telebot.types.InlineKeyboardMarkup()
                key_approve = telebot.types.InlineKeyboardButton(text='Approve', callback_data=f'approved_ad {ad[0]}')
                keyboard.add(key_approve)
                bot.send_message(message.from_user.id, text=f'id: {ad[0]}\n'
                                                            f'name: {ad[1]}\n'
                                                            f'description: {ad[2]}\n'
                                                            f'location: {ad[4]}\n', reply_markup=keyboard)
        else:
            bot.send_message(message.from_user.id, text='There is no pending ads')
    except Exception as e:
        bot.send_message(message.from_user.id, text='An error occurred')
        logging.error(f"Error occurred: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith('approved_ad '))
def change_status(call):
    try:
        status, ad_id = call.data.split()
        ad_id = int(ad_id)
        ads.change_ad_status(ad_id, True)
        bot.send_message(call.message.chat.id, text=f'The status for ad id {ad_id} has been changed to {status}')
        chat_ids = users.get_all_chat_id()
        for chat_id in chat_ids:
            user_criteria = criteria.get(chat_id)
            keywords = tuple(user_criteria['keywords'])
            user_ads = ads.show_ads(keywords=keywords,
                                    min_price=user_criteria['min_price'],
                                    max_price=user_criteria['max_price'])
            for ad in user_ads:
                if ad[0] == ad_id:
                    keyboard = telebot.types.InlineKeyboardMarkup()
                    key_comments = telebot.types.InlineKeyboardButton(text='Show comments',
                                                                      callback_data=f'comments {ad[0]}')
                    keyboard.add(key_comments)
                    bot.send_message(chat_id, text=f'There is new ad that matches your criteria:\n'
                                                   f'\n'
                                                   f'name: {ad[1]}\n'
                                                   f'price: {ad[3]}\n'
                                                   f'dates: {ad[5]} - {ad[6]}\n'
                                                   f'description: {ad[2]}\n'
                                                   f'location: {ad[4]}\n'
                                                   f'Contacts: {ad[7]}, @{ad[9]}', reply_markup=keyboard)
    except Exception as e:
        bot.send_message(call.message.chat.id, text='An error occurred')
        logging.error(f"Error occurred: {e}")


@bot.message_handler(commands=['pending_comments'])
def show_pending_comments(message):
    if not users.check_username(message.chat.id)[1]:
        return None
    try:
        pending_comments = comments.show_comments(is_approved=False)
        if pending_comments:
            for comment in pending_comments:
                keyboard = telebot.types.InlineKeyboardMarkup()
                key_approve = telebot.types.InlineKeyboardButton(text='Approve', callback_data=f'approved_comment {comment[0]}')
                keyboard.add(key_approve)
                bot.send_message(message.from_user.id, text=f'comment id: {comment[0]}\n'
                                                            f'comment: {comment[2]}\n'
                                                            f'user: {comment[3]}\n', reply_markup=keyboard)
        else:
            bot.send_message(message.from_user.id, text='There is no pending comments')
    except Exception as e:
        bot.send_message(message.from_user.id, text='An error occurred')
        logging.error(f"Error occurred: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith('approved_comment '))
def approve_comment(call):
    _, comment_id = call.data.split()
    comment_id = int(comment_id)
    user_id, ad_name = comments.approve_comment(comment_id)
    user_id = int(user_id)
    bot.send_message(call.message.chat.id, text=f'The comment id {comment_id} has been approved')
    bot.send_message(user_id, text=f'You have new comment for ad {ad_name}')


@bot.message_handler(commands=['search_criteria'])
def search_criteria(message):
    if not users.check_username(message.chat.id):
        return None
    try:
        current_criteria = criteria.get(message.chat.id)
        keywords = current_criteria['keywords'] if current_criteria['keywords'] != [] else 'None'
        min_price = current_criteria['min_price']
        max_price = current_criteria['max_price']
        keyboard = telebot.types.InlineKeyboardMarkup()
        key_keywords = telebot.types.InlineKeyboardButton(text='Keywords', callback_data=f'keywords')
        keyboard.add(key_keywords)
        key_min_price = telebot.types.InlineKeyboardButton(text='Minimal price', callback_data=f'min_price')
        keyboard.add(key_min_price)
        key_max_price = telebot.types.InlineKeyboardButton(text='Maximum price', callback_data=f'max_price')
        keyboard.add(key_max_price)
        bot.send_message(message.from_user.id, text=f'Current criteria: Minimum price: {min_price}, Maximum price: {max_price}, Keywords: {keywords}\n\n'
                                                    f'What search criteria do you want to change?',
                         reply_markup=keyboard)

    except Exception as e:
        bot.send_message(message.from_user.id, text='An error occurred')
        logging.error(f"Error occurred: {e}")



@bot.callback_query_handler(func=lambda call: call.data.startswith('keywords'))
def ask_keywords(call):
    try:
        keyboard = telebot.types.InlineKeyboardMarkup()
        key_empty_keywords = telebot.types.InlineKeyboardButton(text='Empty', callback_data=f'empty keywords')
        keyboard.add(key_empty_keywords)
        bot.send_message(call.message.chat.id, text='Please, list keywords separated with spaces or press "Empty" to clear them',
                         reply_markup=keyboard)
        bot.register_next_step_handler(call.message, update_keywords)

    except Exception as e:
        bot.send_message(call.message.chat.id, text='An error occurred')
        logging.error(f"Error occurred: {e}")


def update_keywords(message):
    try:
        try:
            if sessions[message.from_user.id]['empty']:
                sessions[message.from_user.id] = {}
                return None
        except KeyError:
            pass
        keywords = message.text.split()
        current_criteria = criteria.get(message.from_user.id)
        criteria.update(message.from_user.id,
                        keywords=keywords,
                        min_price=current_criteria['min_price'],
                        max_price=current_criteria['max_price'])
        bot.send_message(message.from_user.id, text='The keywords has been updated')

    except Exception as e:
        bot.send_message(message.from_user.id, text='An error occurred')
        logging.error(f"Error occurred: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith('min_price'))
def ask_min_price(call):
    try:
        keyboard = telebot.types.InlineKeyboardMarkup()
        key_empty_keywords = telebot.types.InlineKeyboardButton(text='Empty', callback_data=f'empty min_price')
        keyboard.add(key_empty_keywords)
        bot.send_message(call.message.chat.id, text='Please, enter minimal price or press "Empty" to set 0',
                         reply_markup=keyboard)
        bot.register_next_step_handler(call.message, update_min_price)

    except Exception as e:
        bot.send_message(call.message.chat.id, text='An error occurred')
        logging.error(f"Error occurred: {e}")


def update_min_price(message):
    try:
        try:
            if sessions[message.from_user.id]['empty']:
                sessions[message.from_user.id] = {}
                return None
        except KeyError:
            pass
        min_price = round(float(message.text), 2)
        current_criteria = criteria.get(message.from_user.id)
        criteria.update(message.from_user.id,
                        keywords=current_criteria['keywords'],
                        min_price=min_price,
                        max_price=current_criteria['max_price'])
        bot.send_message(message.from_user.id, text='The minimal price has been updated')

    except ValueError:
        bot.send_message(message.from_user.id, text='The price should be decimal')

    except Exception as e:
        bot.send_message(message.from_user.id, text='An error occurred')
        logging.error(f"Error occurred: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith('max_price'))
def ask_max_price(call):
    try:
        keyboard = telebot.types.InlineKeyboardMarkup()
        key_empty_keywords = telebot.types.InlineKeyboardButton(text='Empty', callback_data=f'empty max_price')
        keyboard.add(key_empty_keywords)
        bot.send_message(call.message.chat.id, text='Please, enter maximum price or press "Empty" to set undefined',
                         reply_markup=keyboard)
        bot.register_next_step_handler(call.message, update_max_price)

    except Exception as e:
        bot.send_message(call.message.chat.id, text='An error occurred')
        logging.error(f"Error occurred: {e}")


def update_max_price(message):
    try:
        try:
            if sessions[message.from_user.id]['empty']:
                sessions[message.from_user.id] = {}
                return None
        except KeyError:
            pass
        max_price = round(float(message.text), 2)
        current_criteria = criteria.get(message.from_user.id)
        if max_price <= current_criteria['min_price']:
            raise ValueError
        criteria.update(message.from_user.id,
                        keywords=current_criteria['keywords'],
                        min_price=current_criteria['min_price'],
                        max_price=max_price)
        bot.send_message(message.from_user.id, text='The maximum price has been updated')

    except ValueError:
        bot.send_message(message.from_user.id, text='The price should be decimal and cannot be less then minimal price')

    except Exception as e:
        bot.send_message(message.from_user.id, text='An error occurred')
        logging.error(f"Error occurred: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith('empty '))
def empty_criteria(call):
    try:
        sessions[call.message.chat.id] = {'empty': True}
        _, criterion = call.data.split()
        current_criteria = criteria.get(call.message.chat.id)
        keywords = current_criteria['keywords'] if criterion != 'keywords' else "{}"
        min_price = current_criteria['min_price'] if criterion != 'min_price' else 0
        max_price = current_criteria['max_price'] if criterion != 'max_price' else 99999.99
        criteria.update(call.message.chat.id,
                        keywords=keywords,
                        min_price=min_price,
                        max_price=max_price)
        bot.send_message(call.message.chat.id, text=f'The {criterion} has been reset')


    except Exception as e:
        bot.send_message(call.message.chat.id, text='An error occurred')
        logging.error(f"Error occurred: {e}")


@bot.message_handler(commands=['search_ads'])
def search_ads(message):
    if not users.check_username(message.chat.id):
        return None
    try:
        current_criteria = criteria.get(message.chat.id)
        keywords = tuple(current_criteria['keywords'])
        current_ads = ads.show_ads(is_approved=(True, ),
                                   min_price=current_criteria['min_price'],
                                   max_price=current_criteria['max_price'],
                                   keywords=keywords)
        if current_ads:
            for ad in current_ads:
                keyboard = telebot.types.InlineKeyboardMarkup()
                key_comments = telebot.types.InlineKeyboardButton(text='Show comments', callback_data=f'comments {ad[0]}')
                keyboard.add(key_comments)
                bot.send_message(message.from_user.id, text=f'name: {ad[1]}\n'
                                                            f'price: {ad[3]}\n'
                                                            f'dates: {ad[5]} - {ad[6]}\n'
                                                            f'description: {ad[2]}\n'
                                                            f'location: {ad[4]}\n'
                                                            f'Contacts: {ad[7]}, @{ad[9]}', reply_markup=keyboard)
        else:
            bot.send_message(message.from_user.id, text='There is no ads with such criteria. Try edit /search_criteria')
    except Exception as e:
        bot.send_message(message.from_user.id, text='An error occurred')
        logging.error(f"Error occurred: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith('comments '))
def show_comments(call):
    try:
        _, ad_id = call.data.split()
        ad_comments = comments.show_comments((ad_id,))
        keyboard = telebot.types.InlineKeyboardMarkup()
        key_add_comment = telebot.types.InlineKeyboardButton(text='Add comment', callback_data=f'add_comment {ad_id}')
        keyboard.add(key_add_comment)
        if ad_comments:
            for comment in ad_comments:
                bot.send_message(call.message.chat.id, text=f'@{comment[2]}: \n'
                                                            f'{comment[1]}')
            bot.send_message(call.message.chat.id, text='You can leave comment here', reply_markup=keyboard)
        else:
            bot.send_message(call.message.chat.id, text='There is no comments for this ad', reply_markup=keyboard)
    except Exception as e:
        bot.send_message(call.message.chat.id, text='An error occurred')
        logging.error(f"Error occurred: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith('add_comment '))
def ask_comment(call):
    try:
        _, ad_id = call.data.split()
        sessions[call.message.chat.id] = {'ad_id': ad_id}
        bot.send_message(call.message.chat.id, text='Please, enter your comment')
        bot.register_next_step_handler(call.message, add_comment)
    except Exception as e:
        bot.send_message(call.message.chat.id, text='An error occurred')
        logging.error(f"Error occurred: {e}")


def add_comment(message):
    try:
        if message.text.startswith('/'):
            raise ValueError
        ad_id = sessions[message.from_user.id]['ad_id']
        comment = {'ad_id': ad_id,
                   'comment': message.text,
                   'user': message.from_user.username}
        comments.create(comment)
        bot.send_message(message.from_user.id, text=f'The comment for ad id {ad_id} has been added')
        sessions[message.from_user.id] = {}
    except ValueError:
        sessions[message.from_user.id] = {}
        bot.send_message(message.from_user.id, text='Comment cannot start with "/"')
    except Exception as e:
        sessions[message.from_user.id] = {}
        bot.send_message(message.from_user.id, text='An error occurred')
        logging.error(f"Error occurred: {e}")


@bot.message_handler(commands=['my_ads'])
def my_ads(message):
    if not users.check_username(message.chat.id):
        return None
    try:
        username = message.from_user.username
        user_ads = ads.show_ads(user=username, is_approved=(True, False))
        if user_ads:
            for ad in user_ads:
                keyboard = telebot.types.InlineKeyboardMarkup()
                key_edit = telebot.types.InlineKeyboardButton(text='Edit', callback_data=f'edit {ad[0]}')
                keyboard.add(key_edit)
                key_remove = telebot.types.InlineKeyboardButton(text='Remove', callback_data=f'remove {ad[0]}')
                keyboard.add(key_remove)
                is_approved = 'Approved' if ad[8] else 'Pending approval'
                bot.send_message(message.from_user.id, text=f'name: {ad[1]}\n'
                                                            f'price: {ad[3]}\n'
                                                            f'dates: {ad[5]} - {ad[6]}\n'
                                                            f'description: {ad[2]}\n'
                                                            f'location: {ad[4]}\n'
                                                            f'Contacts: {ad[7]}, @{ad[9]}\n'
                                                            f'{is_approved}', reply_markup=keyboard)
        else:
            bot.send_message(message.from_user.id, text='You have no ads. Try to /create_ad')
    except Exception as e:
        bot.send_message(message.from_user.id, text='An error occurred')
        logging.error(f"Error occurred: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith('remove '))
def change_status(call):
    _, ad_id = call.data.split()
    ad_id = int(ad_id)
    ads.remove_ad(ad_id)
    bot.send_message(call.message.chat.id, text=f'The ad id {ad_id} has been removed')


@bot.callback_query_handler(func=lambda call: call.data.startswith('edit '))
def change_status(call):
    _, ad_id = call.data.split()
    keyboard = telebot.types.InlineKeyboardMarkup()
    key_name = telebot.types.InlineKeyboardButton(text='Name', callback_data=f'name {ad_id}')
    keyboard.add(key_name)
    key_start_date = telebot.types.InlineKeyboardButton(text='Start date', callback_data=f'start_date {ad_id}')
    keyboard.add(key_start_date)
    key_end_date = telebot.types.InlineKeyboardButton(text='End date', callback_data=f'end_date {ad_id}')
    keyboard.add(key_end_date)
    key_price = telebot.types.InlineKeyboardButton(text='Price', callback_data=f'price {ad_id}')
    keyboard.add(key_price)
    key_description = telebot.types.InlineKeyboardButton(text='Description', callback_data=f'description {ad_id}')
    keyboard.add(key_description)
    key_phone = telebot.types.InlineKeyboardButton(text='Phone', callback_data=f'phone {ad_id}')
    keyboard.add(key_phone)
    key_location = telebot.types.InlineKeyboardButton(text='Location', callback_data=f'location {ad_id}')
    keyboard.add(key_location)
    bot.send_message(call.message.chat.id, text=f'What do you wish to edit?', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data.startswith('name '))
def ask_new_ad_name(call):
    _, ad_id = call.data.split()
    sessions[call.message.chat.id] = {'ad_id': ad_id}
    bot.send_message(call.message.chat.id, text=f'Please, enter new ad name')
    bot.register_next_step_handler(call.message, edit_ad_name)


def edit_ad_name(message):
    try:
        if message.text.startswith('/'):
            raise ValueError
        new_data = message.text
        ad = ads.get_ad_by_id(sessions[message.chat.id]['ad_id'])
        ad.update({'name': new_data})
        ad_id = ads.edit_ad(ad)
        sessions[message.chat.id] = {}
        bot.send_message(message.chat.id, text=f'The ad id {ad_id} has been updated')
    except ValueError:
        sessions[message.chat.id] = {}
        bot.send_message(message.from_user.id, text='Name cannot start with "/"')
    except Exception as e:
        sessions[message.chat.id] = {}
        bot.send_message(message.from_user.id, text='An error occurred')
        logging.error(f"Error occurred: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith('start_date '))
def ask_new_ad_start_date(call):
    _, ad_id = call.data.split()
    sessions[call.message.chat.id] = {'ad_id': ad_id}
    bot.send_message(call.message.chat.id, text=f'Please, enter new ad start date (use format YYYY-MM-DD)')
    bot.register_next_step_handler(call.message, edit_ad_start_date)


def edit_ad_start_date(message):
    try:
        new_data = datetime.datetime.strptime(message.text, '%Y-%m-%d').date()
    except ValueError as err:
        sessions[message.chat.id] = {}
        bot.send_message(message.from_user.id, text='The date has unknown format '
                                                    'Please, use YYYY-MM-DD.')
    except Exception as e:
        sessions[message.chat.id] = {}
        bot.send_message(message.from_user.id, text='An error occurred')
        logging.error(f"Error occurred: {e}")
    else:
        ad = ads.get_ad_by_id(sessions[message.chat.id]['ad_id'])
        if new_data >= ad['end_date']:
            sessions[message.chat.id] = {}
            bot.send_message(message.from_user.id, text='The end date cannot be less than start')
            return None
        ad.update({'start_date': str(new_data)})
        ad_id = ads.edit_ad(ad)
        sessions[message.chat.id] = {}
        bot.send_message(message.chat.id, text=f'The ad id {ad_id} has been updated')


@bot.callback_query_handler(func=lambda call: call.data.startswith('end_date '))
def ask_new_ad_end_date(call):
    _, ad_id = call.data.split()
    sessions[call.message.chat.id] = {'ad_id': ad_id}
    bot.send_message(call.message.chat.id, text=f'Please, enter new ad end date (use format YYYY-MM-DD)')
    bot.register_next_step_handler(call.message, edit_ad_end_date)


def edit_ad_end_date(message):
    try:
        new_data = datetime.datetime.strptime(message.text, '%Y-%m-%d').date()
    except ValueError as err:
        sessions[message.chat.id] = {}
        bot.send_message(message.from_user.id, text='The date has unknown format '
                                                    'Please, use YYYY-MM-DD.')
    except Exception as e:
        sessions[message.chat.id] = {}
        bot.send_message(message.from_user.id, text='An error occurred')
        logging.error(f"Error occurred: {e}")
    else:
        ad = ads.get_ad_by_id(sessions[message.chat.id]['ad_id'])
        if new_data <= ad['start_date']:
            sessions[message.chat.id] = {}
            bot.send_message(message.from_user.id, text='The end date cannot be less than start')
            return None
        ad.update({'end_date': str(new_data)})
        ad_id = ads.edit_ad(ad)
        sessions[message.chat.id] = {}
        bot.send_message(message.chat.id, text=f'The ad id {ad_id} has been updated')


@bot.callback_query_handler(func=lambda call: call.data.startswith('price '))
def ask_new_ad_price(call):
    _, ad_id = call.data.split()
    sessions[call.message.chat.id] = {'ad_id': ad_id}
    bot.send_message(call.message.chat.id, text=f'Please, enter new ad price')
    bot.register_next_step_handler(call.message, edit_ad_price)


def edit_ad_price(message):
    try:
        new_data = round(float(message.text), 2)
        if new_data < 0.01:
            raise ValueError
        ad = ads.get_ad_by_id(sessions[message.chat.id]['ad_id'])
        ad.update({'price': new_data})
        ad_id = ads.edit_ad(ad)
        sessions[message.chat.id] = {}
        bot.send_message(message.chat.id, text=f'The ad id {ad_id} has been updated')
    except ValueError:
        sessions[message.chat.id] = {}
        bot.send_message(message.from_user.id, text='The price should be decimal and more then 0.01')
    except Exception as e:
        sessions[message.chat.id] = {}
        bot.send_message(message.from_user.id, text='An error occurred')
        logging.error(f"Error occurred: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith('description '))
def ask_new_ad_description(call):
    _, ad_id = call.data.split()
    sessions[call.message.chat.id] = {'ad_id': ad_id}
    bot.send_message(call.message.chat.id, text=f'Please, enter new ad description')
    bot.register_next_step_handler(call.message, edit_ad_description)


def edit_ad_description(message):
    try:
        if message.text.startswith('/'):
            raise ValueError
        new_data = message.text
        ad = ads.get_ad_by_id(sessions[message.chat.id]['ad_id'])
        ad.update({'description': new_data})
        ad_id = ads.edit_ad(ad)
        sessions[message.chat.id] = {}
        bot.send_message(message.chat.id, text=f'The ad id {ad_id} has been updated')
    except ValueError:
        sessions[message.chat.id] = {}
        bot.send_message(message.from_user.id, text='Description cannot start with "/"')
    except Exception as e:
        sessions[message.chat.id] = {}
        bot.send_message(message.from_user.id, text='An error occurred')
        logging.error(f"Error occurred: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith('phone '))
def ask_new_ad_phone(call):
    _, ad_id = call.data.split()
    sessions[call.message.chat.id] = {'ad_id': ad_id}
    bot.send_message(call.message.chat.id, text=f'Please, enter new ad phone in format "+7(123)456-78-90"')
    bot.register_next_step_handler(call.message, edit_ad_phone)


def edit_ad_phone(message):
    try:
        new_data = message.text
        phone_pattern = r"^\+7\(\d{3}\)\d{3}-\d{2}-\d{2}$"
        if not re.match(phone_pattern, new_data):
            raise ValueError
        ad = ads.get_ad_by_id(sessions[message.chat.id]['ad_id'])
        ad.update({'phone': new_data})
        ad_id = ads.edit_ad(ad)
        sessions[message.chat.id] = {}
        bot.send_message(message.chat.id, text=f'The ad id {ad_id} has been updated')
    except ValueError:
        sessions[message.chat.id] = {}
        bot.send_message(message.from_user.id, text='The phone should have format "+7(123)456-78-90"')
    except Exception as e:
        sessions[message.chat.id] = {}
        bot.send_message(message.from_user.id, text='An error occurred')
        logging.error(f"Error occurred: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith('location '))
def ask_new_ad_location(call):
    _, ad_id = call.data.split()
    sessions[call.message.chat.id] = {'ad_id': ad_id}
    bot.send_message(call.message.chat.id, text=f'Please, enter new ad location')
    bot.register_next_step_handler(call.message, edit_ad_location)


def edit_ad_location(message):
    try:
        if message.text.startswith('/'):
            raise ValueError
        new_data = message.text
        ad = ads.get_ad_by_id(sessions[message.chat.id]['ad_id'])
        ad.update({'location': new_data})
        ad_id = ads.edit_ad(ad)
        sessions[message.chat.id] = {}
        bot.send_message(message.chat.id, text=f'The ad id {ad_id} has been updated')
    except ValueError:
        sessions[message.chat.id] = {}
        bot.send_message(message.from_user.id, text='Location cannot start with "/"')
    except Exception as e:
        sessions[message.chat.id] = {}
        bot.send_message(message.from_user.id, text='An error occurred')
        logging.error(f"Error occurred: {e}")


bot.infinity_polling(none_stop=True, interval=1)


#ToDo Tests
#ToDo Docker