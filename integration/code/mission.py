import event_log
import crew

def start_mission(mission_name, required_role):
    """Assigns a mission, requires a specific role to be available."""
    available_members = crew.get_members_by_role(required_role)
    
    if not available_members:
        print(f"Mission '{mission_name}' failed: No {required_role} available.")
        event_log.add_log(f"Mission '{mission_name}' cancelled due to missing role: {required_role}.")
        return False
        
    assigned_member = available_members[0]
    event_log.add_log(f"Mission '{mission_name}' started. Assigned {required_role}: {assigned_member}")
    return True
