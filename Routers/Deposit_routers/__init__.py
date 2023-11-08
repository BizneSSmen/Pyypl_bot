from .card import depositCard
from .sbp import sbp
from .wallet_course import depositWallet

depositRouters = [sbp, depositCard, depositWallet]
