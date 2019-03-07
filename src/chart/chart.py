# file: chart.py
# andrew jarcho
# 10/2018


from tests.file_access_wrappers import FileReadAccessWrapper
import re
import sys
from datetime import datetime


class Chart:
    """
    Create a sleep chart from input data
    """
    ASLEEP = 1  # the printed color (black ink)
    AWAKE = 0   # the background color (white paper)

    def __init__(self, filename):
        self.filename = filename
        self.infile = None
        self.cur_line = ''
        self.prev_line = ''
        self.sleep_state = self.AWAKE
        self.date_re = None
        self.cur_date_str = ''
        self.cur_time_str = ''
        self.cur_date_time_str = ''
        self.cur_date = None
        self.cur_time = None
        self.cur_datetime = None
        self.cur_interval = None
        self.cur_nap_id = 0
        self.days_carried = 0
        self.day_row = [self.AWAKE] * 24 * 4
        self.header_seen = False

    def get_a_line(self):
        """

        :return: bool
        Called by: open_file()
        """
        self.cur_line = self.infile.readline().rstrip()
        if not self.header_seen:
            self.skip_header()
        return bool(self.cur_line)

    def skip_header(self):
        while self.cur_line and not self.date_re.match(self.cur_line):
            self.cur_line = self.infile.readline().rstrip()
        self.header_seen = True

    @staticmethod
    def quarter_to_int(q):
        """
        Return one int per quarter hour
        :param q: the state(asleep or awake) during a quarter hour
        :return: 1 for asleep, 0 for awake
        # Called by:
        """
        if q:
            return Chart.ASLEEP
        return Chart.AWAKE

    def open_file(self):
        """
        :return: None
        Called by: main()
        """
        with open(self.filename) as self.infile:
            while self.get_a_line():
                parsed_line = self.parse_line_I()  # a 3-tuple
                if any(parsed_line):
                    self.cur_datetime, self.cur_interval, self.cur_nap_id = \
                        parsed_line
                    print(self.cur_datetime, self.cur_interval,
                          self.cur_nap_id)

    def parse_line_I(self):
        line_array = self.cur_line.split('|')  # cur_line[-1] may be '|'
        line_array = list(map(str.strip, line_array))  # so strip() now
        return self.parse_line_II(line_array)

    @staticmethod
    def parse_line_II(arr):
        if len(arr) < 2:
            return None, None, None
        nap_id = 0
        date_str = arr[0].strip()
        time_str = arr[1].strip()
        interval = arr[2].strip()
        if arr[3]:
            nap_id = int(arr[3].strip())
        date_time_str = date_str + ((' ' + time_str) if time_str else '')
        my_datetime = datetime.strptime(date_time_str,
                                        ('%Y-%m-%d %H:%M:%S' if
                                         time_str else '%Y-%m-%d'))
        return my_datetime, interval, nap_id

    def compile_date_re(self):
        """
        :return: None
        Called by: main()
        """
        self.date_re = re.compile(r' \d{4}-\d{2}-\d{2} \|')


def main():
    chart = Chart('/home/jazcap53/python_projects/spreadsheet_etl/src/chart/chart_raw_data.txt')
    chart.compile_date_re()
    chart.open_file()


if __name__ == '__main__':
    main()


# NOTES
# >>> import datetime
# >>> my_date = '2016-12-07'
# >>> my_time = '23:45:00'
# >>> my_datetime = my_date + ' ' + my_time
# >>> my_datetime
# '2016-12-07 23:45:00'
# >>> my_date_and_time = my_date + ' ' + my_time
# >>> my_datetime = datetime.datetime.strptime(my_date_and_time, '%Y-%m-%d %H:%M:%S')
# >>> my_datetime
# datetime.datetime(2016, 12, 7, 23, 45)
# >>> my_newer_datetime = my_datetime + datetime.timedelta(minutes=15)
# >>> my_newer_datetime
# datetime.datetime(2016, 12, 8, 0, 0)
