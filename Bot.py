#!/usr/bin/env python
# coding: utf-8

import requests
import json
import bs4

from telegram.ext import Updater, MessageHandler, CommandHandler, Filters


def get_synonyms(word, model="tayga_upos_skipgram_300_2_2019"):
    url = "https://rusvectores.org/"+model+"/"+word+"/api/json"
    res = requests.get(url).text
    ans = json.loads(res)
    words = list(ans[model].values())[0]
    return words


def get_distance(word1, word2, model="tayga_upos_skipgram_300_2_2019"):
    url = '/'.join(['https://rusvectores.org', model, word1 + '__' + word2, 'api', 'similarity/'])
    res = requests.get(url).text.split()[0]
    try:
        return 1-float(res)
    except:
        return None


def calculate(pos, neg, model="geowac_lemmas_none_fasttextskipgram_300_5_2020"):
    r = requests.post("https://rusvectores.org/ru/calculator/", data={
        "positive1": pos, 
        "negative1": neg,
        "calcmodel": model
    })
    soup = bs4.BeautifulSoup(r.text)
    ol = soup.find("ol")
    words = ol.get_text().split()
    res = dict()
    for i in range(0, len(words), 2):
        res[words[i]] = 1 - float(words[i+1])
    return res


class Bot:
    def __init__(self, token):
        self.updater = Updater(token)
        self.command = ""
        self.show_distances = False
        self.model = "geowac_lemmas_none_fasttextskipgram_300_5_2020"
        
    def hello(self, update, context):
        message = '''Привет! Это бот который умеет делать некоторые операции над словами.
        /calculator - подбирает слова похожие по смыслу на алгебраическую сумму слов
        /distance - семантическое расстояние от 0 до 1 между словами
        /synonyms - список синонимов к слову'''
        update.message.reply_text(message)
        
    def calculator(self, update, context):
        self.command = "calculator"
        update.message.reply_text('Пришли мне выражение из слов, "+" и "-"  и я пришлю тебе список слов похожих на результат выражения',
                                  reply_to_message_id=update.message.message_id)
    
    def process_calculate(self, text):
        parsed = {"pos":[], "neg":[]}
        state = "pos"
        for symb in text:
            if symb == "+":
                state = "pos"
                parsed[state].append(" ")
            elif symb == "-":
                state = "neg"
                parsed[state].append(" ")
            else:
                parsed[state].append(symb)
        pos, neg = "".join(parsed["pos"]), "".join(parsed["neg"])
        synonyms = calculate(pos, neg, self.model)
        if len(synonyms) == 0:
            reply_message = "Я не знаю таких слов(а)"
        else:
            reply_message = "\n".join([word for word in synonyms])
            if self.show_distances:
                reply_message = "\n".join([f'{word},  Расстояние до слова: {1-synonyms[word]}' for word in synonyms])
        return reply_message
        
    def distance(self, update, context):
        self.command = "distance"
        update.message.reply_text("Пришли мне 2 слова (через пробел) и я пришлю тебе расстояние (от 0 до 1) между ними",
                                  reply_to_message_id=update.message.message_id)
    def process_distance(self, text):
        words = text.split()[:2]
        if len(words) != 2:
            return "Нужно прислать 2 слова."
        word1, word2 = words
        dist = get_distance(word1, word2, self.model)
        if dist is None:
            return "Я не знаю таких слов"
        return f'Расстояние между "{word1}" и "{word2}" = {dist:.5f}'
        
    def synonyms(self, update, context):
        self.command = "synonyms"
        update.message.reply_text("Пришли мне слово и я пришлю тебе список слов похожих на него",
                                  reply_to_message_id=update.message.message_id)
    
    def process_synonyms(self, word):
        synonyms = get_synonyms(word, self.model)
        if synonyms is None:
            reply_message = "Я не знаю такого слова"
        else:
            reply_message = "\n".join([word for word in synonyms])
            if self.show_distances:
                reply_message = "\n".join([f'{word},  Расстояние до слова: {1-synonyms[word]}' for word in synonyms])
        return reply_message
    
    def reply(self, update, context):
        reply_message = "Выбери одну из комманд"
        if self.command == "distance":
            reply_message = self.process_distance(update.message.text)
        elif self.command == "synonyms":
            reply_message = self.process_synonyms(update.message.text)
        elif self.command == "calculator":
            reply_message = self.process_calculate(update.message.text)
        update.message.reply_text(reply_message, reply_to_message_id=update.message.message_id)
        self.command = ""
    
    def enable_distances(self, update, context):
        self.show_distances = not self.show_distances
        message = "Показ расстояний до слов выключен"
        if self.show_distances:
            message = "Показ расстояний до слов включён"
        update.message.reply_text(message, reply_to_message_id=update.message.message_id)
    
    def start_polling(self):
        self.updater.dispatcher.add_handler(CommandHandler('help', self.hello))
        self.updater.dispatcher.add_handler(CommandHandler('synonyms', self.synonyms))
        self.updater.dispatcher.add_handler(CommandHandler('calculator', self.calculator))
        self.updater.dispatcher.add_handler(CommandHandler('distance', self.distance))
        self.updater.dispatcher.add_handler(CommandHandler('start', self.hello))
        self.updater.dispatcher.add_handler(CommandHandler('show_distances', self.enable_distances))
        self.updater.dispatcher.add_handler(MessageHandler(Filters.text, self.reply))
        
        self.updater.start_polling()
        self.updater.idle()


bot = Bot('TOKEN')


bot.start_polling()

