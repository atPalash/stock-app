from datetime import datetime, timedelta


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
    if start_date == "today":
        start_date = datetime.now()
    else:
        start_date = datetime.strptime(start_date, date_format)
    target_date = datetime.strptime(target_date, date_format)

    # Calculate the difference in days
    remaining_days = (target_date - start_date).days

    return remaining_days
