# import datetime
# import math

from java.util import Map
import jep

# jep.setJavaToPythonConverter(Date, lambda jdate: datetime.datetime.fromtimestamp(jdate.getTime() / 1000, datetime.timezone.utc))
jep.setJavaToPythonConverter(Map, lambda map: dict(map.items()))
