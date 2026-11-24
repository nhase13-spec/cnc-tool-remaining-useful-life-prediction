# Research evidence audit

## PHM 2010 (primary)

```csv
tool,wear_cuts_official,bundle_wear_steps,bundle_rows
c1,255,255,34722
c4,315,260,35279
c6,315,290,34674
```

## Threshold sensitivity (µm)

```csv
tool,n_cuts,max_wear_um,threshold_um,crossed,crossing_cut,right_censored,wear_source
c1,255,172.68683719999999,150.0,True,211.0,False,audit
c4,315,210.9193705,150.0,True,266.0,False,audit
c6,315,234.7159485,150.0,True,221.0,False,audit
c1,255,172.68683719999999,200.0,False,,True,audit
c4,315,210.9193705,200.0,True,306.0,False,audit
c6,315,234.7159485,200.0,True,262.0,False,audit
c1,255,172.68683719999999,250.0,False,,True,audit
c4,315,210.9193705,250.0,False,,True,audit
c6,315,234.7159485,250.0,False,,True,audit
c1,255,172.68683719999999,300.0,False,,True,audit
c4,315,210.9193705,300.0,False,,True,audit
c6,315,234.7159485,300.0,False,,True,audit
```

## NASA Milling (secondary)

```json
{
  "available": false,
  "reason": "invalid zip (placeholder or corrupt)"
}
```

## Integrity notes

- No tool crosses 300 µm in available wear files — physical RUL is right-censored at that threshold.
- UniWear bundle uses fewer wear steps than 315 official cuts for some tools.
- c1 lacks local official per-flute CSV; bundle-derived wear used with disclosure.