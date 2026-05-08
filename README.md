# Uplift Hitting Report (BBL Batting v1.0)

투수 리포트 [`Uplift_Pitching_Report`](https://github.com/kkl0511/Uplift_Pitching_Report) (BBL v33.22)와 같은 철학·구조의 **타격 바이오메카닉스 리포트** v1 골격입니다. Driveline의 *Hitting Mechanical Composite Scores+* 5-카테고리 모델을 KBO 코호트(현재는 합성)에 매핑하고, Bat Speed 다중회귀로 효율성(Above Expected)까지 평가합니다.

---

## 빠른 시작

```bash
# 1. 합성 코호트 + 분포·회귀 모델 빌드 (한 번만)
python generate_synthetic_cohort.py
python build_metadata.py
python build_js_files.py

# 2. 실제 측정 선수 데이터 추출 (Uplift 다운로드 CSV)
python extract_uplift_batting_scalars.py path/to/uplift_export.csv

# 3. 합성 Blast/체력 부착 (실제 Blast/체력 측정값이 있다면 이 단계는 건너뜀)
python attach_synthetic_for_target.py

# 4. standalone HTML 리포트 생성
python build_report.py
# → reports/s13_S13_엄준상_v1.html
```

`reports/*.html` 파일은 모든 JS/CSS/데이터가 인라인된 **단일 파일 standalone**입니다. 더블 클릭만으로 열리고, GitHub Pages에 그대로 배포할 수 있습니다.

---

## 데이터 흐름

```
Uplift batting CSV (시계열 503프레임 × 248열)
      │
      ▼  extract_uplift_batting_scalars.py
per-session 스칼라 (~78개 변수)
   • Driveline 14변수 (Stride Posture/Rotation, Swing Posture/Rotation, CoG)
   • Uplift extras (peak_pelvis_av, max_x_factor, attack_angle, on_plane_efficiency …)
   • 9개 결함 binary (drifting_forward, knee_dominant_swing 등)

      ▼  attach_synthetic_for_target.py
+ 합성 Blast Motion (10변수)
+ 합성 체력 (9변수)
+ 합성 일관성 SD (6변수)

      ▼  build_report.py
standalone HTML 리포트
```

병렬 트랙으로 generate_synthetic_cohort.py가 합성 코호트 80명을 만들고, build_metadata.py가 분포·다중회귀를 계산합니다. 이 결과가 `metadata_batting.js`/`cohort_batting.js`로 빌드되어 모든 리포트가 공유합니다.

---

## 카테고리 구조

| ID | 카테고리 | Driveline 가중치 | 변수 |
|----|----------|-----------------:|------|
| **B1** | Stride Posture | 1.53 | Max Pelvis Rot @ Stride · Torso Rot @ FP · Rear Shoulder Add @ FP · Lead Hip Posterior Tilt @ FP |
| **B2** | Stride Rotation | 1.26 | Max Pelvis Rot Velo @ Stride · Max Torso Rot Velo @ Stride |
| **B3** | Swing Posture | 1.13 | Pelvis Rot @ Swing · Lead Hip Adduction @ Swing |
| **B4** | Swing Rotation | **1.64** *(가장 영향력 큼)* | Torso Rot Velo @ Swing · Upper Arm Rot Velo @ Swing · Pelvis Rot Velo @ Swing |
| **B5** | CoG | **1.68** | Max CoG Velo @ Stride · CoG Decel · Max CoG Velo |
| B6 | Bat Path (Blast) | — | Attack Angle · On-Plane Efficiency · Vertical Bat Angle · Connection |
| B7 | Consistency | — | Bat Speed/Attack Angle/X-Factor SD 등 |
| F | Fitness | — | Grip · CMJ · IMTP · Rotational Power · Sprint · Broad Jump |

B4 Swing Rotation과 B5 CoG가 Bat Speed 예측에 가장 영향력이 크다는 Driveline 결과를 가중치에 그대로 반영했습니다.

---

## 점수 산출 방식

투수 리포트와 동일한 hybrid 방식:

- **`higher_is_better`** (예: torso_rotation_velo_at_swing_dps) → z-score 기반 percentile (정규근사)
- **`lower_is_better`** (예: time_to_contact_s, SD 변수들) → (100 − percentile)
- **`two_sided`** (예: attack_angle, X-factor, connection_at_impact) → optimal 근처 Gaussian 점수 ($e^{-z^2/2}$)

카테고리 점수 = $\sum w_i \cdot s_i / \sum w_i$ (Driveline 상대 중요도 가중평균)

---

## Bat Speed 회귀 (v1)

```
predictors = upper_arm_rotation_velo_at_swing_dps  (β = +0.39, 1순위)
             torso_rotation_velo_at_swing_dps      (β = +0.29, 2순위)
             on_plane_efficiency                   (β = +0.16)
             max_x_factor                          (β = +0.16)
             pelvis_to_trunk_velocity_speedup      (β = +0.12)
             cog_decel_mps                         (β = +0.10)
             rotation_pp_w_kg, grip_strength_kg, cmj_pp_bm, height_cm

R² = 0.84  /  LOO-CV R² = 0.77  (n=80, 합성 데이터)
```

표준화 β 1·2위가 **Upper Arm Rot Velo**와 **Torso Rot Velo**라는 결과는 Driveline의 *“Swing Rotation = 가장 영향력 큰 모델”* 주장과 정확히 일치합니다. 합성 코호트가 그렇게 design된 결과이긴 하지만, 실제 데이터로 교체해도 같은 변수가 상위에 올라올 것으로 예상됩니다.

리포트의 **Above Expected (AE)** = 실측 Bat Speed − 예측 Bat Speed. 양수면 메카닉 대비 효율적, 음수면 회복 여지가 있는 상태로 해석됩니다.

---

## 한계 및 v2 로드맵

**v1의 한계** (사용자 인지 필요):
- 코호트 n=80 모두 합성. Driveline 절대값과 직접 비교는 지양 (좌표계·필터링 차이 가능).
- s13의 일부 카테고리 점수가 낮게 나오는 것은 합성 코호트가 elite-skewed인 영향. 실제 데이터로 교체 시 정상화.
- Lead Hip Posterior Tilt는 Uplift CSV에 직접 변수가 없어 `pelvis_global_tilt`로 근사.
- Blast Motion·체력 데이터 모두 합성 (사용자 요청).

**v2에 추가하면 좋을 것**:
1. 실제 KBO/대학 코호트 누적 → 합성 코호트 대체
2. `batch_process_batting.py`로 여러 선수 일괄 처리
3. Hitting Faults 확장 (Casting, Early Hip Rotation, Lunge at Ball 등 — 현재는 Uplift 자체 9개만)
4. Bat Path 시각화 (스윙 궤적 SVG)
5. 키네마틱 시퀀스 시각화 (P→T→A 시간 차)
6. 베이스라인 세션 저장 → 기준선 변화량 표시 (Driveline의 (+1.2 mph) 표기처럼)
7. 좌타/우타 별 코호트 분리

---

## 파일 구성

```
Uplift_Hitting_Report/
├── README.md
├── extract_uplift_batting_scalars.py   # CSV → per-session 스칼라
├── generate_synthetic_cohort.py        # 합성 코호트 80명 생성
├── build_metadata.py                   # 분포·회귀 모델 학습
├── attach_synthetic_for_target.py      # 실측 선수에 Blast/체력 부착
├── build_js_files.py                   # JSON → metadata.js / cohort.js
├── build_report.py                     # standalone HTML 빌드
├── metadata_batting.js                 # (자동 생성) 변수 metadata + 회귀
├── cohort_batting.js                   # (자동 생성) 카테고리·점수 계산
├── app_batting.js                      # 리포트 렌더링 로직
├── report_batting.css                  # 스타일
├── data/
│   ├── bbl_batting_per_session.csv     # 실측 선수 per-session
│   ├── cohort_batting_per_session.csv  # 합성 코호트
│   ├── master_fitness_batting.csv      # 체력 마스터
│   ├── cohort_distributions.json
│   ├── bat_speed_regression.json
│   └── variable_metadata.json
└── reports/
    └── s13_S13_엄준상_v1.html           # 생성된 리포트
```
