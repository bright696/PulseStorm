PulseStorm

High-performance asynchronous HTTP load (DDOS) testing utility

PulseStorm is a powerful, async-based HTTP stress testing tool designed for authorized security testing and server load analysis.

⚠️ Legal Disclaimer

WARNING: This tool is intended for authorized testing only. 

- Use only on systems you own or have explicit written permission to test
- Unauthorized access to computer systems is illegal
- The author (brigt696) assumes no liability for misuse

Features:

Asynchronous Architecture - Built on Python's asyncio for maximum performance
Smart Targeting- Multiple endpoint rotation for cache bypass
User-Agent Rotation - Randomized browser fingerprints
Real-time Metrics - Live RPS monitoring
Adjustable Intensity - 5 preset levels (50 to 5000+ concurrency)

📋 Requirements

- Python 3.9+
- aiohttp library

 Installation:

git clone https://github.com/brigtw696/pulsestorm.git
cd pulsestorm
pip install -r requirements.txt
python pulsestorm.py
Follow the interactive prompts to enter target URL, select concurrency level, and duration.

Performance Tips:
Start with LOW (50) concurrency for initial testing
Each concurrency level uses ~10MB RAM
Ensure sufficient bandwidth for high concurrency tests

License:
MIT License - see LICENSE file for details.
