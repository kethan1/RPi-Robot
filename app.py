#!/usr/bin/env python3
from importlib import import_module
import os
from flask import *
import RPi.GPIO as GPIO

from camera_pi import Camera

app = Flask(__name__)

GPIO.setmode(GPIO.BCM)
pinlist = [26, 19, 13, 6]
GPIO.setup(pinlist, GPIO.OUT)
GPIO.output(pinlist, GPIO.LOW)

moveInfo = []

@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')


def gen(camera):
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/move_robot', methods=["POST"])
def move_robot():
    print(request.json)
    if request.json["direction"] != "still":
        moveInfo = [request.json["direction"], request.json["angle"]]
        print(moveInfo)
    else:
        moveInfo = ["still"]
        GPIO.output(pinlist, GPIO.LOW)
    return "Good"


if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', threaded=True)
    except KeyboardInterrupt:
        GPIO.cleanup()
