const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { PNG } = require('pngjs');
const jpeg = require('jpeg-js');

const root = path.resolve(__dirname, '..', '..');
const fixtures = path.join(root, 'tests', 'fixtures');
const html = fs.readFileSync(path.join(root, 'radar_gpa.html'), 'utf8');
const scriptMatch = html.match(/<script>([\s\S]*)<\/script>/);
assert(scriptMatch, 'radar_gpa.html 中缺少内联脚本');
const coreMatch = scriptMatch[1].match(
  /\/\* radar-gpa-core:start \*\/([\s\S]*?)\/\* radar-gpa-core:end \*\//,
);
assert(coreMatch, 'radar_gpa.html 中缺少算法核心边界标记');
assert(
  html.includes("colorSpaceConversion:'none'"),
  '浏览器解码必须禁用 JPEG 色彩转换，否则学分边界会漂移',
);
assert(!html.includes('.innerHTML='), '课程数据不得通过 innerHTML 写入页面');
const core = new Function(
  `${coreMatch[1]}\nreturn {detect,calculate,courseIndexAtPosition,recalculateCourseGeometry};`,
)();

const cases = [
  ['SYNTHETIC_TERM_1.jpg', 10, 92.98, 3.87, 21.5],
  ['SYNTHETIC_TERM_2.jpg', 16, 91.75, 3.74, 36.0],
  ['Test 2.jpg', 16, 91.91, 3.87, 33.5],
  ['Test 3.jpg', 14, 93.15, 3.88, 30.5],
];

function readImage(file) {
  const bytes = fs.readFileSync(file);
  const pngSignature = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
  if (bytes.subarray(0, pngSignature.length).equals(pngSignature)) {
    return PNG.sync.read(bytes);
  }
  if (bytes[0] === 0xff && bytes[1] === 0xd8) {
    return jpeg.decode(bytes, { useTArray: true });
  }
  throw new Error(`无法识别测试图片格式：${path.basename(file)}`);
}

(async () => {
  for (const [name, expectedCount, expectedWeighted, expectedGpa, expectedCredits] of cases) {
    const image = readImage(path.join(fixtures, name));
    const result = core.detect(
      { data: image.data },
      image.width,
      image.height,
    );
    core.calculate(result);

    const diagnostic = JSON.stringify({name, center: result.center, centerDetection: result.centerDetection, count: result.courses.length, countRanked: result.countDetection.ranked.slice(0, 6), innerRadius: result.innerRadius, maxCredit: result.maxCredit, scores: result.courses.map(c => c.score), creditBoundaries: result.courses.map(c => [c.creditBoundary, c.creditSignal]), courseCredits: result.courses.map(c => c.credit), summary: result.summary});
    assert.strictEqual(result.courses.length, expectedCount, diagnostic);
    assert(Math.abs(result.summary.weighted - expectedWeighted) <= 1.0, diagnostic);
    assert(Math.abs(result.summary.gpa - expectedGpa) <= 0.08, diagnostic);
    assert(Math.abs(result.summary.credits - expectedCredits) <= 0.5, diagnostic);

    console.log(JSON.stringify({
      name,
      count: result.courses.length,
      scores: result.courses.map(c => c.score),
      courseCredits: result.courses.map(c => c.credit),
      summary: result.summary,
      confidence: result.confidence,
      center: result.center,
      innerRadius: result.innerRadius,
      axisCountRanked: result.axisCountDetection?.ranked.slice(0, 8),
      periodicScore: result.periodicScore,
    }, null, 2));

    if (name === 'Test 3.jpg') {
      const oldRadius = result.innerRadius;
      const oldScore = result.courses[0].score;
      result.innerRadius *= 1.05;
      core.recalculateCourseGeometry(result);
      assert.strictEqual(result.outerRadius, result.innerRadius * 1.5, '调整外圆后学分外径必须同步');
      assert(result.courses[0].score <= oldScore, '放大外圆后同一成绩点不应得到更高成绩');
      assert.strictEqual(core.courseIndexAtPosition(result, { x: result.center.x, y: result.center.y + oldRadius }), 4, '点击位置必须吸附到最近课程轴');
    }
  }

  const altered = readImage(path.join(fixtures, 'occluded-sample.jpg'));
  const result = core.detect({ data: altered.data }, altered.width, altered.height);
  core.calculate(result);
  assert.strictEqual(result.courses.length, 17, JSON.stringify({ center: result.center, count: result.courses.length }));
  assert(Math.abs(result.center.x - 396) <= 12 && Math.abs(result.center.y - 936) <= 12, JSON.stringify(result.center));
  assert.strictEqual(result.displayedCredits?.text, '38.0', JSON.stringify(result.displayedCredits));
  assert.strictEqual(result.summary.credits, 38, JSON.stringify(result.summary));
  assert(Math.abs(result.innerRadius - 327) <= 4, JSON.stringify(result.radiusDetection));
  assert(result.courses.some(course => course.score < 100), '遮挡图不得再把所有成绩误判为 100');
  assert.strictEqual(result.creditConstraint?.reference, 'TERM_B', JSON.stringify(result.creditConstraint));
  assert.strictEqual(result.creditConstraint?.insertedCredit, 2, JSON.stringify(result.creditConstraint));
  assert.deepStrictEqual(
    result.courses.map(course => course.credit),
    [4, 3, 1, 4, 2, 2, 1, 2, 1, 3, 1, 2, 5, 3, 2, 1, 1],
  );
  assert(result.confidence < 72, `遮挡图置信度不应为 ${result.confidence}%`);
  assert(result.courses.every(c => c.point && Number.isFinite(c.score) && Number.isFinite(c.credit)), '遮挡图必须为每条轴生成可拖拽点');
  console.log(JSON.stringify({
    name: 'occluded-sample.jpg（带涂鸦）',
    count: result.courses.length,
    confidence: result.confidence,
    center: result.center,
    radarRegion: result.radarRegion,
    displayedCredits: result.displayedCredits,
    creditConstraint: result.creditConstraint,
    innerRadius: result.innerRadius,
    axisCountRanked: result.axisCountDetection?.ranked.slice(0, 8),
    scores: result.courses.map(c => c.score),
    credits: result.courses.map(c => c.credit),
    summary: result.summary,
    note: '遮挡图使用顶部学分卡约束总学分，并保留低置信度提示',
  }, null, 2));
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
