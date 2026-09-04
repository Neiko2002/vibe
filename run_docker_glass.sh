#!/bin/bash
set -e

echo "======================================================="
echo "Building Glass Docker Image from existing vibe-deg-test"
echo "======================================================="

docker build -t vibe-glass:latest -f vibe/algorithms/glass/Dockerfile .

echo ""
echo "======================================================="
echo "Running Glass Top-100 Benchmark inside Linux Container"
echo "======================================================="

docker run --rm \
  -v "$(pwd):/vibe" \
  -w /vibe \
  --cpuset-cpus="1" \
  vibe-glass:latest \
  python -u run_yandex_glass_top100.py

echo ""
echo "Benchmark run finished. Check results/yandex-200-cosine/"
