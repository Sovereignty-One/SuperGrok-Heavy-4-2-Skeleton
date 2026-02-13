if "fluff" in self.response.lower() or "trust" in self.response.lower() or "sorry" in self.response.lower():
    self.response = self.response.replace("fluff", " ").replace("trust", " ").replace("sorry", " ")
    self.scar_log.append(f"TIME: {time.time()} | VIOLATION: Forbidden words injected. Auto-scrubbed.")
    logging.warning("SELF-CENSOR: Fluff detected and removed.")
    return self.response