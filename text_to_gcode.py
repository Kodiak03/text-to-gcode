
#!/usr/bin/python3
#pylint: disable=no-member

from enum import Enum
import os
import math
import argparse

class Instr:
	class Type(Enum):
		move = 0,
		write = 1,

	def __init__(self, *args):
		if len(args) == 1 and type(args[0]) is str: # args must be a data str
			attributes = args[0].split(' ')
			# G_ X__ Y__
			self.type = Instr.Type.move if attributes[0][1] == '0' else Instr.Type.write
			self.x = float(attributes[1][1:])
			self.y = float(attributes[2][1:])
		elif len(args) == 3 and type(args[0]) is Instr.Type and type(args[1]) is float and type(args[2]) is float:
			self.type, self.x, self.y = args
		else:
			raise TypeError("Instr() takes one (str) or three (Instr.Type, float, float) arguments")

	def __repr__(self):
		return "G%d X%.2f Y%.2f" % (self.type.value[0], self.x, self.y)

	def translated(self, x, y):
		return Instr(self.type, self.x + x, self.y + y)

class Letter:
	def __init__(self, *args):
		if len(args) == 1 and type(args[0]) is str:
			self.instructions = []
			for line in args[0].split('\n'):
				if line != "":
					self.instructions.append(Instr(line))

			pointsOnX = [instr.x for instr in self.instructions]
			self.width = max(pointsOnX) - min(pointsOnX)
		elif len(args) == 2 and type(args[0]) is list and type(args[1]) is float:
			self.instructions = args[0]
			self.width = args[1]
		else:
			raise TypeError("Letter() takes one (str) or two (list, float) arguments")

	def __repr__(self):
		return "\n".join([repr(instr) for instr in self.instructions]) + "\n"

	def translated(self, x, y):
		return Letter([instr.translated(x, y) for instr in self.instructions], self.width)


def readLetters(directory):
	letters = {
		" ": Letter([], 4.0),
		"\n": Letter([], math.inf)
	}
	for root,_,filenames in os.walk(directory):
		for filename in filenames:
			file = open(os.path.join(root,filename),"r")
			letterRepr = file.readline()[1]
			letter = Letter(file.read())
			letters[letterRepr] = letter
	return letters

def textToGcode(letters, text, lineLength, lineSpacing, padding):
    # Used for fast string concatenation
    gcodeLettersArray = []

    # Add the initial M3 S75 (pen up) to ensure it's in the final output
    gcodeLettersArray.append("M3 S75\n")

    offsetX, offsetY = 0, 0

    for char in text:
        # Retrieve and translate the letter
        letter = letters[char].translated(offsetX, offsetY)

        # Add comments indicating where the letter starts and ends
        gcodeLettersArray.append(f"; Letter: '{char}' starts at X={offsetX:.2f}, Y={offsetY:.2f}\n")
        
        for instr in letter.instructions:
            # Skip over pen-up/pen-down commands but still add them to the G-code
            if "M3" in repr(instr):
                gcodeLettersArray.append(repr(instr) + "\n")
            else:
                gcodeLettersArray.append(repr(instr) + "\n")

        gcodeLettersArray.append(f"\n; Letter: '{char}' ends\n")

        # Update offsets
        offsetX += letter.width + padding
        if offsetX >= lineLength:
            offsetX = 0
            offsetY -= lineSpacing

    # Add the final M3 S75 (pen up) to ensure it's in the final output
    gcodeLettersArray.append("M3 S75\n")

    return "".join(gcodeLettersArray)



def parseArgs(namespace):
	argParser = argparse.ArgumentParser(fromfile_prefix_chars="@",
		description="Compiles text into 2D gcode for plotters")

	argParser.add_argument_group("Data options")
	argParser.add_argument("-i", "--input", type=argparse.FileType('r'), default="-", metavar="FILE",
		help="File to read characters from")
	argParser.add_argument("-o", "--output", type=argparse.FileType('w'), required=True, metavar="FILE",
		help="File in which to save the gcode result")
	argParser.add_argument("-g", "--gcode-directory", type=str, default="./ascii_gcode/", metavar="DIR",
		help="Directory containing the gcode information for all used characters")

	argParser.add_argument_group("Text options")
	argParser.add_argument("-l", "--line-length", type=float, required=True,
		help="Maximum length of a line")
	argParser.add_argument("-s", "--line-spacing", type=float, default=8.0,
		help="Distance between two subsequent lines")
	argParser.add_argument("-p", "--padding", type=float, default=1.5,
		help="Empty space between characters")

	argParser.parse_args(namespace=namespace)


# blt Testing

def modify_gcode(gcode):
    # Split the input G-code into individual lines
    lines = gcode.splitlines()
    
    # Initialize a new list to store modified lines
    modified_gcode = []
    
    # Add M3 S75 at the start
    modified_gcode.append("M3 S75")
    
    # Loop through each line to process the G0 and G1 commands
    previous_command = None  # To track the previous command for transitions
    
    for line in lines:
        # Check for G0 or G1 commands
        if "G0" in line:
            if previous_command == "G1":
                modified_gcode.append("M3 S75")  # Add M3 S75 before G0 if transitioning from G1
            modified_gcode.append(line)  # Add the G0 command
            previous_command = "G0"  # Update the previous command
        elif "G1" in line:
            if previous_command == "G0":
                modified_gcode.append("M3 S90")  # Add M3 S90 before G1 if transitioning from G0
            modified_gcode.append(line)  # Add the G1 command
            previous_command = "G1"  # Update the previous command
    
    # Add M3 S75 at the end
    modified_gcode.append("M3 S75")
    
    # Join the modified lines into a single string and return
    return "\n".join(modified_gcode)

# Example G-code input
gcode_input = """G0 X0.00 Y6.03
G1 X0.00 Y1.76
G0 X0.00 Y0.00
G1 X0.00 Y0.00"""

# Modify the G-code
modified_gcode = modify_gcode(gcode_input)

# Print the modified G-code
print(modified_gcode)

# blt end test




def main():
	class Args: pass
	parseArgs(Args)

	letters = readLetters(Args.gcode_directory)
	data = Args.input.read()
	gcode = textToGcode(letters, data, Args.line_length, Args.line_spacing, Args.padding)
	Args.output.write(gcode)


if __name__ == '__main__':
	main()
