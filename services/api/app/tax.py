"""Tax is a separate domain; no unapproved formula can become a result."""


def calculate(*args, **kwargs):
    raise ValueError(
        "UNAPPROVED_RULESET: M1 bevat geen goedgekeurde fiscale rekenregels."
    )
