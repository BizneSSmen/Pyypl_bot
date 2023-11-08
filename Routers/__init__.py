from .Cash_exchange_router import cashExchangeRouters
from .Derive_routers import deriveRouters
from .Deposit_routers import depositRouters
from .start_router import mainMenu

routers = [mainMenu, *cashExchangeRouters, *deriveRouters, *depositRouters]
