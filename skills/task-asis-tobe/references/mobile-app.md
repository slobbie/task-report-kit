# 모바일 앱 캡처 (iOS 시뮬레이터, Android 에뮬레이터)

React Native(Expo 개발 빌드) 기준으로 검증한 방법이다. 다른 스택도 순서는 같고 빌드 명령만 프로젝트에 맞춘다.

## 기기와 빌드

- 기기 확인: `xcrun simctl list devices available`, `~/Library/Android/sdk/emulator/emulator -list-avds`, `adb devices`
- 부팅: `xcrun simctl boot <UDID>; open -a Simulator`, Android는 `emulator -avd <이름> -no-snapshot-save -no-audio`를 백그라운드로 실행
- 빌드 명령과 앱 ID는 `package.json` 스크립트, `app.config.*`, `.env*`, `env.js`에서 찾는다. 추측하지 않는다.
- Expo 개발 빌드는 Metro를 따로 띄우고 빌드는 `--no-bundler`로 실행하면 두 플랫폼이 Metro 하나를 같이 쓴다.
  ```
  CI=1 APP_ENV=<env> npx expo run:ios --configuration Debug --scheme <scheme> --device "<시뮬레이터 이름>" --no-bundler
  CI=1 APP_ENV=<env> npx expo run:android --variant=<variant> --no-bundler
  ```
- 빌드는 각각 10분 이상 걸릴 수 있다. 백그라운드로 돌리고 그동안 코드를 읽는다.

## Metro

- **Metro를 `CI=1`로 띄우지 않는다.** CI 모드는 파일 감시가 꺼져서 코드를 고쳐도 앱에 반영되지 않는다. 백그라운드 실행은 `npx expo start --dev-client --port 8081 < /dev/null`처럼 표준 입력만 막는다.
- Android는 `adb reverse tcp:8081 tcp:8081` 후 개발 클라이언트 첫 화면에서 서버 주소(`http://10.0.2.2:8081`)를 누른다.
- 코드 반영 확인: `curl -s "http://localhost:8081/index.bundle?platform=ios&dev=true" | grep -c <새 컴포넌트 이름>`

## 개발 도구 오버레이 끄기

- iOS Expo 톱니 버튼: `xcrun simctl spawn booted defaults write <번들ID> EXDevMenuShowFloatingActionButton -bool NO` 후 앱 재실행
- Android: 개발 메뉴의 "Tools button" 토글을 끈다. 처음 실행 시 개발 메뉴 안내가 뜨면 "Continue"를 누른다.

## Android 설치 실패

- `INSTALL_FAILED_INSUFFICIENT_STORAGE`나 `not enough space`가 나면 기기 아키텍처 전용으로 다시 빌드한다. 크기가 3분의 1 정도로 준다.
  ```
  adb shell getprop ro.product.cpu.abi
  cd android && ./gradlew app:assemble<Variant> -PreactNativeArchitectures=<abi>
  adb install app/build/outputs/apk/<...>.apk
  ```
- 기존 앱을 지워야 하면 사용자 기기 상태를 바꾸는 일이므로 보고 때 알린다.

## Maestro 조작

- 실행: `maestro --device <UDID 또는 emulator-5554> test -e APP_ID=<앱ID> -e OUT=<캡처 폴더> flow.yaml`
- 앱이 로그인된 상태로 뜨면 흐름 시작 전에 로그아웃한다(키체인이 남아 재설치해도 로그인이 유지될 수 있다).
- iOS
  - 접근성 이름이 합쳐진다("Cart, tab, 2 of 3"). 부분 일치 정규식 `".*Cart.*"`로 찾는다.
  - 바텀시트, 커스텀 모달 안의 요소는 계층에 안 잡히는 경우가 많다. 스크린샷을 보고 좌표로 누른다: `tapOn: { point: "50%,84%" }`
  - **좌표에 소수점을 쓰면 오류가 난다.** 정수 퍼센트만 쓴다.
  - `extendedWaitUntil`가 시트 뒤 제목을 못 찾으면 `waitForAnimationToEnd`로 바꾼다.
- Android
  - 텍스트가 계층에 잘 잡힌다. 같은 글자가 여러 개면 `index`보다 좌표가 안전하다(엉뚱한 요소를 누른 사례가 있다).
  - 시스템 권한 창은 `tapOn: { text: "Don.t allow", optional: true }`로 닫는다(곡선 따옴표라 정규식 `.` 사용).
  - **`inputText`로 한글을 넣을 수 없다.** 한글 자판의 낱자를 차례로 누른다(`tapOn: "ㅗ"` 등). 첫 자음이 다른 요소와 겹치면 좌표로 누른다. 잘못 들어가면 `eraseText: 10`으로 지운다.
- 흐름이 중간에 실패하면 전체를 다시 돌리지 말고 현재 화면을 찍어 상태를 보고, 실패 지점부터 이어지는 흐름 파일을 따로 만들어 돌린다. 처음부터 다시 돌리면 엉뚱한 화면에서 탭이 실행된다.

## 캡처

- iOS: `xcrun simctl io booted screenshot <png>`, Android: `adb exec-out screencap -p > <png>`
- 확인용 축소: `sips -Z 500 <png> --out <작은png>`
- 로딩처럼 금방 지나가는 화면: 동작을 실행하는 Maestro와 동시에 0.25~0.3초 간격으로 10초 정도 연속 캡처하고, 파일 크기가 가장 작은 장(대개 흰 화면에 스피너)부터 열어 본다. Maestro는 시작에 몇 초 걸리므로 캡처 구간을 넉넉히 잡는다.

## 번호 표시 좌표

- Maestro가 읽는 요소: `maestro --device <ID> hierarchy`의 `bounds`(픽셀)를 캡처 크기로 나눠 퍼센트로 바꾼다.
- 읽히지 않는 요소(iOS 바텀시트, 커스텀 모달 등): 캡처 이미지에서 글자와 배경색이 바뀌는 줄을 측정해 위치를 잡는다(macOS는 `sips -s format bmp`로 바꿔 행별 픽셀을 읽으면 외부 패키지 없이 측정할 수 있다).
- 같은 항목의 iOS와 Android는 화면 크기가 달라 좌표를 각각 잡는다.
