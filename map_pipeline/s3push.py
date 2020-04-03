import boto3
import json
import os
import re
import pandas as pd

fname  = 'healthmap.covid19-data'
bucket = 'covid-19-fmglobal'
ACCESS_KEY = 'AWS-ACCESS-KEY'
SECRET_KEY = 'AWS-SECRET-KEY'

directory    = '/path/to/archive/'
infile       = directory + 'full-data.json'
outfile_csv  = directory + fname + '.csv'
outfile_json = directory + fname + '.json'

with open(infile, 'r') as F:
    read = json.load(F)
data = read['data']
df   = pd.DataFrame(data)

df.to_csv(outfile_csv, index=False)
asdict = df.to_dict(orient='records')

with open(outfile_json, 'w') as F:
    json.dump(asdict, F, indent=4)



client = boto3.client(
    's3',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
)


for f in [outfile_csv, outfile_json]:
    s3name = f.split('/')[-1]
    response = client.upload_file(f, bucket, f.split('/')[-1])
