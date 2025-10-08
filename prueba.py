import pandas as pd
import json
import pyarrow as pa

with open (r"C:\Users\juan-\Downloads\rick_and_morty_characters.json", encoding='utf-8') as f:
    data = json.load(f)
    
df = pd.json_normalize(data)
df = df[['id', 'name', 'species', 'status', 'type', 'gender', 'origin.name', 'location.name', 'episode']]
df.rename(columns={'origin.name': 'origin_name', 'location.name': 'location_name'}, inplace=True)
df['episode_count'] = df['episode'].apply(len)
df.drop(columns=['episode'], inplace=True)
#file = df.to_json("rick_and_morty_characters_processed.json",orient='records', force_ascii=False)
file = df.to_parquet("rick_and_morty_characters_processed.parquet", engine='pyarrow', index=False)
print(df.head())