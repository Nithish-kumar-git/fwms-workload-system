import urllib.request, json
url = "https://fwms-workload-system-production.up.railway.app/api/reports/subject-summary"
try:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    resp = urllib.request.urlopen(req, timeout=15)
    data = json.loads(resp.read())
    print(f"Total records: {data.get('total', 'NO TOTAL FIELD')}")
    records = data.get('records', data if isinstance(data, list) else [])
    programs = set()
    for r in records:
        programs.add(r.get('program', r.get('program_name', 'UNKNOWN')))
    print(f"Programs in response: {sorted(programs)}")
    print(f"First 3 records:")
    for i, rec in enumerate(records[:3]):
        print(f"  {i+1}. {rec}")
except Exception as e:
    print(f"Error: {e}")
    print("Endpoint may require auth token")
