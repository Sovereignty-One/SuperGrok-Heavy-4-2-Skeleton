# Make sure that you have a stable internet connection
status_dict = {}
# sample websites
websites = [
    
]

def check_websites(websites):
    for item in websites:
        website = item.strip()
        status = requests.get(website).status_code
        status_dict[website] = "UP" if status == 200 else "DOWN"
    print({"Website": "Status"})
    print("\n")
    print(status_dict)


check_websites(websites)