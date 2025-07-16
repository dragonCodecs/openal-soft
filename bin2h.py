#!/usr/bin/env python3
from argparse import ArgumentParser
from pathlib import Path

# Build a quick and dirty arguments parser
parser = ArgumentParser()
parser.add_argument('-i', dest = 'inFile', action = 'store', type = Path, required = True)
parser.add_argument('-o', dest = 'outFile', action = 'store', type = Path, required = True)

# Extract the command line arguments we care about
args = parser.parse_args()

# Try and open the input binary and output text files for read, and write respectively
with args.inFile.open('rb') as inputFile:
	with args.outFile.open('w') as outputFile:
		# Read each byte of the input file one by one and convert to hex, writing it to the output
		count = 0
		while True:
			value: bytes = inputFile.read(1)
			# Check if the value is empty (EOF)
			if value == b'':
				break
			# Fill the file up 16 encoded bytes per line, formatting for C(++) compiler consumption
			if (count & 15) == 0:
				outputFile.write('\t')
			else:
				outputFile.write(' ')
			outputFile.write(f'0x{value.hex()},')
			if (count & 15) == 15:
				outputFile.write('\n')
			count += 1
