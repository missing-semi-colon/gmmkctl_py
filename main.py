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

import sys
from typing import Generator, Callable

import gmmk


def run_func(f: Callable[..., None], args: list) -> None:
	"""
	Handles aquiring and releasing the GMMK and runs the gmmk function `f` on
	`args`

	Args:
		f: Any of the gmmk.set_* functions
		args: arguments for `f`, excluding the device
	"""
	device = None
	try:
		device = gmmk.get_gmmk()
		gmmk.setup(device)
		f(device, *args)
	finally:
		if device:
			# Give control back to whatever had it
			device.attach_kernel_driver(0)

def main() -> None:
	if len(sys.argv) <= 1:
		_show_help()
		return
	command = sys.argv[1]
	args = sys.argv[2:]

	if command in ["--help", "-h"]:
		_show_help()
	elif command in ["--mode", "-m"]:
		if len(args) == 0:
			print("Error: Command '--mode', '-m' requires 1 argument")
			return
		run_func(gmmk.set_mode, [int(args[0])])
	elif command in ["--brightness", "-b"]:
		if len(args) == 0:
			print("Error: Command '--brightness', '-b' requires 1 argument")
			return
		run_func(gmmk.set_brightness, [int(args[0])])
	elif command in ["--delay", "-d"]:
		if len(args) == 0:
			print("Error: Command '--delay', '-d' requires 1 argument")
			return
		run_func(gmmk.set_delay, [int(args[0])])
	elif command in ["--left", "-l"]:
		run_func(gmmk.set_direction_left, [])
	elif command in ["--right", "-r"]:
		run_func(gmmk.set_direction_right, [])
	elif command in ["--colorful", "-f"]:
		run_func(gmmk.set_colorful, [])
	elif command in ["--single", "-s"]:
		run_func(gmmk.set_not_colorful, [])
	elif command in ["--rate", "-z"]:
		if len(args) == 0:
			print("Error: Command '--rate', '-z' requires 1 argument")
			return
		run_func(gmmk.set_rate, [int(args[0])])
	elif command in ["--color", "-c"]:
		if len(args) < 3:
			print("Error: Command '--color', '-c' requires 3 arguments")
			return
		run_func(gmmk.set_color, map(int, args))
	elif command in ["--keys", "-k"]:
		if len(args) == 0:
			print("Error: Command '--keys', '-k' requires 1 argument")
			return
		start, count, colors = _read_key_colors(args[0])
		run_func(gmmk.set_keys, (start, count, colors))
	else:
		print("Command not found")
		_show_help()

def _show_help() -> None:
	str = "Commands:\n"
	str += "	--help, -h		Shows this help text\n"
	str += "	--mode NUM, -m		Set the mode (1-20)\n"
	str += "	--brightness NUM, -b	Set the brightness (0-4)\n"
	str += "	--delay NUM, -d		Set the delay between animation frames. Smaller values are more meaningful (0-255)\n"
	str += "	--left, -l		Set animation to proceed towards the left\n"
	str += "	--right, -r		Set animation to proceed towards the right\n"
	str += "	--colorful, -f		Turn on colorful mode\n"
	str += "	--single, -s		Turn on single color (not colorful) mode\n"
	str += "	--rate NUM, -z		Adjust polling rate (not tested): 0=125Hz, 1=250Hz, 2=500Hz, 3=1000Hz, 4+=?\n"
	str += "	--color R G B, -c	Set color for single color mode (0-255)\n"
	str += "	--keys FILE, -k		Set individual keys' colors according to FILE\n"
	print(str)

def _read_key_colors(filepath: str) -> list:
	"""
	Args:
		filepath: path to the file specifying the key colors

	Returns:
		The number of the starting key, the number of keys and a list of
		triples specifying the color each key should be
	"""
	with open(filepath, "r") as file:
		values = _get_items(file.read())
		start = int(next(values))
		count = int(next(values))

		colors = []
		while True:
			color = (
				int(next(values, -1)),
				int(next(values, -1)),
				int(next(values, -1)) )
			if -1 in color:
				break
			else:
				colors.append(color)
		return start, count, colors

def _get_items(text: str) -> Generator[str, None, None]:
	""" Yields the next string of non-whitespace characters """
	for item in text.split():
		yield item

if __name__ == "__main__":
	main()
