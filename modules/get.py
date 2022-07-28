from operator import index
import os
import re
import traceback
import pandas as pd
from datetime import datetime
from dateutil import tz, parser


class init_getter:
    COLUMN_NAMES = ['index', 'datetime', 'subject', 'from', 'domain', 'labels', 'filtered', 'addLabels', 'removeLabels']
    LABEL_CSV_PATH = 'results/labels.csv'
    FILTER_CSV_PATH = 'results/filters.csv'
    RESULT_EXCEL_PATH = 'results/result.xlsx'
    THRESHOLD_FILE_PATH = 'threshold.txt'
    COUNTS_FROM_PATH = 'results/count_per_from.xlsx'
    COUNTS_DOMAIN_PATH = 'results/count_per_domain.xlsx'
    REGEX_EMAIL = re.compile('.*\<(.*)\@(.*)\>.*')
    REGEX_EMAIL_ONLY = re.compile('(.*)\@(.*)')
    IS_RESULT_EXIST = False

    def __init__(self, logger, auth):
        self.log = logger
        self.service = auth
        self.mail_lists = []
        self.filters = []
        self.last_msg_recv_datetime = None
        self.threshold = None
        self.mail_count = 0
        self.initialize()

    def initialize(self):
        # get mail count if exist result excel
        if os.path.exists(self.RESULT_EXCEL_PATH):
            self.IS_RESULT_EXIST = True
            df = pd.read_excel(self.RESULT_EXCEL_PATH, index_col=False, skiprows=0)
            self.mail_count = len(df)
        else:
            self.mail_count = 0

        # get threshold
        if os.path.exists(self.THRESHOLD_FILE_PATH):
            with open(self.THRESHOLD_FILE_PATH, 'r') as f:
                self.threshold = str(f.readline()).strip()

        if (self.threshold is None or len(self.threshold) == 0):
            if os.path.exists(self.RESULT_EXCEL_PATH):
                os.remove(self.RESULT_EXCEL_PATH)
        else:
            self.threshold = datetime.strptime(self.threshold, '%Y-%m-%d %H:%M:%S')

        self.get_label_list()
        self.get_filter_list()

    def get_label_names(self, list):
        label_names = []
        for li in list:
            for label in self.labellist:
                if label['id'] == li:
                    label_names.append(label['name'])
                    break

        return label_names

    def get_label_list(self):
        try:
            results = self.service.users().labels().list(userId='me').execute()
            self.labellist = results.get('labels', [])
            if not self.labellist:
                self.labellist = None
                return None

            self.log.info('Labels:')
            if os.path.exists(self.LABEL_CSV_PATH):
                os.remove(self.LABEL_CSV_PATH)

            # save result of label list
            f = open(self.LABEL_CSV_PATH, 'w', encoding="UTF-8-sig")
            f.write('index,type,labelid,name\n')
            for index, label in enumerate(self.labellist):
                id = label['id']
                name = label['name']
                type = label['type']
                self.log.info(f'[{index}], Type: {type}, Name: {name}')
                f.write(f'{index},{type},{id},{name}\n')
        except:
            self.labellist = None
            self.log.error(traceback.print_exc())

    def get_filter_list(self):
        try:
            results = self.service.users().settings().filters().list(userId='me').execute()

            filterlist = results.get('filter', [])
            if not filterlist:
                filterlist = None
                return None

            self.log.info('Filters:')
            if os.path.exists(self.FILTER_CSV_PATH):
                os.remove(self.FILTER_CSV_PATH)

            # save result of filter list
            f = open(self.FILTER_CSV_PATH, 'w', encoding="UTF-8-sig")
            f.write('index,id,from,addLabelIds,removeLabelIds\n')

            index = 0
            for filter in filterlist:
                email = filter['criteria']['from']
                addLabels = filter['action']['addLabelIds']
                removeLabels = filter['action']['removeLabelIds']

                add_Labels = '|'.join(self.get_label_names(addLabels))
                remove_Labels = '|'.join(self.get_label_names(removeLabels))

                emails = None
                if any(c in email for c in ['|', '&']):
                    emails = [match for match in re.split('[\|\&]', email) if match]
                else:
                    emails = [email]

                for mail in emails:
                    mail = mail.strip()
                    filter_dict = {'index': index, 'email': mail,
                                   'addLabels': add_Labels, 'removeLabels': remove_Labels}
                    self.filters.append(filter_dict)
                    self.log.info(f'[{index}], email: {mail}, addLabels : {add_Labels}, removeLabels : {remove_Labels}')
                    f.write(f'{index}, {mail},{add_Labels}, {remove_Labels}\n')
                    index += 1

        except:
            self.filters = None
            self.log.error(traceback.print_exc())

    def messages(self):
        try:

            messages = None
            if self.threshold is not None:
                query = "after: {}".format(int(self.threshold.timestamp()))
            elif self.last_msg_recv_datetime is None:
                query = "before: {}".format(int(datetime.now().timestamp()))
            else:
                query = "before: {}".format(int(self.last_msg_recv_datetime.timestamp()))

            # request a list of all the messages
            result = self.service.users().messages().list(maxResults=100, userId='me', q=query).execute()
            messages = result.get('messages')
        except:
            self.log.error(traceback.print_exc())
            return None

        return messages

    def mail_info(self):
        self.log.info('Start get mail list.')

        index = 0
        msgs = self.messages()
        if msgs is None:
            return False

        # iterate through all the messages
        for msg in msgs:
            # Get the message from its id
            txt = self.service.users().messages().get(userId='me', id=msg['id']).execute()

            try:
                self.mail_count += 1
                # get value of 'payload' from dictionary 'txt'
                payload = txt['payload']
                labels = txt['labelIds']
                headers = payload['headers']

                is_set_subject = False
                is_set_sender = False
                is_set_date = False

                # get subject, sender and date
                for d in headers:
                    if d['name'] == 'Subject':
                        subject = d['value']
                    if d['name'] == 'From':
                        sender = d['value']
                    if d['name'] == 'Date':
                        self.last_msg_recv_datetime = parser.parse(d['value']).astimezone(tz.tzlocal())

                    if is_set_subject and is_set_sender and is_set_date:
                        break

                recv_date = self.last_msg_recv_datetime.strftime('%Y-%m-%d %H:%M:%S')
                from_addr = None

                if not any(c in sender for c in ['<', '>']):
                    from_addr = self.REGEX_EMAIL_ONLY.match(sender)
                else:
                    from_addr = self.REGEX_EMAIL.match(sender)
                domain = ''
                if from_addr is None:
                    from_addr = sender
                else:
                    domain = from_addr.group(2)
                    from_addr = from_addr.group(1) + '@' + from_addr.group(2)

                subject = str(subject).strip().replace('\n', '')

                # check label name
                labelnames = []
                if labels is not None:
                    labelnames = ','.join(self.get_label_names(labels))

                # check filtered mail
                filtered = [f for f in self.filters if f['email'] == from_addr]
                if len(filtered) == 0:
                    self.mail_lists.append([self.mail_count, recv_date, subject,
                                           from_addr, domain, labelnames, '', '', ''])
                else:
                    add_labels = []
                    remove_labels = []
                    for f in filtered:
                        if len(add_labels) == 0 or f['addLabels'] not in add_labels:
                            add_labels.append(f['addLabels'])

                        if len(remove_labels) == 0 or f['removeLabels'] not in remove_labels:
                            remove_labels.append(f['removeLabels'])

                    self.mail_lists.append([self.mail_count, recv_date, subject, from_addr,
                                           domain, labelnames, True, add_labels, remove_labels])

                # logging the datetime, subject, sender's email and message
                index = str(self.mail_count).zfill(5)

                self.log.info(f'[{index}] DateTime: {recv_date}, Subject : {subject}, From: {from_addr}')
            except:
                self.log.error(f'[{index}] DateTime: {recv_date}, Subject : {subject}, From: {from_addr}')
                self.log.error(traceback.print_exc())
                pass

        return True

    def export(self):
        try:
            result_exist = None
            result_new = None
            result = None
            if len(self.mail_lists) > 0:
                # make mail lists to pandas datafrom
                result_new = pd.DataFrame(self.mail_lists, columns=self.COLUMN_NAMES)

                # check if results of mail list is exist
                if self.IS_RESULT_EXIST:
                    result_exist = pd.read_excel(self.RESULT_EXCEL_PATH, index_col=None)

            if result_exist is not None:
                if result_new is not None:
                    result = pd.concat([result_exist, result_new], ignore_index=True)
                else:
                    result = result_exist
            else:
                if result_new is not None:
                    result = result_new

            if result is not None:
                result.sort_values('datetime', ascending=False, inplace=True)

                # threshold datetime recevied mail
                with open('threshold.txt', 'w') as f:
                    f.write(result['datetime'][0])

                # save count per 'from' whuch sender email sent to excel
                grp_cols = ['from', 'domain', 'filtered']
                grp_by_sent = result.groupby(grp_cols, as_index=False)[grp_cols]
                grp_count = grp_by_sent.value_counts().sort_values(['count', 'domain', ], ascending=False)

                if os.path.exists(self.COUNTS_FROM_PATH):
                    os.remove(self.COUNTS_FROM_PATH)

                df_grp = pd.DataFrame(grp_count)
                df_grp.to_excel(self.COUNTS_FROM_PATH, index=False)

                # save count per domain whuch sender email sent to excel
                grp_by_sent = result.groupby('domain', as_index=False)['domain']
                grp_count = grp_by_sent.value_counts().sort_values('count', ascending=False)

                if os.path.exists(self.COUNTS_DOMAIN_PATH):
                    os.remove(self.COUNTS_DOMAIN_PATH)

                df_grp = pd.DataFrame(grp_count)
                df_grp.to_excel(self.COUNTS_DOMAIN_PATH, index=False)

                # save results to excel
                if self.IS_RESULT_EXIST:
                    os.remove(self.RESULT_EXCEL_PATH)

                result.to_excel(self.RESULT_EXCEL_PATH, index=False)

            else:
                self.log.info('No new results from my gmail account.')

        except:
            self.log.error(traceback.print_exc())
