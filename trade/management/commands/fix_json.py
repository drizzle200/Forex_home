import json

# Read the file with utf-8-sig (handles BOM)
with open('trades.json', 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Parse JSON
data = json.loads(content)

# Write back without BOM
with open('trades_fixed.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)

print(f"Fixed {len(data)} trades saved to trades_fixed.json")
print(f"First trade target: {data[0].get('target', 'MISSING')}")