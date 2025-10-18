from smbus2 import SMBus, i2c_msg
import time

I2C_BUS = 1
Slave_Addr = 0x8
bus = SMBus(I2C_BUS)

try:
	while True:
		data_to_send = [ord('A')]
		bus.write_i2c_block_data(Slave_Addr, 0, data_to_send)
		print("Sent: ", data_to_send[0])
		time.sleep(0.5)

		read_len = 4
		msg = i2c_msg.read(Slave_Addr, read_len)
		bus.i2c_rdwr(msg)
		
		received = bytes(msg).decode('utf-8', errors = 'ignore')
		print("Received: ", received)
		time.sleep(0.5)
except KeyboardInterrupt:
	print("Stopped By User: ")
finally:
	bus.close()
