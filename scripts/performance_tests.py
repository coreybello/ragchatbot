"""
Comprehensive performance testing suite for RAG Demo
Tests API endpoints, database performance, and system load
"""
import asyncio
import aiohttp
import time
import json
import statistics
import psutil
import logging
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.performance_optimizer import get_system_metrics
from backend.models.database import SessionLocal, Query
from backend.core.config import get_settings

logger = logging.getLogger(__name__)

class PerformanceTester:
    """Comprehensive performance testing suite"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.settings = get_settings()
        self.results = {}
        
    async def test_api_endpoint_performance(self, endpoint: str, method: str = "GET", 
                                          data: Dict = None, iterations: int = 10) -> Dict:
        """Test individual API endpoint performance"""
        print(f"🧪 Testing {method} {endpoint} ({iterations} iterations)")
        
        times = []
        errors = 0
        status_codes = []
        
        async with aiohttp.ClientSession() as session:
            for i in range(iterations):
                try:
                    start_time = time.time()
                    
                    if method.upper() == "POST":
                        async with session.post(f"{self.base_url}{endpoint}", 
                                              json=data,
                                              headers={"Content-Type": "application/json"}) as response:
                            await response.text()
                            status_codes.append(response.status)
                    else:
                        async with session.get(f"{self.base_url}{endpoint}") as response:
                            await response.text()
                            status_codes.append(response.status)
                    
                    end_time = time.time()
                    times.append(end_time - start_time)
                    
                except Exception as e:
                    errors += 1
                    logger.error(f"Request {i} failed: {e}")
                
                # Small delay between requests
                await asyncio.sleep(0.1)
        
        if times:
            return {
                'endpoint': endpoint,
                'method': method,
                'iterations': iterations,
                'success_rate': (iterations - errors) / iterations * 100,
                'avg_response_time_ms': round(statistics.mean(times) * 1000, 2),
                'min_response_time_ms': round(min(times) * 1000, 2),
                'max_response_time_ms': round(max(times) * 1000, 2),
                'median_response_time_ms': round(statistics.median(times) * 1000, 2),
                'std_dev_ms': round(statistics.stdev(times) * 1000, 2) if len(times) > 1 else 0,
                'p95_response_time_ms': round(statistics.quantiles(times, n=20)[18] * 1000, 2) if len(times) > 10 else max(times) * 1000,
                'status_codes': list(set(status_codes)),
                'errors': errors
            }
        else:
            return {'endpoint': endpoint, 'error': 'All requests failed'}
    
    async def test_chat_performance(self, concurrent_users: int = 5, 
                                   queries_per_user: int = 3) -> Dict:
        """Test chat endpoint with concurrent users"""
        print(f"💬 Testing chat performance: {concurrent_users} users, {queries_per_user} queries each")
        
        test_queries = [
            "What is the main topic of the documentation?",
            "How do I configure the system?",
            "What are the performance requirements?",
            "How do I troubleshoot common issues?",
            "What security measures are implemented?"
        ]
        
        async def user_session(user_id: int):
            """Simulate a user session"""
            user_results = []
            
            async with aiohttp.ClientSession() as session:
                for query_num in range(queries_per_user):
                    query = test_queries[query_num % len(test_queries)]
                    
                    try:
                        start_time = time.time()
                        
                        async with session.post(
                            f"{self.base_url}/api/chat",
                            json={"query": f"[User {user_id}] {query}"},
                            headers={"Content-Type": "application/json"}
                        ) as response:
                            
                            if response.status == 200:
                                # Read streaming response
                                full_response = ""
                                async for line in response.content:
                                    line_text = line.decode('utf-8')
                                    if line_text.startswith('data: '):
                                        try:
                                            data = json.loads(line_text[6:])
                                            if data.get('type') == 'content':
                                                full_response += data.get('content', '')
                                        except:
                                            pass
                                
                                end_time = time.time()
                                response_time = end_time - start_time
                                
                                user_results.append({
                                    'user_id': user_id,
                                    'query_num': query_num,
                                    'response_time': response_time,
                                    'response_length': len(full_response),
                                    'success': True
                                })
                            else:
                                user_results.append({
                                    'user_id': user_id,
                                    'query_num': query_num,
                                    'success': False,
                                    'status_code': response.status
                                })
                        
                    except Exception as e:
                        user_results.append({
                            'user_id': user_id,
                            'query_num': query_num,
                            'success': False,
                            'error': str(e)
                        })
                    
                    # Wait between queries
                    await asyncio.sleep(1)
            
            return user_results
        
        # Run concurrent user sessions
        start_time = time.time()
        tasks = [user_session(i) for i in range(concurrent_users)]
        all_results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # Analyze results
        successful_queries = []
        failed_queries = []
        
        for user_results in all_results:
            if isinstance(user_results, list):
                for result in user_results:
                    if result.get('success'):
                        successful_queries.append(result)
                    else:
                        failed_queries.append(result)
        
        if successful_queries:
            response_times = [r['response_time'] for r in successful_queries]
            
            return {
                'concurrent_users': concurrent_users,
                'queries_per_user': queries_per_user,
                'total_queries': len(successful_queries) + len(failed_queries),
                'successful_queries': len(successful_queries),
                'failed_queries': len(failed_queries),
                'success_rate': len(successful_queries) / (len(successful_queries) + len(failed_queries)) * 100,
                'total_test_time_s': round(total_time, 2),
                'avg_response_time_s': round(statistics.mean(response_times), 2),
                'min_response_time_s': round(min(response_times), 2),
                'max_response_time_s': round(max(response_times), 2),
                'p95_response_time_s': round(statistics.quantiles(response_times, n=20)[18], 2) if len(response_times) > 10 else max(response_times),
                'queries_per_second': round(len(successful_queries) / total_time, 2)
            }
        else:
            return {'error': 'No successful queries completed'}
    
    def test_database_performance(self) -> Dict:
        """Test database query performance"""
        print("🗃️ Testing database performance")
        
        db = SessionLocal()
        results = {}
        
        try:
            # Test query performance
            queries = [
                ("simple_select", "SELECT COUNT(*) FROM queries"),
                ("recent_queries", "SELECT * FROM queries ORDER BY timestamp DESC LIMIT 10"),
                ("rated_queries", "SELECT * FROM queries WHERE rating IS NOT NULL LIMIT 10"),
                ("date_range", "SELECT * FROM queries WHERE timestamp > ? LIMIT 100"),
                ("complex_join", """
                    SELECT q.id, q.query, q.rating, q.response_time_ms 
                    FROM queries q 
                    WHERE q.timestamp > ? 
                    ORDER BY q.response_time_ms DESC 
                    LIMIT 50
                """)
            ]
            
            for query_name, sql in queries:
                times = []
                for _ in range(10):  # Run each query 10 times
                    start_time = time.time()
                    
                    if "?" in sql:
                        # Query with parameter
                        yesterday = int(time.time() * 1000) - (24 * 60 * 60 * 1000)
                        db.execute(sql, (yesterday,))
                    else:
                        db.execute(sql)
                    
                    end_time = time.time()
                    times.append(end_time - start_time)
                
                results[query_name] = {
                    'avg_time_ms': round(statistics.mean(times) * 1000, 2),
                    'min_time_ms': round(min(times) * 1000, 2),
                    'max_time_ms': round(max(times) * 1000, 2)
                }
            
            # Test connection overhead
            connection_times = []
            for _ in range(20):
                start_time = time.time()
                test_db = SessionLocal()
                test_db.execute("SELECT 1")
                test_db.close()
                end_time = time.time()
                connection_times.append(end_time - start_time)
            
            results['connection_overhead'] = {
                'avg_time_ms': round(statistics.mean(connection_times) * 1000, 2),
                'min_time_ms': round(min(connection_times) * 1000, 2),
                'max_time_ms': round(max(connection_times) * 1000, 2)
            }
            
        finally:
            db.close()
        
        return results
    
    def test_system_resources(self, duration_seconds: int = 60) -> Dict:
        """Monitor system resources during operation"""
        print(f"📊 Monitoring system resources for {duration_seconds} seconds")
        
        measurements = []
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds:
            measurement = {
                'timestamp': time.time(),
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_io': psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {},
                'network_io': psutil.net_io_counters()._asdict() if psutil.net_io_counters() else {}
            }
            measurements.append(measurement)
            time.sleep(1)
        
        # Calculate averages
        cpu_values = [m['cpu_percent'] for m in measurements]
        memory_values = [m['memory_percent'] for m in measurements]
        
        return {
            'duration_seconds': duration_seconds,
            'measurements_count': len(measurements),
            'avg_cpu_percent': round(statistics.mean(cpu_values), 2),
            'max_cpu_percent': round(max(cpu_values), 2),
            'avg_memory_percent': round(statistics.mean(memory_values), 2),
            'max_memory_percent': round(max(memory_values), 2),
            'detailed_measurements': measurements[-10:]  # Last 10 measurements
        }
    
    async def run_comprehensive_test(self) -> Dict:
        """Run all performance tests"""
        print("🚀 Starting comprehensive performance test suite")
        
        start_time = time.time()
        
        # Test individual endpoints
        print("\n📡 Testing API endpoints...")
        endpoint_tests = [
            ("/", "GET"),
            ("/health", "GET"),
            ("/api/chat", "POST", {"query": "Test query for performance testing"}),
        ]
        
        self.results['endpoints'] = {}
        for endpoint_test in endpoint_tests:
            endpoint = endpoint_test[0]
            method = endpoint_test[1]
            data = endpoint_test[2] if len(endpoint_test) > 2 else None
            
            result = await self.test_api_endpoint_performance(endpoint, method, data, 10)
            self.results['endpoints'][f"{method}_{endpoint.replace('/', '_')}"] = result
        
        # Test chat performance with concurrent users
        print("\n💬 Testing chat with concurrent users...")
        self.results['chat_load_test'] = await self.test_chat_performance(
            concurrent_users=3, 
            queries_per_user=2
        )
        
        # Test database performance
        print("\n🗃️ Testing database performance...")
        self.results['database'] = self.test_database_performance()
        
        # Test system resources
        print("\n📊 Monitoring system resources...")
        self.results['system_resources'] = self.test_system_resources(30)
        
        # Get system metrics
        self.results['system_metrics'] = get_system_metrics()
        
        total_time = time.time() - start_time
        self.results['test_summary'] = {
            'total_test_time_s': round(total_time, 2),
            'timestamp': datetime.now().isoformat(),
            'test_type': 'comprehensive_performance_test'
        }
        
        print(f"\n✅ Performance testing completed in {total_time:.2f} seconds")
        return self.results
    
    def generate_report(self, output_file: str = "performance_report.json"):
        """Generate detailed performance report"""
        if not self.results:
            print("❌ No test results available. Run tests first.")
            return
        
        # Save JSON report
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"📄 Performance report saved to {output_file}")
        
        # Print summary
        print("\n📊 PERFORMANCE SUMMARY")
        print("=" * 50)
        
        if 'endpoints' in self.results:
            print("\n🔗 API Endpoints:")
            for endpoint, data in self.results['endpoints'].items():
                if 'avg_response_time_ms' in data:
                    print(f"  {endpoint}: {data['avg_response_time_ms']}ms avg, {data['success_rate']}% success")
        
        if 'chat_load_test' in self.results:
            chat_data = self.results['chat_load_test']
            if 'avg_response_time_s' in chat_data:
                print(f"\n💬 Chat Load Test:")
                print(f"  {chat_data['concurrent_users']} users, {chat_data['success_rate']:.1f}% success")
                print(f"  Avg response: {chat_data['avg_response_time_s']}s")
                print(f"  Throughput: {chat_data['queries_per_second']} queries/sec")
        
        if 'database' in self.results:
            print(f"\n🗃️ Database Performance:")
            for query_type, data in self.results['database'].items():
                print(f"  {query_type}: {data['avg_time_ms']}ms avg")
        
        if 'system_resources' in self.results:
            sys_data = self.results['system_resources']
            print(f"\n📊 System Resources:")
            print(f"  CPU: {sys_data['avg_cpu_percent']}% avg, {sys_data['max_cpu_percent']}% max")
            print(f"  Memory: {sys_data['avg_memory_percent']}% avg, {sys_data['max_memory_percent']}% max")

async def main():
    """Run performance tests"""
    tester = PerformanceTester()
    
    try:
        results = await tester.run_comprehensive_test()
        tester.generate_report("performance_test_results.json")
    except KeyboardInterrupt:
        print("\n⏹️ Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Testing failed: {e}")
        logger.exception("Performance testing failed")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())