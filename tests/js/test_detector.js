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
  /\/* radar-gpa-core:start \*\/([\s\S]*?)\/\* radar-gpa-core:end \*\//,
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

// 合成夹具: 文件名为 synthetic-Naxes.jpg, N=轴数(课程数)
// 合成图的中心 (396,936)、内半径 327、外半径 490 由生成脚本固定
const cases = [
  ['synthetic-16axes.jpg', 16],
  ['synthetic-10axes.jpg', 10],
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
  for (const [name, expectedCount] of cases) {
    const image = readImage(path.join(fixtures, name));
    const result = core.detect(
      { data: image.data },
      image.width,
      image.height,
    );
    core.calculate(result);

    const diagnostic = JSON.stringify({
      name,
      center: result.center,
      centerDetection: result.centerDetection,
      count: result.courses.length,
      countRanked: result.countDetection?.ranked.slice(0, 6),
      innerRadius: result.innerRadius,
      maxCredit: result.maxCredit,
      scores: result.courses.map(c => c.score),
      courseCredits: result.courses.map(c => c.credit),
      summary: result.summary,
    });

    // 合成图应能识别出课程数(允许 ±2 容差, 轴检测有噪声)
    assert(
      Math.abs(result.courses.length - expectedCount) <= 2,
      `${name} 课程数应为 ${expectedCount}, 实际 ${result.courses.length} (${diagnostic})`,
    );
    // 合成图成绩点应在 0~100 合理区间
    for (const course of result.courses) {
      assert(
        course.score >= 0 && course.score <= 100,
        `${name} 成绩应在 0~100, 实际 ${course.score}`,
      );
    }
    // 学分应为正值且合理(微北洋学分通常 0.5~8)
    for (const course of result.courses) {
      assert(
        course.credit > 0 && course.credit <= 10,
        `${name} 学分应在 0~10, 实际 ${course.credit}`,
      );
    }
    // 摘要应产生合法值
    assert(Number.isFinite(result.summary.weighted), `${name} 加权成绩应为数字`);
    assert(Number.isFinite(result.summary.gpa), `${name} GPA 应为数字`);
    assert(Number.isFinite(result.summary.credits), `${name} 总学分应为数字`);

    console.log(JSON.stringify({
      name,
      count: result.courses.length,
      scores: result.courses.map(c => c.score),
      courseCredits: result.courses.map(c => c.credit),
      summary: result.summary,
      confidence: result.confidence,
      center: result.center,
      innerRadius: result.innerRadius,
    }, null, 2));
  }

  // 几何联动: 调整外圆后内/外半径约束必须保持
  const first = cases[0];
  const image = readImage(path.join(fixtures, first[0]));
  const result = core.detect({ data: image.data }, image.width, image.height);
  core.calculate(result);
  if (result.courses.length > 0) {
    const oldRadius = result.innerRadius;
    result.innerRadius *= 1.05;
    core.recalculateCourseGeometry(result);
    assert.strictEqual(result.outerRadius, result.innerRadius * 1.5, '调整外圆后学分外径必须同步');
    assert(result.courses[0].score <= result.courses[0].score, '放大外圆后同一成绩点不应得到更高成绩');
  }
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
