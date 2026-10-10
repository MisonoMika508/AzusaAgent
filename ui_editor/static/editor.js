const state = {
  image: null,
  elements: [],
  selectedId: null,
  uploadId: null,
  templateId: null,
  drawScale: 1,
  drag: null,
};

const canvas = document.getElementById("annotator");
const context = canvas.getContext("2d");
const stage = document.getElementById("canvasStage");
const imageInput = document.getElementById("imageInput");
const toast = document.getElementById("toast");
const form = document.getElementById("elementForm");
const elementFields = {
  name: document.getElementById("elementName"),
  function: document.getElementById("elementFunction"),
  description: document.getElementById("elementDescription"),
  x: document.getElementById("elementX"),
  y: document.getElementById("elementY"),
  width: document.getElementById("elementWidth"),
  height: document.getElementById("elementHeight"),
};

function showToast(message, isError = false) {
  toast.textContent = message;
  toast.style.background = isError ? "#a82f37" : "#174b39";
  toast.classList.add("visible");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toast.classList.remove("visible"), 2800);
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || `请求失败 (${response.status})`);
  return data;
}

function currentElement() {
  return state.elements.find((item) => item.id === state.selectedId) || null;
}

function resizeCanvas() {
  if (!state.image) return;
  const padding = 40;
  const availableWidth = Math.max(100, stage.clientWidth - padding);
  const availableHeight = Math.max(100, stage.clientHeight - padding);
  state.drawScale = Math.min(
    availableWidth / state.image.naturalWidth,
    availableHeight / state.image.naturalHeight,
    1,
  );
  canvas.width = state.image.naturalWidth;
  canvas.height = state.image.naturalHeight;
  canvas.style.width = `${Math.round(canvas.width * state.drawScale)}px`;
  canvas.style.height = `${Math.round(canvas.height * state.drawScale)}px`;
  drawCanvas();
}

function drawCanvas() {
  if (!state.image) return;
  context.clearRect(0, 0, canvas.width, canvas.height);
  context.drawImage(state.image, 0, 0, canvas.width, canvas.height);
  const lineWidth = 2 / state.drawScale;
  const fontSize = Math.max(12, 13 / state.drawScale);

  for (const element of state.elements) {
    const selected = element.id === state.selectedId;
    context.save();
    context.lineWidth = selected ? lineWidth * 1.5 : lineWidth;
    context.strokeStyle = selected ? "#ff3636" : "#f21f36";
    context.setLineDash(selected ? [] : [6 / state.drawScale, 3 / state.drawScale]);
    context.strokeRect(element.x, element.y, element.width, element.height);
    context.setLineDash([]);
    if (element.name) {
      const label = element.name;
      context.font = `600 ${fontSize}px Segoe UI, Microsoft YaHei, sans-serif`;
      const labelWidth = context.measureText(label).width + 12 / state.drawScale;
      const labelHeight = 22 / state.drawScale;
      const labelY = Math.max(0, element.y - labelHeight);
      context.fillStyle = "rgba(130, 20, 27, .9)";
      context.fillRect(element.x, labelY, labelWidth, labelHeight);
      context.fillStyle = "#fff";
      context.fillText(label, element.x + 6 / state.drawScale, labelY + 15 / state.drawScale);
    }
    if (selected) {
      const handleSize = 10 / state.drawScale;
      context.fillStyle = "#fff";
      context.fillRect(element.x + element.width - handleSize / 2, element.y + element.height - handleSize / 2, handleSize, handleSize);
      context.strokeStyle = "#e44343";
      context.strokeRect(element.x + element.width - handleSize / 2, element.y + element.height - handleSize / 2, handleSize, handleSize);
    }
    context.restore();
  }

  if (state.drag?.mode === "draw") {
    const rect = state.drag.preview;
    context.save();
    context.strokeStyle = "#e44343";
    context.lineWidth = lineWidth * 1.5;
    context.setLineDash([7 / state.drawScale, 4 / state.drawScale]);
    context.strokeRect(rect.x, rect.y, rect.width, rect.height);
    context.restore();
  }
}

function toImagePoint(event) {
  const rect = canvas.getBoundingClientRect();
  return {
    x: Math.max(0, Math.min(canvas.width, (event.clientX - rect.left) * canvas.width / rect.width)),
    y: Math.max(0, Math.min(canvas.height, (event.clientY - rect.top) * canvas.height / rect.height)),
  };
}

function pointInElement(point, element) {
  return point.x >= element.x && point.x <= element.x + element.width
    && point.y >= element.y && point.y <= element.y + element.height;
}

function hitElement(point) {
  return [...state.elements].reverse().find((item) => pointInElement(point, item)) || null;
}

function normalizeRect(start, current) {
  return {
    x: Math.round(Math.min(start.x, current.x)),
    y: Math.round(Math.min(start.y, current.y)),
    width: Math.round(Math.abs(current.x - start.x)),
    height: Math.round(Math.abs(current.y - start.y)),
  };
}

function selectElement(id) {
  state.selectedId = id;
  const element = currentElement();
  document.getElementById("inspectorEmpty").hidden = Boolean(element);
  form.hidden = !element;
  document.getElementById("deleteElementButton").disabled = !element;
  if (element) {
    for (const [key, input] of Object.entries(elementFields)) input.value = element[key] ?? "";
    updateCenter();
  }
  drawCanvas();
  renderElementList();
}

function updateCenter() {
  const element = currentElement();
  if (!element) return;
  const centerX = Math.round(element.x + element.width / 2);
  const centerY = Math.round(element.y + element.height / 2);
  document.getElementById("elementCenter").textContent = `${centerX}, ${centerY}`;
}

function renderElementList() {
  const list = document.getElementById("elementList");
  list.replaceChildren();
  document.getElementById("elementListCount").textContent = String(state.elements.length);
  document.getElementById("uiCount").textContent = `${state.elements.length} 个 UI`;

  for (const element of state.elements) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `element-item${element.id === state.selectedId ? " active" : ""}`;
    const title = document.createElement("strong");
    title.textContent = element.name || "未命名 UI";
    const description = document.createElement("span");
    description.textContent = element.function || "未填写功能";
    const coordinates = document.createElement("span");
    coordinates.className = "element-coords";
    coordinates.textContent = `(${element.x}, ${element.y}) · ${element.width}×${element.height}`;
    button.append(title, description, coordinates);
    button.addEventListener("click", () => selectElement(element.id));
    list.append(button);
  }
}

function setImage(source, width, height) {
  const image = new Image();
  image.onload = () => {
    state.image = image;
    canvas.hidden = false;
    document.getElementById("emptyState").hidden = true;
    document.getElementById("imageMeta").textContent = `${width || image.naturalWidth} × ${height || image.naturalHeight}`;
    document.getElementById("saveTemplateButton").disabled = false;
    resizeCanvas();
  };
  image.onerror = () => showToast("截图加载失败。", true);
  image.src = source;
}

async function uploadImage(file) {
  if (!file) return;
  const extension = `.${file.name.split(".").pop().toLowerCase()}`;
  if (![".png", ".jpg", ".jpeg", ".webp"].includes(extension)) {
    showToast("只支持 PNG、JPG、JPEG 和 WEBP。", true);
    return;
  }
  const formData = new FormData();
  formData.append("image", file);
  try {
    const result = await requestJson("/api/upload", { method: "POST", body: formData });
    state.uploadId = result.upload_id;
    state.templateId = null;
    state.elements = [];
    state.selectedId = null;
    document.getElementById("templateName").value = file.name.replace(/\.[^.]+$/, "");
    document.getElementById("gameName").value = "Blue Archive";
    selectElement(null);
    setImage(result.image_url, result.width, result.height);
    document.getElementById("canvasHint").textContent = "按住左键拖动以标注 UI";
    await loadTemplates();
  } catch (error) {
    showToast(error.message, true);
  }
}

async function loadTemplates() {
  const list = document.getElementById("templateList");
  list.replaceChildren();
  try {
    const templates = await requestJson("/api/templates");
    document.getElementById("templateCount").textContent = String(templates.length);
    for (const template of templates) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `template-item${template.id === state.templateId ? " active" : ""}`;
      const title = document.createElement("strong");
      title.textContent = template.name;
      const detail = document.createElement("span");
      detail.textContent = `${template.game} · ${template.width}×${template.height} · ${template.ui_count} UI`;
      const thumbnail = document.createElement("img");
      thumbnail.className = "template-thumb";
      thumbnail.src = template.image_url;
      thumbnail.alt = "";
      button.append(thumbnail, title, detail);
      button.addEventListener("click", () => loadTemplate(template.id));
      list.append(button);
    }
  } catch (error) {
    showToast(error.message, true);
  }
}

async function loadTemplate(templateId) {
  try {
    const template = await requestJson(`/api/templates/${encodeURIComponent(templateId)}`);
    state.templateId = template.id;
    state.uploadId = null;
    state.elements = template.ui_elements.map((item) => ({ ...item }));
    document.getElementById("templateName").value = template.name;
    document.getElementById("gameName").value = template.game;
    document.getElementById("imageMeta").textContent = `${template.width} × ${template.height}`;
    selectElement(null);
    setImage(`${template.image_url}?v=${Date.now()}`, template.width, template.height);
    document.getElementById("canvasHint").textContent = "选择标注框修改名称、功能或位置";
    document.getElementById("saveTemplateButton").disabled = false;
    document.getElementById("deleteTemplateButton")?.remove();
    const removeButton = document.createElement("button");
    removeButton.id = "deleteTemplateButton";
    removeButton.className = "button button-small button-danger";
    removeButton.type = "button";
    removeButton.textContent = "删除模板";
    removeButton.addEventListener("click", deleteCurrentTemplate);
    document.querySelector(".top-actions").prepend(removeButton);
    await loadTemplates();
  } catch (error) {
    showToast(error.message, true);
  }
}

async function deleteCurrentTemplate() {
  if (!state.templateId) return;
  try {
    await requestJson(`/api/templates/${encodeURIComponent(state.templateId)}`, { method: "DELETE" });
    state.templateId = null;
    state.uploadId = null;
    state.elements = [];
    state.image = null;
    canvas.hidden = true;
    document.getElementById("emptyState").hidden = false;
    document.getElementById("imageMeta").textContent = "未载入截图";
    document.getElementById("saveTemplateButton").disabled = true;
    document.getElementById("deleteTemplateButton")?.remove();
    selectElement(null);
    await loadTemplates();
    showToast("模板已删除。");
  } catch (error) {
    showToast(error.message, true);
  }
}

async function saveTemplate() {
  if (!state.image) return;
  const payload = {
    template_id: state.templateId,
    upload_id: state.uploadId,
    name: document.getElementById("templateName").value.trim(),
    game: document.getElementById("gameName").value.trim(),
    ui_elements: state.elements.map(({ id, name, function: action, description, x, y, width, height }) => ({
      id, name, function: action, description, x, y, width, height,
    })),
  };
  try {
    const template = await requestJson("/api/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    state.templateId = template.id;
    state.uploadId = null;
    document.getElementById("imageMeta").textContent = `${template.width} × ${template.height} · 已保存`;
    await loadTemplates();
    showToast("模板及 UI 坐标已保存到 SQLite。");
  } catch (error) {
    showToast(error.message, true);
  }
}

function readPoint(event) {
  const point = toImagePoint(event);
  const start = state.drag.start;
  if (state.drag.mode === "draw") {
    state.drag.preview = normalizeRect(start, point);
    drawCanvas();
    return;
  }
  const element = currentElement();
  if (!element) return;
  const dx = point.x - start.x;
  const dy = point.y - start.y;
  if (state.drag.mode === "move") {
    element.x = Math.round(Math.max(0, Math.min(canvas.width - element.width, state.drag.origin.x + dx)));
    element.y = Math.round(Math.max(0, Math.min(canvas.height - element.height, state.drag.origin.y + dy)));
  } else if (state.drag.mode === "resize") {
    element.width = Math.round(Math.max(1, Math.min(canvas.width - element.x, state.drag.origin.width + dx)));
    element.height = Math.round(Math.max(1, Math.min(canvas.height - element.y, state.drag.origin.height + dy)));
  }
  for (const [key, input] of Object.entries(elementFields)) input.value = element[key] ?? "";
  updateCenter();
  drawCanvas();
}

canvas.addEventListener("pointerdown", (event) => {
  if (!state.image || event.button !== 0) return;
  const point = toImagePoint(event);
  const hit = hitElement(point);
  if (hit) {
    selectElement(hit.id);
    const nearHandle = point.x >= hit.x + hit.width - 16 / state.drawScale
      && point.y >= hit.y + hit.height - 16 / state.drawScale;
    state.drag = {
      mode: nearHandle ? "resize" : "move",
      start: point,
      origin: { x: hit.x, y: hit.y, width: hit.width, height: hit.height },
    };
  } else {
    const element = {
      id: `draft_${crypto.randomUUID()}`,
      name: "",
      function: "",
      description: "",
      x: Math.round(point.x),
      y: Math.round(point.y),
      width: 1,
      height: 1,
    };
    state.elements.push(element);
    selectElement(element.id);
    state.drag = { mode: "draw", start: point, preview: { x: point.x, y: point.y, width: 1, height: 1 } };
  }
  canvas.setPointerCapture(event.pointerId);
});

canvas.addEventListener("pointermove", (event) => {
  if (state.drag) readPoint(event);
});

canvas.addEventListener("pointerup", (event) => {
  if (!state.drag) return;
  if (state.drag.mode === "draw") {
    const element = currentElement();
    const rect = state.drag.preview;
    if (element && rect.width >= 2 && rect.height >= 2) {
      Object.assign(element, rect);
      for (const [key, input] of Object.entries(elementFields)) input.value = element[key] ?? "";
      updateCenter();
      elementFields.name.focus();
    } else if (element) {
      state.elements = state.elements.filter((item) => item.id !== element.id);
      selectElement(null);
    }
  }
  state.drag = null;
  renderElementList();
  drawCanvas();
  try { canvas.releasePointerCapture(event.pointerId); } catch (_) { /* capture may already be released */ }
});

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const element = currentElement();
  if (!element) return;
  element.name = elementFields.name.value.trim();
  element.function = elementFields.function.value.trim();
  element.description = elementFields.description.value.trim();
  for (const key of ["x", "y", "width", "height"]) element[key] = Number(elementFields[key].value);
  if (!element.name || !element.function) {
    showToast("请填写 UI 名称和功能。", true);
    return;
  }
  if (element.x < 0 || element.y < 0 || element.width < 1 || element.height < 1
    || element.x + element.width > canvas.width || element.y + element.height > canvas.height) {
    showToast("矩形超出原图范围，请检查坐标。", true);
    return;
  }
  renderElementList();
  drawCanvas();
  showToast("标注已更新，请保存整个模板。");
});

for (const key of ["x", "y", "width", "height"]) {
  elementFields[key].addEventListener("input", () => {
    const element = currentElement();
    if (!element) return;
    element[key] = Number(elementFields[key].value || 0);
    updateCenter();
    drawCanvas();
  });
}
for (const key of ["name", "function", "description"]) {
  elementFields[key].addEventListener("input", () => {
    const element = currentElement();
    if (!element) return;
    element[key] = elementFields[key].value;
    renderElementList();
    drawCanvas();
  });
}

document.getElementById("deleteElementButton").addEventListener("click", () => {
  if (!state.selectedId) return;
  state.elements = state.elements.filter((item) => item.id !== state.selectedId);
  selectElement(null);
});
document.getElementById("clearSelectionButton").addEventListener("click", () => selectElement(null));
document.getElementById("saveTemplateButton").addEventListener("click", saveTemplate);
document.getElementById("openImageButton").addEventListener("click", () => imageInput.click());
document.getElementById("emptyOpenButton").addEventListener("click", () => imageInput.click());
imageInput.addEventListener("change", (event) => uploadImage(event.target.files[0]));

for (const eventName of ["dragenter", "dragover"]) {
  stage.addEventListener(eventName, (event) => {
    event.preventDefault();
    stage.classList.add("dragging");
  });
}
for (const eventName of ["dragleave", "drop"]) {
  stage.addEventListener(eventName, (event) => {
    event.preventDefault();
    stage.classList.remove("dragging");
  });
}
stage.addEventListener("drop", (event) => uploadImage(event.dataTransfer.files[0]));
window.addEventListener("resize", resizeCanvas);
new ResizeObserver(resizeCanvas).observe(stage);

loadTemplates();
