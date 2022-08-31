from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import os
from datetime import datetime
from .auth import *


class init_settings:
    def __init__(self):
        self.logger = None
        self.webserver = None
        self.oauth = None
        self.initialize()

    def initialize(self):
        # create folders if not exist
        if not os.path.exists('logs'):
            os.mkdir('logs')

        if not os.path.exists('results'):
            os.mkdir('results')

        # set logger and local web server
        self.getlogger()
        self.run_local_web_server()

        self.oauth = gmail_authenticate()
        if self.oauth:
            self.logger.info('Succeeded to pass google OAuth.')
        else:
            self.logger.info('Failed to pass google OAuth.')
            return

    def getlogger(self):

        logging.basicConfig(level=logging.DEBUG,
                            datefmt='%Y-%m-%d %H:%M:%S',
                            format='%(asctime)s.%(msecs)03d : %(levelname)-8s %(message)s',
                            filename='logs/mymail_{}.log'.format(datetime.today().strftime("%Y%m%d")),
                            filemode='a+')

        # set googleapiclient disable debug logging
        logging.getLogger('googleapiclient').setLevel(logging.WARNING)
        # set terminal log format
        formatter = logging.Formatter('%(asctime)s : %(levelname)-8s %(message)s')
        formatter.default_msec_format = '%s.%03d'

        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        console.setFormatter(formatter)
        logging.getLogger('').addHandler(console)

        self.logger = logging.getLogger('')

    def run_local_web_server(self):
        self.webserver = HTTPServer(('localhost', 8080), BaseHTTPRequestHandler)

    def time_convert(self, sec):
        mins = sec // 60
        sec = sec % 60
        hours = mins // 60
        mins = mins % 60

        elapsed = None
        if hours == 0:
            if mins == 0:
                elapsed = '{:d}s'.format(int(sec))
            else:
                elapsed = '{:02d}:{:02d}'.format(int(mins), int(sec))
        else:
            elapsed = '{:02d}:{:02d}:{:02d}'.format(int(hours), int(mins), int(sec))

        return elapsed
