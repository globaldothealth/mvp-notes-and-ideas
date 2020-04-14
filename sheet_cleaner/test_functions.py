import unittest

import pandas as pd
import numpy as np
from pandas._testing import assert_frame_equal

from functions import duplicate_rows_per_column


class TestFunctions(unittest.TestCase):

    def test_duplicate_rows(self):
        df = pd.DataFrame(
            {"country": ["FR", "CH", "US"],
            "aggr": [np.nan, 3.0, np.nan]})
        dup = duplicate_rows_per_column(df, col="aggr")
        want_df = pd.DataFrame(
            {"country": ["FR", "CH", "US", "CH", "CH", "CH"],
            "aggr":[np.nan] * 6})
        assert_frame_equal(dup, want_df)