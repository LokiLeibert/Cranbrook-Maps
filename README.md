# Route Finder Mobile

## Description

Route Finder Mobile is a navigation application for use in schools. Students can find the best path between locations in their school using an intuitive interface similar to Google Maps.

## Installation

The following Python version and libraries are required:
- Python 3.12 including built-in libraries: 
  - tkinter
  - sqlite 
  - typing 
  - json
  - os
- pysqlciper3
- bcrypt 4.3.0
- numpy 2.3.1
- pillow 11.3.0

`SQLCipher` must be installed on your system.

Install all components into a directory following the same structure as in the repository.

Run by navigating to the install directory and typing `python Login.py`.

## Usage

Login using the username and password that have been provided to you.
Maps can be dragged around, and zoomed in/out using the `+` and `-` keys.
Click anywhere on the seach bar to enter an initial location.
When entering a location, start typing in the search box and select from the drop-down list when the desired location appears.
When navigating, use the left and right arrow buttons to navigate the route, or use the `,` and `.` keys.
To return to the start click the `X` circle button whenever it appears.
To logout, click the blue button with the first letter of your username any time it appears.

## Key Technologies

The most significant features are:
- written in Python 3.12 with interface written with tkinter UI library
- user database is encrypted with AES-256 using the sqlcipher library
- bcrypt password protection for salting and hashing passwords
- Innovative UI code using a component lifetime manager
- A-star route finding algorithm using a distance heuristic based on applying spring physics to the node network
- human-readable navigation file format
- typo-tolerant fuzzy-finder for locations

## Customization and Contribution

Tools are available for creating new maps and administering the user database. Please contact the maintainer of this project if you wish to create your own version for your school.

If you wish to contribute to improving this project, please create a new branch and send the maintainer a link to the new branch.

If you have bug reports or feature suggestions, please submit them via this GitHub repository.

## Licence

If you would like to use code from this project in a way compatible with the GPL3 Licence, please let me know and I will add appropriate Licenced versions to this repository for your use.
