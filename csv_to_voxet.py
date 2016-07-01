# Helper script to convert a .csv file into a GOCAD voxet (block model) file,
# which can be imported into GlassTerra - see https://data.glassterra.com/
#
# Copyright (c) 2016 GlassTerra Pty Ltd
# Author: Saxon Druce
# License: MIT
#
# This script has been developed on Windows with Python 3.4.
# It should work on other platforms, and other Python 3.x versions.
# It may require some changes to support Python 2.x.

import csv
import struct

# The name of the input file.
input_filename = 'BLOCKMODEL1_MOD.csv'

# Which column (zero-based) in the input source file to use for the value to be
# visualized.
value_column = 3

# The base for the name of the output files.
# There will be two output files:
# [output_filename_directory][output_filename_base].vo
# [output_filename_directory][output_filename_base]_[output_property_name]@@
output_filename_base = 'BLOCKMODEL1_MOD'

# The directory that the output files are written to (empty for current 
# directory).
output_filename_directory = ''

# The name of the property in the output file.
output_property_name = 'prop_value'

# The size of each block in x/y/z.
block_size_x = 1
block_size_y = 1
block_size_z = 1

# The value written to the output file which means 'no data', meaning a cell
# will be left empty.
# If the input data has a cell with this same value, it will be treated as an
# empty cell in the output.
no_data_value = -99999

# Simple definition of a class for a block.
class Block:
	def __init__(self, x, y, z, value):
		self.x = x
		self.y = y
		self.z = z
		self.value = value

print('Reading input file')

# Setup list to contain all the blocks.
blocks = []

# Open the input file.
with open(input_filename, 'rt') as csvfile:
    csvreader = csv.reader(csvfile)

    # Skip the header row.
    next(csvreader)

    # Loop over the values in the file.
    for row in csvreader:

		# Get the x/y/z of the block (assumed integral values).     
        x = int(row[0])
        y = int(row[1])
        z = int(row[2])

        # Get the value that we want.
        value = float(row[value_column])

		# Add a block to the list of blocks.
        block = Block(x, y, z, value)
        blocks.append(block)
        
print('- read %d blocks' % (len(blocks)))       

# Work out the min/max of the x/y/z.
min_x = min([block.x for block in blocks])
max_x = max([block.x for block in blocks])
min_y = min([block.y for block in blocks])
max_y = max([block.y for block in blocks])
min_z = min([block.z for block in blocks])
max_z = max([block.z for block in blocks])
print('- x %d to %d' % (min_x, max_x))
print('- y %d to %d' % (min_y, max_y))
print('- z %d to %d' % (min_z, max_z))

# Work out how many blocks there are in each dimension.
num_x = max_x - min_x + 1
num_y = max_y - min_y + 1
num_z = max_z - min_z + 1

# Create the output .vo file.
# This file just contains text metadata which describes the data.
print('Writing output .vo file')
output_filename_vo = output_filename_directory + output_filename_base + '.vo'
with open(output_filename_vo, 'wt') as output_file_vo:

	# Header.
	output_file_vo.write('GOCAD Voxet 1\n')

	# Write out the origin.
	# This is offset so that a minimum block at x,y,z = 1,1,1 will be at 0,0,0.
	output_file_vo.write(
		'AXIS_O %f %f %f\n' %
		(
			block_size_x * (min_x - 1), 
			block_size_y * (min_y - 1), 
			block_size_z * (min_z - 1)
		))

	# Write out the size of each dimension.
	output_file_vo.write('AXIS_U %f 0 0\n' % (block_size_x * (num_x - 1)))
	output_file_vo.write('AXIS_V 0 %f 0\n' % (block_size_y * (num_y - 1)))
	output_file_vo.write('AXIS_W 0 0 %f\n' % (block_size_z * (num_z - 1)))
	output_file_vo.write('AXIS_MIN 0 0 0\n')
	output_file_vo.write('AXIS_MAX 1 1 1\n')

	# Write out the number of blocks.
	output_file_vo.write('AXIS_N %d %d %d\n' % (num_x, num_y, num_z))

	# Write out the property definition.
	output_file_vo.write('\n')
	output_file_vo.write('PROPERTY 1 "%s"\n' % (output_property_name))
	output_file_vo.write('PROP_NO_DATA_VALUE 1 %f\n' % (no_data_value));
	output_file_vo.write(
		'PROP_FILE 1 %s_%s@@\n' % (output_filename_base, output_property_name))

	# Write the end of the file.
	output_file_vo.write('\n')
	output_file_vo.write('END\n')

# Create a dictionary of blocks, indexed on a tuple x/y/z.
blocks_dict = {(block.x, block.y, block.z): block for block in blocks}

# Create the output @@ data file.
# This file contains the binary data for each cell.
# This data is a regular grid of x * y * z cells. Cells which weren't defined
# in the input, are 
print('Writing output @@ file')
output_filename_data = \
	output_filename_directory + output_filename_base + '_' + \
	output_property_name + '@@'
with open(output_filename_data, 'wb') as output_file_data:

	# Loop over the blocks in the output file.
	# u/v/w is equivalent to x/y/z in the output file's zero-based coordinates.
	for w in range(num_z):
		for v in range(num_y):
			for u in range(num_x):

				# Work out the coordinates of the cell.
				x = min_x + u
				y = min_y + v
				z = min_z + w

				# Get the value for this block from the dictionary, ie from
				# the source data, or the no-data value if the block wasn't in
				# the source data.
				key = (x, y, z)
				value = no_data_value
				if key in blocks_dict:
					value = blocks_dict[key].value

				# Write the value to the file as a 4-byte (single precision)
				# float, in big endian format.
				output_file_data.write(struct.pack('>f', value))

# That's it, now import the files into GlassTerra :)
print('Done')
