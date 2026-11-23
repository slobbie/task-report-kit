# 웹 서비스 캡처 (Playwright)

기본은 **데스크톱(1440x900)과 모바일(390x844, 3배율)** 두 화면 크기를 플랫폼처럼 나눠 찍는다. 사용자가 브라우저나 화면 크기를 정하면 그에 맞춘다.

## 준비

- 프로젝트에 Playwright나 Cypress 같은 E2E 도구가 이미 있으면 그 도구와 설정(baseURL, 로그인 헬퍼)을 우선 쓴다.
- 없으면 프로젝트에 의존성을 추가하지 말고 `<작업 폴더>`에 설치한다.
  ```
  cd <작업 폴더>/webcap && npm init -y && npm i playwright
  ```
  Playwright 전용 브라우저를 받지 않아도 된다. 캡처 스크립트가 실패하면 설치된 Chrome(`channel: 'chrome'`)으로 다시 실행한다.
- 개발 서버 실행 명령은 `package.json` 스크립트에서 찾고 백그라운드로 띄운다. 파일 감시(HMR)가 켜진 모드인지 확인한다. 코드를 고친 뒤 예전 화면이 나오면 서버를 다시 띄운다.

## 캡처 스크립트

`scripts/web_capture.mjs`에 흐름(steps) 파일 하나를 넘긴다. **같은 steps 파일을 AS-IS와 TO-BE에 그대로 써서** 같은 단계가 나란히 비교되게 한다. 사라지는 단계는 TO-BE steps에서만 빼고, 번호는 맞춘다.

```
cd <작업 폴더>/webcap
node <스킬 폴더>/scripts/web_capture.mjs steps.mjs shots asis   # 코드 수정 전
node <스킬 폴더>/scripts/web_capture.mjs steps.mjs shots tobe   # 코드 수정 후
```

steps 파일 예시는 스크립트 첫머리 주석에 있다. 결과는 `shots/<desktop|mobile>/<asis|tobe>-<라벨>.png`로 저장된다. 단계가 실패하면 `<asis|tobe>-FAILED.png`에 그 시점 화면을 남기고 오류를 출력한다.

## 요소 찾기

- `getByRole('button', { name: '다음' })`, `getByLabel`, `getByText` 순서로 쓴다. CSS 선택자는 마지막 수단이다.
- 반응형으로 데스크톱과 모바일의 요소가 다르면 `run(page, shot, { viewport })`의 세 번째 인자로 분기한다.
- 모달, 토스트처럼 금방 사라지는 화면은 동작 직후 `shot()`을 바로 부르고, 필요하면 응답을 늦추는 대신 `page.route()`로 해당 API 응답을 잡아 두고 찍는다.

## 개발 서버를 쓸 수 없을 때

운영 주소로 찍을 수 있다. 처음 한 번 사용자 확인, 보기만 하기, 응답 바꾸지 않기, 개인정보 가리기 같은 조건은 [capture-policy.md](capture-policy.md)를 따른다. steps 파일의 `baseURL`만 운영 주소로 바꾸고, 저장이나 전송 버튼을 누르는 단계는 넣지 않는다.

## 테스트 데이터와 외부 호출

- 로그인이 필요하면 테스트 계정을 사용자에게 받는다. 없으면 `page.route()`로 API 응답을 바꿔 화면만 넘긴다. 이 방법은 앱 코드를 고치지 않으므로 `TEMP-CAPTURE` 코드를 남길 위험이 없다.
- 결제, 문자 발송, 외부 인증 요청은 실제로 보내지 않는다. `page.route()`로 막거나 그 단계는 캡처하지 않고 보고 때 알린다.

## 확인

- 찍은 화면은 `sips -Z 500`(macOS) 등으로 줄여 직접 열어 본다.
- 화면 전체가 필요하면 `shot('라벨', { fullPage: true })`를 쓴다. 비교 보고서에서는 같은 단계의 AS-IS와 TO-BE가 같은 옵션이어야 한다.
