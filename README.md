# Azure Function And Document Intelligence Agent

## Features
- Uses `prebuilt-layout` model to detect tables
- Exports tables to CSV and/or JSON
- Pretty console rendering of tables
- Environment-based configuration

## Prerequisites
1. Azure subscription
2. Azure Document Intelligence resource (Cognitive Services / Document Intelligence) with an endpoint + key.
3. Python 3.10+

## Provision (Azure CLI)
If you have not created a resource yet:
```powershell
az group create -n my-docint-rg -l eastus
az cognitiveservices account create `
  -n my-docint-resource `
  -g my-docint-rg `
  -l eastus `
  --kind FormRecognizer `
  --sku S0 `
  --yes
az cognitiveservices account keys list -n my-docint-resource -g my-docint-rg
```
Take the endpoint from:
```powershell
az cognitiveservices account show -n my-docint-resource -g my-docint-rg --query properties.endpoint -o tsv
```

## Setup
Clone / copy this folder then:
```powershell
python -m venv .venv
. .venv/Scripts/Activate.ps1
pip install -r requirements.txt
```
Create `.env` from template:
```powershell
Copy-Item .env.example .env
```
Fill in values:
```
AZURE_DOCUMENTINTELLIGENCE_ENDPOINT=https://<your-resource>.cognitiveservices.azure.com/
AZURE_DOCUMENTINTELLIGENCE_KEY=<key>
```

## Usage
```powershell
python .\src\di_extract_tables.py .\sample.pdf --out output --format both
```
Options:
- `--format csv|json|both` (default both)
- `--no-pretty` skip console table rendering

Outputs:
- `output/<pdfstem>_table{n}.csv` for each table
- `output/<pdfstem>_tables.json` aggregated structure (if json enabled)

## JSON Structure
```json
[
  {
    "table_index": 0,
    "row_count": 5,
    "column_count": 4,
    "cells": [["A1", "B1", ...], ["A2", ...]]
  }
]
```

## Notes / Best Practices
- For semantic elements (headings, paragraphs) or styles, still use `prebuilt-layout`.
- For invoices, receipts, IDs: switch to specific prebuilt model (e.g. `prebuilt-invoice`).
- Large PDFs: consider paging or splitting before processing to reduce latency.
- Handle rate limiting: catch `HttpResponseError` with status 429 and backoff.

## Next Steps
- Add unit tests (mock client) for table normalization
- Add option to merge multi-page tables (requires analyzing cell bounding regions & spans)
- Integrate into a larger pipeline (e.g., Azure Functions or batch job)

## Troubleshooting
| Issue | Cause | Fix |
|-------|-------|-----|
| Auth error 401 | Wrong key | Regenerate keys in portal/CLI |
| Empty tables | Document has no detectable grid | Verify visually / adjust source PDF |
| Mixed languages | Layout model returns raw text only | Use OCR languages options if/when exposed |

## License
Internal / sample usage. Adapt as needed.