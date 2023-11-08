from .card import deriveCard
from .cash import deriveCash
from .wallet_course import deriveWallet

deriveRouters = [deriveWallet, deriveCash, deriveCard]