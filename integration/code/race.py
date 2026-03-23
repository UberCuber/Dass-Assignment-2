import event_log
import crew
import inventory

def setup_race(race_name):
    """Sets up a race ensuring both a driver and a car are available."""
    drivers = crew.get_members_by_role("Driver")
    cars = inventory.get_cars()
    
    if not drivers:
        print("Cannot start race: No drivers available in the crew.")
        return None
    if not cars:
        print("Cannot start race: No cars available in inventory.")
        return None
        
    assigned_driver = drivers[0]
    assigned_car = cars[0]
    
    event_log.add_log(f"Race '{race_name}' is set. Driver: {assigned_driver}, Car: {assigned_car}")
    
    return {
        "name": race_name,
        "driver": assigned_driver,
        "car": assigned_car
    }
