from datetime import datetime, timedelta, date


def find_closest_date(target_date, date_list):
    closest_date = None
    min_difference = timedelta.max
    index = 0
    for i in range(len(date_list)):
        difference = abs(date_list[i] - target_date)
        if difference < min_difference:
            min_difference = difference
            closest_date = date_list[i]
            index = i
    return closest_date, index


def days_until(start_date: str, target_date: str, date_format="%d-%b-%Y"):
    # Parse the date string into a datetime object
    check = date.today()  # TODO check  timezone
    if start_date != "today":
        check = datetime.strptime(start_date, date_format).date()
    target_date = datetime.strptime(target_date, date_format).date()

    # Calculate the difference in days
    remaining_days = (target_date - check).days

    return remaining_days
