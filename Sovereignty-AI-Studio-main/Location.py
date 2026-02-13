import subprocess
import os

def get_country_code() -> str:
    # Option 1: Carrier SIM (Android only)
    try:
        output = subprocess.check_output( ).decode()
        if "Vodafone" in output or "AT&T" in output:
            return "US"
        if "Vodafone" in output and "UK" in output:
            return "UK"
    except:
        pass

    # Option 2: Offline IP geocode (one-time download)
    if os.path.exists("geo.mmdb"):
        import geoip2.database
        # you run: `pip install geoip2` once
        reader = geoip2.database.Reader('geo.mmdb')
        import socket
        ip = socket.gethostbyname(socket.gethostname())
        response = reader.country(ip)
        return response.country.iso_code

    # Option 3: Ask once, cache
    if os.path.exists("last_country.txt"):
        return open("last_country.txt").read().strip()

    # Fallback
    return "US"
