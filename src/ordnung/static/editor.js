/* Ordnung! – PDF editor: fill forms, add text, ticks and a signature.
 * PDF.js shows the pages, pdf-lib writes the result. The original stays as it
 * is, the edited PDF is stored next to it as a new document. */
'use strict';

Object.assign(I18N.de, {
  'pv.edit': 'Bearbeiten',
  'ed.back': '← Zurück', 'ed.text': 'Text', 'ed.check': 'Haken', 'ed.cross': 'Kreuz', 'ed.date': 'Datum',
  'ed.sign': 'Unterschrift', 'ed.save': 'Speichern …', 'ed.zoomin': 'Größer', 'ed.zoomout': 'Kleiner',
  'ed.hint': 'Felder direkt ausfüllen. Für Text, Haken, Datum oder Unterschrift oben wählen und auf die Seite tippen.',
  'ed.hint.place': 'Auf die Stelle tippen, wo es hin soll. Esc bricht ab.',
  'ed.loading': 'Lade PDF …', 'ed.fields': '{n} Formularfelder',
  'ed.del': 'Entfernen', 'ed.move': 'Verschieben', 'ed.size': 'Größe ändern',
  'ed.leave': 'Änderungen verwerfen?',
  'ed.err.encrypted': 'Diese PDF ist geschützt und lässt sich nicht bearbeiten.',
  'ed.err.char': 'Das Zeichen „{c}“ kann Ordnung! nicht in die PDF schreiben.',
  'ed.err.load': 'Die PDF ließ sich nicht öffnen: {msg}',
  'ed.sv.title': 'Als neues Dokument speichern', 'ed.sv.name': 'Titel', 'ed.sv.date': 'Datum',
  'ed.sv.flatten': 'Formular festschreiben (Felder lassen sich danach nicht mehr ändern)',
  'ed.sv.hint': 'Das Original bleibt unverändert. Die neue Datei kommt in denselben Ordner, Tags werden übernommen.',
  'ed.sv.ok': 'Speichern', 'ed.sv.cancel': 'Abbrechen', 'ed.sv.suffix': 'bearbeitet', 'ed.sv.busy': 'Speichere …',
  'ed.sv.nothing': 'Es gibt noch keine Änderung.',
  'sg.title': 'Deine Unterschrift', 'sg.hint': 'Mit Maus, Finger oder Stift ins Feld schreiben, oder ein Foto deiner Unterschrift laden (weißes Papier wird durchsichtig).',
  'sg.clear': 'Leeren', 'sg.upload': 'Bild laden …', 'sg.remove': 'Gespeicherte löschen', 'sg.use': 'Speichern und einsetzen',
  'sg.cancel': 'Abbrechen', 'sg.empty': 'Bitte erst unterschreiben.', 'sg.new': 'Neu unterschreiben',
  'sg.remove.q': 'Gespeicherte Unterschrift löschen?',
});
Object.assign(I18N.en, {
  'pv.edit': 'Edit',
  'ed.back': '← Back', 'ed.text': 'Text', 'ed.check': 'Tick', 'ed.cross': 'Cross', 'ed.date': 'Date',
  'ed.sign': 'Signature', 'ed.save': 'Save …', 'ed.zoomin': 'Larger', 'ed.zoomout': 'Smaller',
  'ed.hint': 'Fill in fields directly. For text, ticks, date or signature pick a tool above and tap the page.',
  'ed.hint.place': 'Tap where it should go. Esc cancels.',
  'ed.loading': 'Loading PDF …', 'ed.fields': '{n} form fields',
  'ed.del': 'Remove', 'ed.move': 'Move', 'ed.size': 'Resize',
  'ed.leave': 'Discard changes?',
  'ed.err.encrypted': 'This PDF is protected and cannot be edited.',
  'ed.err.char': 'Ordnung! cannot write the character “{c}” into the PDF.',
  'ed.err.load': 'Could not open the PDF: {msg}',
  'ed.sv.title': 'Save as new document', 'ed.sv.name': 'Title', 'ed.sv.date': 'Date',
  'ed.sv.flatten': 'Flatten the form (fields cannot be changed afterwards)',
  'ed.sv.hint': 'The original stays unchanged. The new file goes into the same folder, tags are copied.',
  'ed.sv.ok': 'Save', 'ed.sv.cancel': 'Cancel', 'ed.sv.suffix': 'edited', 'ed.sv.busy': 'Saving …',
  'ed.sv.nothing': 'Nothing has been changed yet.',
  'sg.title': 'Your signature', 'sg.hint': 'Sign in the box with mouse, finger or pen, or load a photo of your signature (white paper becomes transparent).',
  'sg.clear': 'Clear', 'sg.upload': 'Load image …', 'sg.remove': 'Delete stored one', 'sg.use': 'Save and insert',
  'sg.cancel': 'Cancel', 'sg.empty': 'Please sign first.', 'sg.new': 'Sign again',
  'sg.remove.q': 'Delete the stored signature?',
});

const Ed = {
  doc: null, bytes: null, pdf: null, pages: [],   // pages: [{vp1, el, layer, rotation}]
  scale: 1, tool: null, items: [], fields: [], sel: null, seq: 0, sigImg: null, sigBytes: null,
};

const ED_TEXT_SIZE = 11;
const ED_INK = '#0a1f5c';

async function loadPdfLibs() {
  if (!window.pdfjsLib) {
    window.pdfjsLib = await import('./vendor/pdfjs/pdf.min.mjs');
    pdfjsLib.GlobalWorkerOptions.workerSrc = 'vendor/pdfjs/pdf.worker.min.mjs';
  }
  if (!window.PDFLib) {
    await new Promise((resolve, reject) => {
      const s = document.createElement('script');
      s.src = 'vendor/pdf-lib/pdf-lib.min.js';
      s.onload = resolve;
      s.onerror = () => reject(new Error('pdf-lib'));
      document.head.appendChild(s);
    });
  }
}

function edDirty() {
  return Ed.items.length > 0 || Ed.fields.some(f => fieldValue(f) !== f.initial);
}

async function openEditor(doc) {
  Object.assign(Ed, { doc, items: [], fields: [], sel: null, tool: null, pages: [] });
  $('editor').hidden = false;
  document.body.classList.add('editing');
  $('ed-title').textContent = doc.title;
  $('ed-pages').innerHTML = `<p class="ed-loading">${esc(t('ed.loading'))}</p>`;
  edHint();
  try {
    await loadPdfLibs();
    const res = await fetch(`api/documents/${doc.id}/file`, { credentials: 'same-origin' });
    if (!res.ok) throw new Error(res.status + ' ' + res.statusText);
    Ed.bytes = new Uint8Array(await res.arrayBuffer());
    Ed.pdf = await pdfjsLib.getDocument({
      data: Ed.bytes.slice(), isEvalSupported: false,
      standardFontDataUrl: new URL('vendor/pdfjs/standard_fonts/', location.href).href,
    }).promise;
    try {
      await PDFLib.PDFDocument.load(Ed.bytes, { updateMetadata: false });
    } catch (e) {
      if (/encrypt/i.test(String(e))) throw new Error(t('ed.err.encrypted'));
    }
    const box = $('ed-pages').clientWidth - 48;
    const first = await Ed.pdf.getPage(1);
    const vp = first.getViewport({ scale: 1 });
    Ed.scale = Math.max(0.5, Math.min(1.6, box / vp.width));
    await edRender(true);
  } catch (e) {
    $('ed-pages').innerHTML = `<p class="ed-loading ed-error">${esc(e.message.startsWith(t('ed.err.encrypted')) ? e.message : t('ed.err.load', { msg: e.message }))}</p>`;
  }
}

function closeEditor(force = false) {
  if (!force && edDirty() && !confirm(t('ed.leave'))) return;
  $('editor').hidden = true;
  document.body.classList.remove('editing');
  $('ed-pages').innerHTML = '';
  if (Ed.pdf) Ed.pdf.destroy();
  Object.assign(Ed, { pdf: null, bytes: null, items: [], fields: [], pages: [] });
}

function edHint() {
  $('ed-hint').textContent = Ed.tool ? t('ed.hint.place') : t('ed.hint');
  document.querySelectorAll('#editor [data-tool]').forEach(b => b.classList.toggle('is-active', b.dataset.tool === Ed.tool));
  $('ed-pages').classList.toggle('placing', !!Ed.tool);
  $('ed-zoom').textContent = Math.round(Ed.scale * 100) + ' %';
}

// ------------------------------------------------------------- rendering

async function edRender(first = false) {
  const keep = first ? null : Ed.fields.map(f => fieldValue(f));
  const host = $('ed-pages');
  host.innerHTML = '';
  Ed.pages = [];
  const dpr = window.devicePixelRatio || 1;
  const fields = [];
  for (let n = 1; n <= Ed.pdf.numPages; n++) {
    const page = await Ed.pdf.getPage(n);
    const vp1 = page.getViewport({ scale: 1 });
    const vp = page.getViewport({ scale: Ed.scale });
    const el = document.createElement('div');
    el.className = 'ed-page';
    el.style.width = vp.width + 'px';
    el.style.height = vp.height + 'px';
    const canvas = document.createElement('canvas');
    canvas.width = Math.floor(vp.width * dpr);
    canvas.height = Math.floor(vp.height * dpr);
    el.appendChild(canvas);
    const layer = document.createElement('div');
    layer.className = 'ed-layer';
    el.appendChild(layer);
    host.appendChild(el);
    const info = { n, page, vp1, el, layer };
    Ed.pages.push(info);
    layer.addEventListener('pointerdown', e => edPlace(e, info));
    await page.render({
      canvasContext: canvas.getContext('2d'), viewport: vp,
      transform: dpr !== 1 ? [dpr, 0, 0, dpr, 0, 0] : null,
      annotationMode: pdfjsLib.AnnotationMode.ENABLE_FORMS,
    }).promise;
    if (first) {
      const annots = await page.getAnnotations({ intent: 'display' });
      for (const a of annots) {
        if (a.subtype !== 'Widget' || !a.fieldName || a.pushButton || a.hidden) continue;
        fields.push({ page: n, a });
      }
    }
  }
  if (first) {
    Ed.fields = fields.map(({ page, a }) => ({
      page, name: a.fieldName, kind: edFieldKind(a), rect: a.rect, readOnly: !!a.readOnly,
      multiLine: !!a.multiLine, options: a.options || [], on: a.exportValue || a.buttonValue || 'Yes',
      value: a.fieldValue, comb: a.comb, maxLen: a.maxLen,
    })).filter(f => f.kind);
  }
  Ed.fields.forEach((f, i) => edFieldInput(f, keep ? keep[i] : undefined));
  if (first) Ed.fields.forEach(f => { f.initial = fieldValue(f); });
  Ed.items.forEach(edDrawItem);
  edHint();
  if (first && Ed.fields.length) $('ed-hint').textContent = t('ed.hint') + ' ' + t('ed.fields', { n: Ed.fields.length });
}

function edFieldKind(a) {
  if (a.fieldType === 'Tx') return 'text';
  if (a.fieldType === 'Ch') return 'choice';
  if (a.fieldType === 'Btn') return a.checkBox ? 'check' : a.radioButton ? 'radio' : null;
  return null;
}

function edFieldInput(f, keep) {
  const info = Ed.pages[f.page - 1];
  const vp = info.page.getViewport({ scale: Ed.scale });
  const [x1, y1, x2, y2] = vp.convertToViewportRectangle(f.rect);
  const box = { left: Math.min(x1, x2), top: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1) };
  let input;
  if (f.kind === 'text') {
    input = document.createElement(f.multiLine ? 'textarea' : 'input');
    input.value = keep ?? (Array.isArray(f.value) ? f.value.join('') : (f.value || ''));
    if (f.maxLen) input.maxLength = f.maxLen;
    input.style.fontSize = Math.max(8, Math.min(box.h * 0.7, 12 * Ed.scale)) + 'px';
  } else if (f.kind === 'choice') {
    input = document.createElement('select');
    input.innerHTML = '<option value=""></option>' + f.options.map(o =>
      `<option value="${esc(o.exportValue ?? o.displayValue)}">${esc(o.displayValue ?? o.exportValue)}</option>`).join('');
    input.value = keep ?? (Array.isArray(f.value) ? f.value[0] : f.value) ?? '';
  } else {
    input = document.createElement('input');
    input.type = f.kind === 'check' ? 'checkbox' : 'radio';
    if (f.kind === 'radio') input.name = 'edr-' + f.name;
    input.checked = keep !== undefined ? keep === f.on : (f.value && f.value !== 'Off' && f.value === f.on);
  }
  input.className = 'ed-field ed-field--' + f.kind;
  input.disabled = f.readOnly;
  input.title = f.name;
  Object.assign(input.style, { left: box.left + 'px', top: box.top + 'px', width: box.w + 'px', height: box.h + 'px' });
  input.addEventListener('pointerdown', e => e.stopPropagation());
  info.layer.appendChild(input);
  f.input = input;
}

function fieldValue(f) {
  if (!f.input) return f.initial;
  if (f.kind === 'check' || f.kind === 'radio') return f.input.checked ? f.on : 'Off';
  return f.input.value;
}

// ------------------------------------------------------------ own items

function edPlace(e, info) {
  if (e.target !== info.layer) return;
  if (!Ed.tool) { edSelect(null); return; }
  e.preventDefault();
  const r = info.layer.getBoundingClientRect();
  const x = (e.clientX - r.left) / Ed.scale;
  const y = (e.clientY - r.top) / Ed.scale;
  const tool = Ed.tool;
  Ed.tool = null;
  edHint();
  if (tool === 'sign') { edSignature(info.n, x, y); return; }
  const item = { id: ++Ed.seq, page: info.n, type: tool, x, y };
  if (tool === 'text' || tool === 'date') {
    Object.assign(item, { type: 'text', size: ED_TEXT_SIZE, y: y - ED_TEXT_SIZE * 0.6,
      text: tool === 'date' ? new Date().toLocaleDateString({ de: 'de-DE', fr: 'fr-FR', it: 'it-IT' }[LANG] || 'en-GB', { day: '2-digit', month: '2-digit', year: 'numeric' }) : '' });
  } else {
    Object.assign(item, { w: 12, h: 12, x: x - 6, y: y - 6 });
  }
  Ed.items.push(item);
  edDrawItem(item);
  edSelect(item);
  if (item.type === 'text' && !item.text) item.el.querySelector('.ed-text').focus();
}

function edDrawItem(item) {
  const info = Ed.pages[item.page - 1];
  item.el?.remove();
  const el = document.createElement('div');
  el.className = 'ed-item ed-item--' + item.type;
  if (item.type === 'text') {
    const span = document.createElement('div');
    span.className = 'ed-text';
    span.contentEditable = 'plaintext-only';
    span.spellcheck = false;
    span.textContent = item.text;
    span.addEventListener('input', () => { item.text = span.innerText.replace(/\n$/, ''); });
    span.addEventListener('focus', () => edSelect(item));
    span.addEventListener('blur', () => {
      if (!item.text.trim()) setTimeout(() => { if (!item.text.trim()) edRemove(item); }, 150);
    });
    el.appendChild(span);
  } else if (item.type === 'sign') {
    const img = document.createElement('img');
    img.src = Ed.sigImg.src;
    img.alt = '';
    img.draggable = false;
    el.appendChild(img);
  } else {
    el.innerHTML = `<svg viewBox="0 0 10 10" preserveAspectRatio="none"><path d="${item.type === 'check' ? 'M1 5.5 L4 8.5 L9 1.5' : 'M1.5 1.5 L8.5 8.5 M8.5 1.5 L1.5 8.5'}"/></svg>`;
  }
  const tools = document.createElement('div');
  tools.className = 'ed-handles';
  tools.innerHTML =
    `<button type="button" class="ed-h ed-h-move" title="${esc(t('ed.move'))}">✥</button>` +
    `<button type="button" class="ed-h ed-h-del" title="${esc(t('ed.del'))}">✕</button>`;
  el.appendChild(tools);
  const size = document.createElement('button');
  size.type = 'button';
  size.className = 'ed-h ed-h-size';
  size.title = t('ed.size');
  el.appendChild(size);
  tools.querySelector('.ed-h-del').addEventListener('click', e => { e.stopPropagation(); edRemove(item); });
  edDraggable(item, el, tools.querySelector('.ed-h-move'), 'move');
  if (item.type !== 'text') edDraggable(item, el, el, 'move');
  edDraggable(item, el, size, 'size');
  el.addEventListener('pointerdown', e => { e.stopPropagation(); edSelect(item); });
  info.layer.appendChild(el);
  item.el = el;
  edPosition(item);
  if (Ed.sel === item) el.classList.add('is-selected');
}

function edPosition(item) {
  const s = Ed.scale, el = item.el;
  el.style.left = item.x * s + 'px';
  el.style.top = item.y * s + 'px';
  if (item.type === 'text') {
    el.style.fontSize = item.size * s + 'px';
  } else {
    el.style.width = item.w * s + 'px';
    el.style.height = item.h * s + 'px';
  }
}

function edDraggable(item, el, handle, mode) {
  handle.addEventListener('pointerdown', e => {
    if (mode === 'move' && handle === el && e.target.closest('.ed-h')) return;
    e.preventDefault();
    e.stopPropagation();
    edSelect(item);
    handle.setPointerCapture(e.pointerId);
    const start = { x: e.clientX, y: e.clientY, ix: item.x, iy: item.y, w: item.w, h: item.h, size: item.size };
    const info = Ed.pages[item.page - 1];
    const move = ev => {
      const dx = (ev.clientX - start.x) / Ed.scale, dy = (ev.clientY - start.y) / Ed.scale;
      if (mode === 'move') {
        item.x = Math.max(0, Math.min(info.vp1.width - 4, start.ix + dx));
        item.y = Math.max(0, Math.min(info.vp1.height - 4, start.iy + dy));
      } else if (item.type === 'text') {
        item.size = Math.max(5, Math.min(72, start.size + dy * 0.6));
      } else {
        const f = Math.max(0.15, (start.w + dx) / start.w);
        item.w = Math.max(5, start.w * f);
        item.h = Math.max(5, start.h * f);
      }
      edPosition(item);
    };
    const up = () => {
      handle.removeEventListener('pointermove', move);
      handle.removeEventListener('pointerup', up);
      handle.removeEventListener('pointercancel', up);
    };
    handle.addEventListener('pointermove', move);
    handle.addEventListener('pointerup', up);
    handle.addEventListener('pointercancel', up);
  });
}

function edSelect(item) {
  if (Ed.sel && Ed.sel.el) Ed.sel.el.classList.remove('is-selected');
  Ed.sel = item;
  if (item && item.el) item.el.classList.add('is-selected');
}

function edRemove(item) {
  item.el?.remove();
  Ed.items = Ed.items.filter(i => i !== item);
  if (Ed.sel === item) Ed.sel = null;
}

// ------------------------------------------------------------- signature

async function edSigLoad() {
  if (!State.me.signature) return false;
  const res = await fetch('api/me/signature?ts=' + Date.now(), { credentials: 'same-origin' });
  if (!res.ok) { State.me.signature = false; return false; }
  Ed.sigBytes = new Uint8Array(await res.arrayBuffer());
  const img = new Image();
  img.src = URL.createObjectURL(new Blob([Ed.sigBytes], { type: 'image/png' }));
  await img.decode();
  Ed.sigImg = img;
  return true;
}

async function edSignature(page, x, y) {
  if (!Ed.sigImg && !(await edSigLoad())) {
    const ok = await signatureDialog();
    if (!ok || !(await edSigLoad())) return;
  }
  const w = 140, h = w * Ed.sigImg.naturalHeight / Math.max(1, Ed.sigImg.naturalWidth);
  const item = { id: ++Ed.seq, page, type: 'sign', x: x - w / 2, y: y - h / 2, w, h };
  Ed.items.push(item);
  edDrawItem(item);
  edSelect(item);
}

function signatureDialog() {
  const dlg = $('sg-dlg');
  const canvas = $('sg-pad');
  const ctx = canvas.getContext('2d');
  let drawn = false;
  const clear = () => { ctx.clearRect(0, 0, canvas.width, canvas.height); drawn = false; };
  clear();
  $('sg-remove').hidden = !State.me.signature;
  $('sg-msg').textContent = '';
  let last = null;
  const pos = e => {
    const r = canvas.getBoundingClientRect();
    return [(e.clientX - r.left) * canvas.width / r.width, (e.clientY - r.top) * canvas.height / r.height];
  };
  canvas.onpointerdown = e => { canvas.setPointerCapture(e.pointerId); last = pos(e); };
  canvas.onpointermove = e => {
    if (!last) return;
    const p = pos(e);
    ctx.strokeStyle = ED_INK;
    ctx.lineWidth = 4 * (e.pressure && e.pointerType === 'pen' ? 0.5 + e.pressure : 1);
    ctx.lineCap = ctx.lineJoin = 'round';
    ctx.beginPath();
    ctx.moveTo(...last);
    ctx.lineTo(...p);
    ctx.stroke();
    last = p;
    drawn = true;
  };
  canvas.onpointerup = canvas.onpointercancel = () => { last = null; };
  $('sg-clear').onclick = clear;
  $('sg-file').value = '';
  $('sg-file').onchange = async () => {
    const file = $('sg-file').files[0];
    if (!file) return;
    const img = new Image();
    img.src = URL.createObjectURL(file);
    await img.decode();
    clear();
    const f = Math.min(canvas.width / img.naturalWidth, canvas.height / img.naturalHeight);
    const w = img.naturalWidth * f, h = img.naturalHeight * f;
    ctx.drawImage(img, (canvas.width - w) / 2, (canvas.height - h) / 2, w, h);
    const data = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const px = data.data;
    for (let i = 0; i < px.length; i += 4) {
      const lum = 0.299 * px[i] + 0.587 * px[i + 1] + 0.114 * px[i + 2];
      // paper → transparent, ink keeps its darkness as opacity
      const a = lum > 190 ? 0 : Math.min(255, (190 - lum) * 2.2);
      px[i + 3] = Math.min(px[i + 3], a);
    }
    ctx.putImageData(data, 0, 0);
    drawn = true;
  };
  return new Promise(resolve => {
    $('sg-remove').onclick = async () => {
      if (!confirm(t('sg.remove.q'))) return;
      await api('me/signature', { method: 'DELETE' });
      State.me.signature = false;
      Ed.sigImg = Ed.sigBytes = null;
      $('sg-remove').hidden = true;
    };
    $('sg-use').onclick = async e => {
      e.preventDefault();
      if (!drawn) { $('sg-msg').textContent = t('sg.empty'); return; }
      const blob = await new Promise(r => canvas.toBlob(r, 'image/png'));
      const res = await fetch('api/me/signature', {
        method: 'PUT', credentials: 'same-origin', headers: { 'Content-Type': 'image/png' }, body: blob,
      });
      if (!res.ok) {
        let d = res.statusText;
        try { d = (await res.json()).detail; } catch { /* keep */ }
        $('sg-msg').textContent = d;
        return;
      }
      State.me.signature = true;
      Ed.sigImg = Ed.sigBytes = null;
      dlg.close('ok');
    };
    dlg.onclose = () => resolve(dlg.returnValue === 'ok');
    dlg.returnValue = '';
    dlg.showModal();
  });
}

// ------------------------------------------------------------------ save

async function edBuildPdf(flatten) {
  const { PDFDocument, StandardFonts, rgb, degrees } = PDFLib;
  const doc = await PDFDocument.load(Ed.bytes, { updateMetadata: false });
  const font = await doc.embedFont(StandardFonts.Helvetica);
  const changed = Ed.fields.filter(f => fieldValue(f) !== f.initial);
  if (changed.length || flatten) {
    const form = doc.getForm();
    for (const name of new Set(changed.map(f => f.name))) {
      const group = Ed.fields.filter(f => f.name === name);
      let field;
      try { field = form.getField(name); } catch { continue; }
      const f = group[0];
      if (field instanceof PDFLib.PDFTextField) {
        const v = fieldValue(f);
        edCheckChars(v, font);
        field.setText(v);
      } else if (field instanceof PDFLib.PDFCheckBox) {
        fieldValue(f) === 'Off' ? field.uncheck() : field.check();
      } else if (field instanceof PDFLib.PDFRadioGroup) {
        const on = group.find(g => fieldValue(g) !== 'Off');
        if (on) field.select(on.on); else field.clear();
      } else if (field instanceof PDFLib.PDFDropdown || field instanceof PDFLib.PDFOptionList) {
        const v = fieldValue(f);
        v ? field.select(v) : field.clear();
      }
    }
    try { form.updateFieldAppearances(font); } catch (e) { console.warn('appearances', e); }
    if (flatten) form.flatten();
  }
  const pages = doc.getPages();
  const sig = Ed.items.some(i => i.type === 'sign') ? await doc.embedPng(await edSigBytes()) : null;
  for (const item of Ed.items) {
    const page = pages[item.page - 1];
    const vp1 = Ed.pages[item.page - 1].vp1;
    const pt = (x, y) => vp1.convertToPdfPoint(x, y);
    // direction of "right" on screen, in PDF space – keeps rotated pages upright
    const [ax, ay] = pt(0, 0), [bx, by] = pt(1, 0);
    const angle = Math.round(Math.atan2(by - ay, bx - ax) * 180 / Math.PI);
    const rotate = degrees(angle);
    if (item.type === 'text') {
      const lines = item.text.split('\n');
      edCheckChars(item.text, font);
      lines.forEach((line, i) => {
        const [x, y] = pt(item.x, item.y + item.size * (0.95 + 1.2 * i));
        page.drawText(line, { x, y, size: item.size, font, color: rgb(0, 0, 0), rotate });
      });
    } else if (item.type === 'sign') {
      const [x, y] = pt(item.x, item.y + item.h);
      page.drawImage(sig, { x, y, width: item.w, height: item.h, rotate });
    } else {
      const [x, y] = pt(item.x, item.y);
      const s = item.w / 10;
      const path = item.type === 'check' ? 'M 1 5.5 L 4 8.5 L 9 1.5' : 'M 1.5 1.5 L 8.5 8.5 M 8.5 1.5 L 1.5 8.5';
      page.drawSvgPath(path, { x, y, scale: s, borderColor: rgb(0, 0, 0), borderWidth: Math.max(0.8, item.w / 9),
        rotate });
    }
  }
  return doc.save({ updateFieldAppearances: false });
}

async function edSigBytes() {
  if (!Ed.sigBytes) await edSigLoad();
  return Ed.sigBytes;
}

function edCheckChars(text, font) {
  for (const c of text) {
    if (c === '\n') continue;
    try { font.encodeText(c); } catch { throw new Error(t('ed.err.char', { c })); }
  }
}

function edSaveDialog() {
  if (!edDirty()) { alert(t('ed.sv.nothing')); return; }
  const dlg = $('ed-save-dlg');
  $('ed-sv-name').value = `${Ed.doc.title} (${t('ed.sv.suffix')})`;
  $('ed-sv-date').value = Ed.doc.date || new Date().toISOString().slice(0, 10);
  $('ed-sv-flatten').checked = false;
  $('ed-sv-flatten-row').hidden = !Ed.fields.length;
  $('ed-sv-msg').textContent = '';
  dlg.showModal();
}

async function edSave(e) {
  e.preventDefault();
  const btn = $('ed-sv-ok');
  btn.disabled = true;
  $('ed-sv-msg').textContent = t('ed.sv.busy');
  try {
    const bytes = await edBuildPdf($('ed-sv-flatten').checked);
    let bin = '';
    for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
    const typed = [...Ed.items.filter(i => i.type === 'text').map(i => i.text),
      ...Ed.fields.filter(f => f.kind === 'text' && fieldValue(f) !== f.initial).map(fieldValue)].join('\n');
    const r = await api(`documents/${Ed.doc.id}/edited`, { method: 'POST', body: JSON.stringify({
      pdf: btoa(bin), title: $('ed-sv-name').value, date: $('ed-sv-date').value || null, text: typed,
    }) });
    $('ed-save-dlg').close();
    closeEditor(true);
    await Promise.all([loadDocs(), loadTree(), loadStatus()].map(p => p.catch(() => null)));
    try { openPreview(await api(`documents/${r.id}`)); } catch { /* list shows it after the scan */ }
  } catch (err) {
    $('ed-sv-msg').textContent = err.message;
  } finally {
    btn.disabled = false;
  }
}

// ------------------------------------------------------------------ wiring

function initEditor() {
  $('pv-edit').addEventListener('click', () => { if (State.selected) openEditor(State.selected); });
  $('ed-close').addEventListener('click', () => closeEditor());
  document.querySelectorAll('#editor [data-tool]').forEach(b => b.addEventListener('click', () => {
    Ed.tool = Ed.tool === b.dataset.tool ? null : b.dataset.tool;
    edSelect(null);
    edHint();
  }));
  const zoom = f => async () => {
    if (!Ed.pdf) return;
    Ed.scale = Math.max(0.4, Math.min(3, Math.round((Ed.scale * f) * 10) / 10));
    await edRender();
  };
  $('ed-zoom-in').addEventListener('click', zoom(1.2));
  $('ed-zoom-out').addEventListener('click', zoom(1 / 1.2));
  $('ed-save').addEventListener('click', edSaveDialog);
  $('ed-sv-form').addEventListener('submit', edSave);
  $('ed-sv-cancel').addEventListener('click', () => $('ed-save-dlg').close());
  $('sg-cancel').addEventListener('click', () => $('sg-dlg').close('cancel'));
  $('ed-sign-new').addEventListener('click', async () => {
    if (await signatureDialog() && await edSigLoad()) Ed.items.filter(i => i.type === 'sign').forEach(edDrawItem);
  });
  document.addEventListener('keydown', e => {
    if ($('editor').hidden || document.querySelector('dialog[open]')) return;
    const typing = e.target.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName);
    if (e.key === 'Escape') {
      if (Ed.tool) { Ed.tool = null; edHint(); } else if (typing) e.target.blur(); else edSelect(null);
    } else if ((e.key === 'Delete' || e.key === 'Backspace') && !typing && Ed.sel) {
      e.preventDefault();
      edRemove(Ed.sel);
    }
  });
  window.addEventListener('beforeunload', e => { if (!$('editor').hidden && edDirty()) e.preventDefault(); });
}

function editorButton(doc) {
  const can = doc && doc.ext === 'pdf' && (State.me.write_areas || []).includes(doc.area);
  $('pv-edit').hidden = !can;
}
