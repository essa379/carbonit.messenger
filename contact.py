"""
CarbonIt Secure Messenger - Decentralized P2P Encrypted Chat
Copyright (C) 2025 Edwin Sam K Reju

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

DISCLAIMER: This software is intended for legal and ethical use only.
The authors and contributors are not responsible for any illegal,
malicious, or unauthorized use of this software. Users assume full
responsibility for complying with all applicable laws in their jurisdiction.
"""

import sys
import os

CONTACT_FILE = r'msg\contact.txt'

def load_contacts():
    """Loads contacts from the contact.txt file into a dictionary."""
    contacts = {}
    if not os.path.exists(CONTACT_FILE):
        return contacts  # Return empty dict if file doesn't exist
        
    try:
        with open(CONTACT_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line:
                    # Split only on the first '=' in case the onion has one
                    name, onion = line.split('=', 1)
                    contacts[name.strip()] = onion.strip()
    except Exception as e:
        print(f"[ERROR] Could not read {CONTACT_FILE}: {e}")
    return contacts

def save_contacts(contacts):
    """Saves the contacts dictionary back to the contact.txt file."""
    try:
        with open(CONTACT_FILE, 'w') as f:
            for name, onion in contacts.items():
                f.write(f"{name}={onion}\n")
    except Exception as e:
        print(f"[ERROR] Could not write to {CONTACT_FILE}: {e}")

def print_usage():
    """Prints the help message."""
    print("\n--- CarbonIt Contact Manager ---")
    print("Usage: python contact.py <command> [args]")
    print("\nCommands:")
    print("  list (or fetch)          - Show all contacts")
    print("  add <name> <onion>       - Add a new contact")
    print("  remove <name>            - Remove a contact")
    print("  change <name> <new_onion> - Update a contact's onion address")

def main():
    if len(sys.argv) < 2:
        print_usage()
        return

    command = sys.argv[1].lower()
    contacts = load_contacts()

    if command == 'add':
        if len(sys.argv) != 4:
            print("Usage: python contact.py add <name> <onion>")
            return
        name = sys.argv[2].lower()
        onion = sys.argv[3]
        if name in contacts:
            print(f"[ERROR] Contact '{name}' already exists. Use 'change' to update.")
        else:
            contacts[name] = onion
            save_contacts(contacts)
            print(f"Added contact: {name}")

    elif command == 'remove':
        if len(sys.argv) != 3:
            print("Usage: python contact.py remove <name>")
            return
        name = sys.argv[2].lower()
        if name in contacts:
            del contacts[name]
            save_contacts(contacts)
            print(f"Removed contact: {name}")
        else:
            print(f"[ERROR] Contact '{name}' not found.")

    elif command == 'change':
        if len(sys.argv) != 4:
            print("Usage: python contact.py change <name> <new_onion>")
            return
        name = sys.argv[2].lower()
        new_onion = sys.argv[3]
        if name in contacts:
            contacts[name] = new_onion
            save_contacts(contacts)
            print(f"Updated contact: {name}")
        else:
            print(f"[ERROR] Contact '{name}' not found. Use 'add' to create it.")

    elif command in ('list', 'fetch'):
        if not contacts:
            print("No contacts found. Add some with 'python contact.py add ...'")
            return
        print("\n--- Contact List ---")
        max_len = max(len(name) for name in contacts.keys()) + 2
        for name, onion in contacts.items():
            print(f"{name:<{max_len}}: {onion}")

    else:
        print(f"[ERROR] Unknown command: '{command}'")
        print_usage()

if __name__ == "__main__":
    main()
