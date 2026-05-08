"""
build_report.py
===============
선수 한 명의 측정값 + 모든 JS/CSS를 단일 standalone HTML 리포트로 합친다.
오프라인에서 그대로 열리고, GitHub Pages 등에 .html 하나로 배포 가능.

사용법:
    python build_report.py                  # 기본: s13 (실제 추출)
    python build_report.py --athlete s13    # 명시적
    python build_report.py --row N          # 합성 코호트 N번째 선수로 빌드 (테스트용)
"""

import argparse
import json
import re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).parent
DATA = ROOT / 'data'
REPORTS = ROOT / 'reports'
REPORTS.mkdir(exist_ok=True)


def load_athlete(athlete_id='s13', cohort_row=None):
    """
    선수 한 명 데이터를 dict로 반환.
    
    s13: bbl_batting_per_session.csv (실제 Uplift 추출 + 합성 Blast/SD)
         master_fitness_batting.csv (합성 체력)
    cohort_row=N: 합성 코호트 N번째 선수 (테스트용)
    """
    if cohort_row is not None:
        cohort = pd.read_csv(DATA / 'cohort_batting_per_session.csv')
        fitness = pd.read_csv(DATA / 'master_fitness_batting.csv')
        a = cohort.iloc[cohort_row].to_dict()
        f_row = fitness[fitness['athlete_id'] == a['athlete_id']]
        if len(f_row) > 0:
            for k, v in f_row.iloc[0].items():
                if k not in a or pd.isna(a.get(k)):
                    a[k] = v
        return a
    else:
        bbl = pd.read_csv(DATA / 'bbl_batting_per_session.csv')
        fitness = pd.read_csv(DATA / 'master_fitness_batting.csv')
        # athlete_id로 매칭 시도, 없으면 첫 행
        if 'athlete_id' in bbl.columns and (bbl['athlete_id'] == athlete_id).any():
            row = bbl[bbl['athlete_id'] == athlete_id].iloc[0]
        else:
            row = bbl.iloc[0]
        a = row.to_dict()
        # 체력 합치기
        f_row = fitness[fitness['athlete_id'] == athlete_id]
        if len(f_row) > 0:
            for k, v in f_row.iloc[0].items():
                if k not in a or pd.isna(a.get(k)):
                    a[k] = v
        return a


def to_jsonable(obj):
    """NaN/Timestamp 등을 JSON 호환으로 변환"""
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_jsonable(v) for v in obj]
    if pd.isna(obj):
        return None
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    if hasattr(obj, 'item'):  # numpy scalar
        return obj.item()
    return obj


def build_html(athlete_data, output_path, title=None):
    """모든 자산을 standalone HTML 하나로 합쳐 저장"""
    # 자산 로드
    css = (ROOT / 'report_batting.css').read_text(encoding='utf-8')
    metadata_js = (ROOT / 'metadata_batting.js').read_text(encoding='utf-8')
    cohort_js   = (ROOT / 'cohort_batting.js').read_text(encoding='utf-8')
    app_js      = (ROOT / 'app_batting.js').read_text(encoding='utf-8')
    
    # 선수 데이터 → JSON 임베드
    athlete_json = json.dumps(to_jsonable(athlete_data), ensure_ascii=False, indent=2)
    
    title = title or f"Uplift Hitting Report — {athlete_data.get('athlete_name', 'Unknown')}"
    
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
{css}
</style>
</head>
<body>

<div id="app">
  <p style="text-align:center;padding:40px;color:#9ca3af">리포트 렌더링 중...</p>
</div>

<script>
window.ATHLETE_DATA = {athlete_json};
</script>

<script>
{metadata_js}
</script>

<script>
{cohort_js}
</script>

<script>
{app_js}
</script>

</body>
</html>
"""
    
    output_path.write_text(html, encoding='utf-8')
    return output_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--athlete', default='s13', help='선수 ID (기본: s13)')
    parser.add_argument('--row', type=int, default=None,
                        help='합성 코호트 N번째 선수로 빌드 (테스트용)')
    parser.add_argument('--out', default=None, help='출력 파일 경로')
    args = parser.parse_args()
    
    athlete = load_athlete(athlete_id=args.athlete, cohort_row=args.row)
    name = athlete.get('athlete_name', 'unknown').replace(' ', '_')
    
    if args.out:
        out_path = Path(args.out)
    else:
        out_path = REPORTS / f"{args.athlete}_{name}_v1.html"
    
    build_html(athlete, out_path)
    print(f"Saved: {out_path}")
    print(f"  Athlete: {athlete.get('athlete_name')}")
    print(f"  Handedness: {athlete.get('handedness')}")
    print(f"  Bat Speed (Blast): {athlete.get('blast_bat_speed_mph')}")
    print(f"  Size: {out_path.stat().st_size:,} bytes")


if __name__ == '__main__':
    main()
