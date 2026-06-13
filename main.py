from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from ai_analyzer import analyze_symptoms
from scorer import calculate_score
from database import init_db, save_session, get_history, delete_session, delete_all_sessions, search_sessions, get_session_by_id
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
        console.print("\n[bold]View History Options:[/bold]")
        console.print("  1 → View last 5 sessions")
        console.print("  2 → Search by symptom keyword")
        
        choice = input("\n> ").strip()
        
        if choice == "2":
            console.print("\n[bold]Enter keyword to search (e.g. headache, fever):[/bold]")
            keyword = input("> ").strip()
            
            if not keyword:
                console.print("[red]❌ Please enter a keyword.[/red]")
                return
            
            rows = search_sessions(keyword)
            title = f"🔍 Search Results for '{keyword}'"
        
        else:
            rows = get_history()
            title = "📜 Last 5 Sessions"
        
        if not rows:
            console.print("\n[yellow]No sessions found.[/yellow]")
            return
        
        table = Table(title=title)
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

def view_full_report():
    try:
        # Show history first so user knows which ID to pick
        rows = get_history()
        
        if not rows:
            console.print("\n[yellow]No history found.[/yellow]")
            return
        
        table = Table(title="📜 Your Sessions")
        table.add_column("ID", style="cyan")
        table.add_column("Date", style="magenta")
        table.add_column("Symptoms", style="white")
        table.add_column("Score", style="yellow")
        table.add_column("Assessment", style="green")
        
        for row in rows:
            table.add_row(str(row[0]), row[1], row[2], str(row[3]), row[4])
        
        console.print(table)
        
        # Ask which session to view
        console.print("\n[bold]Enter the ID of the session you want to view:[/bold]")
        
        try:
            session_id = int(input("> ").strip())
        except ValueError:
            console.print("[red]❌ Please enter a valid number.[/red]")
            return
        
        row = get_session_by_id(session_id)
        
        if not row:
            console.print(f"[red]❌ No session found with ID {session_id}.[/red]")
            return
        
        # Display full report
        console.print(f"\n[bold cyan]📅 Date:[/bold cyan] {row[1]}")
        console.print(f"[bold cyan]🤒 Symptoms:[/bold cyan] {row[2]}")
        console.print(f"[bold cyan]⏱️  Duration:[/bold cyan] {row[3]}")
        console.print(f"[bold cyan]😣 Discomfort:[/bold cyan] {row[4].capitalize()}")
        
        console.print(Panel(row[5], title="📋 Full AI Diagnosis", style="bold green"))
        
        console.print(f"\n[bold]Severity Score:[/bold] {row[6]}/100")
        console.print(f"[bold]Assessment:[/bold] {row[7]}")
        
        # Ask if they want to export as PDF
        console.print("\n[bold]Would you like to export this as PDF? (yes / no)[/bold]")
        pdf_choice = input("> ").strip().lower()
        
        if pdf_choice in ["yes", "y"]:
            data = {
                "symptoms": row[2],
                "duration": row[3],
                "severity": row[4]
            }
            score_data = {
                "score": row[6],
                "severity_level": row[7],
                "flags": []
            }
            try:
                console.print("\n[yellow]📄 Generating PDF...[/yellow]")
                pdf_file = generate_pdf(data, row[5], score_data)
                console.print(f"[bold green]✅ Report saved as: {pdf_file}[/bold green]")
            except Exception as e:
                console.print(f"[red]❌ Could not generate PDF: {e}[/red]")

    except Exception as e:
        console.print(f"[red]❌ Error loading report: {e}[/red]")

def delete_history():
    rows = get_history()
    
    if not rows:
        console.print("\n[yellow]No history found.[/yellow]")
        return
    
    # Show history first
    table = Table(title="📜 Your Sessions")
    table.add_column("ID", style="cyan")
    table.add_column("Date", style="magenta")
    table.add_column("Symptoms", style="white")
    table.add_column("Score", style="yellow")
    
    for row in rows:
        table.add_row(str(row[0]), row[1], row[2], str(row[3]))
    
    console.print(table)
    
    # Ask what to delete
    console.print("\n[bold]What would you like to delete?[/bold]")
    console.print("  1 → Delete a specific session by ID")
    console.print("  2 → Delete ALL history")
    console.print("  3 → Go back")
    console.print("  4 → View full report from history")
    
    choice = input("\n> ").strip()
    
    if choice == "1":
        console.print("\n[bold]Enter the ID of the session to delete:[/bold]")
        try:
            session_id = int(input("> ").strip())
            success = delete_session(session_id)
            if success:
                console.print(f"[green]✅ Session {session_id} deleted successfully.[/green]")
            else:
                console.print(f"[red]❌ No session found with ID {session_id}.[/red]")
        except ValueError:
            console.print("[red]❌ Please enter a valid number.[/red]")
    
    elif choice == "2":
        console.print("\n[bold red]⚠️  Are you sure you want to delete ALL history? (yes / no)[/bold red]")
        confirm = input("> ").strip().lower()
        if confirm in ["yes", "y"]:
            delete_all_sessions()
            console.print("[green]✅ All history deleted.[/green]")
        else:
            console.print("[yellow]Cancelled.[/yellow]")
    
    elif choice == "3":
        return

def main():
    try:
        # Initialize database
        init_db()
        
        # Menu
        console.print(Panel("🏥 Welcome to MediCheck", style="bold blue"))
        console.print("\n[bold]What would you like to do?[/bold]")
        console.print("  1 → Check symptoms")
        console.print("  2 → View history")
        console.print("  3 → Delete history")
        
        choice = input("\n> ").strip()
        
        if choice == "2":
            show_history()
            return
        
        if choice == "3":
             delete_history()
             return
        if choice == "4":
            view_full_report()
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