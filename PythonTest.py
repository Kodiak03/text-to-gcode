print("--------------")
print("Hello World")
print("--------------")



import subprocess


# Absolute path to the Python script
script_path = r"C:\0-Berend\Projects\CodeStuffs\text_to_gcode.py"

# Define the command and arguments
command = [
    "python", script_path,
    "--input", "bltinput.txt",
    "--output", "output2.nc",
    "--line-length", "300",
    "--line-spacing", "10",
    "--padding", "3"
]

# Execute the command
subprocess.run(command)


#py .\text_to_gcode.py --input bltinput.txt --output output.nc --line-length 300 --line-spacing 10 --padding 3
