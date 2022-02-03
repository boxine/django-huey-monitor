from huey import signals as _huey_signals


# We need the information at which point a task is "finished"
# and no longer waits or runs, etc.
# It does not mean that execution was successfully completed!
#
# Collect these Huey signals here:
ENDED_HUEY_SIGNALS = (
    _huey_signals.SIGNAL_CANCELED,
    _huey_signals.SIGNAL_COMPLETE,
    _huey_signals.SIGNAL_ERROR,
    _huey_signals.SIGNAL_EXPIRED,
    _huey_signals.SIGNAL_REVOKED,
    _huey_signals.SIGNAL_INTERRUPTED,
)
