# coding=utf-8
import os

from constants.constant import const
import json
from utils.file import File


class MetaFile:

    file_path = ''

    def __init__(self):
        self.file_path = File.data_file(const.META_FILE)

    def save(self, dict_data={}):
        json_data = json.dumps(dict_data, indent=4)
        with open(self.file_path, 'w+') as json_file:
            json_file.write(json_data)

    def load(self):
        if not os.path.isfile(self.file_path):
            self.save()

        with open(self.file_path, 'r+', encoding='utf8') as json_file:
            json_data = json.load(json_file)
            return json_data
        return {}


meta_file = MetaFile()
