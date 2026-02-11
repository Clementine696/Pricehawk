"""Fix database connection patterns in main.py"""

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# List of functions to fix (starting line numbers from grep output)
fixes = [
    (3967, 'get_available_groups'),
    (3996, 'get_monitored_groups'),
    (4023, 'set_monitored_groups'),
    (4052, 'get_monitored_locations'),
    (4080, 'set_monitored_locations'),
    (4113, 'get_location_prices'),
    (4176, 'export_location_prices'),
]

# Read lines
lines = content.split('\n')

# Fix each function
for start_line, func_name in fixes:
    idx = start_line - 1  # Convert to 0-indexed

    # Find the function
    while idx < len(lines):
        line = lines[idx]

        # Find "conn = get_db()"
        if 'conn = get_db()' in line and '=' in line:
            indent = ' ' * (len(line) - len(line.lstrip()))

            # Add import if needed
            if idx > 0 and 'from psycopg2.extras import RealDictCursor' not in lines[idx-1]:
                lines.insert(idx, f'{indent}from psycopg2.extras import RealDictCursor\n')
                idx += 1

            # Replace line
            lines[idx] = f'{indent}with get_db() as conn:'

            # Find and fix cursor line
            idx += 1
            if idx < len(lines) and 'cursor = conn.cursor' in lines[idx]:
                cursor_indent = ' ' * (len(lines[idx]) - len(lines[idx].lstrip()))
                lines[idx] = f'{cursor_indent}    cursor = conn.cursor(cursor_factory=RealDictCursor)'

            # Find and remove try: line
            idx += 1
            if idx < len(lines) and lines[idx].strip() == 'try:':
                del lines[idx]

            # Find and remove finally block
            finally_found = False
            while idx < len(lines):
                if 'finally:' in lines[idx]:
                    finally_found = True
                    # Remove finally line
                    del lines[idx]
                    # Remove cursor.close() and conn.close()
                    while idx < len(lines) and ('cursor.close()' in lines[idx] or 'conn.close()' in lines[idx]):
                        del lines[idx]
                    break

                # Dedent content (remove 4 spaces from try block)
                if finally_found == False and lines[idx].strip():
                    spaces = len(lines[idx]) - len(lines[idx].lstrip())
                    if spaces >= len(indent) + 8:
                        lines[idx] = ' ' * (spaces - 4) + lines[idx].lstrip()

                idx += 1
            break

        idx += 1
        # Stop if we hit the next function
        if idx < len(lines) and lines[idx].startswith('@app.'):
            break

# Write back
with open('main.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print("Fixed all connection patterns")
