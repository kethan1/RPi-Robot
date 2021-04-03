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

speed=100

motors = [right_forward, right_backward, left_backward, left_forward]
for motor in motors: motor.stop()

# assumes theta in degrees and r = 0 to 100 %
# returns a tuple of percentages: (left_thrust, right_thrust)
def throttle_angle_to_thrust(theta, r=speed):
    theta = ((theta + 180) % 360) - 180  # normalize value to [-180, 180)
    r = min(max(0, r), 100)              # normalize value to [0, 100]
    v_a = r * (45 - theta % 90) / 45          # falloff of main motor
    v_b = min(100, 2 * r + v_a, 2 * r - v_a)  # compensation of other motor
    if theta < -90: return -v_b, -v_a
    if theta < 0:   return -v_a, v_b
    if theta < 90:  return v_b, v_a
    return v_a, -v_b


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
    if request.json["angle"] != "still":
        angle = request.json["angle"]
        if ((angle - 180) % 360) + 180 <= 270:
            angle_adjusted = (((angle - 180) % 360) + 180)+90
        else:
            angle_adjusted = (((angle - 180) % 360) + 180)-90
        thrust = throttle_angle_to_thrust(angle_adjusted)
        if thrust[0] < 0:
            left_backward.start(abs(thrust[0]))
        else:
            left_forward.start(thrust[0])
        if thrust[1] < 0:
            right_backward.start(abs(thrust[1]))
        else:
            right_forward.start(thrust[1])
    else:
        for motor in motors: motor.stop()
    return "Good"


if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', debug=True, threaded=True)
    except KeyboardInterrupt:
        GPIO.cleanup()
