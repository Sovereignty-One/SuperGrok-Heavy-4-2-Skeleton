# remove-Word.py - code fragment
def remove_word(response, scar_log=None):
    import time, logging
    if "fluff" in response.lower() or "trust" in response.lower() or "sorry" in response.lower():
        response = response.replace("fluff", " ").replace("trust", " ").replace("sorry", " ")
        if scar_log is not None:
            scar_log.append(f"TIME: {time.time()} | VIOLATION: Forbidden words injected. Auto-scrubbed.")
        logging.warning("SELF-CENSOR: Fluff detected and removed.")
    return response
