# 🔍 IVRankChart Debug Checklist

**Use if charts still don't appear after first fix**

---

## Quick Diagnosis (2 min)

### Check 1: Data Arrives?

**Console → Network tab → Filter: "Fetch/XHR"**

Find these requests:
- `price-history?symbol=BTCUSDT&days=365`
- `iv-rank?base_coin=BTC&days=365`

Click each → **Response** tab:

**Expected:**
```json
{
  "candles": [{time: 1234, open: 90000, ...}, ...],  // ~365 items
  "count": 365
}
```

**If 0 items or 404:** Backend issue, not frontend.

---

### Check 2: Debug Logs

**Console output should show:**

```
🔍 Effect 2 - Chart Init Check: { ... }
✅ Containers ready, initializing charts
🔍 Effect 3: { loading: false, dataLengths: {price: 365, iv: 365}, ... }
```

**If you see:**
- ⚠️ `Containers not ready` (repeated) → Go to Fix A
- ⚠️ `width: 0` or `height: 0` → Go to Fix B
- ✅ but no charts → Go to Fix C

---

## Fix A: Containers Not Ready (Force Delay)

**File:** `frontend/src/components/Charts/IVRankChart.tsx`

**Find Effect 2, ADD at the very start:**

```typescript
  useEffect(() => {
    // Force delay to ensure DOM is ready
    const timer = setTimeout(() => {
      console.log('🔍 Delayed init check...');
      
      if (!priceChartContainerRef.current || !ivRankChartContainerRef.current) {
        console.warn('Still no containers after delay');
        return;
      }
      
      // ... rest of Effect 2 code
    }, 200); // 200ms delay
    
    return () => clearTimeout(timer);
  }, []);
```

---

## Fix B: Zero Size Containers (Explicit Dimensions)

**File:** `frontend/src/components/Charts/IVRankChart.tsx`

**Find the render section (around line 240):**

```typescript
      <div 
        ref={priceChartContainerRef}
        className="w-full bg-white"
        style={{ height: '60%' }}
      />
```

**Replace with:**

```typescript
      <div 
        ref={priceChartContainerRef}
        className="w-full bg-white"
        style={{ 
          height: '360px',
          minHeight: '360px',
          width: '100%',
          minWidth: '400px',
          position: 'relative'
        }}
      />
```

**Do the same for ivRankChartContainerRef:**

```typescript
      <div 
        ref={ivRankChartContainerRef}
        className="w-full bg-white border-t border-gray-200"
        style={{ 
          height: '120px',
          minHeight: '120px',
          width: '100%',
          minWidth: '400px',
          position: 'relative'
        }}
      />
```

---

## Fix C: Data Loads But Charts Don't Update

**File:** `frontend/src/components/Charts/IVRankChart.tsx`

**Find Effect 3 (data update), ADD after setData calls:**

```typescript
      candlestickSeriesRef.current?.setData(formattedPriceData);
      ivRankSeriesRef.current?.setData(formattedIVData);
      
      // Force re-layout after data load
      setTimeout(() => {
        if (priceChartRef.current && ivRankChartRef.current) {
          priceChartRef.current.timeScale().fitContent();
          ivRankChartRef.current.timeScale().fitContent();
          console.log('✅ Charts fitted to content');
        }
      }, 100);
```

---

## Fix D: Nuclear Option (Force Re-mount)

**File:** `frontend/src/App.tsx`

**Find IVRankChart component:**

```typescript
<IVRankChart 
  baseCoin="BTC"
  symbol="BTCUSDT"
  days={365}
  height="600px"
/>
```

**Change days to 90 (less data):**

```typescript
<IVRankChart 
  baseCoin="BTC"
  symbol="BTCUSDT"
  days={90}
  height="600px"
/>
```

**OR add key prop to force re-mount:**

```typescript
<IVRankChart 
  key={Date.now()}  // Force new instance
  baseCoin="BTC"
  symbol="BTCUSDT"
  days={90}
  height="600px"
/>
```

---

## Reporting Template

After trying fixes, report:

```markdown
## Debug Results

✅ Data arrives: Yes (365 candles) / No (X candles)
✅ Containers exist: Yes (width: Xpx) / No
✅ Effect 2 runs: Yes / No / Loops
✅ Effect 3 runs: Yes / No

Tried:
- [ ] Fix A (delay)
- [ ] Fix B (explicit size)
- [ ] Fix C (fitContent)
- [ ] Fix D (reduce data)

Console output:
[paste last 5 lines]

Charts visible: Yes / No
```

---

**Wait for Codex to finish first fix. If charts still blank, use this checklist.**
