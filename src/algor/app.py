import Algorithmia

from flask import Flask
from flask import render_template

from settings import *

from datetime import timedelta
from withings import WithingsApi, WithingsCredentials


ALGORITHMIA_CLIENT = Algorithmia.client(ALGORITHMIA_KEY)
SIMPLE_MOVING_AVERAGE = ALGORITHMIA_CLIENT.algo('TimeSeries/SimpleMovingAverage/0.2.0')
FORECAST = ALGORITHMIA_CLIENT.algo('TimeSeries/Forecast/0.2.0')

app = Flask(__name__)


@app.route("/")
def withings():
    meh, readings = _fetch_withings()

    return render_template('withings.html', readings=readings)


def _fetch_withings():

    results = []

    creds = WithingsCredentials()
    creds.access_token = ACCESS_TOKEN
    creds.access_token_secret = ACCESS_TOKEN_SECRET
    creds.user_id = USER_ID
    creds.consumer_key = CONSUMER_KEY
    creds.consumer_secret = CONSUMER_SECRET
    client = WithingsApi(creds)

    readings = {
        'systolic': {
            'x': '',
            'y': '',
        },
        'diastolic': {
            'x': '',
            'y': '',
        },
        'simple_moving_average': {
            'systolic': {
                'x': '',
                'y': '',
            },
            'diastolic': {
                'x': '',
                'y': '',
            },
        },
        'systolic_future': {
            'x': '',
            'y': [],
        },
        'diastolic_future': {
            'x': '',
            'y': [],
        },
        'pulse': {
            'x': '',
            'y': '',
        },
    }

    measures = client.get_measures()

    measures.reverse()

    last_reading_date = measures[-1].date
    counter = 1

    for measure in measures:

        if measure.systolic_blood_pressure\
           and measure.diastolic_blood_pressure:

            next_date = last_reading_date + timedelta(days=counter)

            readings['systolic']['x'] += '"' + measure.date.strftime('%Y-%m-%d %H:%M:%S') + '",'
            readings['diastolic']['x'] += '"' + measure.date.strftime('%Y-%m-%d %H:%M:%S') + '",'

            readings['systolic_future']['x'] += '"' + next_date.strftime('%Y-%m-%d %H:%M:%S') + '",'
            readings['diastolic_future']['x'] += '"' + next_date.strftime('%Y-%m-%d %H:%M:%S') + '",'

            readings['systolic']['y'] += str(measure.systolic_blood_pressure) + ','
            readings['diastolic']['y'] += str(measure.diastolic_blood_pressure) + ','

            # keep ints for for sending to ALGORITHMIA
            readings['systolic_future']['y'].append(measure.systolic_blood_pressure)
            readings['diastolic_future']['y'].append(measure.diastolic_blood_pressure)

            if measure.heart_pulse and measure.heart_pulse > 30:
                readings['pulse']['x'] += '"' + measure.date.strftime('%Y-%m-%d %H:%M:%S') + '",'
                readings['pulse']['y'] += str(measure.heart_pulse) + ','

            counter += 1

        if measure.weight:
            pass

    # trim that last ,
    readings['diastolic']['y'] = readings['diastolic']['y'][:-1]
    readings['systolic']['y'] = readings['systolic']['y'][:-1]

    readings['pulse']['y'] = readings['pulse']['y'][:-1]

    # simple moving average of existing data
    readings['diastolic']['x'] = readings['diastolic']['x'][:-1]
    readings['systolic']['x'] = readings['systolic']['x'][:-1]

    readings['pulse']['x'] = readings['pulse']['x'][:-1]

    readings['diastolic_future']['x'] = readings['diastolic_future']['x'][:-1]
    readings['systolic_future']['x'] = readings['systolic_future']['x'][:-1]

    # get simple moving average
    readings['simple_moving_average']['diastolic']['x'] = readings['diastolic']['x']
    readings['simple_moving_average']['systolic']['x'] = readings['systolic']['x']

    readings['simple_moving_average']['diastolic']['y'] = _get_simple_moving_average(readings['diastolic_future']['y'])
    readings['simple_moving_average']['systolic']['y'] = _get_simple_moving_average(readings['systolic_future']['y'])

    # call Algorithmia to get the predictions
    readings['diastolic_future']['y'] = _get_forecast(readings['diastolic_future']['y'])
    readings['systolic_future']['y'] = _get_forecast(readings['systolic_future']['y'])

    return results, readings


def _get_forecast(data):

    string = ''

    reply = FORECAST.pipe(data)
    for reading in reply.result:
        string += str(int(reading)) + ','

    string = string[:-1]

    return string


def _get_simple_moving_average(data):

    string = ''
    reply = SIMPLE_MOVING_AVERAGE.pipe(data)
    for reading in reply.result:
        string += str(int(reading)) + ','

    string = string[:-1]

    return string

if __name__ == "__main__":
    app.run()
