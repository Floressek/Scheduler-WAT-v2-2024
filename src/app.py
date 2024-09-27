from flask import Flask, jsonify, request, Response
import csv
import io
from scraper.scheduler_scraper import scrape_schedule
from src.google_api.update_google_calendar import main as update_google_calendar
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)


@app.route('/scrape/<group>')
def scrape(group):
    user_agent = request.headers.get('User-Agent')
    data, error = scrape_schedule(group, user_agent)
    if error:
        return jsonify({"error": error}), 400

    # Update Google Calendar with the scraped data
    update_google_calendar(data)

    return jsonify(data)


@app.route('/scrape/<group>/csv')
def scrape_csv(group):
    user_agent = request.headers.get('User-Agent')
    data, error = scrape_schedule(group, user_agent)
    if error:
        return jsonify({"error": error}), 400

    output = io.StringIO()
    fieldnames = ['Subject', 'Start Date', 'Start Time', 'End Date', 'End Time', 'All Day Event', 'Description',
                  'Location', 'Private']
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for lesson in data:
        writer.writerow(lesson)

    output.seek(0)
    return Response(
        output.getvalue().encode('utf-8-sig'),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=academic_schedule_{group}.csv"}
    )


if __name__ == '__main__':
    app.run(debug=True)
