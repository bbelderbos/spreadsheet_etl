# file: src/extract/read_fns.py
# andrew jarcho
# 2017-01-25

# python: 3.5

# TODO: fix below docstring
"""
The input is structured in lines as:

    Sunday Date   Sun   Mon  Tue  Wed  Thu  Fri  Sat
                                   x    x    x    x
                                   x         x    x
                                   x              x
                                                  x


    Sunday Date    x     x    x    x    x    x    x
                   x          x    x         x    x
                              x    x         x
                              x              x
                              x

    where each 'x' is a data item (event) we care about.

The output is structured into Events, Days, and Weeks.
The Events from each Day are grouped together. A Week
groups 7 consecutive Days, beginning with a Sunday.

Once the input file has been opened, function read_lines()
controls the data processing: all other functions in this
file are called from read_lines().
"""


import datetime
import re
import logging

from src.extract.container_objs import validate_segment, Week, Day, Event


read_logger = logging.getLogger('extract.read_fns')


def open_file(file_read_wrapper):
    """
    file_read_wrapper allows reading from a fake instead of
        a real file during testing.

    Returns: a file handler open for read
    Called by: client code
    """
    return file_read_wrapper.open()


def read_lines(infile):
    """
    Loop:
        Ignore lines until a Sunday is seen.
        Collect one week of data (until a blank line is seen).
        Append that week of data to lines_buffer[].
        Call _handle_end_of_week() to write good data, discard bad data,
            and empty the buffer.
    Until:
        EOF.

    Called by: client code
    """
    in_week = False
    sunday_date = None
    have_events = False
    new_week = None
    lines_buffer = []
    for line in infile:
        line_as_list = line.strip().split(',')[:22]
        re_date_match_found = _check_for_date(line_as_list[0])
        if not in_week and not re_date_match_found:
            continue
        elif not in_week and re_date_match_found:  # we *just* found a date
            sunday_date = _re_match_to_date_obj(re_date_match_found)
            # create a day_list of 7 (empty) Days
            day_list = [Day(sunday_date +
                            datetime.timedelta(days=x), [])
                        for x in range(7)]
            new_week = Week(*day_list)
            in_week = True
        if in_week:
            if not any(line_as_list):  # a blank line: our week has ended
                _handle_end_of_week(new_week, lines_buffer)
                in_week = False
                sunday_date = None
                # assert lines_buffer == []  # TODO: remove this
            else:  # add the line's events to the present week
                have_events = _get_events(line_as_list[1:], new_week)
    # manage any remaining unstored data
    if sunday_date and have_events and new_week:
        _handle_end_of_week(new_week, lines_buffer)


def _check_for_date(field):
    """
    Does field start with a date?
    Called by: read_lines()
    """
    m = re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})', field)
    return m if m else None


def _re_match_to_date_obj(m):
    """
    Convert a successful regex match to a datetime.date object
    Called by: read_lines()
    """
    # group(3) is the year, group(1) is the month, group(2) is the day
    dt = [int(m.group(x)) for x in (3, 1, 2)]
    dt_obj = datetime.date(dt[0], dt[1], dt[2])  # year, month, day
    return dt_obj


def _get_events(shorter_line, new_week):
    """
    Add each valid event in shorter_line to new_week.
    :param shorter_line: line_as_list, from read_lines(),
        without its first field
    Called by: read_lines()
    """
    find_events = False
    for ix in range(7):
        # a segment is a list of 3 consecutive fields from the .csv file
        segment = shorter_line[3 * ix: 3 * ix + 3]
        if validate_segment(segment):
            an_event = Event(*segment)
        elif segment == ['', '', '']:
            an_event = None
        else:
            read_logger.warning('segment {} not valid in _get_events()\n'
                                '\tsegment date is {}'.
                                format(segment, new_week[ix].dt_date))
            continue
        if new_week and an_event and an_event.action:
            new_week[ix].events.append(an_event)
            find_events = True
    return find_events


# TODO: write docstring, comments
def _handle_end_of_week(wk, buffer):
    """


    :param wk: a Week object, holding Days some of which might be
               missing data (incomplete).
    :param buffer: a list, possibly empty, of header strings and event
                   strings.
    :return: None
    """
    if not buffer:
        read_logger.debug('Empty buffer in _handle_end_of_week()')  # TODO: remove this line
    wk_header = '\nWeek of Sunday, {}:'.format(wk[0].dt_date)
    wk_header += '\n' + '=' * (len(wk_header) - 2)
    buffer.append(wk_header)
    for day in wk:
        dy_header = '    {}'.format(day.dt_date)  # four leading spaces
        buffer.append(dy_header)
        for event in day.events:
            event_str = 'action: {}, time: {}'.format(event.action,
                                                      event.mil_time)
            if event.hours:
                event_str += ', hours: {:.2f}'.format(float(event.hours))
            if event.action == 'b':  # the end of a Day (complete or not)
                _handle_end_of_day(buffer, event)
            buffer.append(event_str)


# TODO: complete docstring
def _handle_end_of_day(buffer, action_b_event):
    """
    Write complete Day's (only) from buffer to stdout.

    :param buffer: a list of strings. May contain header lines and/or
                   Event lines. Event lines start with 'action'.
    :param action_b_event: is the last Event of some Day.
                           action_b_event will have an hours field <=>
                           we have complete data for that Day.

    if we have complete data for this Day:
        output the entire buffer
        clear the buffer
    else:
        do not output anything
        remove Event lines from the buffer
        leave any header lines

    Called by: _handle_end_of_week()
    """
    if action_b_event.hours:  # we have a complete Day
        for line in buffer:  # note: action_b_event is not yet in buffer
            print(line)
        buffer.clear()
    else:  # Day is incomplete: pop Event lines only, starting from end
        read_logger.debug('Incomplete Day')  # TODO: remove this line
        for buf_ix in range(len(buffer) - 1, -1, -1):
            this_line = buffer[buf_ix]
            # if we reach a 3-element 'b' event
            # i.e., if the last Day handled was incomplete
            if this_line != '\n' and this_line[8] == 'b' and \
                            len(this_line) > 21:
                read_logger.debug('reached 3-element b-event {}'.format(this_line))  # TODO: remove this line
                buffer.pop(buf_ix)  # pop one last time, then stop
                break
            elif this_line[:6] == 'action':  # pop only Event lines:
                buffer.pop(buf_ix)           # leave headers in buffer
