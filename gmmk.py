"""
Copyright 2021 paulguy <paulguy119@gmail.com>
Copyright 2021 missing-semi-colon <https://github.com/missing-semi-colon>

This file is part of gmmkctl_py.

gmmkctl_py is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

gmmkctl_py is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with gmmkctl_py.  If not, see <https://www.gnu.org/licenses/>.
"""

import usb.core
import usb.util
from typing import Union

VENDOR_ID = 0x0C45
PRODUCT_ID = 0x652F
ENDPOINT_OUT = 0x03
ENDPOINT_IN = 0x82
PACKET_SIZE = 64
TIMEOUT_MS = 1000

MAX_KEY = 126

SUM_OFFSET = 1
COMMAND_OFFSET = 3

CMD_START = 1
CMD_END = 2

CMD_KEYCOLORS = 0x11
KEYCOLORS_COUNT_OFFSET = 4
KEYCOLORS_START_OFFSET = 5
KEYCOLORS_DATA_OFFSET = 8
KEYCOLORS_DATA_SIZE = PACKET_SIZE - KEYCOLORS_DATA_OFFSET

CMD_SUBCOMMAND = 0x06
SUBCMD_CMD_OFFSET = 4
SUBCMD_ARG_OFFSET = 8

SUBCMD_MODE = [0x01, 0x00, 0x00, 0x00]
SUBCMD_BRIGHTNESS = [0x01, 0x01, 0x00, 0x00]
SUBCMD_DELAY = [0x01, 0x02, 0x00, 0x00]
SUBCMD_DIRECTION = [0x01, 0x03, 0x00, 0x00]
SUBCMD_COLORFUL = [0x01, 0x04, 0x00, 0x00]
SUBCMD_COLOR = [0x03, 0x05, 0x00, 0x00]
SUBCMD_RATE = [0x01, 0x0f, 0x00, 0x00]

ARG_DIRECTION_LEFT = 0xFF
ARG_DIRECTION_RIGHT = 0
ARG_COLORFUL = 1
ARG_NOT_COLORFUL = 0


def get_gmmk() -> usb.core.Device:
	""" Returns the first GMMK found """
	device = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
	if device is None:
		raise ValueError("Device not found")
		return None
	return device

def setup(device: usb.core.Device) -> None:
	""" Obtains control of `device` """
	# Release control of the keyboard from anything that has it
	_detach_kernel_drivers(device)
	# Set configuration to the first found
	device.set_configuration()

def send_cmd(device: usb.core.Device, cmd: list, cmd_arg: Union[int, list]) -> None:
	_cmd_start(device)
	_cmd_body(device, cmd, cmd_arg)
	_cmd_end(device)

def set_mode(device: usb.core.Device, mode: int) -> None:
	send_cmd(device, SUBCMD_MODE, mode)

def set_brightness(device: usb.core.Device, brightness: int) -> None:
	send_cmd(device, SUBCMD_BRIGHTNESS, brightness)

def set_delay(device: usb.core.Device, delay: int) -> None:
	send_cmd(device, SUBCMD_DELAY, delay)

def set_direction_left(device: usb.core.Device) -> None:
	send_cmd(device, SUBCMD_DIRECTION, ARG_DIRECTION_LEFT)

def set_direction_right(device: usb.core.Device) -> None:
	send_cmd(device, SUBCMD_DIRECTION, ARG_DIRECTION_RIGHT)

def set_colorful(device: usb.core.Device) -> None:
	send_cmd(device, SUBCMD_COLORFUL, ARG_COLORFUL)

def set_not_colorful(device: usb.core.Device) -> None:
	send_cmd(device, SUBCMD_COLORFUL, ARG_NOT_COLORFUL)

def set_color(device: usb.core.Device, r: int, g: int, b: int) -> None:
	send_cmd(device, SUBCMD_COLOR, [r, g, b])

def set_rate(device, rate) -> None:
	""" Set the polling rate """
	send_cmd(device, SUBCMD_RATE, rate)

def set_keys(device: usb.core.Device, start: int, count: int, colors: list) -> None:
	"""
	Sets the colors of the keys, starting with the key with number `start` and
	the following `count` keys

	Args:
		device: a GMMK
		start: number of the starting key
		count: number of keys
		colors: colors to set the keys
	"""
	if start > MAX_KEY:
		return
	if start + count > MAX_KEY:
		count = MAX_KEY - start

	_cmd_start(device)

	start_key_offset = 0
	while start_key_offset < count:
		buffer = [0]*PACKET_SIZE
		buffer[0] = 4

		buffer[COMMAND_OFFSET] = CMD_KEYCOLORS

		# Number of key's colors to send in the next packet
		packet_key_count = min(count - start_key_offset, KEYCOLORS_DATA_SIZE // 3)
		# Number of the starting key to send in the next packet
		packet_key_start = start + start_key_offset
		# Each color has 3 bytes
		buffer[KEYCOLORS_COUNT_OFFSET] = packet_key_count * 3
		# The start offset must be split over 2 bytes
		buffer[KEYCOLORS_START_OFFSET:KEYCOLORS_START_OFFSET+2] = [
			(packet_key_start * 3) % 256,
			(packet_key_start * 3) // 256 ]

		# Write the color bytes into the buffer
		color_byte_offset = 0
		while color_byte_offset < buffer[KEYCOLORS_COUNT_OFFSET]:
			color_idx = start_key_offset + (color_byte_offset // 3)
			buffer[KEYCOLORS_DATA_OFFSET+color_byte_offset]   = colors[color_idx][0]
			buffer[KEYCOLORS_DATA_OFFSET+color_byte_offset+1] = colors[color_idx][1]
			buffer[KEYCOLORS_DATA_OFFSET+color_byte_offset+2] = colors[color_idx][2]
			color_byte_offset += 3

		buffer[SUM_OFFSET:COMMAND_OFFSET] = _get_buffer_sum(buffer)

		packet = bytes(buffer)
		device.write(ENDPOINT_OUT, packet)
		device.read(ENDPOINT_IN, PACKET_SIZE, TIMEOUT_MS)
		start_key_offset += packet_key_count

	_cmd_end(device)

def _detach_kernel_drivers(device: usb.core.Device) -> None:
	""" Detaches active drivers so that the device can be controlled """
	c = 1
	for cfg in device:
		for i in range(cfg.bNumInterfaces):
			if device.is_kernel_driver_active(i):
				try:
					device.detach_kernel_driver(i)
				except usb.core.USBError as e:
					print("Could not detach kernel driver")
		c += 1

def _cmd_start(device: usb.core.Device) -> None:
	buffer = [0]*PACKET_SIZE
	buffer[COMMAND_OFFSET] = CMD_START
	packet = bytes(buffer)
	device.write(ENDPOINT_OUT, packet)

def _cmd_body(device: usb.core.Device, cmd: list, cmd_arg: Union[int, list]) -> None:
	buffer = [0]*PACKET_SIZE
	buffer[COMMAND_OFFSET] = CMD_SUBCOMMAND
	buffer[SUBCMD_CMD_OFFSET:SUBCMD_CMD_OFFSET + len(cmd)] = cmd
	if not (type(cmd_arg) is list):
		buffer[SUBCMD_ARG_OFFSET] = cmd_arg
	else:
		buffer[SUBCMD_ARG_OFFSET:SUBCMD_ARG_OFFSET+len(cmd_arg)] = cmd_arg
	packet = bytes(buffer)
	device.write(ENDPOINT_OUT, packet)
	device.read(ENDPOINT_IN, PACKET_SIZE, TIMEOUT_MS)

def _cmd_end(device: usb.core.Device) -> None:
	buffer = [0]*PACKET_SIZE
	buffer[COMMAND_OFFSET] = CMD_END
	packet = bytes(buffer)
	device.write(ENDPOINT_OUT, packet)

def _get_buffer_sum(buffer: list) -> list:
	""" Returns the sum of `buffer` from `COMMAND_OFFSET`, split over 2 bytes """
	b_sum = sum(buffer[COMMAND_OFFSET:])
	b_sum1 = b_sum % 256
	b_sum2 = b_sum // 256
	return [b_sum1, b_sum2]
