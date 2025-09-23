#!/usr/bin/env python3
import json
import csv
import statistics
from datetime import datetime
from pathlib import Path

def analyze_locust_results():
    """Analyze Locust test results and generate performance report"""
    
    results_path = Path('load_tests/results/history')
    report_data = {
        'timestamp': datetime.now().isoformat(),
        'tests': {}
    }
    
    # Find latest CSV files
    for csv_file in results_path.glob('*_stats.csv'):
        test_name = csv_file.stem.replace('_stats', '')
        report_data['tests'][test_name] = analyze_single_test(csv_file)
    
    # Generate summary
    generate_summary_report(report_data)
    
    # Save detailed report
    with open('load_tests/results/reports/performance_report.json', 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print("Performance report generated successfully!")

def analyze_single_test(csv_file):
    """Analyze a single test CSV file"""
    data = {
        'request_count': 0,
        'failure_count': 0,
        'response_times': [],
        'throughput': 0
    }
    
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Name'] and row['Name'] != 'Total':
                    data['request_count'] += int(row['Request Count'])
                    data['failure_count'] += int(row['Failure Count'])
                    
                    if row['Average Response Time']:
                        data['response_times'].append(float(row['Average Response Time']))
                    
                    if row['Requests/s']:
                        data['throughput'] = max(data['throughput'], float(row['Requests/s']))
        
        # Calculate metrics
        data['failure_rate'] = data['failure_count'] / data['request_count'] if data['request_count'] > 0 else 0
        data['avg_response_time'] = statistics.mean(data['response_times']) if data['response_times'] else 0
        data['max_response_time'] = max(data['response_times']) if data['response_times'] else 0
        
    except Exception as e:
        print(f"Error analyzing {csv_file}: {e}")
    
    return data

def generate_summary_report(report_data):
    """Generate human-readable summary report"""
    
    print("=" * 80)
    print("PERFORMANCE TEST REPORT")
    print("=" * 80)
    print(f"Generated: {report_data['timestamp']}")
    print()
    
    for test_name, test_data in report_data['tests'].items():
        print(f"TEST: {test_name.upper()}")
        print("-" * 40)
        print(f"Total Requests: {test_data['request_count']:,}")
        print(f"Failures: {test_data['failure_count']} ({test_data['failure_rate']:.2%})")
        print(f"Average Response Time: {test_data['avg_response_time']:.2f}ms")
        print(f"Max Response Time: {test_data['max_response_time']:.2f}ms")
        print(f"Peak Throughput: {test_data['throughput']:.2f} req/s")
        
        # Recommendations
        recommendations = []
        if test_data['failure_rate'] > 0.05:
            recommendations.append("❌ High failure rate - investigate server stability")
        if test_data['avg_response_time'] > 1000:
            recommendations.append("⚠️  High response time - optimize performance")
        if test_data['throughput'] < 50:
            recommendations.append("⚠️  Low throughput - check database and external services")
        
        if recommendations:
            print("\nRECOMMENDATIONS:")
            for rec in recommendations:
                print(f"  {rec}")
        else:
            print("✅ All metrics within acceptable ranges")
        
        print()

if __name__ == '__main__':
    analyze_locust_results()