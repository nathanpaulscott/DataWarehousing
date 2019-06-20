import sys
import time
import math
import re
import os
import tkinter as tk
from tkinter import filedialog
import csv
import json
from datetime import datetime, timedelta
from random import randint
import pandas as pd
import numpy as np
import requests as rq
from bs4 import BeautifulSoup as bsup
import lxml   #even though not used, it is used in the reading of beautiful soup content, so you need to pip install it and import it



#UTILITY FUNCTIONS
###############################################################
def error_exit_procedure(e_msg):
    #prints any runtime errors to the console, gives the user time to read and then quits
    print(e_msg)
    sys.exit()




def load_csv_file_to_db(file_path):
    #function to load in the given file to a dict data structure
    output_data = {}
    import_data, e_msg = read_csv(file_path)
    if e_msg != '':
        error_exit_procedure(e_msg)
    attr_keys = [x for x in import_data[0][1:]]
    for row in import_data[1:]:
        mainkey = row[0]
        attr_vals = row[1:]
        output_data[mainkey] = dict(zip(attr_keys, attr_vals))
    return output_data



def load_csv_file_to_bridge_db(file_path):
    #function to load in the given file to a list of lists
    output_data = []
    import_data, e_msg = read_csv(file_path)
    if e_msg != '':
        error_exit_procedure(e_msg)
    for row in import_data:
        output_data.append((row[0],row[1]))
    return output_data



def get_file_dialog():
    #prompts the user to select a .txt file containing the text to be analysed
    #and returns the chosen complete file path
    error = ''
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(title='Please select a single file with your given text to analyse.', filetypes = (('text', '*.txt'),('All files','*.*')))

    #check the file exists, if not spit back to user
    if not os.path.exists(file_path):
        error = "file or directory doesn't exist"

    return file_path, error



def load_file(file_path):
    #this loads the file into a string
    #the error string is filled if there are any problems
    #like: file already open error, or file doesn't exist error
    error = ''
    data = ''

    #try to read the file, catch various errors and spit back to user
    try:
        file = open(file_path, 'r')
        data = file.read()
        file.close()
    except Exception as e:
        error = str(e)

    return data, error




def read_csv(file_path):
    #loads a csv into a list of lists
    error = ''
    data = []

    #try to read the file, catch various errors and spit back to user
    try:
        csv_reader = csv.reader(open(file_path, newline=''), dialect='excel', delimiter=',', quotechar='"')
        for r in csv_reader:
            data.append(tuple(r))
    except Exception as e:
        error = str(e)

    return data, error


def write_csv(data, file_path, append_flag):
    # writes the list of lists to a csv file
    error = ''

    #try to read the file, catch various errors and spit back to user
    try:
        csv_writer = csv.writer(open(file_path, 'a' if append_flag else 'w', newline=''), delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for r in data:
            csv_writer.writerow(r)
    except Exception as e:
        error = str(e)

    return error


###############################################################
