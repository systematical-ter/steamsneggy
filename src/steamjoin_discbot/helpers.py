from enum import Enum
class MessageType(str, Enum):
    tiny = "tiny"
    default = "default"

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_