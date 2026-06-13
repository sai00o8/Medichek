from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from ai_analyzer import analyze_symptoms
from scorer import calculate_score
from database import init_db, save_session, get_history

console = Console()

def collect_symptoms():
    console.print(Panel("🏥 Welcome to MediCheck", style="bold blue"))
    
    console.print("\n[bold]What symptoms are you experiencing?[/bold]")
    symptoms = input("> ").strip()
    
    console.print("\n[bold]How long have you had these symptoms?[/bold]")
    duration = input("> ").strip()
    
    console.print("\n[bold]Rate your discomfort (mild / moderate / severe)[/bold]")
    severity = input("> ").strip()
    
    return {
        "symptoms": symptoms,
        "duration": duration,
        "severity": severity
    }

def show_history():
    rows = get_history()
    
    if not rows:
        console.print("\n[yellow]No history found.[/yellow]")
        return
    
    table = Table(title="📜 Last 5 Sessions")
    table.add_column("ID", style="cyan")
    table.add_column("Date", style="magenta")
    table.add_column("Symptoms", style="white")
    table.add_column("Score", style="yellow")
    table.add_column("Assessment", style="green")
    
    for row in rows:
        table.add_row(str(row[0]), row[1], row[2], str(row[3]), row[4])
    
    console.print(table)

def main():
    # Initialize database on startup
    init_db()
    
    # Ask user what they want to do
    console.print(Panel("🏥 Welcome to MediCheck", style="bold blue"))
    console.print("\n[bold]What would you like to do?[/bold]")
    console.print("  1 → Check symptoms")
    console.print("  2 → View history")
    
    choice = input("\n> ").strip()
    
    if choice == "2":
        show_history()
        return
    
    # Default: check symptoms
    data = collect_symptoms()
    
    console.print("\n[yellow]🔍 Analyzing your symptoms...[/yellow]\n")
    
    result = analyze_symptoms(data)
    score_data = calculate_score(data, result)
    
    # Save to database
    save_session(data, result, score_data)
    
    # Print AI report
    console.print(Panel(result, title="📋 MediCheck Report", style="bold green"))
    
    # Print severity score
    console.print(f"\n[bold]Severity Score:[/bold] {score_data['score']}/100")
    console.print(f"[bold]Assessment:[/bold] {score_data['severity_level']}")
    
    # Print urgent flags
    if score_data["flags"]:
        console.print("\n[bold red]⚠️  FLAGS:[/bold red]")
        for flag in score_data["flags"]:
            console.print(f"  {flag}")

if __name__ == "__main__":
    main()