#  MIT License
#
#  Copyright (c) 2026 HySCALE and vHive community
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.

import pandas as pd
import logging as log
import numpy as np
from pathlib import Path

def preprocess_huawei(trace_dir: str, start_time: str, duration: str, output_dir: str, zero_ms_threshold_percent: str) -> pd.DataFrame:
    
    # Time interval filter // Allow cross day filtering?
    start_time = start_time.split(":")
    day = int(start_time[0])
    hours = int(start_time[1])
    minutes = int(start_time[2])
    duration = int(duration)

    # Determine time interval
    td_interval_start = pd.Timedelta(days=day, hours=hours, minutes=minutes)
    td_interval_end = pd.Timedelta(days=day, hours=hours, minutes=(minutes+duration))
    starting_day = td_interval_start.days
    ending_day = td_interval_end.days

    # Read all within time interval
    trace_dir = Path(trace_dir)
    list_of_directories_to_read = ["function_delay_minute", "memory_limit_minute", "memory_usage_minute", "requests_minute"] # Should be a dictionary

    # matrix = {
    #     "function_delay_minute": [Path("function_delay_minute"), ],
    #     "memory_limit_minute": [Path("memory_limit_minute"),],
    #     "memory_usage_minute": [Path("memory_usage_minute"),],
    #     "requests_minute": [Path("function_delay_minute"),],
    # }

    # Read single metric 
    result = []
    for directory in list_of_directories_to_read:
        directory = trace_dir / directory

        final_df = pd.DataFrame()

        # Determine files to read
        for day in range(starting_day, ending_day + 1):
            file_path = directory / f"day_{day:03d}.csv" # Leading zeros, width of 3 (001, 002)
            df = pd.read_csv(file_path)

            # Filter by timestamp
            df = df[df["time"].between(td_interval_start.seconds, td_interval_end.seconds, inclusive='left')] # left <= series < right

            final_df = pd.concat([final_df, df], ignore_index=True)

        result.append(final_df)


    # Transform to sampler format (inv_df, mem_df, run_df)
    inv_df = generate_inv_df(result[3])
    mem_df = generate_mem_df(result[1])
    dur_df = generate_dur_df(result[0])

    # Filter out functions with 0 invocations

    
    return


def generate_inv_df(requests_minute_df: pd.DataFrame) -> pd.DataFrame: # Honestly creating test will make me more confident

    # Make columns into minute bins
    df = requests_minute_df.drop(columns='day')
    df['time'] = df['time']/60 + 1 # inv_df starts from minute 1
    df = df.set_index('time', drop=True)
    df = df.T

    # Add in front 4 columns
    front_cols = ["HashOwner", "HashApp", "HashFunction", "Trigger"]
    empty_front_df = pd.DataFrame(columns=front_cols, index=df.index)
    df = pd.concat([empty_front_df, df], axis=1)

    df["HashOwner"] = 0
    df['HashApp'] = df.index
    df['HashFunction'] = df.index
    df["Trigger"] = "http"

    # Filter out functions with 0 invocations
    minute_bin_columns = df.columns[4:]
    df = df.dropna(subset=minute_bin_columns, how='all')

    return df

# Memory is total function footprint -> allocated memory across all pods for a single function.
def generate_mem_df(memory_limit_minute: pd.DataFrame) -> pd.DataFrame:
    
    # Make columns into minute bins
    df = memory_limit_minute.drop(columns='day')
    df['time'] = df['time']/60 + 1 # inv_df starts from minute 1
    df = df.set_index('time', drop=True)
    df = df.T

    minute_bin_columns = df.columns
    min_bin_df = df[minute_bin_columns]

    # Set IDs
    df["HashFunction"] = df.index
    df["HashOwner"] = 0
    df['HashApp'] = df.index

    # Sample count is estimated as count of non-NAN samples
    df["SampleCount"] = min_bin_df.count(axis=1)

    # Calculate percentiles from datapoints within time interval
    df["AverageAllocatedMb_pct1"] = min_bin_df.quantile(0.01, axis=1)
    df["AverageAllocatedMb_pct5"] = min_bin_df.quantile(0.05, axis=1)
    df["AverageAllocatedMb_pct25"] = min_bin_df.quantile(0.25, axis=1)
    df["AverageAllocatedMb_pct50"] = min_bin_df.quantile(0.50, axis=1)
    df["AverageAllocatedMb_pct75"] = min_bin_df.quantile(0.75, axis=1)
    df["AverageAllocatedMb_pct95"] = min_bin_df.quantile(0.95, axis=1)
    df["AverageAllocatedMb_pct99"] = min_bin_df.quantile(0.99, axis=1)
    df["AverageAllocatedMb_pct100"] = min_bin_df.quantile(1.00, axis=1)    

    # Cleanup - Keep only required columns
    column_order = [
        "HashFunction", "HashOwner", "HashApp", "SampleCount", 
        "AverageAllocatedMb", "AverageAllocatedMb_pct1", "AverageAllocatedMb_pct5", "AverageAllocatedMb_pct25",
        "AverageAllocatedMb_pct50", "AverageAllocatedMb_pct75", "AverageAllocatedMb_pct95", "AverageAllocatedMb_pct99", "AverageAllocatedMb_pct100"
    ]    
    df = df.reindex(columns=column_order)

    return df

# Duration is function execution time averaged over all pods, timestamped in minute basis
def generate_dur_df(function_delay_minute: pd.DataFrame) -> pd.DataFrame:

    # Make columns into minute bins
    df = function_delay_minute.drop(columns='day')
    df['time'] = df['time']/60 + 1 # inv_df starts fro#m minute 1
    df = df.set_index('time', drop=True)
    df = df.T

    minute_bin_columns = df.columns
    min_bin_df = df[minute_bin_columns]

    # Set IDs
    df["HashOwner"] = 0
    df['HashApp'] = df.index
    df["HashFunction"] = df.index

    # Generate stats (derived from datapoints within time interval)
    df["Average"] = min_bin_df.mean(axis=1)
    df["Count"] = min_bin_df.count(axis=1)
    df["Minimum"] = min_bin_df.min(axis=1)
    df["Maximum"] = min_bin_df.max(axis=1)
    df["percentile_Average_0"] = min_bin_df.quantile(0.00, axis=1)
    df["percentile_Average_1"] = min_bin_df.quantile(0.01, axis=1)
    df["percentile_Average_25"] = min_bin_df.quantile(0.25, axis=1)
    df["percentile_Average_50"] = min_bin_df.quantile(0.50, axis=1)
    df["percentile_Average_75"] = min_bin_df.quantile(0.75, axis=1)
    df["percentile_Average_99"] = min_bin_df.quantile(0.99, axis=1)
    df["percentile_Average_100"] = min_bin_df.quantile(1.00, axis=1)

    # Cleanup - Keep only required columns
    new_columns = [
        "HashOwner", "HashApp", "HashFunction", 
        "Average", "Count", "Minimum", "Maximum",
        "percentile_Average_0", "percentile_Average_1", "percentile_Average_25", "percentile_Average_50", 
        "percentile_Average_75", "percentile_Average_99", "percentile_Average_100"
    ] + ["duration"]
    df = df.reindex(columns=new_columns)

    return df

def filter_out_functions_with_zero_invocations():
    return 1

if __name__ == "__main__":

    trace_dir = "../Huawei2023/private_dataset"
    start_time = "00:00:30"  # DD:HH:MM 
    duration = 5             # Minutes
    output_dir = "../Huawei2023/output"
    
    preprocess_huawei(trace_dir, start_time, duration, output_dir, 0)
