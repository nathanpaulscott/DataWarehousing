#Program for CITS5504 project
#Date: 12mar18
#Author: Nathan Scott

import Modules.utility_functions as utils
import Modules.trucks as tk
import Modules.Stockpiles as sp
import Modules.Orders as od
import os

def main():
    # I probably need to iterate through the trucks data a couple of times to make sure I have some statistical data for the uaot drivers, right now I do not see an improvement in the stats
    tk.run_truck_simulation()
    sp.run_stockpile_simulation()
    od.run_orders_simulation()

main()
