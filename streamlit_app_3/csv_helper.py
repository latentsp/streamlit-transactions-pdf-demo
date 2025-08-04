import csv

def load_from_csv():
    with open("data/income_category_test_results.csv", 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            yield row

