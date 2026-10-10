import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { createHash } from 'node:crypto';

const cfg = JSON.parse(await fs.readFile(process.argv[2], 'utf8'));
const base = path.join(cfg.modules, 'pdfjs-dist');
const { createCanvas } = await import(pathToFileURL(path.join(cfg.modules, '@napi-rs/canvas/index.js')));
const { getDocument, version } = await import(pathToFileURL(path.join(base, 'legacy/build/pdf.mjs')));
const data = new Uint8Array(await fs.readFile(cfg.source));
const options = { disableFontFace: true, useSystemFonts: false, isEvalSupported: false,
  standardFontDataUrl: path.join(base, 'standard_fonts') + path.sep };
const plain = await getDocument({ ...options, data: data.slice() }).promise;
const reference = await getDocument({ ...options, data: data.slice(),
  cMapUrl: path.join(base, 'cmaps') + path.sep, cMapPacked: true }).promise;
const result = { ok: true, engine: 'PDF.js', version, source: cfg.source, pages: [], errors: [],
  limitations: ['对照检查检测外部 CMap 依赖；不能发现两种渲染共同存在的错误，也不替代 Codex 实际面板和版式审阅'] };
let selection = Array.from({ length: plain.numPages }, (_, i) => i + 1);
if (cfg.pages) {
  selection = [];
  for (const part of cfg.pages.split(',')) {
    if (!/^\d+(-\d+)?$/.test(part)) throw new Error('页码使用 1,3-5');
    const [first, last = first] = part.split('-').map(Number);
    if (first < 1 || last < first || last > plain.numPages) throw new Error('页码超出范围');
    for (let n = first; n <= last; n++) if (!selection.includes(n)) selection.push(n);
  }
}
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
async function render(pdf, number) {
  const page = await pdf.getPage(number);
  const viewport = page.getViewport({ scale: 1.5 });
  if (viewport.width * viewport.height > 30000000) throw new Error('页面尺寸超过渲染限制');
  const canvas = createCanvas(Math.ceil(viewport.width), Math.ceil(viewport.height));
  const context = canvas.getContext('2d');
  await page.render({ canvasContext: context, viewport }).promise;
  const text = (await page.getTextContent()).items.map(item => item.str || '').join('');
  const pixels = context.getImageData(0, 0, canvas.width, canvas.height).data;
  const value = { text, han: (text.match(/\p{Script=Han}/gu) || []).length, hash: hash(pixels), png: canvas.toBuffer('image/png') };
  page.cleanup();
  return value;
}
let fullText = '';
try {
  for (const number of selection) {
    try {
      const a = await render(plain, number), b = await render(reference, number);
      const textEqual = a.text === b.text, pixelsEqual = a.hash === b.hash;
      const filename = `page-${String(number).padStart(3, '0')}.png`;
      await fs.writeFile(path.join(cfg.output, filename), a.png);
      if (!pixelsEqual) await fs.writeFile(path.join(cfg.output, `reference-${filename}`), b.png);
      const record = { page: number, text_equal: textEqual, pixels_equal: pixelsEqual,
        han_characters: a.han, reference_han_characters: b.han, image: filename, text: a.text, pixel_sha256: a.hash };
      result.pages.push(record);
      fullText += a.text;
      if (!textEqual || !pixelsEqual) result.errors.push({ page: number, reason: '有无外部 CMap 的文本或像素不一致' });
      if (a.text.includes('\uFFFD')) result.errors.push({ page: number, reason: '文字提取含替代字符' });
    } catch (error) {
      result.errors.push({ page: number, reason: String(error) });
    }
  }
  const compact = text => text.replace(/\s+/gu, '');
  for (const text of cfg.expected) if (!result.pages.some(page => compact(page.text).includes(compact(text)))) {
    result.errors.push({ expected: text, reason: '指定文字未在所选页面检出（匹配忽略排版空白）' });
  }
  result.ok = result.errors.length === 0 && result.pages.length === selection.length;
  result.total_pages = plain.numPages;
  result.checked_pages = selection;
  await fs.writeFile(path.join(cfg.output, 'preview.json'), JSON.stringify(result, null, 2));
} finally {
  await plain.destroy();
  await reference.destroy();
}
