import sys
import event_log
import registration
import crew
import inventory
import race
import results
import mission
import reputation

def print_menu():
    print("\n=== StreetRace Manager CLI ===")
    print("1. Register Crew Member")
    print("2. Assign Role")
    print("3. Add Car to Inventory")
    print("4. Add Cash to Inventory")
    print("5. Setup a Race")
    print("6. Record Race Result")
    print("7. Start a Mission")
    print("8. View Event Logs")
    print("9. View Crew Status (Reputation & Cash)")
    print("0. Exit")
    print("==============================")

def main():
    while True:
        print_menu()
        choice = input("Select an option: ")

        if choice == "1":
            name = input("Enter crew member name: ")
            registration.register_member(name)

        elif choice == "2":
            name = input("Enter crew member name: ")
            role = input("Enter role (e.g., Driver, Mechanic, Strategist): ")
            try:
                skill = int(input("Enter skill level (1-10): "))
                crew.assign_role(name, role, skill)
            except ValueError:
                print("Invalid skill level. Must be an integer.")

        elif choice == "3":
            car = input("Enter car name: ")
            inventory.add_car(car)

        elif choice == "4":
            try:
                amount = int(input("Enter amount of cash: "))
                inventory.add_cash(amount)
            except ValueError:
                print("Invalid amount.")

        elif choice == "5":
            race_name = input("Enter race name: ")
            race.setup_race(race_name)

        elif choice == "6":
            race_name = input("Enter race name: ")
            try:
                pos = int(input("Enter finish position (e.g., 1 for win): "))
                prize = int(input("Enter prize money: "))
                # We mock the race object for the results module
                mock_race = {"name": race_name}
                results.record_race_result(mock_race, pos, prize)
            except ValueError:
                print("Invalid input numbers.")

        elif choice == "7":
            mission_name = input("Enter mission name: ")
            req_role = input("Enter required role (e.g., Mechanic): ")
            mission.start_mission(mission_name, req_role)

        elif choice == "8":
            print("\n--- Event Logs ---")
            for log in event_log.get_logs():
                print(log)

        elif choice == "9":
            print(f"\n--- Crew Status ---")
            print(f"Reputation: {reputation.rep_score}")
            print(f"Cash Balance: ${inventory.cash}")
            print(f"Cars Owned: {len(inventory.get_cars())}")

        elif choice == "0":
            print("Exiting StreetRace Manager.")
            sys.exit(0)

        else:
            print("Invalid choice. Try again.")

if __name__ == "__main__":
    main()
