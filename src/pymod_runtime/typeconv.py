import datetime

import jep
from java.util import Date

jep.setJavaToPythonConverter(Date, lambda jdate: datetime.datetime.fromtimestamp(jdate.getTime() / 1000, datetime.timezone.utc))
