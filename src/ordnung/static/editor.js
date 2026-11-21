/* Ordnung! – PDF editor: fill forms, add text, ticks, stamps and a signature.
 * PDF.js shows the pages, pdf-lib writes the result. Saving replaces the
 * document (the original goes to the trash, undo brings it back); "Duplicate"
 * or "save as copy" keeps the original and adds the edited PDF as a second one. */
'use strict';

Object.assign(I18N.de, {
  'pv.edit': 'Bearbeiten',
  'ed.back': '← Zurück', 'ed.text': 'Text', 'ed.check': 'Haken', 'ed.cross': 'Kreuz', 'ed.date': 'Datum',
  'ed.sign': 'Unterschrift', 'ed.save': 'Speichern …', 'ed.zoomin': 'Größer', 'ed.zoomout': 'Kleiner',
  'ed.stamp': 'Stempel', 'pv.dup': 'Duplizieren', 'pv.stamp': 'Stempeln',
  'ed.hint': 'Felder direkt ausfüllen. Für Text, Haken, Datum, Stempel oder Unterschrift oben wählen und auf die Seite tippen.',
  'ed.hint.copy': 'Kopie: Beim Speichern entsteht ein zweites Dokument, das Original bleibt.',
  'ed.hint.place': 'Auf die Stelle tippen, wo es hin soll. Esc bricht ab.',
  'ed.loading': 'Lade PDF …', 'ed.fields': '{n} Formularfelder',
  'ed.del': 'Entfernen', 'ed.move': 'Verschieben', 'ed.size': 'Größe ändern',
  'ed.leave': 'Änderungen verwerfen?',
  'ed.err.encrypted': 'Diese PDF ist geschützt und lässt sich nicht bearbeiten.',
  'ed.err.char': 'Das Zeichen „{c}“ kann Ordnung! nicht in die PDF schreiben.',
  'ed.err.load': 'Die PDF ließ sich nicht öffnen: {msg}',
  'ed.sv.title': 'Speichern', 'ed.sv.name': 'Titel', 'ed.sv.date': 'Datum',
  'ed.sv.replace': 'Dokument ersetzen', 'ed.sv.copy': 'Als Kopie speichern',
  'ed.sv.flatten': 'Formular festschreiben (Felder lassen sich danach nicht mehr ändern)',
  'ed.sv.hint': 'Das alte Dokument kommt in den Papierkorb, Tags werden übernommen. Rückgängig geht direkt danach oder über den Papierkorb.',
  'ed.sv.hint.copy': 'Das Original bleibt unverändert. Die Kopie kommt in denselben Ordner, Tags werden übernommen.',
  'ed.sv.tags': 'Stempel als Tag vergeben: {tags}',
  'ed.sv.ok': 'Speichern', 'ed.sv.cancel': 'Abbrechen', 'ed.sv.suffix': 'Kopie', 'ed.sv.busy': 'Speichere …',
  'ed.sv.nothing': 'Es gibt noch keine Änderung.',
  'ed.saved': '„{title}“ gespeichert, das alte liegt im Papierkorb.', 'ed.saved.copy': 'Kopie „{title}“ angelegt.',
  'ed.stamped': '„{title}“ gestempelt.',
  'stp.title': 'Stempel', 'stp.text': 'Aufschrift', 'stp.date': 'Mit Datum', 'stp.extra': 'Zusatzzeile (frei)',
  'stp.extra.ph': 'z. B. per Überweisung', 'stp.color': 'Farbe', 'stp.keep': 'Als eigene Vorlage merken',
  'stp.tag': 'Aufschrift als Tag vergeben', 'stp.pos': 'Stelle auf Seite 1',
  'stp.pos.tr': 'oben rechts', 'stp.pos.tl': 'oben links', 'stp.pos.br': 'unten rechts', 'stp.pos.bl': 'unten links',
  'stp.pos.c': 'Mitte', 'stp.ok': 'Einsetzen', 'stp.ok.quick': 'Stempeln', 'stp.own': 'eigene', 'stp.forget': 'Vorlage vergessen',
  'stp.empty': 'Bitte eine Aufschrift eingeben.', 'stp.edit': 'Doppelklick: Stempel ändern',
  'stp.c.red': 'Rot', 'stp.c.blue': 'Blau', 'stp.c.green': 'Grün', 'stp.c.black': 'Schwarz',
  'stp.p.paid': 'Bezahlt', 'stp.p.done': 'Erledigt', 'stp.p.received': 'Eingegangen', 'stp.p.booked': 'Gebucht',
  'stp.p.copy': 'Kopie', 'stp.p.void': 'Storniert',
  'sg.title': 'Deine Unterschrift', 'sg.hint': 'Mit Maus, Finger oder Stift ins Feld schreiben, oder ein Foto deiner Unterschrift laden (weißes Papier wird durchsichtig).',
  'sg.clear': 'Leeren', 'sg.upload': 'Bild laden …', 'sg.remove': 'Gespeicherte löschen', 'sg.use': 'Speichern und einsetzen',
  'sg.cancel': 'Abbrechen', 'sg.empty': 'Bitte erst unterschreiben.', 'sg.new': 'Neu unterschreiben',
  'sg.remove.q': 'Gespeicherte Unterschrift löschen?',
});
Object.assign(I18N.en, {
  'pv.edit': 'Edit',
  'ed.back': '← Back', 'ed.text': 'Text', 'ed.check': 'Tick', 'ed.cross': 'Cross', 'ed.date': 'Date',
  'ed.sign': 'Signature', 'ed.save': 'Save …', 'ed.zoomin': 'Larger', 'ed.zoomout': 'Smaller',
  'ed.stamp': 'Stamp', 'pv.dup': 'Duplicate', 'pv.stamp': 'Stamp',
  'ed.hint': 'Fill in fields directly. For text, ticks, date, stamp or signature pick a tool above and tap the page.',
  'ed.hint.copy': 'Copy: saving adds a second document, the original stays.',
  'ed.hint.place': 'Tap where it should go. Esc cancels.',
  'ed.loading': 'Loading PDF …', 'ed.fields': '{n} form fields',
  'ed.del': 'Remove', 'ed.move': 'Move', 'ed.size': 'Resize',
  'ed.leave': 'Discard changes?',
  'ed.err.encrypted': 'This PDF is protected and cannot be edited.',
  'ed.err.char': 'Ordnung! cannot write the character “{c}” into the PDF.',
  'ed.err.load': 'Could not open the PDF: {msg}',
  'ed.sv.title': 'Save', 'ed.sv.name': 'Title', 'ed.sv.date': 'Date',
  'ed.sv.replace': 'Replace the document', 'ed.sv.copy': 'Save as a copy',
  'ed.sv.flatten': 'Flatten the form (fields cannot be changed afterwards)',
  'ed.sv.hint': 'The old document goes to the trash, tags are kept. Undo right afterwards or from the trash.',
  'ed.sv.hint.copy': 'The original stays unchanged. The copy goes into the same folder, tags are copied.',
  'ed.sv.tags': 'Add the stamp as a tag: {tags}',
  'ed.sv.ok': 'Save', 'ed.sv.cancel': 'Cancel', 'ed.sv.suffix': 'copy', 'ed.sv.busy': 'Saving …',
  'ed.sv.nothing': 'Nothing has been changed yet.',
  'ed.saved': '“{title}” saved, the old one is in the trash.', 'ed.saved.copy': 'Copy “{title}” created.',
  'ed.stamped': '“{title}” stamped.',
  'stp.title': 'Stamp', 'stp.text': 'Text', 'stp.date': 'With date', 'stp.extra': 'Extra line (free)',
  'stp.extra.ph': 'e.g. by bank transfer', 'stp.color': 'Colour', 'stp.keep': 'Remember as my own template',
  'stp.tag': 'Add the text as a tag', 'stp.pos': 'Place on page 1',
  'stp.pos.tr': 'top right', 'stp.pos.tl': 'top left', 'stp.pos.br': 'bottom right', 'stp.pos.bl': 'bottom left',
  'stp.pos.c': 'centre', 'stp.ok': 'Insert', 'stp.ok.quick': 'Stamp', 'stp.own': 'own', 'stp.forget': 'Forget template',
  'stp.empty': 'Please enter a text.', 'stp.edit': 'Double-click: change the stamp',
  'stp.c.red': 'Red', 'stp.c.blue': 'Blue', 'stp.c.green': 'Green', 'stp.c.black': 'Black',
  'stp.p.paid': 'Paid', 'stp.p.done': 'Done', 'stp.p.received': 'Received', 'stp.p.booked': 'Booked',
  'stp.p.copy': 'Copy', 'stp.p.void': 'Cancelled',
  'sg.title': 'Your signature', 'sg.hint': 'Sign in the box with mouse, finger or pen, or load a photo of your signature (white paper becomes transparent).',
  'sg.clear': 'Clear', 'sg.upload': 'Load image …', 'sg.remove': 'Delete stored one', 'sg.use': 'Save and insert',
  'sg.cancel': 'Cancel', 'sg.empty': 'Please sign first.', 'sg.new': 'Sign again',
  'sg.remove.q': 'Delete the stored signature?',
});

const Ed = {
  doc: null, bytes: null, pdf: null, pages: [],   // pages: [{vp1, el, layer, rotation}]
  scale: 1, tool: null, items: [], fields: [], sel: null, seq: 0, sigImg: null, sigBytes: null,
  mode: 'replace',                                 // 'replace' | 'copy'
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

async function openEditor(doc, mode = 'replace') {
  Object.assign(Ed, { doc, mode, items: [], fields: [], sel: null, tool: null, pages: [] });
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
  $('ed-hint').textContent = Ed.tool ? t('ed.hint.place') : (Ed.mode === 'copy' ? t('ed.hint.copy') + ' ' : '') + t('ed.hint');
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
  if (tool === 'stamp') { edStamp(info.n, x, y); return; }
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
  } else if (item.type === 'stamp') {
    el.innerHTML = stampSvg(item);
    el.title = t('stp.edit');
    el.addEventListener('dblclick', async e => {
      e.stopPropagation();
      const st = await stampDialog(item);
      if (st) { Object.assign(item, st); edDrawItem(item); edSelect(item); }
    });
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
  } else if (item.type === 'stamp') {
    const L = stampLayout(item);
    el.style.left = (item.x - L.W / 2) * s + 'px';
    el.style.top = (item.y - L.H / 2) * s + 'px';
    el.style.width = L.W * s + 'px';
    el.style.height = L.H * s + 'px';
    el.style.transform = `rotate(${-STAMP_TILT}deg)`;
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
      } else if (item.type === 'text' || item.type === 'stamp') {
        item.size = Math.max(5, Math.min(item.type === 'stamp' ? 90 : 72, start.size + dy * 0.6));
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
  const stampFonts = Ed.items.some(i => i.type === 'stamp') ? await stampEmbedFonts(doc) : null;
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
    } else if (item.type === 'stamp') {
      stampDraw(page, pt, item, stampFonts);
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

const edStampTags = () => [...new Set(Ed.items.filter(i => i.type === 'stamp').map(i => i.text))];

function edSaveMode(mode) {
  const before = Ed.mode;
  Ed.mode = mode;
  document.querySelectorAll('input[name="ed-sv-mode"]').forEach(r => { r.checked = r.value === mode; });
  $('ed-sv-hint').textContent = t(mode === 'copy' ? 'ed.sv.hint.copy' : 'ed.sv.hint');
  const name = $('ed-sv-name'), copyName = `${Ed.doc.title} (${t('ed.sv.suffix')})`;
  // follow the mode with the title unless it was typed in by hand
  if (!name.value || name.value === (before === 'copy' ? copyName : Ed.doc.title)) {
    name.value = mode === 'copy' ? copyName : Ed.doc.title;
  }
  edHint();
}

function edSaveDialog() {
  if (!edDirty()) { alert(t('ed.sv.nothing')); return; }
  const dlg = $('ed-save-dlg');
  $('ed-sv-name').value = '';
  edSaveMode(Ed.mode);
  $('ed-sv-date').value = Ed.doc.date || new Date().toISOString().slice(0, 10);
  $('ed-sv-flatten').checked = false;
  $('ed-sv-flatten-row').hidden = !Ed.fields.length;
  const tags = edStampTags();
  $('ed-sv-tags-row').hidden = !tags.length;
  $('ed-sv-tags').checked = !!tags.length;
  $('ed-sv-tags-label').textContent = t('ed.sv.tags', { tags: tags.join(', ') });
  $('ed-sv-msg').textContent = '';
  dlg.showModal();
}

function pdfBase64(bytes) {
  let bin = '';
  for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
  return btoa(bin);
}

// after saving: show the new document, offer undo for a replaced one
async function edAfterSave(r, oldDoc, msg) {
  await Promise.all([loadDocs(), loadTree(), loadStatus()].map(p => p.catch(() => null)));
  try { openPreview(await api(`documents/${r.id}`)); } catch { /* list shows it after the scan */ }
  toast(esc(msg), r.trash_path ? {
    label: t('op.undo'),
    run: async () => {
      try {
        await api(`documents/${r.id}/trash`, { method: 'POST' });
        await api('trash/restore', { method: 'POST', body: JSON.stringify({ trash_path: r.trash_path }) });
        await Promise.all([loadDocs(), loadTree(), loadStatus()].map(p => p.catch(() => null)));
        try { openPreview(await api(`documents/${oldDoc.id}`)); } catch { closePreview(); }
        toast(esc(t('op.restored')), null, 3000);
      } catch (e) { toast(esc(e.message)); }
    },
  } : null, 10000);
}

async function edSave(e) {
  e.preventDefault();
  const btn = $('ed-sv-ok');
  btn.disabled = true;
  $('ed-sv-msg').textContent = t('ed.sv.busy');
  try {
    const bytes = await edBuildPdf($('ed-sv-flatten').checked);
    const typed = [...Ed.items.filter(i => i.type === 'text').map(i => i.text),
      ...Ed.items.filter(i => i.type === 'stamp').map(stampText),
      ...Ed.fields.filter(f => f.kind === 'text' && fieldValue(f) !== f.initial).map(fieldValue)].join('\n');
    const replace = Ed.mode !== 'copy', oldDoc = Ed.doc, title = $('ed-sv-name').value;
    const r = await api(`documents/${Ed.doc.id}/edited`, { method: 'POST', body: JSON.stringify({
      pdf: pdfBase64(bytes), title, date: $('ed-sv-date').value || null, text: typed, replace,
      add_tags: $('ed-sv-tags').checked ? edStampTags() : [],
    }) });
    $('ed-save-dlg').close();
    closeEditor(true);
    await edAfterSave(r, oldDoc, t(replace ? 'ed.saved' : 'ed.saved.copy', { title }));
  } catch (err) {
    $('ed-sv-msg').textContent = err.message;
  } finally {
    btn.disabled = false;
  }
}

// ------------------------------------------------------------------ wiring

function initEditor() {
  $('pv-edit').addEventListener('click', () => { if (State.selected) openEditor(State.selected, 'replace'); });
  $('pv-dup').addEventListener('click', () => { if (State.selected) openEditor(State.selected, 'copy'); });
  $('pv-stamp').addEventListener('click', () => { if (State.selected) quickStamp(State.selected); });
  document.querySelectorAll('input[name="ed-sv-mode"]').forEach(r => r.addEventListener('change', () => edSaveMode(r.value)));
  initStampDialog();
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
  $('pv-dup').hidden = !can;
  $('pv-stamp').hidden = !can;
}

// ------------------------------------------------------------------ stamp
/* A stamp is a rounded double frame with a big text, optionally a date and an
 * extra line, slightly tilted like a rubber stamp. Layout is computed once in
 * PDF units with the real Helvetica widths, so screen and PDF match; in the PDF
 * it is vector text and lines (sharp, and the text stays selectable). */

const STAMP_TILT = 6;                               // degrees, counter-clockwise
const STAMP_SIZE = 22;                              // size of the big text in pt
const STAMP_RGB = { red: [0.76, 0.09, 0.11], blue: [0.09, 0.24, 0.62], green: [0.07, 0.46, 0.2], black: [0.12, 0.12, 0.12] };
const STAMP_PRESETS = [
  { key: 'paid', date: true, color: 'red' }, { key: 'done', date: true, color: 'green' },
  { key: 'received', date: true, color: 'blue' }, { key: 'booked', date: true, color: 'blue' },
  { key: 'void', date: true, color: 'red' }, { key: 'copy', date: false, color: 'black' },
];
let StampM = null, StampOwn = null, StampLast = null, stampResolve = null;

const edLocale = () => ({ de: 'de-DE', fr: 'fr-FR', it: 'it-IT' }[LANG] || 'en-GB');
const todayIso = () => { const d = new Date(); return new Date(d - d.getTimezoneOffset() * 6e4).toISOString().slice(0, 10); };
const stampCss = c => 'rgb(' + (STAMP_RGB[c] || STAMP_RGB.red).map(v => Math.round(v * 255)).join(',') + ')';

function stampDateText(iso) {
  if (!iso) return '';
  return new Date(iso + 'T12:00:00').toLocaleDateString(edLocale(), { day: '2-digit', month: '2-digit', year: 'numeric' });
}

function stampLines(st) {
  const lines = [{ text: st.text.toLocaleUpperCase(edLocale()), bold: true, k: 1 }];
  if (st.date) lines.push({ text: stampDateText(st.date), bold: true, k: 0.5 });
  if (st.extra) lines.push({ text: st.extra, bold: false, k: 0.42 });
  return lines;
}

const stampText = st => [st.text, stampDateText(st.date), st.extra].filter(Boolean).join(' ');

async function stampEmbedFonts(doc) {
  const { StandardFonts } = PDFLib;
  return { bold: await doc.embedFont(StandardFonts.HelveticaBold), reg: await doc.embedFont(StandardFonts.Helvetica) };
}

async function stampMeasureReady() {
  await loadPdfLibs();
  if (!StampM) StampM = await stampEmbedFonts(await PDFLib.PDFDocument.create());
}

function stampWidth(text, bold, size) {
  if (StampM) {
    try { return (bold ? StampM.bold : StampM.reg).widthOfTextAtSize(text, size); } catch { /* checked on save */ }
  }
  return text.length * size * (bold ? 0.68 : 0.55);
}

// local frame: origin in the middle of the stamp, y down, PDF units
function stampLayout(st) {
  const s = st.size || STAMP_SIZE;
  const padX = 0.55 * s, padY = 0.38 * s, gap = 0.22 * s;
  let y = padY, w = 0;
  const lines = stampLines(st).map((l, i) => {
    const size = s * l.k;
    if (i) y += gap;
    y += 0.72 * size;                               // cap height of Helvetica
    const lw = stampWidth(l.text, l.bold, size);
    w = Math.max(w, lw);
    const out = { ...l, size, w: lw, base: y };
    if (!l.bold) y += 0.21 * size;                  // descenders of the lower-case extra line
    return out;
  });
  const W = w + 2 * padX, H = y + padY;
  lines.forEach(l => { l.x = -l.w / 2; l.y = l.base - H / 2; });
  return { W, H, lines, bw: 0.085 * s, r1: 0.24 * s, inset: 0.21 * s, bw2: 0.03 * s, r2: 0.12 * s };
}

function stampSvg(st) {
  const L = stampLayout(st), c = stampCss(st.color);
  const rect = (ins, rad, sw) => `<rect x="${-L.W / 2 + ins}" y="${-L.H / 2 + ins}" width="${L.W - 2 * ins}" ` +
    `height="${L.H - 2 * ins}" rx="${rad}" fill="none" stroke="${c}" stroke-width="${sw}"/>`;
  return `<svg class="stamp-svg" viewBox="${-L.W / 2} ${-L.H / 2} ${L.W} ${L.H}" preserveAspectRatio="none">` +
    rect(L.bw / 2, L.r1, L.bw) + rect(L.inset, L.r2, L.bw2) +
    L.lines.map(l => `<text x="${l.x}" y="${l.y}" font-size="${l.size}" font-weight="${l.bold ? 700 : 400}" ` +
      `textLength="${l.w}" lengthAdjust="spacingAndGlyphs" fill="${c}">${esc(l.text)}</text>`).join('') +
    '</svg>';
}

function stampCheck(st, fonts) {
  stampLines(st).forEach(l => edCheckChars(l.text, l.bold ? fonts.bold : fonts.reg));
}

// pt(x, y): screen point of the page at scale 1 → PDF point (handles rotated pages)
function stampDraw(page, pt, st, fonts) {
  const { rgb, degrees } = PDFLib;
  stampCheck(st, fonts);
  const L = stampLayout(st);
  const tr = STAMP_TILT * Math.PI / 180, co = Math.cos(tr), si = Math.sin(tr);
  const map = (px, py) => pt(st.x + px * co + py * si, st.y - px * si + py * co);
  const color = rgb(...(STAMP_RGB[st.color] || STAMP_RGB.red));
  const [ax, ay] = map(0, 0), [bx, by] = map(1, 0);
  const rotate = degrees(Math.atan2(by - ay, bx - ax) * 180 / Math.PI);
  const frame = (ins, rad, width) => {
    const x0 = -L.W / 2 + ins, y0 = -L.H / 2 + ins, x1 = L.W / 2 - ins, y1 = L.H / 2 - ins;
    const corners = [[x1 - rad, y0 + rad, -90], [x1 - rad, y1 - rad, 0], [x0 + rad, y1 - rad, 90], [x0 + rad, y0 + rad, 180]];
    const pts = [];
    for (const [cx, cy, a0] of corners) {
      for (let k = 0; k <= 8; k++) {
        const a = (a0 + k * 90 / 8) * Math.PI / 180;
        pts.push(map(cx + rad * Math.cos(a), cy + rad * Math.sin(a)));
      }
    }
    // drawSvgPath flips y; with x = y = 0 the path is given in PDF coordinates
    const d = pts.map(([x, y], i) => `${i ? 'L' : 'M'} ${x.toFixed(2)} ${(-y).toFixed(2)}`).join(' ') + ' Z';
    page.drawSvgPath(d, { x: 0, y: 0, scale: 1, borderColor: color, borderWidth: width, borderOpacity: 0.9 });
  };
  frame(L.bw / 2, L.r1, L.bw);
  frame(L.inset, L.r2, L.bw2);
  for (const l of L.lines) {
    const [x, y] = map(l.x, l.y);
    page.drawText(l.text, { x, y, size: l.size, font: l.bold ? fonts.bold : fonts.reg, color, rotate, opacity: 0.9 });
  }
}

// ---- dialog

async function stampOwnLoad() {
  if (!StampOwn) {
    try { StampOwn = (await api('me/prefs')).stamps || []; } catch { StampOwn = []; }
  }
  return StampOwn;
}

async function stampOwnSave(list) {
  try { StampOwn = (await api('me/prefs', { method: 'PUT', body: JSON.stringify({ stamps: list }) })).stamps; }
  catch (e) { toast(esc(e.message)); }
}

function stampValue() {
  const clean = v => v.trim().replace(/\s+/g, ' ');
  return {
    text: clean($('stp-text').value), extra: clean($('stp-extra').value), color: $('stp-dlg').dataset.color || 'red',
    date: $('stp-date-on').checked ? ($('stp-date').value || todayIso()) : '',
  };
}

function stampSetColor(c) {
  $('stp-dlg').dataset.color = c;
  document.querySelectorAll('#stp-colors .stp-color').forEach(b => b.classList.toggle('is-active', b.dataset.color === c));
}

function stampFill(v) {
  $('stp-text').value = v.text || '';
  $('stp-date-on').checked = !!v.date;
  $('stp-date').value = (typeof v.date === 'string' && v.date) || $('stp-date').value || todayIso();
  $('stp-date').disabled = !v.date;
  $('stp-extra').value = v.extra || '';
  stampSetColor(v.color || 'red');
  stampPreview();
}

function stampPreview() {
  const v = stampValue();
  $('stp-preview').innerHTML = v.text ? stampSvg({ ...v, size: STAMP_SIZE }) : '';
  let msg = '';
  if (v.text && StampM) { try { stampCheck(v, StampM); } catch (e) { msg = e.message; } }
  $('stp-msg').textContent = msg;
}

function stampPresets() {
  const box = $('stp-presets');
  box.innerHTML = '';
  const chip = (v, own) => {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'fd-button stp-chip';
    b.style.setProperty('--stp-c', stampCss(v.color));
    b.textContent = v.text + (v.extra ? ' · ' + v.extra : '');
    b.addEventListener('click', () => stampFill({ ...v, date: v.date ? ($('stp-date').value || todayIso()) : '' }));
    box.appendChild(b);
    if (own) {
      const x = document.createElement('button');
      x.type = 'button';
      x.className = 'fd-button fd-button--transparent stp-forget';
      x.title = t('stp.forget');
      x.textContent = '✕';
      x.addEventListener('click', async () => {
        await stampOwnSave(StampOwn.filter(o => o !== v));
        stampPresets();
      });
      const wrap = document.createElement('span');
      wrap.className = 'stp-own';
      box.replaceChild(wrap, b);
      wrap.append(b, x);
    }
  };
  STAMP_PRESETS.forEach(p => chip({ text: t('stp.p.' + p.key), date: p.date, extra: '', color: p.color }, false));
  (StampOwn || []).forEach(o => chip(o, true));
}

async function stampDialog(initial = null, quick = false) {
  await stampMeasureReady();
  await stampOwnLoad();
  stampFill(initial || StampLast || { text: t('stp.p.paid'), date: todayIso(), extra: '', color: 'red' });
  $('stp-pos-row').hidden = !quick;
  $('stp-tag-row').hidden = !quick;
  $('stp-ok').textContent = t(quick ? 'stp.ok.quick' : 'stp.ok');
  $('stp-keep').checked = false;
  stampPresets();
  $('stp-dlg').showModal();
  $('stp-text').focus();
  $('stp-text').select();
  return new Promise(res => { stampResolve = res; });
}

function initStampDialog() {
  const box = $('stp-colors');
  for (const c of Object.keys(STAMP_RGB)) {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'stp-color';
    b.dataset.color = c;
    b.title = t('stp.c.' + c);
    b.setAttribute('aria-label', t('stp.c.' + c));
    b.style.background = stampCss(c);
    b.addEventListener('click', () => { stampSetColor(c); stampPreview(); });
    box.appendChild(b);
  }
  ['stp-text', 'stp-extra', 'stp-date'].forEach(id => $(id).addEventListener('input', stampPreview));
  $('stp-date-on').addEventListener('change', () => { $('stp-date').disabled = !$('stp-date-on').checked; stampPreview(); });
  $('stp-cancel').addEventListener('click', () => $('stp-dlg').close());
  $('stp-dlg').addEventListener('close', () => { const r = stampResolve; stampResolve = null; if (r) r(null); });
  $('stp-form').addEventListener('submit', async e => {
    e.preventDefault();
    const v = stampValue();
    if (!v.text) { $('stp-msg').textContent = t('stp.empty'); return; }
    try { stampCheck(v, StampM); } catch (err) { $('stp-msg').textContent = err.message; return; }
    if ($('stp-keep').checked) {
      await stampOwnSave([...StampOwn, { text: v.text, date: !!v.date, extra: v.extra, color: v.color }]);
    }
    StampLast = v;
    const r = stampResolve;
    stampResolve = null;
    $('stp-dlg').close();
    if (r) r({ ...v, pos: $('stp-pos').value, tag: $('stp-tag').checked });
  });
}

// ---- in the editor: tap the page, then fill in the dialog

async function edStamp(page, x, y) {
  const st = await stampDialog();
  if (!st) return;
  const item = { id: ++Ed.seq, page, type: 'stamp', x, y, size: STAMP_SIZE,
    text: st.text, date: st.date, extra: st.extra, color: st.color };
  Ed.items.push(item);
  edDrawItem(item);
  edSelect(item);
}

// ---- from the preview: stamp page 1 at a chosen corner and save in place

async function quickStamp(doc) {
  let st;
  try { st = await stampDialog(null, true); } catch (e) { toast(esc(e.message)); return; }
  if (!st) return;
  try {
    const res = await fetch(`api/documents/${doc.id}/file`, { credentials: 'same-origin' });
    if (!res.ok) throw new Error(res.status + ' ' + res.statusText);
    const bytes = new Uint8Array(await res.arrayBuffer());
    const view = await pdfjsLib.getDocument({ data: bytes.slice(), isEvalSupported: false }).promise;
    const vp1 = (await view.getPage(1)).getViewport({ scale: 1 });
    view.destroy();
    let out;
    try { out = await PDFLib.PDFDocument.load(bytes, { updateMetadata: false }); } catch (e) {
      throw new Error(/encrypt/i.test(String(e)) ? t('ed.err.encrypted') : t('ed.err.load', { msg: String(e) }));
    }
    const item = { text: st.text, date: st.date, extra: st.extra, color: st.color, size: STAMP_SIZE + 2 };
    const L = stampLayout(item), tr = STAMP_TILT * Math.PI / 180, m = 36;
    const hx = (L.W * Math.cos(tr) + L.H * Math.sin(tr)) / 2, hy = (L.W * Math.sin(tr) + L.H * Math.cos(tr)) / 2;
    const W = vp1.width, H = vp1.height;
    [item.x, item.y] = { tl: [m + hx, m + hy], br: [W - m - hx, H - m - hy], bl: [m + hx, H - m - hy],
      c: [W / 2, H / 2] }[st.pos] || [W - m - hx, m + hy];
    stampDraw(out.getPages()[0], (x, y) => vp1.convertToPdfPoint(x, y), item, await stampEmbedFonts(out));
    const saved = await out.save();
    const r = await api(`documents/${doc.id}/edited`, { method: 'POST', body: JSON.stringify({
      pdf: pdfBase64(saved), title: doc.title, date: doc.date || null, text: stampText(item), replace: true,
      add_tags: st.tag ? [st.text] : [],
    }) });
    await edAfterSave(r, doc, t('ed.stamped', { title: doc.title }));
  } catch (e) {
    toast(esc(e.message));
  }
}
