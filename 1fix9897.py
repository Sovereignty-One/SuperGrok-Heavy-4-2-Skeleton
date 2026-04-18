import os

def change_port(root_dir="."):
    for foldername, subfolders, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith(".py"):
                filepath = os.path.join(foldername, filename)
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if '9898' in content:
                    new_content = content.replace('9898', '9897')
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
                    print(f"Fixed: {filepath}")

print("Starting port change 9898 → 9897 in all .py files...")
change_port()
print("Done!") 
