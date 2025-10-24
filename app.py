"""app.py: render and route to webpages"""
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def eventpage():
    return render_template('bookit-eventpage.html')

if __name__ == '__main__':
    app.run(debug=True)
