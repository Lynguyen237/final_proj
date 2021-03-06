import os
import json

import crud
import model
import server
from request_climate import get_climate

# os.system('dropdb climates') #Comment out after the first run
# os.system('createdb climates') #Comment out after the first run

model.connect_to_db(server.app)
# model.db.create_all() #Comment out after the first run

# **** Check point to ensure you only run this file the first time you create any city objects **** 
if len(City.query.all()) != 0:
    raise (f'You should not have any city object created before the first run')
# **** End of check point ****


#========= CITY TABLE =================
# Load data from a city JSON file as a list of dictionary and save it in a variable
with open('data/cities_json/cities_batch_1_1to2k.json') as f:
    city_list = json.loads(f.read())

# Create cities (city objects), store them in a list to add climate data later
cities_in_db = []
for city in city_list: #city is a dictionary & city_list a list of dictionaries
    city_name, country, iso2, lat, lon, pop = (city['city_ascii'],
                                               city['country'],
                                               city['iso2'],
                                               city['lat'],
                                               city['lng'],
                                               city['population'])
        
    # create a city object
    db_city = crud.create_city(city_name, country, iso2, lat, lon, pop)
    cities_in_db.append(db_city)


#========= CONTINENT TABLE =================
# Create a continent dictionary with 2-letter continent codes as keys & continent objects as values.
with open('data/continent.json') as f:
    continent_list = json.loads(f.read())

continents_in_db = {}
for continent in continent_list:
    continent_name, continent_code = (continent['Name'],
                                      continent['Code'])
    # create a continent object
    db_continent = crud.create_continent(continent_name, continent_code)
    continents_in_db [continent_code] = db_continent


# Create country_continent dictionary with ios2 country codes as keys & continent objects as values
with open('data/country-continent.json') as f:
    country_continent = json.loads(f.read())

country_continent_dict = {}
for item in country_continent:
    iso2 = item['Two_Letter_Country_Code']
    country_continent_dict[iso2] = continents_in_db[item['Continent_Code']]


#========= CLIMATE TABLE =================
# Loop over the list of city objects 
# and create corresponding climate data
for city in cities_in_db:
    # Find the city's continent by looking up iso2 key in the country_continent dict
    continent = country_continent_dict[city.iso2]
    city.continent = continent # Associate the city with the right continent via sqlalchemy relationship
    model.db.session.commit() # Commit changes

    # Request 12-month climate data for a given city
    climate_data = get_climate(city.lat, city.lon) 
    
    for month_data in climate_data['data']:

        month, prcp, pres = (month_data['month'],
                             month_data['prcp'],
                             month_data['pres'])
        
        tavg, tmax, tmin, tsun = (month_data['tavg'],
                                  month_data['tmax'],
                                  month_data['tmin'],
                                  month_data['tsun'])
        
        # Create the climate rows in the 'climates' table
        db_climate = crud.create_climate (month,
                                          prcp,
                                          pres,
                                          tavg,
                                          tmax,
                                          tmin,
                                          tsun,
                                          city,
                                          continent)                        
