import event_log
import registration

# Map of crew member name -> skill level (integer 1-10)
skills = {}

def assign_role(name, role, skill_level):
    """Assigns a specific role (like Driver or Mechanic) to a registered member."""
    if not registration.is_registered(name):
        print(f"Error: {name} must be registered first before receiving a role.")
        return False
        
    registration.crew_members[name] = role
    skills[name] = skill_level
    event_log.add_log(f"Assigned {name} as a '{role}' (Skill level: {skill_level})")
    return True

def get_members_by_role(role):
    """Returns a list of members who have the specified role."""
    return [name for name, r in registration.crew_members.items() if r == role]
