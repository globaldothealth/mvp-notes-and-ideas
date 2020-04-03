'''
Pipeline to fetch covid-19 data from Open Line List and reformat for map on : 
    healthmap.org/covid-19

Author : Thomas Brewer
email  : thomas.brewer@childrens.harvard.edu
'''



testing = False

import configparser
import pandas as pd
from shutil import copyfile
from functions import *


configfile = '/var/www/scripts/covid-19/DataPipeline/.CONF'
config = configparser.ConfigParser()
config.read(configfile)
logfile = config['FILES'].get('LOG')


COLNAMES = ['ID', 'latitude', 'longitude', 'city', 'province', 'country',
            'age', 'sex', 'symptoms', 'source', 'date_confirmation', 'geo_resolution'] # desired columns from sheets
# A1 notation ranges from sheets

def main():
    try :
        sheets       = get_GoogleSheets(config)
        unique_data  = []
        full_data    = []

        for sheet in sheets:
            sheet.data = load_sheet(sheet, config)
            # Edit ids in original to keep track (temporary)
            if sheet.name == 'outside_Hubei':
                sheet.data.ID = sheet.data.ID.apply(lambda x: f'000-1-{x}')
            elif sheet.name == 'Hubei':
                sheet.data.ID = sheet.data.ID.apply(lambda x: f'000-2-{x}')
            
            full= clean_data(sheet.data, COLNAMES)
            full_data.append(full)

        # Reformat things and save

        # full data
        full_data   = pd.concat(full_data, ignore_index=True, sort=False)
        unique_data = reduceToUnique(full_data) 

        full_data = {'data': full_data.to_dict(orient='records')}
        fullpath  = config['FILES'].get('FULL')
        savedata(full_data, fullpath)
        
        # aggregated data
        unique_data = {'data': unique_data} 
        uniquepath  = config['FILES'].get('TOTALS')
        savedata(unique_data, uniquepath)

        # animation data
        anipath = config['FILES'].get('ANIMATION')
        anidata = animation_formating(fullpath)
        savedata(anidata, anipath)

        # aggregated data, geojson
        #geo_unique = {'
                
        # save all results
        #fullpath   = config['FILES'].get('FULL')
        #savedata(full_data, fullpath)
    
        #uniquepath = config['FILES'].get('TOTAL_OLD')
        #savedata(unique_data, uniquepath)

        geo_uniquepath = config['FILES'].get('GEO_TOTALS')
        convert_to_geojson(uniquepath, geo_uniquepath)

        geo_anipath    = config['FILES'].get('GEO_ANIME')
        animation_formating_geo(fullpath, geo_anipath)
        

        if not testing:
            # Copy files to HTML directoryi
            htmlpath1 = config['HTML'].get('TOTALS')
            htmlpath2 = config['HTML'].get('ANIMATION')
            copyfile(uniquepath, htmlpath1) 
            copyfile(anipath, htmlpath2)

            htmlpath1 = config['HTML'].get('GEO_TOTALS')
            htmlpath2 = config['HTML'].get('GEO_ANIME')
            copyfile(geo_uniquepath, htmlpath1)
            copyfile(geo_anipath, htmlpath2)

    except Exception as Err:
        message = f'Update Error, {Err}'
        log_message(message, config)
        raise Err


if __name__ == '__main__':
    main()


