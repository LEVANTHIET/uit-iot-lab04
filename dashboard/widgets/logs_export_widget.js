function escapeCell(value) {
  return String(value === undefined || value === null ? '' : value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function formatTs(tsMs) {
  const dt = new Date(Number(tsMs));
  const pad = (n) => String(n).padStart(2, '0');
  return `${dt.getFullYear()}-${pad(dt.getMonth() + 1)}-${pad(dt.getDate())} `
    + `${pad(dt.getHours())}:${pad(dt.getMinutes())}:${pad(dt.getSeconds())}`;
}

function extractDatasourceMeta(ds) {
  const meta = ds && ds.datasource ? ds.datasource : {};
  const entityObj = meta.entity && meta.entity.id ? meta.entity.id.id : '';
  const deviceId = meta.entityId || entityObj || 'unknown-id';
  const deviceName = meta.entityName || meta.name || deviceId;
  const keyName = ds && ds.dataKey ? (ds.dataKey.name || ds.dataKey.label || 'value') : 'value';
  return { deviceId, deviceName, keyName };
}

function flattenCtxRows(ctxData) {
  const rows = [];
  if (!Array.isArray(ctxData)) {
    return rows;
  }
  ctxData.forEach((ds) => {
    const meta = extractDatasourceMeta(ds);
    const points = Array.isArray(ds.data) ? ds.data : [];
    points.forEach((pt) => {
      const tsMs = Array.isArray(pt) ? Number(pt[0]) : Number(pt.ts);
      const val = Array.isArray(pt) ? pt[1] : pt.value;
      rows.push({
        deviceId: String(meta.deviceId),
        deviceName: String(meta.deviceName),
        sensorKey: String(meta.keyName),
        sensorValue: String(val),
        receivedAt: formatTs(tsMs),
        tsMs: tsMs
      });
    });
  });
  rows.sort((a, b) => b.tsMs - a.tsMs);
  return rows;
}

function populateSelect(selectEl, values, defaultLabel) {
  const current = selectEl.value;
  const unique = Array.from(new Set(values)).sort();
  let html = `<option value="">${escapeCell(defaultLabel)}</option>`;
  unique.forEach((val) => {
    html += `<option value="${escapeCell(val)}">${escapeCell(val)}</option>`;
  });
  selectEl.innerHTML = html;
  if (unique.includes(current)) {
    selectEl.value = current;
  }
}

function filterRows(rows, deviceVal, keyVal, queryVal) {
  const q = queryVal.trim().toLowerCase();
  return rows.filter((r) => {
    if (deviceVal && r.deviceName !== deviceVal) { return false; }
    if (keyVal && r.sensorKey !== keyVal) { return false; }
    if (!q) { return true; }
    const text = `${r.deviceId} ${r.deviceName} ${r.sensorKey} ${r.sensorValue} ${r.receivedAt}`.toLowerCase();
    return text.includes(q);
  });
}

function downloadBlob(content, mimeType, filename) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

function buildCsvPayload(rows) {
  const headers = ['ID thiết bị', 'Tên thiết bị', 'Tên giá trị', 'Giá trị cảm biến', 'Thời gian nhận dữ liệu'];
  const lines = [headers.join(',')];
  rows.forEach((r) => {
    const cols = [r.deviceId, r.deviceName, r.sensorKey, r.sensorValue, r.receivedAt]
      .map((c) => `"${String(c).replace(/"/g, '""')}"`);
    lines.push(cols.join(','));
  });
  return '\ufeff' + lines.join('\n');
}

function buildExcelHtmlPayload(rows) {
  const headers = ['ID thiết bị', 'Tên thiết bị', 'Tên giá trị', 'Giá trị cảm biến', 'Thời gian nhận dữ liệu'];
  const ths = headers.map((h) => `<th>${escapeCell(h)}</th>`).join('');
  const trs = rows.map((r) => (
    `<tr><td>${escapeCell(r.deviceId)}</td><td>${escapeCell(r.deviceName)}</td>`
    + `<td>${escapeCell(r.sensorKey)}</td><td>${escapeCell(r.sensorValue)}</td>`
    + `<td>${escapeCell(r.receivedAt)}</td></tr>`
  )).join('');
  return `<html xmlns:o="urn:schemas-microsoft-com:office:office" `
    + `xmlns:x="urn:schemas-microsoft-com:office:excel"><head><meta charset="UTF-8"/></head>`
    + `<body><table border="1"><thead><tr>${ths}</tr></thead><tbody>${trs}</tbody></table></body></html>`;
}

function renderTableRows(tbodyEl, countEl, rows) {
  countEl.textContent = `${rows.length} bản ghi`;
  if (!rows.length) {
    tbodyEl.innerHTML = '<tr><td colspan="5" class="tb-empty">Không có dữ liệu phù hợp bộ lọc.</td></tr>';
    return;
  }
  const html = rows.slice(0, 500).map((r) => (
    `<tr><td>${escapeCell(r.deviceId)}</td><td>${escapeCell(r.deviceName)}</td>`
    + `<td>${escapeCell(r.sensorKey)}</td><td>${escapeCell(r.sensorValue)}</td>`
    + `<td>${escapeCell(r.receivedAt)}</td></tr>`
  )).join('');
  tbodyEl.innerHTML = html;
}

self.onInit = function () {
  const root = self.ctx.$container[0];
  const els = {
    dev: root.querySelector('#tbDeviceFilter'),
    key: root.querySelector('#tbKeyFilter'),
    search: root.querySelector('#tbSearchFilter'),
    reset: root.querySelector('#tbResetBtn'),
    csv: root.querySelector('#tbCsvBtn'),
    xls: root.querySelector('#tbXlsBtn'),
    body: root.querySelector('#tbLogsBody'),
    count: root.querySelector('#tbRowCount')
  };
  let allRows = [];
  let visibleRows = [];

  function refreshView() {
    visibleRows = filterRows(allRows, els.dev.value, els.key.value, els.search.value);
    renderTableRows(els.body, els.count, visibleRows);
  }

  self.onDataUpdated = function () {
    allRows = flattenCtxRows(self.ctx.data);
    populateSelect(els.dev, allRows.map((r) => r.deviceName), 'Tất cả thiết bị');
    populateSelect(els.key, allRows.map((r) => r.sensorKey), 'Tất cả giá trị');
    refreshView();
  };

  els.dev.addEventListener('change', refreshView);
  els.key.addEventListener('change', refreshView);
  els.search.addEventListener('input', refreshView);
  els.reset.addEventListener('click', () => {
    els.dev.value = '';
    els.key.value = '';
    els.search.value = '';
    refreshView();
  });
  els.csv.addEventListener('click', () => {
    downloadBlob(buildCsvPayload(visibleRows), 'text/csv;charset=utf-8;', 'iot_logs.csv');
  });
  els.xls.addEventListener('click', () => {
    downloadBlob(buildExcelHtmlPayload(visibleRows), 'application/vnd.ms-excel;charset=utf-8;', 'iot_logs.xls');
  });
  self.onDataUpdated();
};

self.onDestroy = function () {};
