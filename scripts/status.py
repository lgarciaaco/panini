"""Show collection overview."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
load_dotenv()

from src import catalog, inventory, reports

def main():
    all_codes = catalog.all_codes()
    inventory.init(all_codes)
    stats = inventory.stats()
    reports.print_stats(stats, len(all_codes))
    grps = catalog.groups()
    reports.print_group_table(grps, catalog, inventory)

if __name__ == "__main__":
    main()
