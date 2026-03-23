import pytest
import sys
import os

# Add the code directory to path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../code')))

import registration
import crew
import inventory
import race
import results
import mission
import reputation
import event_log

@pytest.fixture(autouse=True)
def reset_system_state():
    """Resets the global state of all modules before each test to ensure complete isolation."""
    registration.crew_members.clear()
    crew.skills.clear()
    inventory.cash = 0
    inventory.cars.clear()
    inventory.parts.clear()
    reputation.rep_score = 0
    event_log.logs.clear()

def test_register_and_enter_race():
    """TC1: Core Happy Path - Register -> Assign Role -> Add Inventory -> Setup Race."""
    registration.register_member("Dominic")
    crew.assign_role("Dominic", "Driver", 10)
    inventory.add_car("Dodge Charger")
    
    my_race = race.setup_race("Street King")
    assert my_race is not None
    assert my_race["driver"] == "Dominic"
    assert my_race["car"] == "Dodge Charger"

def test_enter_race_without_registered_driver():
    """TC2: Try to start a race without valid registered drivers."""
    inventory.add_car("Toyota Supra")
    # No driver registered or assigned
    my_race = race.setup_race("Empty Race")
    assert my_race is None

def test_enter_race_without_valid_car():
    """TC3: Try to start a race without any cars in inventory."""
    registration.register_member("Brian")
    crew.assign_role("Brian", "Driver", 9)
    # No cars added to inventory
    my_race = race.setup_race("Walker Memorial")
    assert my_race is None

def test_race_results_prize_money_integration():
    """TC4: Race completion updates inventory and reputation (Win)."""
    inventory.cash = 100
    reputation.rep_score = 50 
    mock_race = {"name": "Neon Nights", "driver": "Brian", "car": "Skyline"}
    
    results.record_race_result(mock_race, position=1, prize_money=5000)
    assert inventory.cash == 5100  # 100 + 5000
    assert reputation.rep_score == 60  # 50 + 10 (win bonus)

def test_race_results_loss_reputation_penalty():
    """TC5: Race completion updates reputation but not inventory on a loss outside top 3."""
    inventory.cash = 100
    reputation.rep_score = 50 
    mock_race = {"name": "Losers Bracket", "driver": "Jesse", "car": "Jetta"}
    
    # Position 4 is a loss
    results.record_race_result(mock_race, position=4, prize_money=500)
    assert inventory.cash == 100  # No cash awarded for 4th place
    assert reputation.rep_score == 45  # 50 - 5 (loss penalty)

def test_assign_mission_role_validation_success():
    """TC6: Mission strictly requiring a Mechanic succeeds if one is available."""
    registration.register_member("Letty")
    crew.assign_role("Letty", "Mechanic", 9)
    
    success = mission.start_mission("Engine Swap", "Mechanic")
    assert success is True

def test_assign_mission_role_validation_failure():
    """TC7: Mission strictly requiring a Strategist fails if only a Driver exists."""
    registration.register_member("Tej")
    crew.assign_role("Tej", "Driver", 5)
    
    success = mission.start_mission("Plan the heist", "Strategist")
    assert success is False

def test_multi_race_campaign_aggregation():
    """TC8: Multiple races aggregated correctly across modules."""
    inventory.cash = 0
    reputation.rep_score = 0
    mock_race_1 = {"name": "Race 1", "driver": "Dom", "car": "Charger"}
    mock_race_2 = {"name": "Race 2", "driver": "Letty", "car": "Interceptor"}
    
    # 1 Win, 1 Loss
    results.record_race_result(mock_race_1, position=1, prize_money=1000)
    results.record_race_result(mock_race_2, position=5, prize_money=1000)
    
    # Net logic: Win -> +1000 cash, +10 rep. Loss -> +0 cash, -5 rep.
    assert inventory.cash == 1000
    assert reputation.rep_score == 5

def test_inventory_spending_cash_blocks_invalid():
    """TC9: Win a race to gain money, then attempt to spend more than available."""
    inventory.cash = 0
    mock_race = {"name": "Quick Cash Race"}
    results.record_race_result(mock_race, position=2, prize_money=2000) # 2nd place yields half: $1000
    
    assert inventory.cash == 1000
    assert inventory.spend_cash(1500) is False # Fails over-spending
    assert inventory.cash == 1000
    assert inventory.spend_cash(500) is True   # Succeeds valid spending
    assert inventory.cash == 500

def test_event_log_end_to_end_capture():
    """TC10: Full sequence populates event logs completely and identically across calls."""
    registration.register_member("Mia")
    crew.assign_role("Mia", "Strategist", 8)
    inventory.add_cash(100)
    
    logs = event_log.get_logs()
    assert len(logs) == 3
    assert "Registered new member: Mia" in logs[0]
    assert "Assigned Mia as a 'Strategist'" in logs[1]
    assert "Added $100 cash" in logs[2]

def test_crew_requires_registration_integration():
    """TC11: Cannot bypass Registration module to directly assign roles in Crew module."""
    # Attempt assigning role before registration
    success = crew.assign_role("Vince", "Mechanic", 5)
    
    assert success is False
    assert len(crew.get_members_by_role("Mechanic")) == 0
