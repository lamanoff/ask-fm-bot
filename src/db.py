from pymongo import MongoClient
import os


client = MongoClient(os.environ['CONNECTION_STRING'])
db = client['AskFM']

users = db['users']
messages = db['messages']


def add_user(user_id, username, datetime):
    user_filter = {
        'user_id': user_id
    }
    user = users.find_one(user_filter)
    if user and user['status'] == 'deleted':
        update = {
            'status': 'active'
        }
        users.update_one(user_filter, {'$set': update})
        return
    elif user:
        return
    data = {
        'user_id': user_id,
        'username': username,
        'datetime': datetime,
        'status': 'active'
    }
    users.insert_one(data)


def delete_user(user_id):
    user_filter = {
        'user_id': user_id
    }
    update = {
        'status': 'deleted'
    }
    users.update_one(user_filter, {'$set': update})


def add_message(user_id_from, user_id_to, username_from, username_to, content, message_type, datetime):
    message = {
        "user_id_from": user_id_from,
        "user_id_to": user_id_to,
        "username_from": username_from,
        "username_to": username_to,
        "content": content,
        "message_type": message_type,
        "datetime": datetime
    }
    messages.insert_one(message)
