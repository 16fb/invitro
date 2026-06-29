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
#  SOFTWARE.

from pathlib import Path

import pandas as pd
import numpy as np
import pytest
import os

from sampler.preprocessHuawei import (
    preprocess_huawei,
    generate_inv_df
)

# def test_preprocess_huawei():

#     os.getcwd() # Actual 

#     # Test preprocess_huawei
#     trace_dir = "yes"
#     start_time = "00:00:00"  # DD:HH:MM 
#     duration = 5             # Minutes
    
#     #preprocess_huawei(trace_dir: str, start_time: str, duration: str, output_dir: str)

# MAYBE STILL IMPLEMENT
# def test_time_slicing():
#     return 0

NaN = np.nan

def test_generate_inv_df():

    # Zero is equivalent to NaN
    input_df = pd.DataFrame({
        "day":  [0, 0, 0],
        "time": [0, 60, 120],
        "0":    [10, 20, 30],       #
        "1":    [NaN, NaN, NaN],    # Zero invocations -> drop
        "2":    [NaN, 10, NaN],     # At least 1 invocation -> keep
        "3":    [5583, 3552, 4254], # 
        "4":    [200, 0, 20],       # '0' in input -> keep
    })

    expected_df = pd.DataFrame({
        "HashOwner":    ["0", "0", "0", "0"],
        "HashApp":      ["0", "2", "3", "4"],
        "HashFunction": ["0", "2", "3", "4"],
        "Trigger":      ["http", "http", "http", "http"],
        "1":            [10, 0, 5583, 200],
        "2":            [20, 10, 3552, 0],
        "3":            [30, 0, 4254, 20],
    })

    inv_df = generate_inv_df(input_df)
    pd.testing.assert_frame_equal(inv_df, expected_df)

# def test_generate_inv_df_error_thrown():
#     raise Exception("Starting hour and starting minute should not be negative")

def test_generate_mem_df():
    return 0

def test_generate_dur_df():
    return 0

# Full function happy path test
def test_preprocess_huawei():
    return 0