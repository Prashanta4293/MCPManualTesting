"""Export reviewed workbook matches without treating old outcomes as current results."""
import json
from pathlib import Path
import openpyxl

root = Path(__file__).resolve().parents[1]
source = openpyxl.load_workbook(root / 'test_data/Hotels Under Tourism List.xlsx', data_only=True)
comparison = openpyxl.load_workbook(root / 'comparison_results/hotel_web_excel_comparison.xlsx', data_only=True)
matches = []
for row in list(comparison['Matched Records'].values)[1:]:
    sheet, number = row[2], int(row[3])
    original = list(source[sheet].values)[number - 1]
    matches.append({'name': original[1], 'phone': str(original[3]), 'sourceSheet': sheet,
                    'sourceRow': number, 'comparisonId': row[0]})
out = root / 'tests/data/hotel-matches.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(matches, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'Exported {len(matches)} previously confirmed name/phone matches to {out}')
