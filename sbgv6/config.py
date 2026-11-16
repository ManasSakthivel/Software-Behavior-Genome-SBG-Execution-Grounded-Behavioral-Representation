"""Frozen constants (hashed into artifacts/v6/FREEZE_V6.json before held-out runs)."""
N_MIN = 3          # min observations for an invariant to be asserted
K_W = 8            # support at which invariant weight saturates
U_MIN = 0.5        # min usable-trace fraction per side
ALPHA0 = 0.5       # activation level giving full confidence
MAX_NUM_SLOTS = 6  # numeric slots per point for pair relations
NUM_CAP = 10**6    # |const| cap for const predicates
PROTOCOL = "output_free_v8"
