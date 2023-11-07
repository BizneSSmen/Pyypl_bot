from .start_router import mainMenu
from .Deposit_routers import depositCard, sbp, depositWallet
from .Derive_routers import deriveCard, deriveCash, deriveWallet
from .Cash_exchange_router import cashExchange


userRouters = [mainMenu, depositCard, depositWallet, sbp, deriveCard, deriveCash, cashExchange, deriveWallet]
