#!/usr/bin/env bash
set -e

# Detect python executable
if command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
elif command -v python.exe >/dev/null 2>&1; then
    PYTHON_CMD="python.exe"
elif command -v py >/dev/null 2>&1; then
    PYTHON_CMD="py"
elif command -v py.exe >/dev/null 2>&1; then
    PYTHON_CMD="py.exe"
else
    echo "Error: Python executable not found" >&2
    exit 1
fi

# Detect C++ deglib directory in Windows or WSL paths
DEG_CPP_DIR=""
if [ -d "C:/Lang/cpp/DynamicExplorationGraph/python" ]; then
    DEG_CPP_DIR="C:/Lang/cpp/DynamicExplorationGraph/python"
elif [ -d "/mnt/c/Lang/cpp/DynamicExplorationGraph/python" ]; then
    DEG_CPP_DIR="/mnt/c/Lang/cpp/DynamicExplorationGraph/python"
fi

# Rebuild deglib C++ extension if needed (fast incremental build)
if [ -n "$DEG_CPP_DIR" ]; then
    (cd "$DEG_CPP_DIR" && "$PYTHON_CMD" setup.py build_ext --inplace > /dev/null 2>&1)
fi

# Run the benchmark and emit canonical METRIC lines
"$PYTHON_CMD" -u run_benchmark_autoresearch.py
