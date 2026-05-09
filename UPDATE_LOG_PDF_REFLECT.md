# 업데이트 로그

## v2 — HS 코호트 재보정 (2026-05-09)

### 컨텍스트
엄준상 = **고교 2학년**, 전국 고교 통틀어 최상위급 타자.
v1의 elite-skewed 합성 코호트(Driveline 프로 기반)에서는 그의 점수가 부당하게 낮게 나오던 문제를 수정.

### 변경 파일
- `generate_synthetic_cohort.py` — HS-baseline 분포 파라미터로 재설계
- `data/cohort_batting_per_session.csv` — 새 분포로 재생성된 80명 합성
- `data/master_fitness_batting.csv` — 새 분포 + s13 행은 엄준상 실측값 보존
- `data/cohort_distributions.json`, `data/variable_metadata.json`, `data/bat_speed_regression.json` — 재계산
- `metadata_batting.js`, `cohort_batting.js` — JSON으로부터 재빌드
- `reports/s13_S13_엄준상_v1.html` — 재빌드
- `README.md` — v2 컨텍스트 추가

### 새 HS 코호트 분포 (엄준상 percentile)

| 변수 | 코호트 mean | sd | 엄준상 값 | z | percentile |
|---|---:|---:|---:|---:|---:|
| Peak Pelvis ang.velocity | 470 | 73 | 599.7 | +1.77 | **96.2%** |
| Peak Trunk ang.velocity | 580 | 84 | 717.7 | +1.64 | **94.9%** |
| Peak Arm ang.velocity | 742 | 123 | 947.3 | +1.67 | **95.3%** |
| Pelvis→Trunk speedup | 1.04 | 0.11 | 1.20 | +1.45 | **92.6%** |
| Max X-Factor | 14.4 | 4.2 | 22.0 | +1.83 | **96.6%** |
| Peak Arm AV SD (lower=better) | 169 | 40 | 95.1 | -1.87 | **3.1%** |
| Peak Trunk AV SD (lower=better) | 68 | 19 | 36.2 | -1.69 | **4.6%** |
| Max X-Factor SD (lower=better) | 4.5 | 1.6 | 1.7 | -1.77 | **3.8%** |

→ 모든 핵심 회전 변수에서 상위 5% 이내, 일관성 변수도 상위 5% 이내.

### Bat Speed 회귀 (재학습)
- R² = 0.77 / adj R² = 0.74 / LOO-CV R² = 0.69
- 표준화 β 1순위: torso_rotation_velo_at_swing (β = +0.314)
- 2순위: upper_arm_rotation_velo_at_swing (β = +0.265)

---

## v1 — Uplift PDF (2025-10-02) 반영 (이전)

엄준상 선수의 Uplift Daily Hitting Report PDF 10스윙 평균/SD를 BBL CSV에 반영.

| 컬럼 | 이전 (단일 스윙 #2) | 이후 (10스윙 평균/SD) |
|---|---:|---:|
| peak_pelvis_angular_velocity | 603.95 | **599.70** |
| peak_trunk_angular_velocity | 689.91 | **717.70** |
| peak_arm_angular_velocity | 923.17 | **947.30** |
| max_x_factor | 20.96 | **22.00** |
| pelvis_to_trunk_velocity_speedup | 1.142 | **1.197** |
| trunk_to_arm_velocity_speedup | 1.338 | **1.320** |
| launch_position | 146.47 | **83.00** |
| trunk_tilt_at_launch | 6.80 | **-10.40** |
| peak_arm_av_sd_dps | 228.4 | **95.09** |
| peak_trunk_av_sd_dps | 79.9 | **36.16** |
| max_x_factor_sd_deg | 5.396 | **1.70** |

Fault flag (sway 1.0, drift 1.0, knee 0.0, hip 0.0)는 이미 PDF와 일치.

---

## 재빌드 명령

```bash
cd BBL_Hitting_Report
python generate_synthetic_cohort.py   # HS 코호트 80명 (s13만 master_fitness에서 실측 보존)
python build_metadata.py              # 분포·회귀 학습
python build_js_files.py              # metadata.js / cohort.js 생성
python build_report.py                # → reports/s13_S13_엄준상_v1.html
```
