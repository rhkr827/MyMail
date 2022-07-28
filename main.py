from datetime import datetime
import os
import gc
import traceback
import numpy as np
import pandas as pd
from time import sleep, time

from modules import *


def main():
    mail_count = 0
    log = None
    webServer = None
    service = None

    try:
        # initialize settings class
        start_time = time()
        setting = init_settings()
        if setting is None:
            exit()

        log = setting.logger
        webServer = setting.webserver
        service = setting.oauth

        if webServer:
            log.info('Start local web server.')

        # initialize get class
        getter = init_getter(log, service)

        if getter.labellist is None:
            log.info('No labels found.')
            webServer.server_close()
            exit()

        if getter.filters is None:
            log.info('No filters found.')
            webServer.server_close()
            exit()

        while(1):
            if getter.mail_info() == False:
                break

            mail_count = getter.mail_count
            # collect garbage
            sleep(0.1)
            gc.collect()

    except:
        log.error('An Error is occurred. Stop running.')
        log.error(traceback.print_exc())
        webServer.server_close()

    # close web server
    webServer.server_close()
    end_time = time()
    diff = end_time - start_time
    elapsed = setting.time_convert(diff)
    log.info('Finished. Total mail count : {}, Total elapsed : {}'.format(mail_count, elapsed))

    # export result and counts per 'from' e-mail address
    getter.export()


if __name__ == '__main__':
    main()
