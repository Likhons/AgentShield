// Renders thumbnail.html to agentshield_thumbnail.png (1280x720, YouTube) via a 2x screenshot, downscaled by ffmpeg.
//   node video/thumbnail/render.cjs
// Needs Playwright (PLAYWRIGHT_DIR, default: the npx cache copy used for the film captures), Microsoft Edge and ffmpeg.
const path = require('path');
const { execFileSync } = require('child_process');
const pw = process.env.PLAYWRIGHT_DIR || 'C:/Users/User/AppData/Local/npm-cache/_npx/9833c18b2d85bc59/node_modules/playwright';
const { chromium } = require(pw);

(async () => {
  const dir = __dirname;
  const big = path.join(dir, 'thumbnail@2x.png');
  const out = path.join(dir, 'agentshield_thumbnail.png');
  const browser = await chromium.launch({ channel: 'msedge', args: ['--allow-file-access-from-files'] });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 2 });
  await page.goto('file:///' + path.join(dir, 'thumbnail.html').replace(/\\/g, '/'));
  await page.evaluate(() => document.fonts.ready);
  const fonts = await page.evaluate(() => ['800 76px Bricolage', 'italic 500 84px Fraunces', '600 24px Jakarta', '700 27px JBMono', '700 31px Anek', '500 25px Baloo']
    .map((f) => [f, document.fonts.check(f)]));
  console.log('fonts', JSON.stringify(fonts));
  if (fonts.some(([, ok]) => !ok)) throw new Error('a font did not load');
  await page.screenshot({ path: big });
  await browser.close();
  execFileSync('ffmpeg', ['-v', 'error', '-y', '-i', big, '-vf', 'scale=1280:720:flags=lanczos', out]);
  require('fs').unlinkSync(big);
  console.log('saved', out);
})().catch((e) => { console.error(e); process.exit(1); });
