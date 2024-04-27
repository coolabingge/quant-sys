# coding=utf-8

CONF_FILE = 'quant.cfg'
CONF_DIR = 'conf'
DATA_DIR = 'data'
META_FILE = 'meta.json'

TIME = 'open_time'
OPEN = 'open'
HIGH = 'high'
LOW = 'low'
CLOSE = 'close'
VOLUME = 'volume'
DATA_COLUMNS = {
    0: TIME,
    1: OPEN,
    2: HIGH,
    3: LOW,
    4: CLOSE,
    5: VOLUME
}

# 算法周期配置
ALGORITHM_CONFIG = {
    'DEFAULT': {
        'MA': [7, 30],
        'EMA': [9],
        'BBI': [3, 6, 12, 24],
        'MACD': [12, 26, 9],
        'BOLL': [20, 2]
    },
    'BITMEX': {
        'MA': [7, 30],
        'EMA': [9],
        'BBI': [3, 6, 12, 24],
        'MACD': [12, 26, 9],
        'BOLL': [20, 2]
    },
    'OKEX': {
        'MA': [7, 30],
        'EMA': [9],
        'BBI': [3, 6, 12, 24],
        'MACD': [12, 26, 9],
        'BOLL': [20, 2]
    }
}


# API参数配置
API_ENV = 'EnvTest'
PROXIES = {"http": "http://172.20.1.3:1080", 'https': 'http://172.20.1.3:1080'}
USE_PROXY = True
API_CONFIG = {
    'BITMEX': {
        'EnvTest': {
            'test': True,
            'wsUrl': 'wss://testnet.bitmex.com/realtime',
            'apiKey': 'sq7mxq-ij3vuMRli-wVnlI8g',
            'secret': 'jCBIWDV5OOotjQLkB2B8Wwe6fJe8-yVfUsCFReg73WnlRum6',
            'urls': {
                'api': {
                    'public': 'https://testnet.bitmex.com',
                    'private': 'https://testnet.bitmex.com'
                }
            }
        },
        'EnvNormal': {
            'test': False,
            'wsUrl': 'wss://www.bitmex.com/realtime',
            'apiKey': 'nNLOwiL8vGY9k6XIquJa_bpX',
            'secret': '0MlN1R3IKDWrfgGuzHDeNinyE0eKZrXtPZzkcGyEmPBtjbYk'
        }
    }
}
