#!/bin/bash
# Health Monitor for bybit_options project
# Monitors memory usage and resource consumption
# Detects out-of-memory conditions and resource leaks

set -e

INTERVAL=${1:-10}  # Default: check every 10 seconds
DURATION=${2:-600} # Default: monitor for 10 minutes
THRESHOLD_MB=6000  # Alert if memory exceeds 6GB (conservative for 7.7GB system)

echo "🔍 Health Monitor Started"
echo "📊 System Configuration:"
echo "   Total Memory: $(free -h | awk 'NR==2 {print $2}')"
echo "   Memory Threshold: ${THRESHOLD_MB}MB"
echo "   Check Interval: ${INTERVAL}s"
echo "   Total Duration: ${DURATION}s (~$((DURATION/60)) minutes)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

start_time=$(date +%s)
max_memory=0
warning_count=0

while true; do
    current_time=$(date +%s)
    elapsed=$((current_time - start_time))
    
    if [ $elapsed -gt $DURATION ]; then
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "✅ Monitoring Complete"
        break
    fi
    
    # Get memory info
    mem_info=$(free -m | awk 'NR==2 {print $3","$4","$7}')
    IFS=',' read -r used_mb available_mb total_available <<< "$mem_info"
    
    # Get swap info
    swap_info=$(free -m | awk 'NR==3 {print $3}')
    swap_used=$swap_info
    
    # Get process info
    top_proc=$(ps aux --sort=-%mem | head -2 | tail -1 | awk '{printf "%s (%.1f%% - %s)", $11, $4, $6}')
    
    # Check threshold
    status="✓"
    if [ $used_mb -gt $THRESHOLD_MB ]; then
        status="⚠️ WARNING"
        warning_count=$((warning_count + 1))
    fi
    
    # Track max memory
    if [ $used_mb -gt $max_memory ]; then
        max_memory=$used_mb
    fi
    
    # Print status
    timestamp=$(printf "%02d:%02d" $((elapsed / 60)) $((elapsed % 60)))
    printf "[%s] %s Memory: %4dMB / %dMB | Available: %dMB | Swap: %dMB | Top: %s\n" \
        "$timestamp" "$status" "$used_mb" "$((available_mb + used_mb))" "$total_available" "$swap_used" "$top_proc"
    
    sleep $INTERVAL
done

echo ""
echo "📈 Summary:"
echo "   Peak Memory Usage: ${max_memory}MB"
echo "   Warnings Issued: $warning_count"
echo "   Current Memory: $(free -m | awk 'NR==2 {printf "%dMB / %dMB", $3, $2}')"
echo "   Status: $([ $warning_count -eq 0 ] && echo '✅ HEALTHY' || echo '⚠️ POTENTIAL ISSUES')"
