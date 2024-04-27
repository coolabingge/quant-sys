# coding=utf-8

import os

class File:

    @staticmethod
    def root_path():
        return os.path.abspath(os.path.dirname(__file__)).split('utils')[0]

    @staticmethod
    def data_path():
        return os.path.join(File.root_path(), const.DATA_DIR)

    @staticmethod
    def conf_path():
        return os.path.join(File.root_path(), const.CONF_DIR)

    @staticmethod
    def data_file(file_name=None):
        return os.path.join(File.data_path(), file_name)

    @staticmethod
    def conf_file(conf_file_name=None):
        return os.path.join(File.conf_path(), conf_file_name)
