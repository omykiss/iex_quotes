# iex_quotes
Python application that gets historical stock price data from IEX and transforms it for ingestion into Quicken

To run the program execute iex_quotes_main.py. Output will be written to ./output.

It uses IEX's REST API. If accurate data is desired, an 
account at IEX will be required for prod mode. If inaccurate test data
is sufficient, no account is required and can be executed in dev mode.
The program assumes there is a environment configuration CSV file called 
env_file.csv in the same directory as the program. It contains the environment 
name, IEX API token and IEX API URL. For example, one possible environment 
configuration csv record would be:
    prod,123token,www.apiurl.com
The environment configuration CSV file included in the repo has a dev envrionment
configured and ready to do

