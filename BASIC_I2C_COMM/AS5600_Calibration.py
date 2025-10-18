from smbus2 import SMBus
import time, json, os

# I2C Setup parameter
I2C_BUS = 1
MUX_ADDR = 0x70
AS5600_ADDR = 0x36
CHANNEL = 0
CONFIG_FILE = "joint0_config.json"


bus = SMBus(I2C_BUS)

def select_channel(ch):
	bus.write_byte(MUX_ADDR, 1 << ch)
	time.sleep(0.002)

def read_raw_angle():
	# Read raw angle 0-360 from AS5600
	select_channel(CHANNEL)
	bus.write_byte(AS5600_ADDR, 0x0E)
	data = bus.read_i2c_block_data(AS5600_ADDR, 0X0E, 2)
	raw = (data[0] << 8 | data[1]) & 0x0FFF
	return raw * 360.0 / 4096.0

def calibrated_angle(raw, zero_offset, invert=False):
	# Convert raw angles to joint angles relativt to mechanical zero
	val = raw - zero_offset
	if invert:
		val = -val

	val = val % 360
	if val > 180:
		val -=360
	return val


def load_config():
	if os.path.exists(CONFIG_FILE):
		try:
			with open(CONFIG_FILE, "r") as f:
				cfg = json.load(f)
			if isinstance(cfg, dict) and "zero_offset" in cfg and "invert" in cfg:
				return cfg

		except Exception:
			pass
	return {"zero_offset": 0.0, "invert": False}


def save_config(cfg):
	with open(CONFIG_FILE, "w") as f:
		json.dump(cfg, f)



if __name__ == "__main__":
	cfg = load_config()
	
	print("Joint0 AS5600 Zero Calibration")
	print("Move Joint to Mechabical Zero")
	print("Press ENTER to set this position to zero")

	raw = read_raw_angle()
	cfg["zero_offset"] = raw
	save_config(cfg)
	print("Mechanical zero set at raw: ", round(raw, 2))
	bus.close()


