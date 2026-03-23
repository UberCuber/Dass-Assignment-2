import event_log

logs = []

def add_log(message):
    """Adds a message to the event log."""
    logs.append(message)
    print(f"[LOG] {message}")

def get_logs():
    return logs
