# ADSDashboard
UI/Backend Flask Application for FA22-SP23 EGR483/EGR484 Atmospheric Deposition Sampler team  (University of Portland)

## Description
This Flask application is to be compatible with the Atmospheric Deposition Sampler device. It will receive two types of HTTP requests from an ESP32, one to indicate a change in rain events, and another to pass miscellaneous sensor data. In turn, the Flask application will store the data into a local database, and when needed, query the database and populate the ADS Dashboard's interface with the necessary information.

## Setup
Server setup is automated by the two batch files. Note that these only work on Windows operating systems - future development may be done to support Linux or MacOS development as well. These batch files set up a Python virtual environment, verify correct package installation, upgrade necessary packages, and runs the Flask application in their respective modes.

The first batch file, ```run_dev_server.bat```, will set up the Flask application in development mode. This is primarily used for bug fixes, testing, feature development, and more. A development server should not be used for the final product.

The second batch file, ```run_waitress_server.bat```, uses waitress, which is a pure Python WGSI server for running a Flask application in production mode. This is a mode where multithreading is enabled (defaulted to 4), and should be used for the final product.

To run the server, either double-click on either of the batch files in your File Explorer, or navigate to the directory of the batch files and run the name of the batch file in the Command Prompt.
