// app_batting.js
// =====================================================================
// 타격 리포트 메인 렌더링 로직
//
// 의존: metadata_batting.js, cohort_batting.js
// 입력: window.ATHLETE_DATA  (HTML에서 임베드되는 선수 측정값 객체)
// =====================================================================


// ===== 유틸 =====
const fmt = (v, d = 1) => (v == null || isNaN(v)) ? '—' : Number(v).toFixed(d);
const fmtPct = (v) => (v == null || isNaN(v)) ? '—' : `${Math.round(v)}th`;
const fmtScore = (v) => (v == null || isNaN(v)) ? '—' : Math.round(v);

// 점수에 따른 컬러 (회색/적색/연두/녹색)
function scoreColor(s) {
  if (s == null) return 'var(--c-muted)';
  if (s < 30)  return 'var(--c-bad)';
  if (s < 50)  return 'var(--c-warn)';
  if (s < 70)  return 'var(--c-mid)';
  return 'var(--c-good)';
}

// percentile → 5/50/95 위치 표시용
function pctBand(pct) {
  if (pct == null) return 'unknown';
  if (pct < 25) return 'low';
  if (pct < 75) return 'mid';
  return 'high';
}


// ===== 1. 선수 카드 =====
function renderAthleteCard(a) {
  const name = a.athlete_name || '—';
  const hand = a.handedness === 'right' ? '우타' : a.handedness === 'left' ? '좌타' : '—';
  const date = a.capture_datetime ? new Date(a.capture_datetime).toLocaleDateString('ko-KR') : '—';
  const fps = a.fps ? Math.round(a.fps) : '—';
  return `
    <section class="athlete-card">
      <div class="athlete-id">
        <div class="athlete-name">${name}</div>
        <div class="athlete-meta">${hand} · ${date} · ${fps} fps · Uplift Mocap</div>
      </div>
      <div class="athlete-body">
        <div class="vital"><label>신장</label><span>${fmt(a.height_cm,1)} cm</span></div>
        <div class="vital"><label>체중</label><span>${fmt(a.weight_kg,1)} kg</span></div>
        <div class="vital"><label>악력</label><span>${fmt(a.grip_strength_kg,1)} kg</span></div>
        <div class="vital"><label>CMJ</label><span>${fmt(a.cmj_height_cm,1)} cm</span></div>
        <div class="vital"><label>30m</label><span>${fmt(a.sprint_30m_s,2)} s</span></div>
      </div>
    </section>
  `;
}


// ===== 2. 헤드라인 KPI: Bat Speed (실측 vs 예측) + 종합 점수 =====
function renderHeadline(a, scores) {
  const actual    = a.blast_bat_speed_mph;
  const predicted = predictBatSpeed(a);
  const residual  = (actual != null && predicted != null) ? (actual - predicted) : null;
  const overall   = scores.overall;

  // Mechanical ceiling: 종합 점수가 100→Bat Speed 평균, 점수가 130 정도면 어느 정도 ceiling?
  // 간이: ceiling = predicted + (score-100)/50 * 5 (대략)
  let ceiling = null;
  if (overall != null && predicted != null) {
    ceiling = predicted + Math.max(0, (130 - overall)) * 0.05;
    ceiling = predicted + (130 - 100) * (predicted * 0.005);  // 약 +1.5% per 30점
  }

  // Driveline 표기 흉내: "Bat Speed 84.6 mph (+13.8 AE)"
  // AE = Above Expected; 우리 잔차값을 AE로
  const aeStr = residual == null ? '' :
    `<span class="ae ${residual > 0 ? 'pos' : 'neg'}">${residual >= 0 ? '+' : ''}${fmt(residual,1)}<sub>AE</sub></span>`;

  return `
    <section class="headline">
      <div class="hl-row">
        <div class="hl-block primary">
          <div class="hl-value">${fmt(actual, 1)} <small>mph</small></div>
          <div class="hl-label">Bat Speed (Blast) ${aeStr}</div>
          <div class="hl-sub">예측 ${fmt(predicted,1)} mph · 잔차(효율) ${residual==null?'—':(residual>0?'+':'')+fmt(residual,1)} mph</div>
        </div>
        <div class="hl-block">
          <div class="hl-value" style="color:${scoreColor(overall)}">${fmtScore(overall)}</div>
          <div class="hl-label">Total Mechanical Score</div>
          <div class="hl-sub">코호트 평균 = 50점 (높을수록 우수)</div>
        </div>
        <div class="hl-block">
          <div class="hl-value">${fmt(a.blast_peak_hand_speed_mph,1)} <small>mph</small></div>
          <div class="hl-label">Peak Hand Speed</div>
          <div class="hl-sub">손의 최대 선속도</div>
        </div>
        <div class="hl-block">
          <div class="hl-value">${fmt(a.max_x_factor,1)}<small>°</small></div>
          <div class="hl-label">Max X-Factor</div>
          <div class="hl-sub">Hip-Shoulder 분리 최대값</div>
        </div>
      </div>
    </section>
  `;
}


// ===== 3. Driveline 5-카테고리 레이더 (SVG) =====
function renderRadar(scores) {
  // B1~B5만 (Driveline 원형 5각형)
  const cats = ['B1_StridePosture','B2_StrideRotation','B3_SwingPosture','B4_SwingRotation','B5_CoG'];
  const labels = ['Stride Posture','Stride Rotation','Swing Posture','Swing Rotation','CoG'];
  const values = cats.map(c => scores[c]?.score ?? null);

  // SVG 좌표
  const W = 360, H = 360;
  const cx = W/2, cy = H/2;
  const R = 130;  // 점수 100에 해당하는 반지름

  // 각 꼭짓점 좌표 (12시 방향부터 시계방향)
  const angle = (i) => (-Math.PI/2) + (i * 2*Math.PI/5);
  const point = (i, r) => `${cx + r*Math.cos(angle(i))},${cy + r*Math.sin(angle(i))}`;

  // 격자: 25/50/75/100점 동심오각형
  const rings = [25,50,75,100].map(p => {
    const r = R * p/100;
    const pts = [...Array(5).keys()].map(i => point(i, r)).join(' ');
    return `<polygon points="${pts}" class="radar-ring" />`;
  }).join('');

  // 축선
  const axes = [...Array(5).keys()].map(i => {
    const [x,y] = point(i,R).split(',');
    return `<line x1="${cx}" y1="${cy}" x2="${x}" y2="${y}" class="radar-axis"/>`;
  }).join('');

  // Elite 기준선 (점수 50, 코호트 평균)
  const elitePts = [...Array(5).keys()].map(i => point(i, R*0.5)).join(' ');

  // 선수 점수 폴리곤
  const playerPts = values.map((v,i) => {
    const r = (v == null) ? 0 : R * Math.min(100, Math.max(0, v))/100;
    return point(i, r);
  }).join(' ');

  // 라벨
  const labelEls = labels.map((lab,i) => {
    const [x,y] = point(i, R + 28).split(',').map(Number);
    let anchor = 'middle';
    if (i === 1 || i === 2) anchor = 'start';
    else if (i === 3 || i === 4) anchor = 'end';
    return `<text x="${x}" y="${y+4}" class="radar-label" text-anchor="${anchor}">${lab}</text>`;
  }).join('');

  // 점수 점
  const pointDots = values.map((v,i) => {
    if (v == null) return '';
    const r = R * Math.min(100, Math.max(0, v))/100;
    const [x,y] = point(i,r).split(',');
    return `<circle cx="${x}" cy="${y}" r="4" class="radar-dot"/>`;
  }).join('');

  return `
    <section class="radar-section">
      <h2>Driveline 5-Category Radar</h2>
      <div class="radar-wrap">
        <svg viewBox="0 0 ${W} ${H}" class="radar-svg" role="img" aria-label="5-category mechanical scores">
          ${rings}
          ${axes}
          <polygon points="${elitePts}" class="radar-elite"/>
          <polygon points="${playerPts}" class="radar-player"/>
          ${pointDots}
          ${labelEls}
        </svg>
        <div class="radar-legend">
          <div><span class="sw player"></span>선수 점수</div>
          <div><span class="sw elite"></span>코호트 평균 (50점)</div>
          ${cats.map((c,i) => `
            <div class="cat-mini">
              <span class="cat-mini-name">${labels[i]}</span>
              <span class="cat-mini-score" style="color:${scoreColor(values[i])}">${fmtScore(values[i])}</span>
            </div>`).join('')}
        </div>
      </div>
    </section>
  `;
}


// ===== 4. 변수 row (값 + percentile bar + 점수) =====
function renderVariableRow(varKey, value, weight) {
  const m = VARIABLE_METADATA[varKey];
  if (!m) {
    return `<tr><td colspan="5">알 수 없는 변수: ${varKey}</td></tr>`;
  }
  const score = scoreVariable(varKey, value);
  // percentile (z 기반 근사)
  let pct = null;
  if (value != null && !isNaN(value)) {
    const z = (value - m.mean) / m.sd;
    pct = 100 * normCdf(z);
  }

  const valStr = `${fmt(value, m.unit==='s' ? 3 : 2)} <small>${m.unit}</small>`;
  const refStr = `μ ${fmt(m.mean, 1)} · σ ${fmt(m.sd,1)}`;
  const dirIcon = m.direction === 'higher_is_better' ? '↑' :
                  m.direction === 'lower_is_better' ? '↓' : '◎';

  // percentile bar — 0~100 위치에 marker
  const pctBar = pct == null ? '' : `
    <div class="pct-bar">
      <div class="pct-track">
        <div class="pct-tick low"></div>
        <div class="pct-tick mid"></div>
        <div class="pct-tick high"></div>
      </div>
      <div class="pct-marker" style="left:${Math.max(0,Math.min(100,pct))}%"></div>
      <div class="pct-text">${fmtPct(pct)}</div>
    </div>
  `;

  return `
    <tr class="var-row">
      <td class="var-name">
        <div class="var-name-kr">${m.label_kr || varKey}</div>
        <div class="var-name-en">${m.label_en || ''} <span class="dir-icon" title="${m.direction}">${dirIcon}</span></div>
      </td>
      <td class="var-value">${valStr}</td>
      <td class="var-ref">${refStr}</td>
      <td class="var-pctbar">${pctBar}</td>
      <td class="var-score" style="color:${scoreColor(score)}">${fmtScore(score)}</td>
    </tr>
  `;
}


// ===== 5. 카테고리 카드 (B1~B7, F) =====
function renderCategoryCard(catKey, scores, athleteValues) {
  const cat = CATEGORIES[catKey];
  if (!cat) return '';
  const r = scores[catKey];
  const score = r?.score;

  const rows = cat.variables.map(v =>
    renderVariableRow(v.key, athleteValues[v.key], v.weight)
  ).join('');

  const importance = cat.driveline_relative_importance != null
    ? `<span class="dl-imp">Driveline 가중치: ${cat.driveline_relative_importance}</span>`
    : '';

  return `
    <section class="cat-card" data-cat="${catKey}">
      <header class="cat-header">
        <h3>
          <span class="cat-id">${catKey.split('_')[0]}</span>
          ${cat.label_kr}
        </h3>
        <div class="cat-score" style="color:${scoreColor(score)}">${fmtScore(score)}</div>
      </header>
      <p class="cat-desc">${cat.description} ${importance}</p>
      <table class="var-table">
        <thead>
          <tr>
            <th>변인</th>
            <th>선수</th>
            <th>코호트 (μ·σ)</th>
            <th>코호트 백분위</th>
            <th>점수</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </section>
  `;
}


// ===== 6. Faults 카드 =====
function renderFaults(a) {
  const faultKeys = Object.keys(FAULT_LABELS);
  const present = faultKeys.filter(k => a[k] === 1 || a[k] === true);
  const absent  = faultKeys.filter(k => a[k] === 0 || a[k] === false);

  if (present.length === 0) {
    return `
      <section class="faults-card">
        <h2>결함 진단 (Uplift)</h2>
        <p class="faults-clean">측정된 9개 결함 항목 중 발현된 결함이 없습니다. 좋습니다.</p>
      </section>
    `;
  }

  const rows = present.map(k => {
    const info = FAULT_LABELS[k];
    return `
      <div class="fault-item severity-${info.severity}">
        <span class="fault-mark">⚠</span>
        <span class="fault-label">${info.kr}</span>
        <span class="fault-sev">${info.severity === 'high' ? '주의' : '관찰'}</span>
      </div>
    `;
  }).join('');

  return `
    <section class="faults-card">
      <h2>결함 진단 (Uplift) — ${present.length}건</h2>
      <div class="faults-grid">${rows}</div>
      <p class="faults-note">
        결함 항목은 Uplift 자체 알고리즘 판정. 현장 영상 검토 권장.
        총 ${faultKeys.length}개 항목 중 ${absent.length}개 정상.
      </p>
    </section>
  `;
}


// ===== 7. 코치 노트 (자동 우선순위) =====
function renderCoachNotes(scores, athleteValues) {
  // 각 카테고리 점수를 보고 가장 점수 낮은 카테고리, 가장 약한 변수 식별
  const catList = ['B1_StridePosture','B2_StrideRotation','B3_SwingPosture',
                   'B4_SwingRotation','B5_CoG','B6_BatPath','B7_Consistency','F_Fitness'];
  const ranked = catList
    .map(c => ({c, score: scores[c]?.score, w: CATEGORIES[c].driveline_relative_importance || 0.8}))
    .filter(x => x.score != null)
    .sort((a,b) => (a.score * (a.w+0.5)) - (b.score * (b.w+0.5)));  // 점수×가중

  const weakest = ranked.slice(0, 2);
  const strongest = ranked.slice(-2).reverse();

  // 가장 점수 낮은 변수 1~3개
  const allDetails = [];
  for (const c of catList) {
    const r = scores[c];
    if (!r?.detail) continue;
    for (const d of r.detail) {
      if (d.score != null) {
        allDetails.push({ ...d, cat: c });
      }
    }
  }
  const lowestVars = allDetails.sort((a,b) => a.score - b.score).slice(0, 3);

  const weakBullets = weakest.map(w => {
    const cat = CATEGORIES[w.c];
    return `<li><strong>${cat.label_kr}</strong> 점수 ${fmtScore(w.score)} — ${cat.description.split('.')[0]}.</li>`;
  }).join('');

  const lowestBullets = lowestVars.map(v => {
    const m = VARIABLE_METADATA[v.key];
    return `<li><strong>${m?.label_kr || v.key}</strong> = ${fmt(v.value,2)} ${m?.unit || ''} (점수 ${fmtScore(v.score)})</li>`;
  }).join('');

  const strongBullets = strongest.map(s => {
    const cat = CATEGORIES[s.c];
    return `<li><strong>${cat.label_kr}</strong> 점수 ${fmtScore(s.score)}</li>`;
  }).join('');

  return `
    <section class="coach-notes">
      <h2>코치 노트 — 자동 우선순위</h2>
      <div class="cn-grid">
        <div class="cn-block weak">
          <h4>우선 보강 카테고리</h4>
          <ul>${weakBullets}</ul>
        </div>
        <div class="cn-block focus">
          <h4>점수 낮은 변수 Top 3</h4>
          <ul>${lowestBullets}</ul>
        </div>
        <div class="cn-block strong">
          <h4>강점 카테고리</h4>
          <ul>${strongBullets}</ul>
        </div>
      </div>
      <p class="cn-note">
        본 우선순위는 코호트 분포 기준 자동 산출. 실제 코칭 결정은 영상 검토와
        선수 신체 컨디션을 함께 고려해야 함.
      </p>
    </section>
  `;
}


// ===== 8. 메서드 노트 (footer) =====
function renderMethodNote() {
  return `
    <section class="method-note">
      <h3>방법론 노트</h3>
      <ul>
        <li><strong>코호트:</strong> 합성 데이터 n=${COHORT_INFO.n_total} (실제 데이터 누적 시 교체 예정).</li>
        <li><strong>점수 산출:</strong>
          higher/lower-is-better 변수는 z-score 기반 percentile,
          two-sided 변수(어택앵글, X-factor 등)는 optimal 근처 Gaussian 점수.</li>
        <li><strong>카테고리 가중치:</strong> Driveline의 Per-1mph 상대 중요도를 변수 weight로 사용.
          B1 Stride Posture (1.53), B2 Stride Rotation (1.26), B3 Swing Posture (1.13),
          B4 Swing Rotation (1.64), B5 CoG (1.68).</li>
        <li><strong>Bat Speed 회귀:</strong> n=${BAT_SPEED_REGRESSION.n}, R² = ${BAT_SPEED_REGRESSION.R2}, LOO-CV R² = ${BAT_SPEED_REGRESSION.LOO_CV_R2}.
          예측-실측 잔차(AE)는 메카닉 효율성의 proxy.</li>
        <li><strong>Blast Motion / 체력:</strong> 본 v1 버전에서는 합성 데이터.
          실제 데이터로 교체할 때 athleteValues에 그대로 덮어쓰면 됩니다.</li>
        <li><strong>Driveline 절대값 비교:</strong> Uplift와 Driveline의 좌표계·필터링이 다를 수 있어
          숫자 직접 비교는 지양. 코호트 내 상대 percentile이 1차 평가 기준.</li>
      </ul>
    </section>
  `;
}


// ===== 메인 렌더 =====
function renderReport() {
  const a = window.ATHLETE_DATA;
  if (!a) {
    document.getElementById('app').innerHTML = '<p class="error">선수 데이터가 로드되지 않았습니다.</p>';
    return;
  }
  const scores = overallScore(a);

  const html = `
    <div class="report-shell">
      <header class="report-top">
        <div class="brand">
          <div class="brand-mark">⚾ Uplift Hitting Report</div>
          <div class="brand-sub">v1.0 · Mechanical Composite Scores</div>
        </div>
        <div class="brand-cohort">코호트 n=${COHORT_INFO.n_total}</div>
      </header>

      ${renderAthleteCard(a)}
      ${renderHeadline(a, scores)}
      ${renderRadar(scores)}

      <div class="cat-grid">
        ${renderCategoryCard('B1_StridePosture', scores, a)}
        ${renderCategoryCard('B2_StrideRotation', scores, a)}
        ${renderCategoryCard('B3_SwingPosture', scores, a)}
        ${renderCategoryCard('B4_SwingRotation', scores, a)}
        ${renderCategoryCard('B5_CoG', scores, a)}
        ${renderCategoryCard('B6_BatPath', scores, a)}
        ${renderCategoryCard('B7_Consistency', scores, a)}
        ${renderCategoryCard('F_Fitness', scores, a)}
      </div>

      ${renderFaults(a)}
      ${renderCoachNotes(scores, a)}
      ${renderMethodNote()}

      <footer class="report-foot">
        Generated ${new Date().toLocaleString('ko-KR')} · Uplift Hitting Report v1.0
      </footer>
    </div>
  `;

  document.getElementById('app').innerHTML = html;
}

// 자동 실행
if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', renderReport);
  } else {
    renderReport();
  }
}
