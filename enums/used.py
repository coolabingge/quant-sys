from enum import Enum


class Side(Enum):
    Open_More = 1
    Open_Empty = 2
    Close_More = 3
    Close_Empty = 4


class PositionType(Enum):
    More = 'long'
    Empty = 'short'


class OrderType(Enum):
    Limit = 'Limit'
    Market = 'Market'
    Stop = 'Stop'
    StopLimit = 'StopLimit'
    MarketIfTouched = 'MarketIfTouched'
    LimitIfTouched = 'LimitIfTouched'
    Pegged = 'Pegged'


class RunningStatus(Enum):
    Running = 'Running'
    Pause = 'Pause'
    Stop = 'Stop'


class OpenType(Enum):
    Much = 'Much'
    Less = 'Less'


class Exchange(Enum):
    BitMex = 'BITMEX'
    Okex = 'OKEX'


class Env(Enum):
    Test = 'Test'
    Dist = 'Dist'
