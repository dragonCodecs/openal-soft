#!/usr/bin/env python3
from argparse import ArgumentParser
from pathlib import Path
from sys import exit
from subprocess import run

# Build a quick and dirty arguments parser
parser = ArgumentParser()
parser.add_argument('-i', dest = 'inFile', action = 'store', type = Path, required = True)
parser.add_argument('-o', dest = 'outFile', action = 'store', type = Path, required = True)
parser.add_argument('-v', dest = 'verFile', action = 'store', type = Path, required = True)
parser.add_argument('-g', dest = 'gitPath', action = 'store', type = Path, required = False)

# Extract the command line arguments we care about
args = parser.parse_args()

# Try and open the three files for read, write and read respectively (though do them out of order so we don't
# make the output file until we know the others are okay)
with args.inFile.open('r') as inputFile:
	# Extract the version tag from this file and make sure we get one single line string value out
	with args.verFile.open('rb') as versionTagFile:
		versionTagData: bytes = versionTagFile.read()
	versionTagLines = versionTagData.split(b'\n')
	if len(versionTagLines) > 2:
		print('ERROR: Version tag file improperly formed')
		exit(1)
	# Turn the version tag into a string for further consumption
	versionTag = versionTagLines[0].decode('utf-8')

	with args.outFile.open('w') as outputFile:
		# Find out if there's a current branch to describe what we're being built against
		branch = 'UNKNOWN'
		hash = 'unknown'

		if 'gitPath' in args:
			# Extract the current branch name
			gitResult = run((str(args.gitPath), 'rev-parse', '--abbrev-ref', 'HEAD'), capture_output = True)
			if gitResult.returncode != 0:
				print('WARNING: Could not properly determine branch')
			else:
				branch = gitResult.stdout.decode('utf-8').strip()

			# Extract the current commit hash
			gitResult = run((str(args.gitPath), 'rev-parse', '--short', 'HEAD'), capture_output = True)
			if gitResult.returncode != 0:
				print('WARNING: Could not properly determine commit hash')
			else:
				hash = gitResult.stdout.decode('utf-8').strip()

		# Extract to the first '-' of the version tag to get the actual version number
		versionTagParts = versionTag.split('-')
		version = versionTagParts[0]
		# Split this into its dotted components for the version number value
		versionParts = version.split('.')
		# Now re-combine that for the version number value, and append `,0`
		versionNumber = f'{",".join(versionParts)},0'

		# Having computed everything needed.. go thorugh reading each line of the input file and replacing
		# the necessary expressions with their computed values
		while True:
			line: str = inputFile.readline()
			# Check if this was the end of file
			if line == '':
				break
			# Do the necessary replacements and write the line to the output
			outputFile.write(
				line
					.replace('${LIB_VERSION_NUM}', versionNumber)
					.replace('${LIB_VERSION}', version)
					.replace('${GIT_BRANCH}', branch)
					.replace('${GIT_COMMIT_HASH}', hash)
			)
