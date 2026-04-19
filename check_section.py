import urllib.request, json

base = 'https://fwms-workload-system-production.up.railway.app/api/reports'

def get(path):
    req = urllib.request.Request(base+path, headers={'Accept':'application/json'})
    resp = urllib.request.urlopen(req, timeout=30)
    return json.loads(resp.read())

data = get('/admin/section-check/MCT48')
print('=== STAFF ===')
print(json.dumps(data['staff'], indent=2))
print('\n=== ALL SECTIONS ===')
print(json.dumps(data['all_sections'], indent=2))
print('\n=== SECTION B EXISTS ===')
print(json.dumps(data['section_b_exists'], indent=2))
print('\n=== MCA GENERAL SEM II OFFERINGS (all sections) ===')
for o in data.get('mca_general_sem2_offerings', []):
    print(f"  Sec:{o['sec_name']}/{o['sec_label']} | {o['code']} | shift={o['shift']} | active={o['is_active']}")
print(f"\n  Total: {len(data.get('mca_general_sem2_offerings', []))}")
print('\n=== MCA GENERAL SEC B OFFERINGS ===')
for o in data.get('mca_general_sec_b_offerings', []):
    print(f"  Sem:{o['sem_name']} | {o['code']} | shift={o['shift']} | active={o['is_active']}")
print(f"\n  Total: {len(data.get('mca_general_sec_b_offerings', []))}")
