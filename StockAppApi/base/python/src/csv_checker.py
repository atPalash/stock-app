import csv

def is_csv_html(file_path):
    with open(file_path, 'r') as file:
        contents = file.read()
        # Checking if the file contains any HTML tags or patterns
        if '<html' in contents or '</html>' in contents or '<body' in contents or '</body>' in contents:
            return True
        else:
            return False
