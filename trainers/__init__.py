"""Importing this package registers every trainer strategy it contains.

To add a new training algorithm: create `trainers/<name>.py` implementing
`run(ctx: core.trainer.TrainerContext) -> {"skill": str, "history": list[dict]}`
and calling `register("<name>", run)` at import time, then import it below.
"""

from trainers import avo, expel, gated, naive, reflact  # noqa: F401
