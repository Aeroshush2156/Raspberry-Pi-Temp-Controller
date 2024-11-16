from flask import Flask, jsonify, render_template, send_file, request
from flask_sqlalchemy import SQLAlchemy
import time, glob, threading, logging, csv, random
from logging.handlers import RotatingFileHandler
import RPi.GPIO as GPIO

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///temperature.db'
db = SQLAlchemy(app)


# Configure logging
logging.basicConfig(level=logging.INFO)
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)

# GPIO setup
HEAT_PIN = 17  # GPIO pin for heating relay
COOL_PIN = 27  # GPIO pin for cooling relay

# PWM Setup
HEAT_PWM = GPIO.PWM(HEAT_PIN, 1000)  # 1 kHz frequency
COOL_PWM = GPIO.PWM(COOL_PIN, 1000)  # 1 kHz frequency
HEAT_PWM.start(0)  # Start with 0% duty cycle (off)
COOL_PWM.start(0)  # Start with 0% duty cycle (off)
GPIO.setmode(GPIO.BCM)
GPIO.setup(HEAT_PIN, GPIO.OUT)
GPIO.setup(COOL_PIN, GPIO.OUT)




class Temperature(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    temp = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

# Function to read raw data from the temperature sensor
def read_temp_raw():
    try:
        base_dir = '/sys/bus/w1/devices/'
        device_folder = glob.glob(base_dir + '28*')[0]  # Assuming only one DS18B20 sensor
        device_file = device_folder + '/w1_slave'

        with open(device_file, 'r') as f:
            lines = f.readlines()
        return lines
    except Exception as e:
        logging.error(f"Error reading temperature sensor: {e}")
        return []

# Function to read and parse temperature data
def read_temp():
    lines = read_temp_raw()
    while lines and lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)  # Wait and try again if the sensor is not ready
        lines = read_temp_raw()
    if lines:
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos + 2:]
            temp_c = float(temp_string) / 1000.0
            return temp_c
    return None

# Function to save temperature to the database
def save_temp_to_db():
    while True:
        with app.app_context():
            temp = read_temp()
            if temp is not None:
                new_temp = Temperature(temp=temp)
                db.session.add(new_temp)
                db.session.commit()
                logging.info(f"Saved temperature: {temp}°C")
            else:
                logging.warning("Failed to read temperature")
        time.sleep(60)  # Save temperature every minute
@app.route('/data', methods=['GET'])
def get_data():
    readings = Temperature.query.all()
    data = [{'id': r.id, 'temp': r.temp, 'timestamp': r.timestamp.isoformat()} for r in readings]
    return jsonify(data)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/save_data', methods=['POST'])
def save_data():
    readings = Temperature.query.all()
    with open('temperature_data.csv', 'w', newline='') as csvfile:
        fieldnames = ['id', 'temp', 'timestamp']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for r in readings:
            writer.writerow({'id': r.id, 'temp': r.temp, 'timestamp': r.timestamp.isoformat()})
    return jsonify({'message': 'Data saved successfully'})

@app.route('/download', methods=['GET'])
def download_data():
    return send_file('temperature_data.csv', as_attachment=True)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        threading.Thread(target=save_temp_to_db, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=False)

# Function to control heating and cooling

def calculate_duty_cycle(current, desired):
    """ Simple linear calculation for duty cycle based on temperature difference. """
    difference = desired - current
    duty_cycle = max(0, min(100, difference * 10))  # Scale duty cycle proportionally (modify scaling as necessary)
    return duty_cycle

def control_temperature(target_temp):
    current_temp = read_temp()
    if current_temp is not None:
        if current_temp < target_temp:
            duty_cycle = calculate_duty_cycle(current_temp, target_temp)
            HEAT_PWM.ChangeDutyCycle(duty_cycle)
            COOL_PWM.ChangeDutyCycle(0)  # Turn off cooling
            logging.info(f"Heating ON, Cooling OFF. Current Temp: {current_temp}°C, Target Temp: {target_temp}°C")
        elif current_temp > target_temp:
            duty_cycle = calculate_duty_cycle(current_temp, target_temp)
            COOL_PWM.ChangeDutyCycle(duty_cycle)
            HEAT_PWM.ChangeDutyCycle(0)  # Turn off heating
            logging.info(f"Heating OFF, Cooling ON. Current Temp: {current_temp}°C, Target Temp: {target_temp}°C")
        else:
            HEAT_PWM.ChangeDutyCycle(0)  # Turn off heating
            COOL_PWM.ChangeDutyCycle(0)  # Turn off cooling
            logging.info(f"Heating OFF, Cooling OFF. Current Temp: {current_temp}°C, Target Temp: {target_temp}°C")

@app.route('/set_target_temp', methods=['POST'])
def set_target_temp():
    target_temp = request.json.get('target_temp')
    if target_temp is not None:
        try:
            target_temp = float(target_temp)  # Convert target_temp to float
            control_temperature(target_temp)
            return jsonify({'message': 'Target temperature set successfully'})
        except ValueError:
            return jsonify({'message': 'Invalid target temperature'}), 400
    return jsonify({'message': 'Invalid target temperature'}), 400

@app.route('/system_status', methods=['GET'])
def system_status():
    current_temp = read_temp()
    target_temp = request.args.get('target_temp', type=float)
    app.logger.info(f"Current Temp: {current_temp}, Target Temp: {target_temp}")
    if current_temp is not None and target_temp is not None:
        if current_temp < target_temp:
            status = 'Heating'
        elif current_temp > target_temp:
            status = 'Cooling'
        else:
            status = 'Idle'
        app.logger.info(f"System Status: {status}")
        return jsonify({'status': status})
    app.logger.warning("Failed to determine system status")
    return jsonify({'status': 'Unknown'}), 400