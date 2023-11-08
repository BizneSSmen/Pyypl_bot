import io
from dataclasses import dataclass
import re


@dataclass
class OperationTypes:
    debit: str = 'debit'
    credit: str = 'credit'
    change: str = 'change'


@dataclass
class OperationStatuses:
    created: str = 'created'
    approved: str = 'approved'
    initialized: str = 'initialized'
    moderating: str = 'moderating'
    processing: str = 'processing'
    completed: str = 'completed'
    canceled: str = 'canceled'


class Claim:
    def __init__(self):
        self.__receiptAllowedTypes: list[str] = ['doc', 'docx', 'gif', 'png', 'jpeg', 'webp', 'psd', 'scg', 'pdf', 'jpg',
                                                 'openoffice']
        self.__operationType: str | None = None
        self.__description: str | None = None
        self.__cardPaidFrom: str | None = None
        self.__cardAwaitingTo: str | None = None
        self.__phoneNumber: str | None = None
        self.__status: str | None = None
        self.__targetAmount: int = 0
        self.__finalAmount: int = 0
        self.__currencyA: str | None = None
        self.__currencyB: str | None = None
        self.__exchangeAppliedRate: float | None = None
        self.__fee: int = 0
        self.__receiptType: str | None = None
        self.__receiptSize: int = 0
        self.__receiptBinary: str | None = None

    @property
    def operationType(self) -> str | None:
        return self.__operationType

    @property
    def description(self) -> str | None:
        return self.__description

    @property
    def cardPaidFrom(self) -> str | None:
        return self.__cardPaidFrom

    @property
    def cardAwaitingTo(self) -> str | None:
        return self.__cardAwaitingTo

    @property
    def phoneNumber(self) -> str | None:
        return self.__phoneNumber

    @property
    def status(self) -> str | None:
        return self.__status

    @property
    def targetAmount(self) -> int | None:
        return self.__targetAmount

    @property
    def finalAmount(self) -> int | None:
        return self.__finalAmount

    @property
    def exchangeAppliedRate(self) -> float | None:
        return self.__exchangeAppliedRate

    @property
    def fee(self) -> int | None:
        return self.__fee

    @property
    def receiptType(self) -> str | None:
        return self.__receiptType

    @property
    def receiptSize(self) -> int | None:
        return self.__receiptSize

    @property
    def receiptBinary(self) -> io.BytesIO:
        return self.__receiptBinary

    @property
    def currencyA(self) -> io.BytesIO:
        return self.__currencyA

    """
    Methods for change claim's operation type
    """

    def setDebit(self):
        self.__operationType = OperationTypes.debit

    def setCredit(self):
        self.__operationType = OperationTypes.credit

    def setChange(self):
        self.__operationType = OperationTypes.change

    """
    Methods for changing claim's status
    """

    def setCreated(self):
        self.__status = OperationStatuses.created

    def setApproved(self):
        self.__status = OperationStatuses.approved

    def setInitialized(self):
        self.__status = OperationStatuses.initialized

    def setModerating(self):
        self.__status = OperationStatuses.moderating

    def setProcessing(self):
        self.__status = OperationStatuses.processing

    def setCompleted(self):
        self.__status = OperationStatuses.completed

    def setCanceled(self):
        self.__status = OperationStatuses.canceled

    """
    Method for set the full claim description
    :param _str: line containing the card number 
    """

    def setDescription(self, _str: str) -> None:
        self.__description = _str

    """
    Method for set the number of the card used to pay
    :param _str: line containing the card number 
    """

    def setCardPaidFromNumber(self, _str: str) -> bool:
        cardPattern: re.Pattern = re.compile('[0-9]{16}$')
        if cardPattern.match(_str):
            self.__cardPaidFrom = " ".join(re.findall('.{%s}' % 4, cardPattern.match(_str).group()))
            return True
        else:
            return False

    """
    Method for set card number
    :param _str: the number of the card to which the transfer is planned
    """

    def setCardAwaitingTo(self, _str: str) -> bool:
        cardPattern: re.Pattern = re.compile('[0-9]{16}$')
        if cardPattern.match(_str):
            self.__cardAwaitingTo = cardPattern.match(_str).group()
            return True
        else:
            return False

    """
    Method for set card number
    :param _str: the user's phone number
    """

    def setPhoneNumber(self, _str: str) -> bool:
        phonePattern: re.Pattern = re.compile(r"(\+\d{1,3})?\s?\(?\d{1,4}\)?[\s.-]?\d{3}[\s.-]?\d{4}")
        if phonePattern.match(_str):
            self.__phoneNumber = phonePattern.match(_str).group()
            return True
        else:
            return False

    """
       Method for set target amount
       :param amount: planned amount
    """

    def setTargetAmount(self, amount: int | str) -> bool:
        if amount.isdigit():
            self.__targetAmount = int(amount)
            return True
        else:
            return False

    """
       Method for set final amount
       :param amount: final amount
    """

    def setFinalAmount(self, amount: int | str):
        self.__finalAmount = int(amount)

    """
       Method for set exchange rate
       :param rate: current exchange rate
    """

    def setExchangeAppliedRate(self, rate: float | str):
        self.__exchangeAppliedRate = float(rate)

    """
       Method for set fee
       :param fee: current fee
    """

    def setFee(self, fee: int | str):
        self.__fee = float(fee)

    """
       Method for set receipt type
       :param _str: string that contains receipt type
    """

    def setReceiptType(self, _str: str) -> bool:
        if (receiptType := _str.split('.')[-1]) in self.__receiptAllowedTypes:
            self.__receiptType = receiptType
            return True
        else:
            return False

    def setReceiptSize(self, size: int):
        self.__receiptSize = size

    def setReceiptBinary(self, binary: str):
        self.__receiptBinary = binary

    def setCurrencyA(self, _str: str):
        self.__currencyA = _str

    def setCurrencyB(self, _str: str):
        self.__currencyB = _str

    def getAllAttr(self):
        return vars(self)
