"""Extract Annexure-1 of CGWB 'Ground Water Quality in Shallow Aquifers of NCT of Delhi (AAP 2023-24)' (May 2022 samples).
Needs poppler's pdftotext. Usage: python scripts/quality_samples.py report.pdf"""
import re, subprocess, sys, pandas as pd
rows = []
for p in range(68, 73):
    lines = subprocess.run(["pdftotext", "-f", str(p), "-l", str(p), "-layout", sys.argv[1], "-"], capture_output=True, text=True).stdout.split("\n")
    for i, l in enumerate(lines):
        m = re.match(r"\s*(7[67]\.\d{2,3})\s+(28\.\d{2,3})\s+(.*)", l)
        if not m: continue
        rest = m[3]; nm = re.match(r"(.*?)\s+(\d\.\d{2})\s+\d+\s", rest); name = nm[1].strip() if nm else ""
        v = list(map(float, re.findall(r"[-\d.]+", rest[len(name):])))
        if not name: name = ((lines[i-1].strip() if i else "") + " " + (lines[i+1].strip() if i+1 < len(lines) else "")).strip()
        rows.append(dict(lon=float(m[1]), lat=float(m[2]), name=name, pH=v[0], EC=v[1], Cl=v[4], NO3=v[6], F=v[7]))
Q = pd.DataFrame(rows); Q["flag"] = (Q.EC > 3000) | (Q.F > 1.5) | (Q.NO3 > 45) | (Q.Cl > 1000)
print(len(Q), "samples | EC>3000:", (Q.EC > 3000).sum(), "F>1.5:", (Q.F > 1.5).sum(), "NO3>45:", (Q.NO3 > 45).sum(), "Cl>1000:", (Q.Cl > 1000).sum(),
      "(report states 95, 24, 15, 33, 11)")
Q.to_csv("data/quality_samples_2022.csv", index=False)
