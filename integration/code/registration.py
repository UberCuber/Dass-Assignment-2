import event_log

# Map of crew member name -> assigned role (defaults to None)
crew_members = {}

def register_member(name):
    """Registers a new crew member without a role."""
    if name not in crew_members:
        crew_members[name] = "Unassigned"
        event_log.add_log(f"Registered new member: {name}")
    else:
        print(f"Member '{name}' is already registered.")

def is_registered(name):
    return name in crew_members
