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

global FORECAST_ON_AVERAGE
FORECAST_ON_AVERAGE = FALSE

# naff cahce to say on API calls while testing
global RESULTS
RESULTS = False


@app.route("/")
def withings():

    global RESULTS

    if not RESULTS:
        RESULTS = _fetch_withings()

    return render_template('withings.html', readings=RESULTS)


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
        # predictions
        'future' : {
            'x': '',
            'diastolic': '',
            'systolic': '',
            'pulse': '',
            'simple_moving_average' : {
                'diastolic': '',
                'pulse': '',
                'systolic': '',
            }
        },
        # analysis of past readings
        'past': {
            'x': '',
            'diastolic': '',
            'systolic': '',
            'pulse': '',
            'simple_moving_average' : {
                'diastolic': '',
                'pulse': '',
                'systolic': '',
            }
        }
    }

    measures = client.get_measures()

    # make sure the graph goes left to right
    measures.reverse()

    last_reading_date = measures[-1].date
    counter = 1

    raw_readings = {
        'systolic': [],
        'diastolic': [],
        'pulse': [],
    }

    for measure in measures:

        if measure.systolic_blood_pressure\
           and measure.diastolic_blood_pressure:

            next_date = last_reading_date + timedelta(days=counter)

            # sort out date times
            readings['past']['x'] += '"' + measure.date.strftime('%Y-%m-%d %H:%M:%S') + '",'
            readings['future']['x'] += '"' + next_date.strftime('%Y-%m-%d %H:%M:%S') + '",'

            readings['past']['systolic'] += str(measure.systolic_blood_pressure) + ','
            readings['past']['diastolic'] += str(measure.diastolic_blood_pressure) + ','

            # keep ints for for sending to ALGORITHMIA
            # should really rename it...
            raw_readings['systolic'].append(measure.systolic_blood_pressure)
            raw_readings['diastolic'].append(measure.diastolic_blood_pressure)

            if measure.heart_pulse and measure.heart_pulse > 30:
                raw_readings['pulse'].append(measure.heart_pulse)
                readings['past']['pulse'] += str(measure.heart_pulse) + ','

            counter += 1

        if measure.weight:
            pass

    # trim that last ,
    readings['past']['diastolic'] = readings['past']['diastolic'][:-1]
    readings['past']['systolic'] = readings['past']['systolic'][:-1]
    readings['past']['pulse'] = readings['past']['pulse'][:-1]

    # simple moving average of existing data
    readings['past']['simple_moving_average']['diastolic'], average_diastolic = _get_simple_moving_average(raw_readings['diastolic'])
    readings['past']['simple_moving_average']['systolic'], average_systolic = _get_simple_moving_average(raw_readings['systolic'])
    readings['past']['simple_moving_average']['pulse'], average_pulse = _get_simple_moving_average(raw_readings['pulse'])

    global FORECAST_ON_AVERAGE

    if FORECAST_ON_AVERAGE:
        readings['future']['diastolic'], future_diastolic = _get_forecast(average_diastolic)
        readings['future']['systolic'], future_systolic = _get_forecast(average_systolic)
        readings['future']['pulse'], future_pulse = _get_forecast(average_pulse)
    else:
        # populate the standard graphs and get the raw data to feed into thenext algorithm
        readings['future']['diastolic'], future_diastolic = _get_forecast(raw_readings['diastolic'])
        readings['future']['systolic'], future_systolic = _get_forecast(raw_readings['systolic'])
        readings['future']['pulse'], future_pulse = _get_forecast(raw_readings['pulse'])

    # simple moving average of future data
    readings['future']['simple_moving_average']['diastolic'], average_diastolic = _get_simple_moving_average(future_diastolic)
    readings['future']['simple_moving_average']['systolic'], average_systolic = _get_simple_moving_average(future_systolic)
    readings['future']['simple_moving_average']['pulse'], average_pulse = _get_simple_moving_average(future_pulse)

    return readings


def _get_forecast(data):

    string = ''
    raw = []

    reply = FORECAST.pipe(data)
    for reading in reply.result:
        string += str(int(reading)) + ','
        raw.append(reading)

    string = string[:-1]

    return string, raw


def _get_simple_moving_average(data):

    string = ''
    raw = []

    reply = SIMPLE_MOVING_AVERAGE.pipe(data)
    for reading in reply.result:
        string += str(int(reading)) + ','
        raw.append(reading)

    string = string[:-1]

    return string, raw

if __name__ == "__main__":
    app.run()
