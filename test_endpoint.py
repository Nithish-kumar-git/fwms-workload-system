import urllib.request, json

base = 'https://fwms-workload-system-production.up.railway.app/api/reports'

def get(path):
    try:
        req = urllib.request.Request(base+path, headers={'Accept':'application/json'})
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        print(f"Response body: {e.read().decode('utf-8')}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

# Test the endpoint
print("Testing /admin/section-check/MCT48...")
data = get('/admin/section-check/MCT48')
if data:
    print(json.dumps(data, indent=2))
