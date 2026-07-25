from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import random
from pathlib import Path

def generate_pdf():
    names = [
        "Raju", "Kari", "Shivakumar", "Suresh", "Kumar", "Manja", "Ravi", "Seena", 
        "Gopi", "Don", "Prakash", "Girish", "Naveen", "Manoj", "Karthik", "Darshan", 
        "Prashanth", "Mahesh", "Vinod", "Harish", "Arun", "Babu", "Chetan", "Deepak",
        "Eshwar", "Farooq", "Ganesh", "Hari", "Imran", "Jagadish", "Kiran", "Lokesh",
        "Mohan", "Nithin", "Omkar"
    ]
    
    # Select 32 distinct names
    offenders = random.sample(names, 32)
    
    # 4 distinct gangs
    gangs = [
        offenders[0:8],
        offenders[8:16],
        offenders[16:24],
        offenders[24:32]
    ]
    
    records = []
    for i, name in enumerate(offenders):
        # Find which gang this person is in
        my_gang = next(g for g in gangs if name in g)
        
        is_kingpin = name == my_gang[0]
        num_crimes = random.randint(15, 30) if is_kingpin else random.randint(1, 10)
        risk = "High" if num_crimes >= 10 else ("Medium" if num_crimes >= 5 else "Low")
        
        # Connect only within the gang (1-3 associates)
        possible_associates = [r for r in my_gang if r != name]
        k = random.randint(1, min(3, len(possible_associates)))
        assoc = random.sample(possible_associates, k=k)
            
        records.append({
            "id": i + 1,
            "name": name,
            "associates": ", ".join(assoc),
            "crimes": num_crimes,
            "risk": risk
        })
        
    out_dir = Path("data/raw")
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / "Case_Dossier_Alpha.pdf"
    
    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    width, height = letter
    
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "CONFIDENTIAL - POLICE INTELLIGENCE DOSSIER")
    
    y = height - 100
    for rec in records:
        if y < 100:
            c.showPage()
            y = height - 50
            
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, f"Offender ID: {rec['id']}")
        c.setFont("Helvetica", 11)
        # Note: Must use exactly 'Accused: ' or 'Arrested: ' for regex to match
        c.drawString(50, y - 15, f"Accused: {rec['name']}")
        c.drawString(50, y - 30, f"Total Crimes: {rec['crimes']}")
        c.drawString(50, y - 45, f"Risk Level: {rec['risk']}")
        c.drawString(50, y - 60, f"Associates: {rec['associates']}")
        
        y -= 90
        
    c.save()
    print(f"Intelligence Report generated at: {pdf_path}")

if __name__ == "__main__":
    generate_pdf()
