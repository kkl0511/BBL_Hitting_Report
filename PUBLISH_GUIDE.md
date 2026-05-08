# GitHub Desktop으로 배포하기

이 ZIP 파일은 이미 git 저장소가 초기화되어 있고 첫 커밋이 만들어져 있습니다. GitHub Desktop에서 두어 번 클릭만 하면 GitHub에 올라갑니다.

---

## 절차

### 1. ZIP 압축 해제

`Uplift_Hitting_Report_v1.zip`을 GitHub 폴더에 압축 해제합니다. 보통 GitHub Desktop이 사용하는 기본 폴더는:

- **macOS**: `~/Documents/GitHub/`
- **Windows**: `C:\Users\<사용자명>\Documents\GitHub\`

압축 해제 후 폴더 이름이 `Uplift_Hitting_Report` 인지 확인하세요. (ZIP 안의 최상위 폴더 이름이 그대로 사용됩니다.)

### 2. GitHub Desktop에서 로컬 저장소 추가

1. GitHub Desktop 앱 열기
2. 상단 메뉴 **File → Add Local Repository...** 클릭
3. **Choose...** 버튼 → 위에서 압축 해제한 `Uplift_Hitting_Report` 폴더 선택
4. **Add Repository** 클릭

> 💡 만약 "This directory does not appear to be a Git repository" 같은 메시지가 뜨면 ZIP이 제대로 풀린 게 맞는지 (`.git` 숨김 폴더가 폴더 안에 있어야 함) 확인하세요.

### 3. GitHub에 게시

1. GitHub Desktop 화면 상단의 **Publish repository** 버튼 (또는 메뉴 Repository → Push) 클릭
2. 다이얼로그에서:
   - **Name**: `Uplift_Hitting_Report` (그대로 두기)
   - **Description**: `타격 바이오메카닉스 리포트 (Driveline 5-카테고리 + KBO 코호트)` (선택)
   - **Keep this code private**: 비공개로 시작하려면 체크 (나중에 GitHub 웹에서 public 전환 가능)
   - **Organization**: 개인 계정에 올리려면 None
3. **Publish Repository** 클릭

완료. 이제 `https://github.com/kkl0511/Uplift_Hitting_Report`에 코드가 올라갔습니다.

---

## 첫 커밋 메시지 예시 (이미 들어가 있음)

```
v1.0: Initial release

Uplift Hitting Report v1.0 — Driveline 5-카테고리 모델 + KBO 코호트(합성).
...
```

원치 않으시면 GitHub Desktop의 History 탭에서 우클릭 → "Amend Last Commit"으로 메시지를 바꿀 수 있습니다.

---

## 이후 워크플로 (참고용)

투수 리포트와 동일하게 작업하시면 됩니다:

```
1. 파일 수정
2. GitHub Desktop이 자동 감지 → 좌측 Changes 탭에 변경사항 표시
3. 좌측 하단에 커밋 메시지 입력 → "Commit to main"
4. 우측 상단 Push origin 클릭 → GitHub 반영
```

또는 GitHub 웹에서 새 파일을 직접 편집하면 GitHub Desktop에서 "Fetch origin" 후 자동 동기화됩니다.

---

## 만약 GitHub CLI(`gh`) 또는 터미널 사용을 선호하시면

```bash
cd ~/Documents/GitHub/Uplift_Hitting_Report
gh repo create Uplift_Hitting_Report --private --source=. --push
```

또는 GitHub 웹에서 빈 repo `Uplift_Hitting_Report`를 먼저 만든 뒤:

```bash
cd ~/Documents/GitHub/Uplift_Hitting_Report
git remote add origin https://github.com/kkl0511/Uplift_Hitting_Report.git
git push -u origin main
```
