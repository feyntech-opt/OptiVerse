import csv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich import box
import random
from datetime import datetime

def load_gate_assignments(csv_file):
    assignments = []
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            assignments.append(row)
    return assignments

def create_airplane_ascii():
    airplane = r"""
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
    return airplane

def create_terminal_layout(assignments):
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="footer", size=3)
    )

    # Header
    header_text = Text("IGI Airport Gate Assignments", style="bold magenta", justify="center")
    layout["header"].update(Panel(header_text, border_style="bold", padding=(1, 1)))

    # Body
    table = Table(title="Flight Information", box=box.DOUBLE_EDGE)
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

    layout["body"].update(table)

    # Footer
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    footer_text = Text(f"Last Updated: {current_time}", style="italic", justify="center")
    layout["footer"].update(Panel(footer_text, border_style="bold", padding=(1, 1)))

    return layout

def display_gate_assignments(csv_file):
    console = Console()

    # Display ASCII art of an airplane
    airplane_art = create_airplane_ascii()
    console.print(Panel(airplane_art, border_style="bold", padding=(1, 1)), justify="center")

    assignments = load_gate_assignments(csv_file)
    layout = create_terminal_layout(assignments)

    console.print(layout)

    # Display some statistics
    total_flights = len(assignments)
    total_passengers = sum(int(a['Passengers']) for a in assignments)
    console.print(f"[bold green]Total Flights:[/bold green] {total_flights}")
    console.print(f"[bold blue]Total Passengers:[/bold blue] {total_passengers}")

if __name__ == "__main__":
    csv_file = 'gate_assignments.csv'
    display_gate_assignments(csv_file)