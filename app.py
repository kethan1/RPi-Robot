#!/usr/bin/env python3
from flask import *
import RPi.GPIO as GPIO
import time
import os

from camera_pi import Camera

app = Flask(__name__)

GPIO.setmode(GPIO.BCM)
pinlist = [26, 19, 13, 6]
GPIO.setup(pinlist, GPIO.OUT)

right_forward = GPIO.PWM(6, 50)
right_backward = GPIO.PWM(26, 50)
left_backward = GPIO.PWM(19, 50)
left_forward = GPIO.PWM(13, 50)

motors = [right_forward, right_backward, left_backward, left_forward]
for motor in motors: motor.stop()

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
    if request.json["angle"] != "still":
        angle = request.json["angle"]
        print(angle)
        if 0 <= angle <= 90:
            percent_right = ((90-angle)/90)*100
            percent_forward = (angle/90)*100
            print("forward, right")
        elif 90 < angle <= 180:
            print("forward, left")
        elif -179 <= angle <= -90:
            percent_left = int(round(((abs(angle)-90)/90)*100, 0))
            percent_back = int(round((90-percent_left/90)*100, 0))
            # right_backward.start(percent_back)
            # left_backward.start(percent_left)
            print("backward, left", percent_left, percent_back)
        elif -90 < angle <= -1:
            percent_right = 0-(0-angle)
            percent_back = -90-(-90-angle)
            print("backward, right", percent_right, percent_back)
    else:
        for motor in motors: motor.stop()
    return "Good"


if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', threaded=True)
    except KeyboardInterrupt:
        GPIO.cleanup()
