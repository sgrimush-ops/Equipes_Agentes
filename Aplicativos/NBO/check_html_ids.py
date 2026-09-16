import os
import re
import sys

def check():
    sys.stdout.reconfigure(encoding='utf-8')
    base_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(base_dir, 'dashboard_nbo.html')
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    html_ids = set(re.findall(r'id=[\'"]([a-zA-Z0-9_\-]+)[\'"]', html))
    js_ids = set(re.findall(r'document\.getElementById\([\'"]([a-zA-Z0-9_\-]+)[\'"]\)', html))
    
    print(f"Total HTML IDs defined: {len(html_ids)}")
    print(f"Total JS IDs queried: {len(js_ids)}")
    
    missing = js_ids - html_ids
    if missing:
        print("Missing IDs:")
        for m in missing:
            print(" -", m)
    else:
        print("All JS referenced IDs exist in HTML!")

if __name__ == '__main__':
    check()
