"""
Hotel Booking System - a small Python + SQLite command-line project.

Tables:  users, rooms, bookings  (bookings links a user to a room)
Roles :  admin    -> manages rooms and all bookings
         customer -> books rooms and manages their own bookings
"""

import sqlite3
import hashlib

db = sqlite3.connect("hotel.db")
db.execute("PRAGMA foreign_keys = ON")


def setup_database():
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role     TEXT NOT NULL            -- 'admin' or 'customer'
        );
        CREATE TABLE IF NOT EXISTS rooms (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            room_no   TEXT NOT NULL UNIQUE,
            room_type TEXT NOT NULL,
            price     REAL NOT NULL,          -- price per night
            is_booked INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS bookings (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            room_id INTEGER NOT NULL,
            nights  INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (room_id) REFERENCES rooms(id)
        );
    """)

    if db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        db.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                   ("admin", hash_password("admin123"), "admin"))
        db.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                   ("john", hash_password("john123"), "customer"))
        for room in [("101", "Single", 1500), ("102", "Double", 2500),
                     ("201", "Deluxe", 3800), ("202", "Suite", 6500)]:
            db.execute(
                "INSERT INTO rooms (room_no, room_type, price) VALUES (?, ?, ?)", room)
        db.execute(
            "INSERT INTO bookings (user_id, room_id, nights) VALUES (2, 2, 3)")
        db.execute("UPDATE rooms SET is_booked = 1 WHERE id = 2")
    db.commit()


def hash_password(password):
    # don't store plain passwords
    return hashlib.sha256(password.encode()).hexdigest()


def get_text(prompt):
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Please don't leave this empty.")


def get_number(prompt):
    while True:
        try:
            number = float(input(prompt))
            if number > 0:
                return number
            print("The number must be greater than 0.")
        except ValueError:
            print("Please enter a valid number.")


def get_id(prompt):
    return int(get_number(prompt))


def register():
    username = get_text("Choose a username: ")
    password = get_text("Choose a password (min 4 characters): ")
    if len(password) < 4:
        print("Password is too short.")
        return

    db.execute("INSERT INTO users (username, password, role) VALUES (?, ?, 'customer')",
               (username, hash_password(password)))
    db.commit()
    print("Registered! You can log in now.")


def login():
    username = get_text("Username: ")
    password = get_text("Password: ")
    user = db.execute("SELECT * FROM users WHERE username = ? AND password = ?",
                      (username, hash_password(password))).fetchone()
    if user is None:
        print("Wrong username or password.")
    return user


def view_rooms(only_free=False):
    sql = "SELECT id, room_no, room_type, price, is_booked FROM rooms"
    if only_free:
        sql += " WHERE is_booked = 0"
    rows = db.execute(sql).fetchall()
    if not rows:
        print("No rooms found.")
    for r in rows:
        status = "Booked" if r[4] else "Free"
        print(f"ID {r[0]} | Room {r[1]} | {r[2]} | Rs.{r[3]}/night | {status}")


def add_room():
    room_no = get_text("Room number: ")
    room_type = get_text("Room type (Single/Double/Deluxe/Suite): ")
    price = get_number("Price per night: ")
    db.execute("INSERT INTO rooms (room_no, room_type, price) VALUES (?, ?, ?)",
               (room_no, room_type, price))
    db.commit()
    print("Room added.")


def update_room():
    view_rooms()
    room_id = get_id("Room ID to update: ")
    if db.execute("SELECT 1 FROM rooms WHERE id = ?", (room_id,)).fetchone() is None:
        print("Room not found.")
        return
    room_type = get_text("New room type: ")
    price = get_number("New price per night: ")
    db.execute("UPDATE rooms SET room_type = ?, price = ? WHERE id = ?",
               (room_type, price, room_id))
    db.commit()
    print("Room updated.")


def delete_room():
    view_rooms()
    room_id = get_id("Room ID to delete: ")
    cursor = db.execute("DELETE FROM rooms WHERE id = ?", (room_id,))
    db.commit()
    print("Room deleted." if cursor.rowcount else "Room not found.")


def view_bookings(user):
    sql = """SELECT b.id, u.username, r.room_no, b.nights, r.price * b.nights
             FROM bookings b JOIN users u ON u.id = b.user_id
                             JOIN rooms r ON r.id = b.room_id"""
    params = ()
    if user[3] == "customer":
        sql += " WHERE b.user_id = ?"
        params = (user[0],)
    rows = db.execute(sql, params).fetchall()
    if not rows:
        print("No bookings found.")
    for b in rows:
        print(
            f"Booking {b[0]} | Guest: {b[1]} | Room {b[2]} | {b[3]} night(s) | Total Rs.{b[4]}")
    return rows


def book_room(user):
    view_rooms(only_free=True)
    room_id = get_id("Room ID to book: ")
    room = db.execute(
        "SELECT price FROM rooms WHERE id = ? AND is_booked = 0", (room_id,)).fetchone()
    if room is None:
        print("That room doesn't exist or is already booked.")
        return
    nights = get_id("Number of nights: ")
    db.execute("INSERT INTO bookings (user_id, room_id, nights) VALUES (?, ?, ?)",
               (user[0], room_id, nights))
    db.execute("UPDATE rooms SET is_booked = 1 WHERE id = ?", (room_id,))
    db.commit()
    print(f"Booked! Total = Rs.{room[0] * nights}")


def update_booking(user):
    if not view_bookings(user):
        return
    booking_id = get_id("Booking ID to change: ")
    found = db.execute(
        "SELECT 1 FROM bookings WHERE id = ? AND user_id = ?", (booking_id, user[0])).fetchone()
    if found is None:
        print("Booking not found.")
        return
    nights = get_id("New number of nights: ")
    db.execute("UPDATE bookings SET nights = ? WHERE id = ?",
               (nights, booking_id))
    db.commit()
    print("Booking updated.")


def cancel_booking(user):
    if not view_bookings(user):
        return
    booking_id = get_id("Booking ID to cancel: ")
    sql, params = "SELECT room_id FROM bookings WHERE id = ?", [booking_id]
    if user[3] == "customer":
        sql += " AND user_id = ?"
        params.append(user[0])
    booking = db.execute(sql, params).fetchone()
    if booking is None:
        print("Booking not found.")
        return
    db.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
    db.execute("UPDATE rooms SET is_booked = 0 WHERE id = ?",
               (booking[0],))   # room is free again
    db.commit()
    print("Booking cancelled.")


def run(action, *args):
    """Run an action; any error is shown nicely instead of crashing the program."""
    try:
        action(*args)
    except sqlite3.IntegrityError:
        db.rollback()
        print("Error: that is a duplicate, or other records still depend on it.")
    except sqlite3.Error as error:
        db.rollback()
        print("Database error:", error)
    except Exception as error:
        print("Something went wrong:", error)


def customer_menu(user):
    while True:
        print(f"\n--- Customer Menu ({user[1]}) ---")
        print("1. View available rooms\n2. Book a room\n3. View my bookings")
        print("4. Change nights of a booking\n5. Cancel a booking\n0. Logout")
        choice = input("Choose: ").strip()
        if choice == "1":
            run(view_rooms, True)
        elif choice == "2":
            run(book_room, user)
        elif choice == "3":
            run(view_bookings, user)
        elif choice == "4":
            run(update_booking, user)
        elif choice == "5":
            run(cancel_booking, user)
        elif choice == "0":
            print("Logged out.")
            break
        else:
            print("Invalid choice, try again.")


def admin_menu(user):
    while True:
        print(f"\n--- Admin Menu ({user[1]}) ---")
        print("1. View all rooms\n2. Add a room\n3. Update a room\n4. Delete a room")
        print("5. View all bookings\n6. Cancel a booking\n0. Logout")
        choice = input("Choose: ").strip()
        if choice == "1":
            run(view_rooms)
        elif choice == "2":
            run(add_room)
        elif choice == "3":
            run(update_room)
        elif choice == "4":
            run(delete_room)
        elif choice == "5":
            run(view_bookings, user)
        elif choice == "6":
            run(cancel_booking, user)
        elif choice == "0":
            print("Logged out.")
            break
        else:
            print("Invalid choice, try again.")


def main():
    setup_database()
    print("=== Welcome to the Hotel Booking System ===")
    try:
        while True:
            print("\n--- Main Menu ---\n1. Login\n2. Register\n0. Exit")
            choice = input("Choose: ").strip()
            if choice == "1":
                user = login()
                if user:
                    admin_menu(
                        user) if user[3] == "admin" else customer_menu(user)
            elif choice == "2":
                run(register)
            elif choice == "0":
                break
            else:
                print("Invalid choice, try again.")
    except (KeyboardInterrupt, EOFError):
        pass
    db.close()
    print("Goodbye!")


main()
