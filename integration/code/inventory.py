import event_log

cash = 0
cars = []
parts = []

def add_cash(amount):
    global cash
    cash += amount
    event_log.add_log(f"Added ${amount} cash. Total: ${cash}")

def spend_cash(amount):
    global cash
    if cash >= amount:
        cash -= amount
        event_log.add_log(f"Spent ${amount} cash. Total: ${cash}")
        return True
    return False

def add_car(car_name):
    cars.append(car_name)
    event_log.add_log(f"Added car to inventory: {car_name}")

def get_cars():
    return cars
