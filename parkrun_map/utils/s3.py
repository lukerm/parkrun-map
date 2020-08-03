import os

import pandas as pd
import pyarrow.parquet as pq
import s3fs


NUMBER_ID_DIGITS = 4


def read_data_for_athlete_id(athlete_id: int, parquet_table_location: str, s3_mode: bool = False) -> pd.DataFrame:
    athlete_id_str = str(int(athlete_id)).zfill(NUMBER_ID_DIGITS)

    # Append a path that will filter down to the appropriate final digits of the athlete ID
    pq_root = parquet_table_location
    for digit in range(-NUMBER_ID_DIGITS, 0):
        pq_root = os.path.join(pq_root, f'athlete_id_digit_{digit}={athlete_id_str[digit]}')

    df_athletes = pq.read_table(pq_root, filesystem=s3fs.S3FileSystem() if s3_mode else None).to_pandas()
    return df_athletes[df_athletes['athlete_id'] == athlete_id].copy()
