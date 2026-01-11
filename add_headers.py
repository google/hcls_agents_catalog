import os

# --- CONFIGURATION ---
COPYRIGHT_HOLDER = "Google LLC"
YEAR = "2026"

LICENSE_HEADER = f"""# Copyright {YEAR} {COPYRIGHT_HOLDER}
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""

def add_license_to_file(filepath):
    with open(filepath, 'r') as f:
        content = f.readlines()

    # Skip if the file is empty
    if not content:
        content = [LICENSE_HEADER]
    # Check if license already exists
    elif any("Licensed under the Apache License" in line for line in content[:15]):
        print(f"Skipping: {filepath} (Header already exists)")
        return
    else:
        # Handle Shell Script Shebangs
        if content[0].startswith("#!"):
            content.insert(1, "\n" + LICENSE_HEADER + "\n")
        else:
            content.insert(0, LICENSE_HEADER + "\n")

    with open(filepath, 'w') as f:
        f.writelines(content)
    print(f"Updated: {filepath}")

def main():
    # Targets the specific directories mentioned in your error log
    targets = ['./rxnorm'] 
    
    for target in targets:
        for root, _, files in os.walk(target):
            for file in files:
                if file.endswith(('.py', '.sh')):
                    add_license_to_file(os.path.join(root, file))

if __name__ == "__main__":
    main()