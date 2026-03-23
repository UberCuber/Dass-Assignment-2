import event_log
import inventory
import reputation

def record_race_result(race, position, prize_money):
    """Records the outcome of a race, updating inventory cash and crew reputation."""
    if not race:
        return False
        
    event_log.add_log(f"Recorded results for '{race['name']}': Finished Position {position}")
    
    if position == 1:
        inventory.add_cash(prize_money)
        reputation.add_rep(10)
        event_log.add_log(f"Victory! Earned ${prize_money}.")
    elif position <= 3:
        inventory.add_cash(prize_money // 2)
        reputation.add_rep(5)
        event_log.add_log(f"Podium finish! Earned ${prize_money // 2}.")
    else:
        reputation.remove_rep(5)
        event_log.add_log("Lost the race. Reputation took a hit.")
        
    return True
