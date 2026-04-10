import urllib.request, json
import time

# Wait for deployment
print("Waiting 30 seconds for Railway deployment...")
time.sleep(30)

url = "https://fwms-workload-system-production.up.railway.app/api/reports/debug-offerings"
try:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    resp = urllib.request.urlopen(req, timeout=15)
    data = json.loads(resp.read())
    
    print("\n=== OPEN CYCLES ===")
    for cycle in data.get('open_cycles', []):
        print(f"  Cycle {cycle['id']}: semester_id={cycle['semester_id']}, status={cycle['status']}, academic_year_id={cycle['academic_year_id']}")
    
    print("\n=== OFFERINGS BY PROGRAM/SEMESTER ===")
    offerings = data.get('offerings_by_program_semester', [])
    
    # Filter for MCA programs
    mca_offerings = [o for o in offerings if 'MCA' in o['program'].upper()]
    
    print(f"\nTotal programs: {len(set(o['program'] for o in offerings))}")
    print(f"MCA programs found: {len(set(o['program'] for o in mca_offerings))}")
    
    print("\nMCA Offerings:")
    for o in mca_offerings:
        print(f"  {o['program']} - Sem {o['semester']}: {o['count']} offerings, active={o['all_active']}, year_ids={o['academic_year_ids']}")
    
    print("\nAll Programs:")
    for prog in sorted(set(o['program'] for o in offerings)):
        print(f"  - {prog}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
