// 웹 화면 캡처 스크립트 (Playwright)
// 사용법: node web_capture.mjs <steps.mjs> <출력폴더> [asis|tobe]
//
// steps.mjs 는 아래 형식으로 작성한다. 같은 steps를 AS-IS와 TO-BE에 그대로 쓴다.
//   export const baseURL = 'http://localhost:3000';
//   export const viewports = {             // 생략하면 아래 기본값
//     desktop: { width: 1440, height: 900 },
//     mobile: { width: 390, height: 844, isMobile: true, deviceScaleFactor: 3, hasTouch: true },
//   };
//   export async function run(page, shot) {
//     await page.goto('/login');
//     await shot('01-login');                       // <출력폴더>/<뷰포트>/<단계>-01-login.png
//     await page.getByRole('button', { name: '다음' }).click();
//     await page.getByText('주문 정보').waitFor();
//     await shot('02-order');
//     // 번호 표시가 필요하면 요소와 설명을 넘긴다. <파일>.marks.json에 이미지 대비 퍼센트 좌표가 저장된다.
//     await shot('03-detail', { marks: [
//       { n: 1, selector: '[data-testid="price"]', text: '가격 표시 위치가 바뀝니다.' },
//     ] });
//   }
import path from 'node:path';
import fs from 'node:fs';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';

const [stepsPath, outDir, stage = 'asis'] = process.argv.slice(2);
if (!stepsPath || !outDir) {
  console.error('usage: node web_capture.mjs <steps.mjs> <outDir> [asis|tobe]');
  process.exit(1);
}

// 이 스크립트는 스킬 폴더에 있으므로, 실행한 폴더(프로젝트나 작업 폴더)의 playwright를 쓴다
const requireFromCwd = createRequire(path.join(process.cwd(), 'noop.js'));
const { chromium } = requireFromCwd('playwright');
const steps = await import(pathToFileURL(path.resolve(stepsPath)).href);
const viewports = steps.viewports ?? {
  desktop: { width: 1440, height: 900 },
  mobile: { width: 390, height: 844, isMobile: true, deviceScaleFactor: 3, hasTouch: true },
};

// Playwright 전용 브라우저가 없으면 설치된 Chrome으로 실행한다 (npx playwright install 생략 가능)
const browser = await chromium.launch().catch(() => chromium.launch({ channel: 'chrome' }));
let failed = false;
for (const [name, vp] of Object.entries(viewports)) {
  const { width, height, ...rest } = vp;
  const context = await browser.newContext({
    viewport: { width, height },
    baseURL: steps.baseURL,
    locale: 'ko-KR',
    ...rest,
  });
  const page = await context.newPage();
  const dir = path.join(outDir, name);
  fs.mkdirSync(dir, { recursive: true });
  const shot = async (label, opts = {}) => {
    await page.waitForLoadState('networkidle').catch(() => {});
    const file = path.join(dir, `${stage}-${label}.png`);
    await page.screenshot({ path: file, fullPage: opts.fullPage ?? false });
    if (opts.marks?.length) {
      // 요소의 실제 위치를 캡처 이미지 대비 퍼센트로 저장한다 (build_report.py의 marks에 경로로 넘긴다)
      const fullPage = opts.fullPage ?? false;
      const size = await page.evaluate((fp) => ({
        w: fp ? document.documentElement.scrollWidth : innerWidth,
        h: fp ? document.documentElement.scrollHeight : innerHeight,
        sx: fp ? 0 : scrollX,
        sy: fp ? 0 : scrollY,
      }), fullPage);
      const out = [];
      for (const mk of opts.marks) {
        const box = await page.locator(mk.selector).first().evaluate((el) => {
          const r = el.getBoundingClientRect();
          return { x: r.left + scrollX, y: r.top + scrollY, w: r.width, h: r.height };
        }).catch(() => null);
        if (!box) { console.error(`  번호 ${mk.n}: 요소를 찾지 못함 ${mk.selector}`); continue; }
        const pad = 4;
        out.push({
          n: mk.n,
          x: +(((box.x - size.sx - pad) / size.w) * 100).toFixed(2),
          y: +(((box.y - size.sy - pad) / size.h) * 100).toFixed(2),
          w: +(((box.w + pad * 2) / size.w) * 100).toFixed(2),
          h: +(((box.h + pad * 2) / size.h) * 100).toFixed(2),
          text: mk.text ?? '',
        });
      }
      fs.writeFileSync(file.replace(/\.png$/, '.marks.json'), JSON.stringify(out, null, 1));
    }
    console.log(`shot ${name} ${file}`);
  };
  try {
    await steps.run(page, shot, { viewport: name });
  } catch (e) {
    failed = true;
    const file = path.join(dir, `${stage}-FAILED.png`);
    await page.screenshot({ path: file }).catch(() => {});
    console.error(`FAILED ${name}: ${e.message}\n  현재 화면: ${file}`);
  }
  await context.close();
}
await browser.close();
process.exit(failed ? 1 : 0);
