#!/bin/bash
cd /home/dmitrii/projects/bybit_options
source venv/bin/activate
python -m strategy.data.data_collector >> logs/collector.log 2>&1
