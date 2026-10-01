"""Run all local audits after acquiring the pinned inputs; no inference calls."""
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
for script in ('audit.py','independent_audit.py','extension_audit.py','verify_accounting.py','plot_results.py'):
    subprocess.run([sys.executable,str(ROOT/script)],cwd=ROOT,check=True)
print('All audits, checks, and figure generation completed.')
