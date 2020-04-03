'''
Get WHO data for Global counts side bar on map. 

Query copied after using interface at : 
    https://services.arcgis.com/5T5nSi527N4F7luB/ArcGIS/rest/services/COVID_19_CasesByCountry(pl)_VIEW/FeatureServer/0/query
'''

import requests
import json
 
query = 'https://services.arcgis.com/5T5nSi527N4F7luB/ArcGIS/rest/services/COVID_19_CasesByCountry(pl)_VIEW/FeatureServer/0/query?where=1%3D1&objectIds=&time=&geometry=&geometryType=esriGeometryEnvelope&inSR=&spatialRel=esriSpatialRelIntersects&resultType=none&distance=0.0&units=esriSRUnit_Meter&returnGeodetic=true&outFields=cum_conf%2C+ADM0_NAME&returnGeometry=false&returnCentroid=true&featureEncoding=esriDefault&multipatchOption=xyFootprint&maxAllowableOffset=&geometryPrecision=&outSR=&datumTransformation=&applyVCSProjection=false&returnIdsOnly=false&returnUniqueIdsOnly=false&returnCountOnly=false&returnExtentOnly=false&returnQueryGeometry=false&returnDistinctValues=false&cacheHint=false&orderByFields=&groupByFieldsForStatistics=&outStatistics=&having=&resultOffset=&resultRecordCount=&returnZ=false&returnM=false&returnExceededLimitFeatures=true&quantizationParameters=&sqlFormat=none&f=pjson&token='

req = requests.get(query)

if req.status_code == 200:
    data = json.loads(req.text)
    features = {'features': data['features']}

    with open('/path/to/archive/who.json', 'w') as F:
        json.dump(features, F)

    with open('/path/to/site/who.json', 'w') as F: 
        json.dump(features, F)
