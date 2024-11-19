# ta-tools
A script for managing gradescope extensions

# Getting started

## Prerequisites
Python version 3.11 or higher with the following python libraries:
- piazza-api
- python-dotenv
- python-dateutil
- pytz
- requests
- tomli_w

## Setup
1. After installing the required python packages, clone this repo and install the fork of gradescope-api
```sh
git clone https://github.com/reidoko/ta-tools.git
cd ta-tools
# install gradescope-api
git clone https://github.com/reidoko/gradescope-api.git
cd gradescope-api
pip install .
cd ..
```

2. Create a .env file with the corresponding login information for gradescope/piazza. Piazza is only used for pulling the class list during configuration. If you download the roster csv from Piazza you don't need to bother with it.
```
GS_EMAIL=...
GS_PASSWORD=...
PZ_EMAIL=...
PZ_PASSWORD=...
```

3. Run ./gs-config.py with no arguments for the interactive setup process.

Alternatively, supply the course id (gradescope.com/courses/__XXXXXX__), 
roster file from piazza (from manga class -> download roster as csv), and an identifier to
use for that class (e.g. fs24) as follows:
```
./gs-config.py -g XXXXXX -r /path/to/roster.csv -id fs24
```

Now, you should be able to process extensions with ./gs-extend.py. 
The most recent course that you add is used as the default for trying to apply extensions. 
If you want to change the default class, edit the value of `default-course` in `settings.toml`.

## Usage
Example 1: 2-day extension for a student on all assignments containing the string "hw1"
```sh
./gs-extend.py "student name" -s hw1 -d 2
```

Example 2: Grant an extension of default length (set in settings.toml) for all of 
the names in a file `students.txt` for homework with the title "hw1"
```sh
./gs-extend.py $(cat students.txt) -s hw1
```
