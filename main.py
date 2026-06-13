from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from ai_analyzer import analyze_symptoms
from scorer import calculate_score
from database import init_db, save_session, get_history
from report_gen import generate_pdf

console = Console()

def collect_symptoms():
    console.print(Panel("🏥 Welcome to MediCheck", style="bold blue"))
    
    while True:
        console.print("\n[bold]What symptoms are you experiencing?[/bold]")
        symptoms = input("> ").strip()
        
        if not symptoms:
            console.print("[red]❌ Please enter your symptoms.[/red]")
            continue
        
        if symptoms.isdigit():
            console.print("[red]❌ Please describe your symptoms in words.[/red]")
            continue
        
        # Check if input is actual symptoms or casual chat
        from ai_analyzer import is_valid_symptom, get_casual_response
        
        if not is_valid_symptom(symptoms):
            casual_reply = get_casual_response(symptoms)
            console.print(f"\n[bold cyan]🏥 MediCheck:[/bold cyan] {casual_reply}\n")
            continue
        
        break
    
    while True:
        console.print("\n[bold]How long have you had these symptoms?[/bold]")
        duration = input("> ").strip()
        if duration:
            break
        console.print("[red]❌ Please enter a valid duration.[/red]")
    
    while True:
        console.print("\n[bold]Rate your discomfort (mild / moderate / severe)[/bold]")
        severity = input("> ").strip().lower()
        if severity in ["mild", "moderate", "severe"]:
            break
        console.print("[red]❌ Please type exactly: mild, moderate, or severe[/red]")
    
    return {
        "symptoms": symptoms,
        "duration": duration,
        "severity": severity
    }

def show_history():
    try:
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

    except Exception as e:
        console.print(f"[red]❌ Could not load history: {e}[/red]")

def main():
    try:
        # Initialize database
        init_db()
        
        # Menu
        console.print(Panel("🏥 Welcome to MediCheck", style="bold blue"))
        console.print("\n[bold]What would you like to do?[/bold]")
        console.print("  1 → Check symptoms")
        console.print("  2 → View history")
        
        choice = input("\n> ").strip()
        
        if choice == "2":
            show_history()
            return
        
        # Collect symptoms with validation
        data = collect_symptoms()
        
        # AI Analysis
        try:
            console.print("\n[yellow]🔍 Analyzing your symptoms...[/yellow]\n")
            result = analyze_symptoms(data)
        except Exception:
            console.print("[red]❌ Could not connect to AI. Check your internet and API key.[/red]")
            return
        
        # Scoring
        try:
            score_data = calculate_score(data, result)
        except Exception as e:
            console.print(f"[red]❌ Scoring failed: {e}[/red]")
            return
        
        # Save to database
        try:
            save_session(data, result, score_data)
        except Exception as e:
            console.print(f"[red]❌ Could not save session: {e}[/red]")
        
        # Print report
        console.print(Panel(result, title="📋 MediCheck Report", style="bold green"))
        console.print(f"\n[bold]Severity Score:[/bold] {score_data['score']}/100")
        console.print(f"[bold]Assessment:[/bold] {score_data['severity_level']}")
        
        if score_data["flags"]:
            console.print("\n[bold red]⚠️  FLAGS:[/bold red]")
            for flag in score_data["flags"]:
                console.print(f"  {flag}")
        
        # PDF option
        console.print("\n[bold]Would you like to save this as a PDF report? (yes / no)[/bold]")
        pdf_choice = input("> ").strip().lower()
        
        if pdf_choice in ["yes", "y"]:
            try:
                console.print("\n[yellow]📄 Generating PDF report...[/yellow]")
                pdf_file = generate_pdf(data, result, score_data)
                console.print(f"[bold green]✅ Report saved as: {pdf_file}[/bold green]")
            except Exception as e:
                console.print(f"[red]❌ Could not generate PDF: {e}[/red]")
        else:
            console.print("\n[yellow]📄 Report not saved.[/yellow]")

    except KeyboardInterrupt:
        console.print("\n\n[yellow]👋 MediCheck closed. Stay healthy![/yellow]")

if __name__ == "__main__":
    main() 