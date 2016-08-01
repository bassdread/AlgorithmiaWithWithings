# AlgorithmiaWithWithings
Run Algorithmia tasks against Withings data in Python

# Setup Withings
You will need an app configuring on the Withings side. http://oauth.withings.com/partner/dashboard provides some simple steps to setup a new app. You will need the API Key and API Secret which map to CONSUMER_KEY and CONSUMER_SECRET in the Python app below.

More information on the OAuth setup can be found here: http://oauth.withings.com/api

# Setup the App
```
git clone git@github.com:bassdread/AlgorithmiaWithWithings.git
cd AlgorithmiaWithWithings
virtualenv .
source bin/activate
pip install -r requirements.txt
cp src/algor/settings/__init__.py.example src/algor/settings/__init__.py
vi src/algor/settings/__init__.py
# add you settings and save the changes.
python src/algor/app.py # run the app
```

Now you wil have the available graphs at http://127.0.0.1:5000.
