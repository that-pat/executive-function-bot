import time
import json
import requests
import schedule
import urllib

from CREDENTIALS import *
from dbhelper import DBHelper
import todo_list as todo
import feeling_tracker as ft

db = DBHelper()
URL = "https://api.telegram.org/bot{}/".format(TOKEN)

def get_url(url):
  response = requests.get(url)
  content = response.content.decode("utf8")
  return content

def get_json_from_url(url):
  content = get_url(url)
  js = json.loads(content)
  return js

def get_updates(offset=None):
  url = URL + "getUpdates?timeout=100"
  if offset:
    url += "&offset={}".format(offset)
  js = get_json_from_url(url)
  return js

def get_last_update_id(updates):
  update_ids = []
  for update in updates["result"]:
    update_ids.append(int(update["update_id"]))
  return max(update_ids)

def send_message(text, chat_id, reply_markup=None):
  text = urllib.quote_plus(text)
  url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
  if reply_markup:
    url += "&reply_markup={}".format(reply_markup)
  get_url(url)

def build_keyboard(items):
  keyboard = [[item] for item in items]
  reply_markup = {"keyboard":keyboard, "one_time_keyboard": True}
  return json.dumps(reply_markup)

def command_handler(text, chat_id):
  todoitems = db.get_items(chat_id)
  if text == "/start":
    start_message = """Welcome to the Executive Function Bot. I'm here to
    help you get things done. For now, I operate as a traditional To Do list.
    Tell me things that you want to do and use /done to mark them complete.
    """
    send_message(start_message, chat_id)
  elif text == "/addtodo":
    send_message("What do you need to do?", chat_id)
    return "addtodo"
  elif text == "/finishtodo":
    keyboard = build_keyboard(todoitems)
    send_message("Select an item to mark complete", chat_id, keyboard)
    return "removetodo"
  elif text == "/starttrackingfeelings":
    send_message("Feeling Tracking Enabled", chat_id)
    options = ["Daily", "A few times a day", "Hourly"]
    keyboard = build_keyboard(options)
    send_message("How often would you like to talk about your feelings?", chat_id, keyboard)
    return "configfeelingtrackingfrequency"
  elif text == "/debug":
    ft.debug(chat_id)
  else:
    send_message("I'm sorry, I don't know that command. Use /help for a list of commands.", chat_id)

def listener_handler(listener, text, chat_id):
  if listener == "removetodo":
    todo.remove_item_from_list(text, chat_id)
    send_message(todo.get_item_list(chat), chat_id)
  elif listener == "addtodo":
    todo.add_item_to_list(text, chat)
    send_message(todo.get_item_list(chat), chat)
  elif listener == "configfeelingtrackingfrequency":
    ft.set_frequency(chat, text)
    options = ["Morning", "Afternoon", "Evening", "Throughout the day"]
    keyboard = build_keyboard(options)
    send_message("Do you have a preference of when you want to talk about your feelings?", chat, keyboard)
    return "configfeelingtrackingtime"
  elif listener == "configfeelingtrackingtime":
    ft.set_time_pref(chat, text)
    send_message("Thanks for letting me know!", chat)
  else:
    print listener
    continue

def handle_updates(updates, listener):
  for update in updates["result"]:
    text = update["message"]["text"]
    chat = update["message"]["chat"]["id"]

    if text.startswith("/"):
      return command_handler(text, chat)
    elif listener is not None:
      return listener_handler(listener, text, chat)
    elif text == "end":
      return None
    else:
      continue

def main():
  db.setup()
  last_update_id = None
  listener = None
  while True:
    updates = get_updates(last_update_id)
    if len(updates["result"]) > 0:
      last_update_id = get_last_update_id(updates) + 1
      listener = handle_updates(updates, listener)
    schedule.run_pending()
    time.sleep(0.5)

if __name__ == '__main__':
  main()
send_message(text, chat)
