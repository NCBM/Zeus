# pyright: reportPrivateUsage = none

import jep

class InvalidActivityException[**Ts](jep._PyJObject): ...

class ActivityRequiredException[**Ts](jep._PyJObject): ...

class ActivityCompletedException[**Ts](jep._PyJObject): ...

