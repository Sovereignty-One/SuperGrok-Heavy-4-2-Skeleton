# echo_guard.py
def speak_once():
    global said
    if said:
        return ""
    said = True
    return "I see you."
