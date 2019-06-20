import Modules.utility_functions as utils





# trains from mines to port can carry aroudn 25K tonnes => normally distribute or something but cap it
# trucks, we know, get stats from your truck analysis on ave daily Tput
# deposit size ave and distribution
# stockpile capacities
# ship Tput



#Stockpile_Id,Stockpile_Name,Location_Id,Max Capacity (kt),Type,Tier,Lead Time (mths)
#Location_Id,Location_Name,Location_Code,Poor Road pct,Ave Train Capacity (kt/d),Max Train Capacity (kt/d),Ave Shipping Capacity (kt/d),Max Shipping Capacity (kt/d)

def run_orders_simulation():
    def d2s(date):
        return utils.datetime.strftime(date, '%Y-%m-%d')

    def s2d(date_s):
        return utils.datetime.strptime(date_s, '%Y-%m-%d')

    def get_nearest_date(dates, target):
        #dates = [s2d(x) for x in dates]
        return min(dates, key=lambda x: abs(s2d(x) - target))

    #------------------------------------------------------------------------------
    #------------------------------------------------------------------------------



    # load the csvs
    root_dir = 'D:/A.Nathan/1a.UWA 2018/CITS5504 - Data Warehousing/Assignment/Data/'
    order_seed = utils.load_csv_file_to_db(root_dir + 'Order Data/Order Start.csv')
    customers_db = utils.load_csv_file_to_db(root_dir + 'Order Data/DimCustomer.csv')
    countries_db = utils.load_csv_file_to_db(root_dir + 'Order Data/DimCountry.csv')
    port_db = utils.load_csv_file_to_db(root_dir + 'Order Data/DimPort.csv')
    transporter_db = utils.load_csv_file_to_db(root_dir + 'Order Data/DimTransporter.csv')
    deal_db = utils.load_csv_file_to_db(root_dir + 'Order Data/DimDeal.csv')
    ore_price_db = utils.load_csv_file_to_db(root_dir + 'Order Data/IronOre Price.csv')
    audusd_db = utils.load_csv_file_to_db(root_dir + 'Order Data/AUDUSD.csv')
    bridge_db = utils.load_csv_file_to_bridge_db(root_dir + 'Order Data/Bridge-Customer-Port.csv')

    # write headers to csv
    output_db = [[
                'OrderDate_Id',
                'Target_ShipmentDate_Id',
                'Actual_ShipmentDate_Id',
                'Target_PaymentDate_Id',
                'Actual_PaymentDate_Id',
                'Order_Id',
                'Shipment_Id',
                'Customer_Id',
                'Deal_Id',
                'Transporter_Id',
                'Destination_Port_Id',
                'Currency_Id',
                'Late Shipment Penalty (pct)',
                'Late Payment Penalty (pct)',
                'Price(mill AUD)',
                'Price(mill USD)',
                'Actual Payement (mill AUD)',
                'Actual Payement (mill USD)',
                'Balance (mill AUD)',
                'Balance (mill USD)',
                'Quantity(kt)'
                ]]
    utils.write_csv(output_db, root_dir + 'Order Data/Output.csv', False)



    output_db = []
    #start_date = utils.datetime.strptime('01-01-2012', '%d-%m-%Y')
    #end_date = utils.datetime.strptime('6-04-2018', '%d-%m-%Y')
    current_date = utils.datetime.now()

    #go through each order
    temp=1
    for k, v in order_seed.items():
        #if temp > 10:
        #    break
        #print('{0}: {1}'.format(k,v))
        #go through each shipment - the FT grain
        num_shipments = int(v['shipment number'])
        shipment_size = float(v['shipment quantity (kt)'])
        shipment_freq = 30 if v['shipment freq'] == 'M' else 90
        order_date_d = s2d(v['OrderDate_Id'])
        customer_id = v['Customer_Id']
        deal_id = v['Deal_Id']
        transporter_id = v['Transporter_Id']
        order_id = k
        leadtime_order_days = round(utils.np.random.uniform(90,365),0)
        for shipment_id in range(0,num_shipments-1):
            #shipping
            target_ship_date_d = order_date_d + utils.timedelta(days=leadtime_order_days) + utils.timedelta(days=shipment_freq*shipment_id)
            actual_ship_date_lag_mean = 9 - utils.math.log(float(utils.datetime.strftime(target_ship_date_d,'%Y'))-1999,1.5)
            actual_ship_date_d = target_ship_date_d + utils.timedelta(days=round(utils.np.random.normal(actual_ship_date_lag_mean,actual_ship_date_lag_mean/2),0))
            late_ship_penalty = actual_ship_date_d-target_ship_date_d
            late_ship_penalty = min(100,max(0,int(late_ship_penalty.days)/7)*int(deal_db[deal_id]['Late Shipment Penalty']))
            if current_date < actual_ship_date_d:
                actual_ship_date_d = None
                late_ship_penalty = 0

            #get the port
            port_id = utils.np.random.choice([x[1] for x in bridge_db if x[0] == customer_id],size=None,replace=False)

            #payment
            target_pay_date_d = target_ship_date_d + utils.timedelta(days=14)
            actual_pay_date_lag_mean = 11 - utils.math.log(float(utils.datetime.strftime(target_pay_date_d,'%Y'))-1999,2)
            actual_pay_date_d = target_pay_date_d + utils.timedelta(days=round(utils.np.random.normal(actual_pay_date_lag_mean,actual_pay_date_lag_mean/2),0))
            late_pay_penalty = actual_pay_date_d-target_pay_date_d
            late_pay_penalty = min(100,max(0,int(late_pay_penalty.days)/7)*int(deal_db[deal_id]['Late Payment Penalty']))
            if current_date < actual_pay_date_d:
                actual_pay_date_d = None
                late_pay_penalty = 0

            #determine pricing
            if actual_ship_date_d is not None:
                exch_rate = float(audusd_db[get_nearest_date(audusd_db.keys(), actual_ship_date_d)]['AUDUSD'])
                price_usd = float(ore_price_db[get_nearest_date(ore_price_db.keys(),actual_ship_date_d)]['Value'])*shipment_size*1000/1e6*(1-float(deal_db[deal_id]['Discount'])/100-late_ship_penalty/100+(late_pay_penalty if late_pay_penalty is not None else 0)/100)
                price_aud = price_usd/exch_rate
            else:
                price_usd = 'TBD'
                price_aud = 'TBD'

            actual_payment_usd = 'TBD'
            actual_payment_aud = 'TBD'
            balance_usd = 'TBD'
            balance_aud = 'TBD'
            if actual_pay_date_d is not None:
                actual_payment_usd = price_usd - round(abs(utils.np.random.normal(0,float(countries_db[customers_db[customer_id]['Country_Id']]['Dodgyness'])**2*price_usd/100)),2)
                actual_payment_aud = actual_payment_usd/exch_rate
                balance_usd = actual_payment_usd - price_usd
                balance_aud = balance_usd/exch_rate

            output_db = [[
                d2s(order_date_d),
                d2s(target_ship_date_d),
                'NULL' if actual_ship_date_d is None else d2s(actual_ship_date_d),
                d2s(target_pay_date_d),
                'NULL' if actual_pay_date_d is None else d2s(actual_pay_date_d),
                order_id,
                shipment_id+1,
                customer_id,
                deal_id,
                transporter_id,
                port_id,
                1,
                late_ship_penalty,
                late_pay_penalty,
                price_aud,
                price_usd,
                actual_payment_aud,
                actual_payment_usd,
                balance_aud,
                balance_usd,
                shipment_size
                ]]
            utils.write_csv(output_db, root_dir + 'Order Data/Output.csv', True)
        temp += 1
    #--------------------------------------------------------------------

