import os
import sys
import json
import subprocess

def generate_slots_for_faculty(faculty_id, start_date=None, days=14):
    """
    Subprocess Bridge:
    Delegates schedule period evaluation and slot creation to the PHP CLI script
    located at utils/generate_slots.php.
    """
    if not faculty_id:
        return 0

    base_dir = os.path.dirname(os.path.abspath(__file__))
    php_script = os.path.join(base_dir, "generate_slots.php")

    if not os.path.exists(php_script):
        print(f"[SlotGenerator Bridge Error] PHP worker script not found at {php_script}", file=sys.stderr)
        return 0

    command = ["php", php_script, str(faculty_id), str(days)]

    try:
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )

        output = proc.stdout.strip()
        data = json.loads(output)

        if data.get("status") == "success":
            return data.get("created_count", 0)
        else:
            print(f"[SlotGenerator PHP Error] {data.get('message')}", file=sys.stderr)
            return 0

    except subprocess.CalledProcessError as e:
        print(f"[SlotGenerator Bridge Error] Process returned non-zero code. Stderr: {e.stderr}", file=sys.stderr)
        return 0
    except json.JSONDecodeError:
        print(f"[SlotGenerator Bridge Error] Invalid JSON from PHP: {proc.stdout}", file=sys.stderr)
        return 0
    except Exception as ex:
        print(f"[SlotGenerator Bridge Error] Unexpected error: {ex}", file=sys.stderr)
        return 0