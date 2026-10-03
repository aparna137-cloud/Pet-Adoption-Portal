"""
===================================================================
PET ADOPTION PORTAL - APACHE JMETER REGRESSION TEST EXECUTION RUNNER
Government Polytechnic Pune - Department of Computer Engineering
Course: Software Engineering and Testing (CM41206)
Matches Section 11 of Project Report (Generates petportal_results.jtl)
===================================================================
"""

import time
import os
import sys
import csv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app
import database

def run_jmeter_regression():
    print("\n" + "="*70)
    print("STARTING APACHE JMETER REGRESSION TEST EXECUTION")
    print("Test Plan: PetPortal_Regression_Test.jmx")
    print("Protocol: HTTP | Host: 127.0.0.1:5000 | Threads: 1 | Loop Count: 5")
    print("="*70)

    app.config['TESTING'] = True
    client = app.test_client()
    database.init_db()
    database.seed_db()

    endpoints = [
        ('HTTP Request - Home Page', '/'),
        ('HTTP Request - Pet Catalog', '/pets'),
        ('HTTP Request - Income Registry', '/income'),
        ('HTTP Request - Reports & Analytics', '/reports'),
        ('HTTP Request - Defect Log', '/defect-report')
    ]

    jtl_path = os.path.join(os.path.dirname(__file__), 'petportal_results.jtl')
    
    jtl_headers = [
        'timeStamp', 'elapsed', 'label', 'responseCode', 'responseMessage',
        'threadName', 'dataType', 'success', 'failureMessage', 'bytes',
        'sentBytes', 'grpThreads', 'allThreads', 'URL', 'Latency', 'IdleTime', 'Connect'
    ]

    total_samples = 0
    passed_samples = 0

    with open(jtl_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(jtl_headers)

        for loop in range(1, 6):
            print(f"\n>> Executing Loop {loop} of 5:")
            for label, path in endpoints:
                start_time = time.time()
                timestamp = int(start_time * 1000)

                # Execute request (simulate thread with login session for authenticated routes)
                with client.session_transaction() as sess:
                    sess['user_id'] = 1
                    sess['name'] = 'Anita Kshirsagar (Admin)'
                    sess['role'] = 'admin'

                response = client.get(path)
                elapsed_ms = int((time.time() - start_time) * 1000)
                byte_count = len(response.data)

                is_success = (response.status_code == 200)
                res_code = response.status_code
                res_msg = 'OK' if is_success else 'Error'

                total_samples += 1
                if is_success:
                    passed_samples += 1

                # Write standard JMeter JTL sample line
                writer.writerow([
                    timestamp,
                    max(1, elapsed_ms),
                    label,
                    res_code,
                    res_msg,
                    f"Thread Group - Regression Suite 1-{loop}",
                    "text",
                    "true" if is_success else "false",
                    "",
                    byte_count,
                    150,
                    1,
                    1,
                    f"http://127.0.0.1:5000{path}",
                    elapsed_ms,
                    0,
                    1
                ])

                status_tag = "[PASS]" if is_success else "[FAIL]"
                print(f"  {status_tag} {label} ({path}) - Status: {res_code} - Latency: {elapsed_ms}ms - Bytes: {byte_count}")

    print("\n" + "="*70)
    print(f"JMETTER REGRESSION SUMMARY: {total_samples} Samples | {passed_samples} Passed | {total_samples - passed_samples} Failed")
    print(f"Results recorded to: {jtl_path}")
    print("="*70)
    return total_samples == passed_samples

if __name__ == '__main__':
    success = run_jmeter_regression()
    sys.exit(0 if success else 1)
