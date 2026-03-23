import event_log

rep_score = 0

def add_rep(points):
    """Increases the crew's reputation."""
    global rep_score
    rep_score += points
    event_log.add_log(f"Reputation increased by {points}. Total: {rep_score}")

def remove_rep(points):
    """Decreases the crew's reputation."""
    global rep_score
    rep_score -= points
    event_log.add_log(f"Reputation decreased by {points}. Total: {rep_score}")
