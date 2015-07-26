import sys

import willie  # NOQA

sys.modules['sopel'] = sys.modules['willie']
