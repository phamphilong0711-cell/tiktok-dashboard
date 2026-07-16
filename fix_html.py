import os

if os.path.exists('templates/index.html'):
    with open('templates/index.html', 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Xoá jinja2 url_for
    content = content.replace("{{ url_for('static', filename='style.css') }}", "static/style.css")
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    os.remove('templates/index.html')
    print("Moved index.html and replaced Jinja2 syntax.")
else:
    print("templates/index.html not found.")
