import Modules.utility_functions as utils





# trains from mines to port can carry aroudn 25K tonnes => normally distribute or something but cap it
# trucks, we know, get stats from your truck analysis on ave daily Tput
# deposit size ave and distribution
# stockpile capacities
# ship Tput



#Stockpile_Id,Stockpile_Name,Location_Id,Max Capacity (kt),Type,Tier,Lead Time (mths)
#Location_Id,Location_Name,Location_Code,Poor Road pct,Ave Train Capacity (kt/d),Max Train Capacity (kt/d),Ave Shipping Capacity (kt/d),Max Shipping Capacity (kt/d)

def run_stockpile_simulation():
    e_msg = ''


    def convert_type(type):
        if type == 'IG_0':
            type = 2
        elif type == 'IG_1':
            type = 3
        elif type == 'IG_2':
            type = 4
        elif type == 'IG_3':
            type = 5
        elif type == 'SP_0':
            type = 1
        return type

    def calc_new_level(incoming, outgoing, pile_id):
        current_level = stockpile_DB[pile_id]['Quantity (kt)']
        max_level = float(stockpile_DB[pile_id]['Max Capacity (kt)'])
        new_level_0 = current_level + incoming - outgoing
        new_level = min(max_level,max(0,new_level_0))
        stockpile_DB[pile_id]['Quantity (kt)'] = new_level
        #workout excess and shortfalls
        excess, shortfall = 0,0
        if new_level < new_level_0:
            excess = new_level_0 - new_level
        elif new_level > new_level_0:
            shortfall = new_level - new_level_0
        #calc real ingress and egress
        stockpile_DB[pile_id]['Ingress (kt)'] = incoming - excess
        stockpile_DB[pile_id]['Egress (kt)'] = outgoing - shortfall
        stockpile_DB[pile_id]['Ingress Excess (kt)'] = excess
        stockpile_DB[pile_id]['Egress Shortfall (kt)'] = shortfall
        return excess

    def move_ig_tier(loc_id):
        #this moves one tier 3 to tier 2, one tier 2 to tier 1 and one tier 1 to tier 0
        t1_flag, t2_flag, t3_flag = False, False, False
        for pile_id in [x for x in stockpile_DB if stockpile_DB[x]['Location_Id'] == loc_id and float(stockpile_DB[x]['Tier']) > 0]:
            if t1_flag is False and stockpile_DB[pile_id]['Tier'] == '1':
                stockpile_DB[pile_id]['Tier'] = '0'
                stockpile_DB[pile_id]['Lead Time (mths)'] = '2'
                t1_flag = True
            if t2_flag is False and stockpile_DB[pile_id]['Tier'] == '2':
                stockpile_DB[pile_id]['Tier'] = '1'
                stockpile_DB[pile_id]['Lead Time (mths)'] = '6'
                t2_flag = True
            if t3_flag is False and stockpile_DB[pile_id]['Tier'] == '3':
                stockpile_DB[pile_id]['Tier'] = '2'
                stockpile_DB[pile_id]['Lead Time (mths)'] = '12'
                t3_flag = True

    def calc_new_params(days, demand_debt):
        demand_year_rand = [1,1,1.1,1.2,.7,.8,1,1,1,1]
        train_year_rand = [1,1,1,1,1,1,1,1,1,1]
        truck_year_rand = [1,1,1,1,1,.8,1,1,1,1]
        #calc new demand and max caps
        #do demand first
        demand = demand_year_rand[int(days/365)]*(demand_int + demand_slope*(days**1.2))
        demand += demand_noise_const*utils.math.cos(2*utils.math.pi*(days%365)/365+utils.math.pi)
        demand = max(0,demand - demand_noise_const*abs(utils.np.random.normal(0,0.5,1)[0]))
        demand += demand_debt

        #do ships
        ship_cap = float(location_DB['5']['Orig Shipping Capacity (kt/d)']) + ship_slope*(days)
        ship_cap = max(0,ship_cap - ship_noise_const*abs(utils.np.random.normal(0,0.5,1)[0]))
        location_DB['5']['Cur Shipping Capacity (kt/d)'] = ship_cap

        #do mines trains and trucks
        for item in [x for x in location_DB if x != '5']:
            train_cap = train_year_rand[int(days/365)]*(float(location_DB[item]['Orig Train Capacity (kt/d)']) + train_slope * (days))
            train_cap = max(0,train_cap - train_noise_const * abs(utils.np.random.normal(0, max(0.25,0.5-0.25*days/2300), 1)[0]))
            location_DB[item]['Cur Train Capacity (kt/d)'] = train_cap
            truck_cap = truck_year_rand[int(days/365)]*(float(location_DB[item]['Orig Mine Production Capacity (kt/d)']) + truck_slope * (days))
            truck_cap = max(0,truck_cap - truck_noise_const * abs(utils.np.random.normal(0, max(0.25,0.5-0.25*days/2300), 1)[0]))
            location_DB[item]['Cur Mine Production Capacity (kt/d)'] = truck_cap

        return demand
    #------------------------------------------------------------------------------
    #------------------------------------------------------------------------------



    # load the csvs
    root_dir = 'D:/A.Nathan/1a.UWA 2018/CITS5504 - Data Warehousing/Assignment/Data/'
    stockpile_DB = utils.load_csv_file_to_db(root_dir + 'Stockpile Data/Stockpiles.csv')
    location_DB = utils.load_csv_file_to_db(root_dir + 'Truck Data/Locations.csv')

    output_DB = [[
                'Date',
                'Stockpile_Id',
                'Location_Id',
                'Type_Id',
                'Current Level (kt)',
                'Loading (pct)',
                'Demand (kt)',
                'Demand Debt (kt)',
                'Ingress (kt)',
                'Ingress Excess (kt)',
                'Egress (kt)',
                'Egress Shortfall (kt)'
                ]]

    # write headers to csv
    utils.write_csv(output_DB, root_dir + 'Stockpile Data/Output.csv', False)

    output_DB = []
    start_date = utils.datetime.strptime('01-01-2012', '%d-%m-%Y')
    end_date = utils.datetime.strptime('29-03-2018', '%d-%m-%Y')
    current_date = start_date

    #initialise stockpiles
    #add the current quantity, ingress and egress holders per stockpile Id
    for pile in stockpile_DB:
        stockpile_DB[pile]['Ingress (kt)'] = 0
        stockpile_DB[pile]['Egress (kt)'] = 0
        stockpile_DB[pile]['Ingress Excess (kt)'] = 0
        stockpile_DB[pile]['Egress Shortfall (kt)'] = 0
        if stockpile_DB[pile]['Type'] == 'IG':
            stockpile_DB[pile]['Quantity (kt)'] = float(stockpile_DB[pile]['Max Capacity (kt)'])
        else:
            stockpile_DB[pile]['Quantity (kt)'] = float(stockpile_DB[pile]['Max Capacity (kt)'])/2

    #start time
    cap_low_limit_port = 30
    cap_limit_port = 80
    cap_limit_mine = 80
    #low limit, we schedule tier move at this level of tier 0
    cap_limit_low_ig0 = 20

    demand = 50     #original demand kt/d
    demand_debt = 0
    ship_reduction = 0
    ship_reduction_step = 2
    train_reduction = 0
    train_reduction_next = 0
    train_reduction_step = 2
    truck_reduction = {'1':0,'2':0,'3':0,'4':0}
    truck_reduction_next = {'1':0,'2':0,'3':0,'4':0}
    truck_reduction_step = 2
    extraction_project = []
    extraction_project_lead_time = 60

    #parameter models
    demand_int = demand
    demand_slope = 0.016
    demand_noise_fraction = 0.05
    demand_noise_const = 10
    ship_slope = 0.095
    ship_noise_const = 10
    train_slope = 0.05
    train_noise_const = 5
    truck_slope = 0.02
    truck_noise_const = 15

    break_flag = False
    while break_flag is False:
        #this calcs new values daily for demand and max capacities of all nodes => basically from different growth curves + noise
        demand = calc_new_params((current_date - start_date).days, demand_debt)
        print(str(demand_debt))

        #check for expiring extraction projects
        #it will move one tier 1 to 0, 1 tier 2 to 1 and one tier 3 to 2
        for project in extraction_project:
            project[1] += -1
            if project[1] == 0:
                move_ig_tier(project[0])

        #get rid of processed extraction projects
        extraction_project = [x for x in extraction_project if x[1] > 0]

        #do the processing
        # port first
        pile_id = [x for x in stockpile_DB if stockpile_DB[x]['Location_Id'] == '5'][0]
        egress=0
        egress = min(demand,min((1-ship_reduction/100)*float(location_DB['5']['Cur Shipping Capacity (kt/d)']),float(stockpile_DB[pile_id]['Quantity (kt)'])))
        demand_debt = demand - egress
        ingress = (1-train_reduction/100)*sum([min(stockpile_DB[x]['Quantity (kt)'],float(location_DB[stockpile_DB[x]['Location_Id']]['Cur Train Capacity (kt/d)'])) for x in stockpile_DB if stockpile_DB[x]['Location_Id'] != '5' and stockpile_DB[x]['Type'] == 'SP'])
        excess = calc_new_level(ingress, egress, pile_id)
        #if excess > 0:
        #    train_reduction = 100*(1-(ingress-excess)*(1-train_reduction/100)/ingress)
        # check port overload levels
        pct_load = 100*stockpile_DB[pile_id]['Quantity (kt)']/float(stockpile_DB[pile_id]['Max Capacity (kt)'])
        if pct_load > cap_limit_port:
            train_reduction_next = min(100, train_reduction + train_reduction_step)
        elif pct_load < cap_limit_port - 20:
            train_reduction_next = max(0, train_reduction - train_reduction_step)
        #control shipping capcity to meet demand
        if demand_debt > 0:
            ship_reduction = max(0, ship_reduction - ship_reduction_step)
        else:
            ship_reduction = min(100, ship_reduction + ship_reduction_step)

        #now work through each mine
        for mine in [x for x in location_DB if x != '5']:
            # main mine stockpile next
            ig0piles2process = [x for x in stockpile_DB if stockpile_DB[x]['Location_Id'] == mine and stockpile_DB[x]['Type'] == 'IG' and stockpile_DB[x]['Tier'] == '0' and stockpile_DB[x]['Quantity (kt)'] > 0 and mine != '5']
            total_ig0_quantity = sum([stockpile_DB[x]['Quantity (kt)'] for x in ig0piles2process])
            pile_id = [x for x in stockpile_DB if stockpile_DB[x]['Location_Id'] == mine and stockpile_DB[x]['Type'] == 'SP' and mine != '5'][0]
            egress = (1-train_reduction/100)*min(stockpile_DB[pile_id]['Quantity (kt)'], float(location_DB[mine]['Cur Train Capacity (kt/d)']))
            ingress = (1-truck_reduction[mine]/100)*min(total_ig0_quantity, float(location_DB[mine]['Cur Mine Production Capacity (kt/d)']))
            excess = calc_new_level(ingress, egress, pile_id)
        #    if excess > 0:
        #        truck_reduction[mine] = 100 * (1 - (ingress - excess) * (1 - truck_reduction[mine] / 100) / ingress)
            #check mine overload levels
            pct_load = 100 * stockpile_DB[pile_id]['Quantity (kt)'] / float(stockpile_DB[pile_id]['Max Capacity (kt)'])

            #if mine == '1': print(pct_load)

            if pct_load > cap_limit_mine:
                truck_reduction_next[mine] = min(100, truck_reduction[mine] + truck_reduction_step)
            elif pct_load < cap_limit_mine - 20:
                truck_reduction_next[mine] = max(0, truck_reduction[mine] - truck_reduction_step)

            # ig0 - under extraction ore next
            for pile_id in ig0piles2process:
                if total_ig0_quantity == 0:
                    egress = 0
                elif len(ig0piles2process) == 1:
                    egress = (1 - truck_reduction[mine] / 100) * float(location_DB[mine]['Cur Mine Production Capacity (kt/d)'])
                else:    # len(ig0piles2process) > 1:
                    #give more capacity to the emptier piles to finish them sooner
                    egress = (1-truck_reduction[mine]/100)*float(location_DB[mine]['Cur Mine Production Capacity (kt/d)'])*(1-stockpile_DB[pile_id]['Quantity (kt)']/total_ig0_quantity)/(len(ig0piles2process)-1)
                ingress = 0     #we just use it up till it's gone
                excess = calc_new_level(ingress, egress, pile_id)
            #check for low ig0 levels
            if len(ig0piles2process) == 0:
                # trigger new extraction project at this mine
                extraction_project.append([mine, extraction_project_lead_time])
            elif 100*sum([stockpile_DB[x]['Quantity (kt)'] for x in ig0piles2process])/sum([float(stockpile_DB[x]['Max Capacity (kt)']) for x in ig0piles2process]) < cap_limit_low_ig0 and len([x for x in extraction_project if x[0] == mine]) == 0:
                #trigger new extraction project at this mine
                extraction_project.append([mine,extraction_project_lead_time])

        #now output the data
        for pile_id in stockpile_DB:
            output_DB.append([
                current_date,
                pile_id,
                stockpile_DB[pile_id]['Location_Id'],
                convert_type(stockpile_DB[pile_id]['Type'] + '_' + stockpile_DB[pile_id]['Tier']),
                round(stockpile_DB[pile_id]['Quantity (kt)'],2),
                round(100*float(stockpile_DB[pile_id]['Quantity (kt)'])/float(stockpile_DB[pile_id]['Max Capacity (kt)']),1),
                round(demand,2),
                round(demand_debt,2),
                round(stockpile_DB[pile_id]['Ingress (kt)'],2),
                round(stockpile_DB[pile_id]['Ingress Excess (kt)'],2),
                round(stockpile_DB[pile_id]['Egress (kt)'],2),
                round(stockpile_DB[pile_id]['Egress Shortfall (kt)'],2)])

        #increment date and test for exit
        current_date += utils.timedelta(days=1)
        if current_date > end_date:
            break_flag = True

        train_reduction = train_reduction_next
        truck_reduction = truck_reduction_next

    # append data to csv
    utils.write_csv(output_DB, root_dir + 'Stockpile Data/Output.csv', True)

    return e_msg