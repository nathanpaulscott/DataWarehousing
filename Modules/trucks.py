import Modules.utility_functions as utils


def run_truck_simulation():
    e_msg=''

    # local functions
    # -------------------------------------------------------
    def get_driver_id(p_date, truck):
        d_id = ''
        if truck_DB[truck]['Auto_Since'] == 'Not Yet':
            d_id = truck_DB[truck]['Driver_ID_Human']
        else:
            auto_date = utils.datetime.strptime(truck_DB[truck]['Auto_Since'], '%d-%b-%y')
            if auto_date < p_date:
                d_id = truck_DB[truck]['Driver_ID_Auto']
            else:
                d_id = truck_DB[truck]['Driver_ID_Human']
        return d_id

    def get_tire_limit(truck, poor_road_pct):
        tire_limit = float(truck_DB[truck]['Tire_Life_Poor_Surface (1000kms)']) *1000 * poor_road_pct/100\
                     + float(truck_DB[truck]['Tire_Life_Standard_Surface (1000kms)']) * 1000 * (1 - poor_road_pct / 100)
        return round(utils.np.random.normal(tire_limit, tire_limit * 0.15, 1)[0], 0)

    def get_service_limit(service_code):
        return round(utils.np.random.normal(float(mission_DB[str(service_code)]['Service period mean (km)']),float(mission_DB[str(service_code)]['Service period SD (km)']), 1)[0], 0)

    def get_trip_time(mission_id):
        #i am doing some weird rayleigh conversion to get trip duration here, I like the distribution
        mean = float(mission_DB[str(mission_id)]['Duration Mean (hrs)'])
        sd = 0.65*float(mission_DB[str(mission_id)]['Duration SD (hrs)'])
        duration = mean * (1 -  sd / mean) + utils.np.random.rayleigh(sd)
        return duration

    def get_trip_dist(mission_id):
        mean = float(mission_DB[str(mission_id)]['Distance Mean (km)'])
        sd = 0.8*float(mission_DB[str(mission_id)]['Distance SD (km)'])
        if mean == 0:
            return 0
        distance = mean*(1-sd/mean) + utils.np.random.rayleigh(sd)
        return distance

    def get_rest_time(mean, sd):
        rest_time = mean + utils.np.random.rayleigh(sd)
        return rest_time

    def get_trip_production(mission_id, truck, trip_duration):
        production = 0
        if mission_id == 6:
            # assume the truck max payload can be carried on a mission type 6 job 1x/hr
            production = float(truck_DB[truck]['Max payload (tonnes)']) * trip_duration
        return production

    def get_fuel_burn(truck, trip_time, d_id, poor_road_pct, mission_id):
        if float(mission_DB[str(mission_id)]['Use Fuel']) == 0:
            return 0
        idle_time = float(driver_DB[driver_id]['Time Waste Hrs'])
        fuel_burn_idle = float(truck_DB[truck]['Fuel_Burn_Idle (l/hr)']) * idle_time
        non_idle_loaded_time = (trip_time - idle_time) * 0.6
        non_idle_unloaded_time = (trip_time - idle_time) * 0.4
        fuel_burn_loaded = float(truck_DB[truck]['Fuel_Burn_Loaded_Poor_Surface (l/hr)']) * poor_road_pct / 100 + \
                           float(truck_DB[truck]['Fuel_Burn_Loaded_Standard_Surface (l/hr)']) * (1 - poor_road_pct / 100)
        fuel_burn_loaded *= non_idle_loaded_time * (1 + float(driver_DB[d_id]['Fuel Burn mult']))
        fuel_burn_unloaded = float(truck_DB[truck]['Fuel_Burn_Unloaded_Poor_Surface (l/hr)']) * poor_road_pct / 100 + \
                             float(truck_DB[truck]['Fuel_Burn_Unloaded_Standard_Surface (l/hr)']) * (
                                         1 - poor_road_pct / 100)
        fuel_burn_unloaded *= non_idle_unloaded_time * (1 + float(driver_DB[d_id]['Fuel Burn mult']))
        fuel_burn_total = fuel_burn_loaded + fuel_burn_unloaded + fuel_burn_idle
        return round(utils.np.random.normal(fuel_burn_total, fuel_burn_total * 0.1, 1)[0], 0)

    def get_parts_cost(mission_id, tire_change, accident_cost, truck):
        cost = 0
        if mission_id == 1:
            cost = float(truck_DB[truck]['Service_Type_1_Cost_Parts'])
        elif mission_id == 2:
            cost = float(truck_DB[truck]['Service_Type_2_Cost_Parts'])
        elif mission_id == 3:
            cost = float(truck_DB[truck]['Service_Type_3_Cost_Parts'])
        elif mission_id == 4:
            if tire_change > 0:
                cost = float(truck_DB[truck]['Tire Cost (1000AUD)']) * 1000 * tire_change
            else:
                cost = float(truck_DB[truck]['Service_Type_1_Cost_Parts'])
        elif mission_id == 5:
            if tire_change > 0:
                cost = float(truck_DB[truck]['Tire Cost (1000AUD)']) * 1000 * tire_change
            elif accident_cost > 0:
                cost = accident_cost
            else:
                cost = float(truck_DB[truck]['Service_Type_1_Cost_Parts'])
        return cost

    def get_labour_cost(mission_id, tire_change, accident_cost, truck):
        cost = 0
        if mission_id == 1:
            cost = float(truck_DB[truck]['Service_Type_1_Cost_Labour'])
        elif mission_id == 2:
            cost = float(truck_DB[truck]['Service_Type_2_Cost_Labour'])
        elif mission_id == 3:
            cost = float(truck_DB[truck]['Service_Type_3_Cost_Labour'])
        elif mission_id == 4:
            if tire_change > 0:
                cost = 500 * tire_change
            else:
                cost = float(truck_DB[truck]['Service_Type_1_Cost_Labour'])
        elif mission_id == 5:
            if tire_change > 0:
                cost = 500 * tire_change
            elif accident_cost > 0:
                cost = accident_cost / 7
            else:
                cost = float(truck_DB[truck]['Service_Type_1_Cost_Labour'])
        return cost

    def calc_events(d_id, duration):
        events = {}
        #this will scale the lambda (poisson mean by the duration of the trip, if more, there is more time, so more chance for an event etc...
        time_adjust = duration/4.2
        events['Brake Temperature Events'] = utils.np.random.poisson(time_adjust*float(driver_DB[d_id]['Brake Temperature Events']))
        events['Overspeed Events'] = utils.np.random.poisson(time_adjust*float(driver_DB[d_id]['Overspeed Events']))
        events['Engine Overspeed Events'] = utils.np.random.poisson(time_adjust*float(driver_DB[d_id]['Engine Overspeed Events']))
        events['Overload Events'] = utils.np.random.poisson(time_adjust*float(driver_DB[d_id]['Overload Events']))
        events['Tire Wall Events'] = utils.np.random.poisson(time_adjust*float(driver_DB[d_id]['Tire Wall events']))
        events['Tire Loss Events'] = utils.np.random.poisson(time_adjust*float(driver_DB[d_id]['Tire Loss Events']))
        events['Accidents'] = utils.np.random.poisson(time_adjust*float(driver_DB[d_id]['Accidents']))
        return events

    def update_ufs_uws_tire_limits(events, uws, ufs, tire):
        tot_events = sum(list(events.values())[:5])
        uws += -12*tot_events
        ufs += -16*tot_events
        tire += -19*tot_events
        return uws, ufs, tire


    # ---------------------------------------------------------
    # ---------------------------------------------------------
    # ---------------------------------------------------------
    # ---------------------------------------------------------




    # load the csvs
    root_dir = 'D:/A.Nathan/1a.UWA 2018/CITS5504 - Data Warehousing/Assignment/Data/Truck Data/'
    truck_DB = utils.load_csv_file_to_db(root_dir + 'Trucks.csv')
    driver_DB = utils.load_csv_file_to_db(root_dir + 'Drivers.csv')
    location_DB = utils.load_csv_file_to_db(root_dir + 'Locations.csv')
    mission_DB = utils.load_csv_file_to_db(root_dir + 'Missions.csv')

    output_DB = [[
        'Date',
        'Time Out',
        'Time In',
        'Truck_Id',
        'Driver_Id',
        'Location_Id',
        'Mission_Id',
        'Duration (hrs)',
        'Distance (kms)',
        'Product Delivered (tonnes)',
        'Ave Speed',
        'Parts Cost',
        'Labour Cost',
        'Fuel Burn',
        'Brake Temperature Events',
        'Overspeed Events',
        'Engine Overspeed Events',
        'Overload Events',
        'Tire Wall events',
        'Tire Loss Events',
        'Accidents']]

    # write headers to csv
    utils.write_csv(output_DB, root_dir + 'Output.csv', False)

    #truck_DB = {k: v for k, v in truck_DB.items() if float(k) <= 1}

    i = 0
    tot = len(truck_DB)
    for truck in truck_DB:
        i += 1
        print('Doing truck ' + str(i) + ' of ' + str(tot))

        output_DB = []
        start_date = utils.datetime.strptime('01-01-2012', '%d-%m-%Y')
        end_date = utils.datetime.strptime('29-03-2018', '%d-%m-%Y')
        current_date = start_date

        # init counter vars
        poor_road_pct = float(location_DB[truck_DB[truck]['Location_Id']]['Poor Road pct'])
        driver_id = get_driver_id(current_date, truck)
        location_id = truck_DB[truck]['Location_Id']
        tire_limit = get_tire_limit(truck, poor_road_pct)
        s1_limit = get_service_limit(1)
        s2_limit = get_service_limit(2)
        s3_limit = get_service_limit(3)
        uws_limit = get_service_limit(4)
        ufs_limit = get_service_limit(5)
        s1_dist = 0
        s2_dist = 0
        s3_dist = 0
        tire_dist = 0
        uws_dist = 0  # unsched_workshop service
        ufs_dist = 0  # unsched_field service
        trip_distance = 0

        break_flag = False
        while break_flag is False:
            # increment counters
            s1_dist += trip_distance
            s2_dist += trip_distance
            s3_dist += trip_distance
            tire_dist += trip_distance
            uws_dist += trip_distance  # unsched_workshop service
            ufs_dist += trip_distance  # unsched_field service

            # reset vars
            tire_change = 0
            accident_cost = 0
            trip_distance = 0
            trip_duration = 0

            # start - around a 15 mins break with rayleigh dist
            rest_time = get_rest_time(10, 5)
            time_out = current_date + utils.timedelta(minutes=rest_time)
            driver_id = get_driver_id(current_date, truck)

            #init events_DB
            event_DB = calc_events(driver_id, 0)

            # test for mission type
            if s1_dist > s1_limit:
                s1_limit = get_service_limit(1)
                s1_dist = 0
                mission_id = 1
                s1_limit = get_service_limit(1)
            elif s2_dist > s2_limit:
                s2_limit = get_service_limit(2)
                s2_dist = 0
                mission_id = 2
            elif s3_dist > s3_limit:
                s3_limit = get_service_limit(3)
                s3_dist = 0
                mission_id = 3
            elif uws_dist > uws_limit:
                uws_limit = get_service_limit(4)
                uws_dist = 0
                mission_id = 4
            elif ufs_dist > ufs_limit:
                ufs_limit = get_service_limit(5)
                ufs_dist = 0
                mission_id = 5
            elif tire_dist > tire_limit:
                tire_limit = get_tire_limit(truck, poor_road_pct)
                tire_dist = 0
                mission_id = 4
                tire_change = 6
            else:
                # toss a coin for 6 or 7
                mission_id = 6
                if utils.np.random.choice(a=[0, 1], size=1, p=[0.5, 0.5])[0] == 0: mission_id = 7
                #calc trip dist and duration early for this type of mission
                trip_distance = get_trip_dist(mission_id)
                trip_duration = get_trip_time(mission_id)
                #only calc events for field missions (id = 6 or 7)
                event_DB = calc_events(driver_id, trip_duration)
                #update the ufs-uws-tire limits due to events, basically shorten a bit depending on the number of events, so worse drivers will be more expensive
                uws_limit, ufs_limit, tire_limit = update_ufs_uws_tire_limits(event_DB, uws_limit, ufs_limit, tire_limit)
                # test for mission ending event (tire failure, breakdown)
                if event_DB['Tire Loss Events'] > 0:
                    ufs_limit = get_service_limit(5)
                    ufs_dist = 0
                    mission_id = 5
                    tire_change = 1
                elif event_DB['Accidents'] > 0:
                    ufs_limit = get_service_limit(5)
                    ufs_dist = 0
                    mission_id = 5
                    accident_cost = utils.np.random.normal(20000, 5000, 1)[0]

            # get mission dist and duration if not calculated already for mission 6 or 7
            if mission_id not in [6,7]:
                trip_distance = get_trip_dist(mission_id)
                trip_duration = get_trip_time(mission_id)

            # now calc output for given mission
            trip_production = get_trip_production(mission_id, truck, trip_duration)
            if trip_duration == 0:
                ave_speed = 0
            else:
                ave_speed = trip_distance / trip_duration
            parts_cost = get_parts_cost(mission_id, tire_change, accident_cost, truck)
            labour_cost = get_labour_cost(mission_id, tire_change, accident_cost, truck)
            fuel_burn = get_fuel_burn(truck, trip_duration, driver_id, poor_road_pct, mission_id)

            # fill out output data
            current_date += utils.timedelta(hours=trip_duration)
            time_in = current_date
            new_data = [utils.datetime.date(time_out), time_out, time_in, truck, driver_id, location_id, mission_id,
                        trip_duration, trip_distance, trip_production, ave_speed, parts_cost, labour_cost, fuel_burn]
            new_data += list(event_DB.values())
            output_DB.append(new_data)

            if current_date > end_date:
                break_flag = True

        # when finished with each truck, append to csv
        utils.write_csv(output_DB, root_dir + 'Output.csv', True)
    # --------------------------------------------------------------------------------------

    return e_msg
