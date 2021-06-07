# gmmkctl_py
Cross platform utility to control the features of a Glorious modular mechanical keyboard.

It is a translation into Python of the original [gmmkctl](https://github.com/paulguy/gmmkctl) which is written in C. Many thanks to [paulguy](https://github.com/paulguy) and the other contributors to gmmkctl for doing most of the hard work already.

## Dependencies
- pyusb (`pip install pyusb`)

## Usage
Running with `sudo` is necessary due to needing hardware access.  
`sudo python main.py [COMMAND] [ARGS]`

For all possible commands run `python main.py -h`

### Setting individual key colors
To set the colors of individual keys you must know the numbers associated with those keys, check the respective file in the "keymaps" folder according to your layout to find these.

You must create a file with a structure where:  
- The first value is the number of the key you want to start at  
- The second value is the number of consecutive keys you will specify colors for (the number of triples following this value)  
- All following values are RGB triples with each component in the range 0-255  

Every value, including each component of the RGB triples, must be seperated by whitespace.

See "example_key_colors" folder for examples.

Once you have created the file you must run:  
`sudo python main.py -k [filepath]`  
followed by:  
`sudo python main.py -m 20`  
to set the key colors and change mode to view them.
