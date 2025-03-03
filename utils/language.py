from enum import Enum

class Language(Enum):
    ENGLISH = "en"
    PERSIAN = "fa"

class ResponseLength(Enum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"

class ResponseStyle(Enum):
    FORMAL = "formal"
    CONVERSATIONAL = "conversational"
    SCIENTIFIC = "scientific"
    HUMOROUS = "humorous"
