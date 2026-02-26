from langchain_core.tools import tool
from datetime import datetime

reservations_db = {
    "downtown": {
        "2025-12-25": {"18:00": 20, "19:00": 8,  "20:00": 0},
        "2025-12-26": {"18:00": 0,  "19:00": 4,  "20:00": 12},
    },
    "marina": {
        "2025-12-25": {"18:00": 20, "19:00": 20, "20:00": 6},
        "2025-12-26": {"18:00": 10, "19:00": 0,  "20:00": 0},
    },
    "uptown": {
        "2025-12-25": {"18:00": 0,  "19:00": 5,  "20:00": 20},
        "2025-12-26": {"18:00": 0,  "19:00": 0,  "20:00": 8},
    },
}

BRANCH_CAPACITY = 20

bookings_db = []

loyalty_db = {
    "USR001": {"name": "Alice Chen",    "points": 1240, "tier": "Platinum"},
    "USR002": {"name": "Bob Malik",     "points": 480,  "tier": "Silver"},
    "USR003": {"name": "Carol Singh",   "points": 720,  "tier": "Gold"},
    "USR004": {"name": "David Youssef", "points": 150,  "tier": "Silver"},
    "USR005": {"name": "Sara El-Amin",  "points": 995,  "tier": "Gold"},
}

specials_db = {
    "downtown": {
        "starter": "Lobster Bisque $16",
        "main":    "Braised Lamb Shank $38",
        "dessert": "Pistachio Panna Cotta $12",
    },
    "marina": {
        "starter": "Grilled Octopus $19",
        "main":    "Barramundi en Papillote $32",
        "dessert": "Salted Caramel Tart $11",
    },
    "uptown": {
        "starter": "Burrata and Heirloom Tomatoes $15",
        "main":    "Duck Confit $36",
        "dessert": "Dark Chocolate Mousse $13",
    },
}

TIER_BENEFITS = {
    "Silver":   "10% discount on food",
    "Gold":     "15% discount + free dessert monthly",
    "Platinum": "20% discount + priority reservations + free birthday meal",
}


@tool
def check_table_availability(date: str, time: str, branch: str) -> str:
    """Check table availability at a NovaBite branch. Date format: YYYY-MM-DD. Time format: HH:MM."""
    branch_key = branch.lower().strip()

    if branch_key not in reservations_db:
        return f"Branch '{branch}' not found. Available branches: downtown, marina, uptown."

    seats_taken = reservations_db[branch_key].get(date, {}).get(time, 0)
    seats_available = BRANCH_CAPACITY - seats_taken

    if seats_available <= 0:
        return f"No tables available at NovaBite {branch.title()} on {date} at {time}. Please try a different time."

    return f"{seats_available} seat(s) available at NovaBite {branch.title()} on {date} at {time}."


@tool
def book_table(name: str, date: str, time: str, branch: str, party_size: int = 2) -> str:
    """Book a table at a NovaBite branch. Date format: YYYY-MM-DD. Time format: HH:MM."""
    branch_key = branch.lower().strip()

    if branch_key not in reservations_db:
        return f"Branch '{branch}' not found. Available branches: downtown, marina, uptown."

    seats_taken = reservations_db[branch_key].get(date, {}).get(time, 0)
    seats_available = BRANCH_CAPACITY - seats_taken

    if seats_available < party_size:
        return f"Not enough seats for {party_size} at NovaBite {branch.title()} on {date} at {time}. Only {seats_available} seat(s) left."

    if date not in reservations_db[branch_key]:
        reservations_db[branch_key][date] = {}
    if time not in reservations_db[branch_key][date]:
        reservations_db[branch_key][date][time] = 0
    reservations_db[branch_key][date][time] += party_size

    confirmation_id = f"NB-{1001 + len(bookings_db)}"
    bookings_db.append({
        "id": confirmation_id,
        "name": name,
        "branch": branch_key,
        "date": date,
        "time": time,
        "party_size": party_size,
    })

    return f"Booking confirmed! ID: {confirmation_id}. Table for {party_size} under {name} at NovaBite {branch.title()} on {date} at {time}."


@tool
def get_today_special(branch: str) -> str:
    """Get today's special dishes at a NovaBite branch."""
    branch_key = branch.lower().strip()

    if branch_key not in specials_db:
        return f"Branch '{branch}' not found. Available branches: downtown, marina, uptown."

    s = specials_db[branch_key]
    today = datetime.now().strftime("%A, %d %B %Y")
    return (
        f"Today's specials at NovaBite {branch.title()} ({today}):\n"
        f"  Starter: {s['starter']}\n"
        f"  Main:    {s['main']}\n"
        f"  Dessert: {s['dessert']}"
    )


@tool
def check_loyalty_points(user_id: str) -> str:
    """Check a customer's Nova Rewards loyalty points balance and tier."""
    user = loyalty_db.get(user_id.upper().strip())

    if not user:
        return f"No account found for ID '{user_id}'."

    name    = user["name"]
    points  = user["points"]
    tier    = user["tier"]
    benefit = TIER_BENEFITS.get(tier, "")

    return f"{name} has {points} Nova Rewards points ({tier} tier). Benefit: {benefit}."
