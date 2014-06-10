#!/bin/env python
import os
import sys
from datetime import datetime, timedelta
import time
import logging
import requests


FORMAT = '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s'
DATEFORMAT = "%d/%b/%Y %H:%M:%S"
logging.basicConfig(format=FORMAT, datefmt=DATEFORMAT, level=logging.DEBUG)

OPEN_STATUS = {
    'O': 'Open',
    'C': 'Closed',
    'S': 'Supposed to be closed',
    'U': 'Unknown'
}

RUN_STATUS = {
    'R': 'Running',
    'S': 'Stopped',
    'NF': 'Not Found',
    'U': 'Unknown'
}


class StatusLight(object):

    _red_light_pin = 1
    _green_light_pin = 2
    _url = None
    _interval = 3600
    _running_state = None
    _status = None

    def __init__(self,
                 url,
                 interval=None,
                 red_light_pin=None,
                 green_light_pin=None):
        self._url = url
        logging.info("Init StatusLight")

        if interval is not None:
            self._interval = interval

        if red_light_pin is not None:
            self._red_light_pin = red_light_pin

        if green_light_pin is not None:
            self._green_light_pin = green_light_pin

        self._state = OPEN_STATUS.get('U')
        self._running_state = RUN_STATUS.get('R')

    def polling(self):
        logging.info("Run polling")
        res = requests.get(self._url)

        if res.status_code == requests.codes.ok:
            data = res.json()
            is_open = data['state']['open']

            if is_open:
                hours = timedelta(hours=data['state']['ext_duration'])
                lastchange = datetime.fromtimestamp(
                    data['state']['lastchange']
                )

                if lastchange + hours < datetime.now():
                    self._state = OPEN_STATUS.get('S')
                else:
                    self._state = OPEN_STATUS.get('O')
            else:
                self._state = OPEN_STATUS.get('C')

            logging.debug(
                'Open Status: {status}'.format(
                    status=self._state
                )
            )
        elif res.status_code == 404:
            self._running_state = RUN_STATUS.get('NF')

    def display(self):
        logging.info("Run display")
        if self._state == OPEN_STATUS.get('O'):
            # Red: Off / Green: ON
            logging.debug('Red: Off / Green: ON')
            pass
        elif self._state == OPEN_STATUS.get('C'):
            # Red: ON / Green: Off
            logging.debug('Red: ON / Green: Off')
            pass
        elif self._state == OPEN_STATUS.get('S'):
            # Red: ON / Green: ON
            logging.debug('Red: ON / Green: ON')
            pass
        else:
            # All lights Off
            logging.debug('All lights Off')
            pass

    def live(self):
        while self._running_state == RUN_STATUS.get('R'):
            logging.debug("Live")
            start = time.clock()
            self.polling()
            self.display()
            work_duration = time.clock() - start
            logging.debug("Time to sleep")
            time.sleep(self._interval - work_duration)


if __name__ == "__main__":

    usage = 'Usage: python %s <url> <interval>' % os.path.basename(sys.argv[0])
    status_light = None

    if len(sys.argv) == 2:
        status_light = StatusLight(sys.argv[1])
        logging.debug(
            "Creating StatusLight object with url=%s"
            .format(url=sys.argv[1])
        )
    elif len(sys.argv) > 2:
        status_light = StatusLight(sys.argv[1], int(sys.argv[2]))
        logging.debug(
            "Creating StatusLight object with url=%s and interval=%s"
            .format(url=sys.argv[1], interval=sys.argv[2])
        )
    else:
        logging.error(usage)
        print usage
        sys.exit(1)

    if status_light:
        status_light.live()