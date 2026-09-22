"""
MIT-WPU FixLink - Admin SLA Escalation Background Monitor (The Anti-Stagnation Protocol)

Monitors the timestamp of all Pending faculty schedule submissions.
If any department batch remains in the "Pending" state for >48 hours:
- Identifies the stale batch
- Logs an SLA violation alert
- Dispatches an automated email ping to the responsible Department Head
- Notifies Super Admins on the dashboard

Usage:
    python scripts/monitor_sla_escalation.py
    python scripts/monitor_sla_escalation.py --dry-run
"""
import sys
import os
import argparse
from datetime import datetime

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Ensure utf-8 stdout for Windows consoles
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from app import create_app, db
from app.sla_service import get_pending_batches_sla_status, trigger_department_sla_escalation

def run_sla_monitor(dry_run=False):
    app = create_app()
    with app.app_context():
        print("=" * 70)
        print("[SLA MONITOR] FIXLINK ANTI-STAGNATION PROTOCOL: ADMIN SLA MONITOR")
        print(f"Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print("=" * 70)
        
        status = get_pending_batches_sla_status()
        batches = status['batches']
        
        if not batches:
            print("[OK] All clear. No pending schedule submissions in the queue.")
            return 0
            
        print(f"[INFO] Evaluated {len(batches)} department batch(es) across university.")
        print(f"[STATUS] Stale Batches (>48h): {status['stale_batches_count']}")
        print(f"[STATUS] Total Queued Hours in Stale Batches: {status['total_stale_hours']} hrs\n")
        
        for batch in batches:
            dept = batch['department_name']
            subs_count = batch['submission_count']
            hours = batch['total_hours']
            elapsed = batch['elapsed_hours']
            overdue = batch['hours_overdue']
            head_email = batch['head_email']
            
            if batch['is_stale']:
                print(f"[SLA BREACH - {dept}]")
                print(f"   |-- Pending Faculty Submissions: {subs_count}")
                print(f"   |-- Queued Lecture Hours: {hours} hrs")
                print(f"   |-- Pending Duration: {elapsed} hours ({overdue}h past 48h SLA limit)")
                print(f"   |-- Responsible HOD: {batch['head_name']} <{head_email}>")
                
                if dry_run:
                    print("   +-- [DRY RUN] Escalation email simulation only. No email sent.")
                else:
                    result = trigger_department_sla_escalation(dept)
                    if result['success']:
                        print(f"   +-- [SENT] Escalation email successfully dispatched to {head_email}!")
                    else:
                        print(f"   +-- [FAILED] Failed to dispatch escalation email: {result.get('message')}")
            else:
                print(f"[WITHIN SLA - {dept}]")
                print(f"   |-- Pending Submissions: {subs_count} ({hours} hrs)")
                print(f"   +-- Pending Duration: {elapsed}h / 48.0h threshold")
                
            print("-" * 70)
            
        return status['stale_batches_count']

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="FixLink SLA Anti-Stagnation Monitor")
    parser.add_argument('--dry-run', action='store_true', help="Run evaluation without sending emails")
    args = parser.parse_args()
    
    sys.exit(0 if run_sla_monitor(dry_run=args.dry_run) >= 0 else 1)

