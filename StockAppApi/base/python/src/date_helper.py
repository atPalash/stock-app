from datetime import timedelta

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
