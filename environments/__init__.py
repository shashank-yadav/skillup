"""Importing this package registers every environment plugin it contains.

To add a new environment: create `environments/<name>/env.py` implementing
`core.environment.Environment` and calling `register("<name>", YourClass)` at
import time, then import it below.
"""

from environments import alfworld  # noqa: F401
from environments import conversation_judge  # noqa: F401

try:
    from environments import hf_dataset  # noqa: F401
    from environments import livemathbench  # noqa: F401
    from environments import mbpp  # noqa: F401
    from environments import bigcodebench  # noqa: F401
    from environments import sql  # noqa: F401
    from environments import writing  # noqa: F401
except ImportError:
    # Optional: needs `pip install datasets`. Not required for ALFWorld or
    # any other environment that doesn't use these plugins.
    pass
