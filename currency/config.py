"""Class of config"""
import json

class Config():
    def __init__(self, app_id, precision=2, expire=300, base="USD", currencies=["EUR", "CNY", "JPY", "GBP"]):
        self.app_id = str(app_id)
        self.precision = int(precision)
        self.expire = int(expire)
        self.base = str(base)
        self.currencies = currencies
    def save(self, path="config.json"):
        with open(path, "w+") as file:
            json.dump(self.__dict__, file)
