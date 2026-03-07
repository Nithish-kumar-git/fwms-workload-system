import requests, sys

r = requests.post("http://localhost:8000/api/auth/dev-login")
print(f"Login: {r.status_code}")
if r.status_code != 200:
    print(r.text); sys.exit(1)

t = r.json()["token"]
r2 = requests.post(
    "http://localhost:8000/api/allocation/run",
    headers={"Authorization": f"Bearer {t}"}
)
print(f"Allocation status: {r2.status_code}")
if r2.status_code == 200:
    d = r2.json()
    print(f"SUCCESS")
    print(f"  subjects_total:       {d.get('subjects_total')}")
    print(f"  subjects_assigned:    {d.get('subjects_assigned')}")
    print(f"  subjects_unassigned:  {d.get('subjects_unassigned')}")
    print(f"  faculty_balanced:     {d.get('faculty_balanced')}")
    print(f"  faculty_overloaded:   {d.get('faculty_overloaded')}")
    print(f"  faculty_underloaded:  {d.get('faculty_underloaded')}")
else:
    try:
        print(f"Error: {r2.json().get('detail', r2.text)}")
    except Exception:
        print(f"Raw: {r2.text}")
