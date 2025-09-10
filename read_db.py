import shelve
import json

# The shelve file can contain complex Python objects.
# To print it nicely, we can convert it to JSON.
# Note: This might fail if the objects are not JSON serializable, but for this case it should be fine.

try:
    with shelve.open('hr_app_state.db') as db:
        print("--- Database Contents ---")
        if not db:
            print("Database is empty.")
        else:
            for key in db.keys():
                print(f"\n--- Job ID: {key} ---")
                # Pretty print the content of the job
                print(json.dumps(db[key], indent=2))
except Exception as e:
    print(f"Error reading database file: {e}")
