# pyright: reportPrivateUsage = none

import jep

class TransactionRequiredException[**Ts](jep._PyJObject): ...

class TransactionRolledbackException[**Ts](jep._PyJObject): ...

class InvalidTransactionException[**Ts](jep._PyJObject): ...

