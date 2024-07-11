import csv
import sqlite3
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich import box
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.tree import Tree
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
import random
import time

# Initialize Rich console
console = Console()

def load_gate_assignments(csv_file):
    assignments = []
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            assignments.append(row)
    return assignments

def create_airplane_ascii():
    return r"""
         ___
        /   \
       /     \
      /       \
     /  _   _  \
    |  (_) (_)  |
    |    ___    |
    |   |___|   |
    |__|     |__|
       |     |
       |_____|
    """

def create_main_layout():
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="footer", size=3)
    )
    return layout

def create_header(text):
    return Panel(Text(text, style="bold magenta", justify="center"), border_style="bold", padding=(1, 1))

def create_footer():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return Panel(Text(f"Last Updated: {current_time}", style="italic", justify="center"), border_style="bold", padding=(1, 1))

def create_gate_assignments_table(assignments):
    table = Table(title="Gate Assignments", box=box.DOUBLE_EDGE)
    table.add_column("Flight", style="cyan", justify="center")
    table.add_column("Airline", style="magenta", justify="center")
    table.add_column("Gate", style="yellow", justify="center")
    table.add_column("Arrival", style="green", justify="center")
    table.add_column("Departure", style="red", justify="center")
    table.add_column("Passengers", style="blue", justify="center")

    for assignment in assignments:
        table.add_row(
            assignment['Flight ID'],
            assignment['Airline'],
            assignment['Gate'],
            assignment['Arrival Time'],
            assignment['Departure Time'],
            assignment['Passengers']
        )
    return table

def create_statistics_panel(assignments, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    total_flights = len(assignments)
    total_passengers = sum(int(a['Passengers']) for a in assignments)

    cursor.execute("SELECT COUNT(DISTINCT airline) FROM flights")
    total_airlines = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM gates")
    total_gates = cursor.fetchone()[0]

    stats_tree = Tree("📊 [bold]Airport Statistics[/bold]")
    stats_tree.add("🛫 [cyan]Total Flights:[/cyan] {total_flights}")
    stats_tree.add("👥 [blue]Total Passengers:[/blue] {total_passengers}")
    stats_tree.add("🏢 [magenta]Airlines Operating:[/magenta] {total_airlines}")
    stats_tree.add("🚪 [yellow]Available Gates:[/yellow] {total_gates}")

    conn.close()
    return Panel(stats_tree, title="Statistics", border_style="bold")

def create_airline_distribution(assignments):
    airline_counts = {}
    for assignment in assignments:
        airline = assignment['Airline']
        airline_counts[airline] = airline_counts.get(airline, 0) + 1

    table = Table(title="Airline Distribution", box=box.SIMPLE)
    table.add_column("Airline", style="magenta")
    table.add_column("Flights", style="cyan", justify="right")
    table.add_column("Distribution", style="green")

    total_flights = len(assignments)
    for airline, count in sorted(airline_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_flights) * 100
        bar = "█" * int(percentage / 2)
        table.add_row(airline, str(count), f"{bar} {percentage:.1f}%")

    return table

def fetch_airport_info(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name, iata_code, icao_code FROM airports LIMIT 1")
    airport_info = cursor.fetchone()

    conn.close()
    return airport_info

def display_gate_assignments(csv_file, db_path):
    assignments = load_gate_assignments(csv_file)
    airport_info = fetch_airport_info(db_path)

    layout = create_main_layout()
    layout["header"].update(create_header(f"{airport_info[0]} ({airport_info[1]}/{airport_info[2]}) Gate Assignments"))
    layout["body"].split_row(
        Layout(create_gate_assignments_table(assignments), name="assignments"),
        Layout(name="sidebar", ratio=2).split_column(
            Layout(create_statistics_panel(assignments, db_path)),
            Layout(create_airline_distribution(assignments))
        )
    )
    layout["footer"].update(create_footer())

    console.print(layout)

def interactive_flight_search(assignments):
    flight_ids = [a['Flight ID'] for a in assignments]
    flight_completer = WordCompleter(flight_ids, ignore_case=True)

    while True:
        flight_id = prompt("Enter a flight ID to search (or 'q' to quit): ", completer=flight_completer)
        if flight_id.lower() == 'q':
            break

        flight = next((a for a in assignments if a['Flight ID'] == flight_id), None)
        if flight:
            console.print(Panel(f"""
[bold]Flight Details:[/bold]
Flight ID: {flight['Flight ID']}
Airline: {flight['Airline']}
Gate: {flight['Gate']}
Arrival: {flight['Arrival Time']}
Departure: {flight['Departure Time']}
Passengers: {flight['Passengers']}
            """, title=f"Flight {flight_id} Information", border_style="bold"))
        else:
            console.print(f"[red]Flight {flight_id} not found.[/red]")

def display_live_updates(csv_file, db_path):
    with Live(console=console, refresh_per_second=1) as live:
        for _ in range(60):  # Simulate updates for 60 seconds
            assignments = load_gate_assignments(csv_file)
            layout = create_main_layout()
            layout["header"].update(create_header("Live Gate Assignment Updates"))
            layout["body"].update(create_gate_assignments_table(assignments))
            layout["footer"].update(create_footer())
            live.update(layout)
            time.sleep(1)

def main_menu(csv_file, db_path):
    while True:
        console.clear()
        console.print(create_airplane_ascii(), justify="center")
        console.print("[bold]IGI Airport Gate Assignment System[/bold]", justify="center")
        console.print("\n1. View Gate Assignments")
        console.print("2. Search Flight")
        console.print("3. View Live Updates")
        console.print("4. Exit")

        choice = prompt("Enter your choice: ")

        if choice == '1':
            console.clear()
            display_gate_assignments(csv_file, db_path)
            prompt("Press Enter to continue...")
        elif choice == '2':
            console.clear()
            assignments = load_gate_assignments(csv_file)
            interactive_flight_search(assignments)
        elif choice == '3':
            console.clear()
            display_live_updates(csv_file, db_path)
        elif choice == '4':
            break
        else:
            console.print("[red]Invalid choice. Please try again.[/red]")
            time.sleep(1)

if __name__ == "__main__":
    csv_file = 'gate_assignments.csv'
    db_path = 'igi_airport.db'
    main_menu(csv_file, db_path)