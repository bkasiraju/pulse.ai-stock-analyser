#!/bin/bash
cd "$(dirname "$0")"
python3 app.py --quick
echo ""
echo "Press any key to exit..."
read -n 1
