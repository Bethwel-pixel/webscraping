from flask import Flask, render_template, request, jsonify
from flask import send_from_directory
import csv
import json
import time
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from urllib.request import urlopen, Request
import os


app = Flask(__name__)

# Function to search Google for business hours
def search_google(phone_number):
    try:
        url = f"https://www.google.com/search?q={quote_plus(phone_number)}"
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        page = urlopen(req)
        soup = BeautifulSoup(page, 'html.parser')
        business_hours = soup.find('div', class_='BNeawe vvjwJb AP7Wnd')
        if business_hours:
            x = business_hours.text.split()
            return {'phone_number': phone_number, 'info': x[0], 'more-info': ' '.join(x[1:])}
        else:
            return {'phone_number': phone_number, 'info': 'Not found', 'more-info': 'Not found'}
    except Exception as e:
        print(f"Error searching for business hours for {phone_number}: {e}")
        return {'phone_number': phone_number, 'info': 'Error', 'more-info': str(e)}

def save_results(results):
    try:
        # Load existing results from JSON file
        with open('output.json', 'r') as json_file:
            existing_results = json.load(json_file)
    except FileNotFoundError:
        # Create a new file if it doesn't exist
        existing_results = []

    # Append new results to existing results
    updated_results = existing_results + results

    # Write updated results to JSON file
    with open('output.json', 'w') as json_file:
        json.dump(updated_results, json_file)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    phone_numbers = request.json['phoneNumbers'].split(',')
    results = [search_google(phone) for phone in phone_numbers]
    save_results(results)
    write_results_to_csv("output.json", "results.csv")
    return jsonify(results)

@app.route('/import-csv', methods=['POST'])
def import_csv():
    csv_file = request.files['csvFile']

    # Check if the file is empty
    if csv_file.filename == '':
        return jsonify({'error': 'Empty file uploaded'})

    # Check if the file is a CSV file
    if not csv_file.filename.endswith('.csv'):
        return jsonify({'error': 'Uploaded file is not a CSV'})

    # Read the CSV file and extract phone numbers
    phone_numbers = []
    # Open the CSV file in text mode with newline=''
    csv_data = csv_file.stream.read().decode("utf-8")
    reader = csv.reader(csv_data.splitlines(), delimiter=',')
    for row in reader:
        phone_numbers.extend(row)
    # Perform search for each phone number
    results = []
    for phone in phone_numbers:
        results.append(search_google(phone))
        time.sleep(1)  # Introduce a 1-second delay between requests
    print(results)
    # Write results to JSON file
    save_results(results)
    write_results_to_csv("output.json", "results.csv")
    return jsonify(results)


@app.route('/results')
def table():
    # Load results from JSON file
    with open('output.json', 'r') as json_file:
        results = json.load(json_file)
    
    return render_template("table.html", results=results)

def write_results_to_csv(json_file, csv_file):
    # Read the JSON file
    with open(json_file, 'r') as f:
        results = json.load(f)

    # Write the results to a CSV file
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['phone_number', 'info', 'more-info'])
        writer.writeheader()
        for result in results:
            writer.writerow(result)

if __name__ == '__main__':
    app.run(debug=True)