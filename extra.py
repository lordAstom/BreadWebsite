import logging
import datetime
from config import Data
import json
data = Data()

class Log(object):
    def __init__(self, name, file):
        login_ch = logging.FileHandler(file)
        login_ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
        login_ch.setFormatter(formatter)
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(login_ch)

    def warn(self, message):
        self.logger.warning(message)

    def info(self, message):
        self.logger.info(message)

    def error(self, message):
        self.logger.error(message)
loggin_logger = Log("login ssuccseful", "order_debug.log")

class ReVerify(object):
    def __init__(self, logger):
        self.logger = logger
        self.invalid_values = data.invalid_characters

    def verify_string(self, string):
        string = str(string)
        for letter in string:
            if letter in self.invalid_values:
                self.logger.error("error in string")
                return False
        return True

    def verify_int(self, integer, minimum, maximum):
        try:
            value = int(integer)
            if not (minimum <= value <= maximum):
                self.logger.error(f"invalid integer in loaf form -->{value}")
                return False
            else:
                return True
        except ValueError:
            self.logger.error("non integer in loaf form")
            return False


class OrderViewer(object):
    bread_types = data.bread_types

    def __init__(self, order, lang):
        if lang == "en":
            self.en = True
            self.es = False
            self.message = "Your Order"
        elif lang == "es":
            self.en = False
            self.es = True
            self.message = "Tu pedido:"
            self.tipos_pan = data.tipos_pan
        self.order = order
        self.is_form = False

    def __iter__(self):
        self.a = 0
        return self

    def __next__(self):
        if self.a < min([10, len(self.order)]):
            values = ["first","second","third","fourth","fifth","sixth",
                      "seventh","eighth","ninenth","tenth"]
            b = 1
            self.price = 0
            self.current_order = json.loads(self.order[self.a].order)
            self.date = self.order[self.a].date
            self.order_instance = self.order[self.a]
            self.time_day = self.order[self.a].time_day
            d = self.date.split("-")
            self.date = datetime.date(int(d[0]),int(d[1]),int(d[2])).strftime('%d/%m/%y')
            if self.es:
                if self.time_day == "Morning":
                    self.time_day = "Mañana"
                elif self.time_day == "Evening":
                    self.time_day = "Tarde"
            self.message = ""
            self.customer = self.order[self.a].client
            loggin_logger.info(f"{self.current_order}")
            for bread in self.current_order.keys():
                if self.current_order[bread] == 1:
                    if self.en:
                        self.message += f" 1 {bread.replace('_', ' ')},"
                    elif self.es:
                        self.message += f" 1 {data.tipos_pan[bread]},"
                    self.price += data.prices[bread]
                elif self.current_order[bread] > 1:
                    if self.en:
                        if bread[-1] == "k":
                            self.message += f" {self.current_order[bread]} {bread.replace('_', ' ')}s,"
                        elif bread[-1] == "f":
                            self.message += f" {self.current_order[bread]} {bread.replace('_', ' ')[:-1]}ves,"
                    elif self.es:
                        self.message += f" {self.current_order[bread]} {data.tipos_pan[bread].replace('a d','as d')},"
                    self.price += self.current_order[bread]*data.prices[bread]
                b += 1
                if self.is_form:
                    self.form_data = eval(f"self.form.{values[self.a]}")
            self.a += 1
            try:
                if self.message[-1] == ",":
                    self.message = self.message[:-1]
            except IndexError:
                return self.a
            return self.a
        else:
            raise StopIteration

    def add_form(self, form):
        self.is_form = True
        self.form = form

def valid_day(date, lang):
    days = [2, 5, 6]
    data = date.weekday()
    if data in days:
        if lang == "en":
            return "Current day are not valid"
        elif lang == "es":
            return "Dia Invalido"
    else:
        return

def valid_period(date, period, lang):
    date = date.weekday()
    if date in [0, 1, 3] and period == "Morning":
        if lang == "en":
            return "No bread in the Morning this day"
        elif lang == "es":
            return "No hay pan por la mañana este dia"
    if date == 4 and period == "Evening":
        if lang == "en":
            return "No bread Friday evening"
        elif lang == "es":
            return "No hay pan Viernes por la tarde"
