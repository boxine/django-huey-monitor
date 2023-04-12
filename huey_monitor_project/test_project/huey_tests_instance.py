from huey import MemoryHuey


HUEY = MemoryHuey(
    immediate=True,  # execute task synchronously
    initial_delay=0.001,
    max_delay=0.001,
)
