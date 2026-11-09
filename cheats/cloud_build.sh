#!/usr/bin/env bash
# cheats/cloud_build.sh: build a placeholder ROM in a cloud session.
#
# The real ROM (ext/Original.nes) is not in git. build.sh takes 48 data
# files (graphics, music and so on, 44420 bytes) out of it. This script
# writes those files as zero bytes instead, so every code byte of
# bin/Z.nes is right but those data bytes are 0. The data ranges (file
# offsets, with the 16-byte header) go to bin/placeholder_ranges.txt;
# cheats/tools/zgg.py reads it and warns about codes that touch them.
#
# It installs cc65 if ca65 is missing. It refuses to run where the real
# ROM is present, so it never replaces real data files.

set -eu -o pipefail
cd "$(dirname "$0")/.."

if [ -f ext/Original.nes ] || [ -f ext/original.nes ]
then
	echo "ext/Original.nes is here; use ./build.sh for a real build." >&2
	exit 1
fi

if ! command -v ca65 > /dev/null || ! command -v ld65 > /dev/null
then
	echo "Installing cc65"
	SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"
	if ! { $SUDO apt-get update -qq && $SUDO apt-get install -y -qq cc65; } > /dev/null 2>&1
	then
		rm -rf /tmp/cc65
		git clone -q --depth 1 https://github.com/cc65/cc65 /tmp/cc65
		make -s -C /tmp/cc65 bin > /dev/null
		export PATH="/tmp/cc65/bin:$PATH"
	fi
fi

mkdir -p ext obj bin
ln -sf "$(command -v ca65)" ext/ca65
ln -sf "$(command -v ld65)" ext/ld65

: > bin/placeholder_ranges.txt
grep -E "<Binary " src/bins.xml | tr -d '\r' | while IFS= read -r line
do
	offset=$(sed -E "s/.*Offset='([0-9]+)'.*/\1/" <<< "$line")
	length=$(sed -E "s/.*Length='([0-9]+)'.*/\1/" <<< "$line")
	file_name=$(sed -E "s/.*FileName='([^']+)'.*/\1/" <<< "$line")
	mkdir -p "bin/$(dirname "$file_name")"
	head -c "$length" /dev/zero > "bin/$file_name"
	echo "$((offset + 16)) $length $file_name" >> bin/placeholder_ranges.txt
done

./build.sh --no-verify --no-extract > /dev/null
echo "Built bin/Z.nes with placeholder data ($(wc -l < bin/placeholder_ranges.txt | tr -d ' ') ranges in bin/placeholder_ranges.txt)."
