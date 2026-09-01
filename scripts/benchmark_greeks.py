import time
import numpy as np
from py_vollib.black_scholes import black_scholes
from py_vollib.black_scholes.greeks.analytical import delta, vega, gamma

# Constants
S = 100000.0  # Spot
K = 100000.0  # Strike
T = 0.5       # Time (6 months)
r = 0.05      # Risk-free rate
sigma = 0.5   # Volatility

def benchmark_single():
    print("--- Single Option Benchmark ---")
    start = time.time()
    ITERATIONS = 1000
    
    for _ in range(ITERATIONS):
        p = black_scholes('c', S, K, T, r, sigma)
        d = delta('c', S, K, T, r, sigma)
        v = vega('c', S, K, T, r, sigma)
        g = gamma('c', S, K, T, r, sigma)
        
    end = time.time()
    total_time = end - start
    per_op = (total_time / ITERATIONS) * 1000  # ms
    print(f"Time for {ITERATIONS} cycles: {total_time:.4f}s")
    print(f"Per Option (Price+Greeks): {per_op:.4f} ms")
    print(f"Throughput: {ITERATIONS / total_time:.0f} options/sec")

if __name__ == "__main__":
    benchmark_single()
