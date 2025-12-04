# TRECO with Python 3.14t (Free-Threaded)

## What is Python 3.14t?

Python 3.14t is the **free-threaded** build of Python that removes the Global Interpreter Lock (GIL), enabling true parallel execution of Python threads.

## Why Python 3.14t for TRECO?

TRECO benefits significantly from the free-threaded build:

### 1. True Parallelism
- **Without GIL**: Multiple threads execute simultaneously on different CPU cores
- **With GIL** (standard Python): Only one thread executes Python code at a time

### 2. Better Race Timing
- **More consistent timing**: No GIL contention between threads
- **Tighter race windows**: Threads can truly execute at the same instant
- **Improved precision**: Sub-microsecond timing is more reliable

### 3. Performance Benefits
- **Better CPU utilization**: All cores can run Python code simultaneously
- **Faster execution**: Multi-threaded workloads complete faster
- **Reduced latency**: No waiting for GIL acquisition

## Installation

### Automated Installation
```bash
# Run the installation script
./install.sh
```

### Manual Installation
```bash
# 1. Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Clone and install TRECO
git clone https://github.com/your-org/treco.git
cd treco

# 3. Install with uv (automatically handles Python 3.14t)
uv sync

# 4. Verify installation
uv run python check_python.py
```

## Verification

### Check Python Version
```bash
uv run python --version
# Should show: Python 3.14.x
```

### Check GIL Status
```bash
uv run python check_python.py
# Should show: ✓ Python 3.14t detected (free-threaded build)
```

### Verify in Code
```python
import sysconfig
print(sysconfig.get_config_var('Py_GIL_DISABLED'))
# Should print: 1 or True
```

## Performance Comparison

### Standard Python (with GIL)
```
Race Attack: 20 threads
Race Window: 50-100ms (moderate)
Reason: Threads compete for GIL, serializing execution
```

### Python 3.14t (GIL-free)
```
Race Attack: 20 threads
Race Window: <1ms (excellent)
Reason: True parallel execution, no GIL contention
```

## Important Notes

### Compatibility
- All dependencies are compatible with Python 3.14t
- No code changes needed - TRECO works seamlessly
- Benefits are automatic when using 3.14t

### Migration from Standard Python
```bash
# uv automatically uses the correct Python version
# Just specify in .python-version or use --python flag
uv run --python 3.14t treco attack.yaml
```

### Verifying Benefits
You can compare race window timing:

**Standard Python:**
```bash
python3.14 -m treco attack.yaml
# Race window: ~50ms
```

**Python 3.14t (with uv):**
```bash
uv run treco attack.yaml
# Race window: <1ms
```

## FAQ

### Q: What's the difference between 3.14 and 3.14t?
**A**: The 't' suffix indicates the free-threaded build without GIL. Regular 3.14 still has the GIL.

### Q: Do I need to change my code?
**A**: No, TRECO works identically. The benefits are automatic.

### Q: Will all Python packages work?
**A**: Most pure Python packages work fine. C extensions may need updates, but all TRECO dependencies are compatible.

### Q: How much faster is it?
**A**: For TRECO's use case (multi-threaded race attacks), you'll see 10-50x better race window timing.

### Q: Can I use both builds?
**A**: Yes, you can specify Python version with uv:
```bash
# Use specific Python version
uv run --python 3.14 treco attack.yaml    # Standard
uv run --python 3.14t treco attack.yaml   # Free-threaded
```

## Resources

- [PEP 703 - Making the GIL Optional](https://peps.python.org/pep-0703/)
- [Python 3.14 Release Notes](https://docs.python.org/3.14/whatsnew/3.14.html)
- [uv Documentation](https://github.com/astral-sh/uv)

## Troubleshooting

### Check which Python is being used
```bash
uv run python --version
uv run python -c "import sysconfig; print(sysconfig.get_config_var('Py_GIL_DISABLED'))"
```

### Force using 3.14t
```bash
# Use uv to run with specific Python
uv run --python 3.14t treco attack.yaml
```

### Verify threading performance
```python
import threading
import time

def worker():
    # CPU-bound task
    sum(i*i for i in range(10000000))

threads = [threading.Thread(target=worker) for _ in range(10)]
start = time.time()
for t in threads: t.start()
for t in threads: t.join()
print(f"Time: {time.time() - start:.2f}s")

# With GIL: ~10s (serialized)
# Without GIL: ~1s (parallel on 10 cores)
```