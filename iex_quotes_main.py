"""
This application gets stock prices from IEX and formats them for input 
into Quicken. It uses IEX's REST API. If accurate data is desired, an 
account at IEX will be required for prod mode. If inaccurate test data
is sufficient, no account is required and can be executed in dev mode.
The program assumes there is a CSV called env_file.csv in the same
directory as itself. It contains the environment name, IEX API token and 
IEX API URL. For example, one possible csv record would be:
    dev,123token,www.apiurl.com
"""

from datetime import datetime, timedelta
import re
import requests
import requests.auth
import urllib
import json
import csv
import os
import sys
import glob
import traceback

hist_prices = {}

def is_pos_digit(digit):
    """
    Determines if input is a positive digit (includes zero).

    Parameters
    ----------
    digit : str
        The digit to be evaluated

    Returns
    -------
    boolean
        True is returned if the digit is >= 0, False otherwise
    """
    flag = False
    if digit.isdigit():
        flag = True
    return flag

def exception_exit(error_message):
    """
    Print error message and exit to command prompt

    Parameters
    ----------
    error_message : str
        The error message to be printed to the console
    """
    print(error_message)
    print('Program is exiting.')  
    sys.exit(1)

def confirm_selection(selection):
    """
    Confirm input Y/N selection

    Parameters
    ----------
    selection : str
        The inputted value to be evaluated as either 'Y' or not 'Y'

    Returns
    -------
    boolean
        True is returned if the selection is 'y' or 'Y'. False is
        returned otherwise
    """
    confirm_flag = False
    if selection.upper() == 'Y':
        confirm_flag = True
    return confirm_flag

def read_env_file(env_file):
    """
    Read the IEX API token and url from a csv file

    Parameters
    ----------
    env_file : str
        The environment csv filename

    Returns
    -------
    dict
        Key is env name (dev, prod) and value is a list consisting of
        the api token and api url
    """
    items = {}
    with open (env_file, 'r') as file:
        reader = csv.reader(file, delimiter = ',')
        for row in reader:
            items[row[0]] = [row[1], row[2]]
    return items

def set_env(envs):
    """
    Convert dictionary to list to dictionary to support env selection 
    via user inputted number

    Parameters
    ----------
    envs : dict
        The environment consisting of env name (dev, prod) as the key 
        and a list consisting of the api token and url

    Returns
    -------
    list
        Consisting of the api token and url
    """
    env_options = []
    for key, value in envs.items():
            temp = [key,value]
            env_options.append(temp)
    env = { i : env_options[i] for i in range(0, len(env_options) ) }        
    for i in env:
        print(str(i) + ': ' + str(env[i]))    
    
    selection_num = (input('Choose the environment to set (by number):'))
    if not is_pos_digit(selection_num):
        #exception_exit(selection_num + ' is not a valid number in this context')
        raise TypeError(selection_num + ' is not a valid number in this context')
    else:
        input_env = int(selection_num)
        if input_env not in range(0, len(env_options)):
            raise ValueError(selection_num + ' is out of range')

    print('Environment selected: ' + str(env[input_env]))    
    
    selection_str = input('Confirm your environment selection (y/n):')
    
    if not confirm_selection(selection_str):
        raise ValueError('Selection was not confirmed.')

    #env is of the form: [<env_name>, [<token>, <url>]]
    iex_token = env[input_env][1][0]        
    base_url = env[input_env][1][1]

    return [iex_token, base_url]
        
def create_symbols(input_csv):
    """
    Creates the symbols list from the input CSV file containing ticker 
    symbols

    Parameters
    ----------
    input_csv : str
        The filename for the csv with the ticker symbols

    Returns
    -------
    list
        Ticker symbols to process downstream
    """
    symbols = []
    try:
        with open(input_csv,'rt') as csv_file: 
            reader = csv.reader(csv_file, delimiter=',', quotechar='|')    
            for row in reader:
                stock_count = len(row) + 1
                print('There are ' + str(stock_count) + ' stocks to process in the input file') 
                for column in row:
                    symbols.append(column)
    except FileNotFoundError as e:
        print(type(e))
        exception_exit('Error: Could not open the ticker symbol input file, ' + input_csv 
            + '. Make sure the file is located in the root directory (where this program is '
            'running from)')
    except:        
        exception_exit('Error: Someting went wrong reading the ticker symbol input file')
                
    return symbols

def get_hist_prices_payload(range, ticker_symbol, token, base_url):
    """
    Gets historical closing prices from IEX 

    Parameters
    ----------
    range : str
        The date range for the historical prices (5 days or 1 month)
    ticker_symbol : str
        The ticker symbol of the stock that will be queried
    token : str
        The IEX API token
    base_url : str
        The root url that refers to either the dev or prod IEX endpoint

    Returns
    -------
    str
        REST API response payload containing pricing data
    """
    symbol_url = ticker_symbol.lower()
    base_url2 = '/chart/'
    range_url = range.lower()
    token_url = '?token=' + token
    close_price_opt_url = '&chartCloseOnly=TRUE'
    url = base_url + symbol_url + base_url2 + range_url + token_url + close_price_opt_url
    print("Historical closing price URL to be submitted: " + url)
    response = requests.get(url)
    if response.status_code == 200:
        return response.text

def parse_hist_prices_payload(payload):
    """
    Parse JSON payload returned by get_hist_prices_payload into a 
    dictionary of dictionaries

    Parameters
    ----------
    payload : str
        The JSON payload returned by IEX to be parsed

    Returns
    -------
    dict
        Key is date and value is closing price for that date
    """
    date_prices = {}
    parsed_payload = json.loads(payload)
    for dp in parsed_payload:        
        date_prices[dp['date']] = dp['close']
    return date_prices

def format_date(date):
    """
    Format an IEX date to be Quicken input compliant

    Parameters
    ----------
    date : str
        The IEX formatted date (YYYY-MM-DD) to be Quicken formatted

    Returns
    -------
    str
        Quicken formatted date (MM/DD/YYYY)
    """
    formatted_date = datetime.strptime(date, '%Y-%m-%d').strftime('%m/%d/%y')
    return formatted_date

def format_ticker(ticker):
    """
    Format an IEX ticker to be Quicken input compliant. TSX tickers have
    a '-ct' that needs to be removed. All tickers are uppercased.

    Parameters
    ----------
    ticker : str
        The IEX formatted ticker to be Quicken formatted

    Returns
    -------
    str
        Quicken formatted ticker
    """
    if re.match('.+-ct$',ticker, re.IGNORECASE) is not None:        
        formatted_ticker = ticker[:-3].upper()
    else:
        formatted_ticker = ticker.upper()
    return formatted_ticker

if __name__ == "__main__":
    env_file = 'env_file.csv'
    envs = {}
    # Open and read the environment file
    print("Loading environment file...")
    try:
        envs = read_env_file(env_file)        
    except FileNotFoundError as e:
        print(type(e))
        exception_exit('Error: Could not find environment file, ' + env_file 
            + '. Make sure the file is located in the root directory (where this program is '
            'running from)')
    except:        
        exception_exit('Error: Someting went wrong reading the environment file')                                

    # Set the environment based on user input
    print("Listing available environments...")
    try:
        env = set_env(envs)
    except (ValueError, TypeError) as e:
        print(type(e))
        exception_exit(e)                  
    except:
        traceback.print_exc()        
        exception_exit('Error: Someting went wrong setting the environment')
        
    # List the input CSV files options
    print("Listing CSV files...")
    extension = 'csv'
    csv_files = glob.glob('*.{}'.format(extension))
    print(csv_files)
    csv_file_options = { i : csv_files[i] for i in range(0, len(csv_files) ) }
    print(csv_file_options)

    # Set input symbol csv filename
    input_csv_filename_number = (
        int(input("Choose input CSV file number (just the number, nothing else): ")))
    if input_csv_filename_number >= 0 and input_csv_filename_number < len(csv_file_options): 
        input_csv_filename = csv_file_options[input_csv_filename_number]   
        print("Input CSV file is set to: " + input_csv_filename)    
    else:
        exception_exit('Error: ' + str(input_csv_filename_number) 
            + ' is not a valid file number. Exiting program.')        
    # Create array that holds symbols in the ticker list CSV
    tickers = []
    tickers = create_symbols(input_csv_filename)

    # Loop through ticker array and get historical prices via REST 
    # call to IEX
    print("Choose the date range of the historical prices to retrieve")
    iex_hist_price_call_range_number = int(input("1. Five days | 2. One month:"))

    if iex_hist_price_call_range_number == 1:
        iex_hist_price_range_string = '5d'
    elif iex_hist_price_call_range_number == 2:
        iex_hist_price_range_string = '1m'    
    else:
        exception_exit('Error: ' + str(iex_hist_price_call_range_number) 
            + ' is not a valid date range selection')
        sys.exit()
    print("Date range selection is: " + iex_hist_price_range_string)

    quicken_values = {}    
    for i in tickers:
        payload = get_hist_prices_payload(
            range=iex_hist_price_range_string, 
            ticker_symbol=i, 
            token=env[0],
            base_url=env[1]
            )
        hist_prices[i] = parse_hist_prices_payload(payload)    
        quicken_values[i] = (hist_prices[i])

    # Create unique output csv filename
    now = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_csv_filename = './output/iex_quotes_' + now + '.csv'
    
    # Format data returned from IEX for input into Quicken
    for ticker in quicken_values:        
        for (date,price) in quicken_values[ticker].items():
            output_line = (format_ticker(ticker) + ',' + str(price) + ',' + format_date(date))
            with open(output_csv_filename, 'a') as csv_out_file:
                csv_out_file.write(output_line + '\n')    
    os.system("pause")

