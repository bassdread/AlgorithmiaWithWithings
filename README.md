# AlgorithmiaWithWithings
Run Algorithmia tasks against Withings data in Python

# Setup
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
