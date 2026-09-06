import re

with open('trac_jobs_sample.html', 'r', encoding='utf-8') as f:
    text = f.read()

print("File size:", len(text))

# Prior attempt used 'job-result'
blocks = text.split('job-result')
print(f"Found {len(blocks)} job-result blocks")

if len(blocks) == 1:
    # Try another split, looking for job links
    matches = re.findall(r'<a[^>]+href="(/job/[^"]+)"[^>]*>(.*?)</a>', text, re.IGNORECASE)
    print(f"Found {len(matches)} job link matches")
    for m in matches[:5]: 
        print(m)

    # Let's also look for employer
    employers = re.findall(r'employer[^>]*>(.*?)<', text, re.IGNORECASE)
    print(f"Found {len(employers)} employer matches")
    for e in employers[:5]:
        print(e)
