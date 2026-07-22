const chatWindow = document.getElementById("chat-window");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const exerciseTpl = document.getElementById("exercise-card-template");
const mealTpl = document.getElementById("meal-card-template");

function scrollToBottom() {
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function addBubble(sender, html) {
  const row = document.createElement("div");
  row.className = `chat-row ${sender}`;
  if (sender === "bot") {
    row.innerHTML = `<div class="avatar">⚡</div><div class="bubble">${html}</div>`;
  } else {
    row.innerHTML = `<div class="bubble">${html}</div>`;
  }
  chatWindow.appendChild(row);
  scrollToBottom();
  return row;
}

function addTyping() {
  const row = document.createElement("div");
  row.className = "chat-row bot";
  row.id = "typing-row";
  row.innerHTML = `<div class="avatar">⚡</div><div class="bubble typing-indicator"><span></span><span></span><span></span></div>`;
  chatWindow.appendChild(row);
  scrollToBottom();
}

function removeTyping() {
  const el = document.getElementById("typing-row");
  if (el) el.remove();
}

function buildExerciseCard(ex) {
  const node = exerciseTpl.content.cloneNode(true);
  node.querySelector(".exercise-gif").src = ex.gif_url || ex.thumbnail;
  node.querySelector(".exercise-gif").alt = ex.name;
  node.querySelector(".ex-name").textContent = ex.name;
  node.querySelector(".tag-bodypart").textContent = ex.body_part;
  node.querySelector(".tag-target").textContent = ex.target;
  node.querySelector(".tag-equipment").textContent = ex.equipment;
  node.querySelector(".ex-secondary").textContent = ex.secondary_muscles && ex.secondary_muscles.length
    ? "Also works: " + ex.secondary_muscles.join(", ") : "";
  const list = node.querySelector(".ex-instructions");
  (ex.instructions || []).slice(0, 5).forEach((step) => {
    const li = document.createElement("li");
    li.textContent = step;
    list.appendChild(li);
  });
  return node;
}

function buildMealCard(meal) {
  const node = mealTpl.content.cloneNode(true);
  node.querySelector(".meal-title").textContent = meal.title;
  node.querySelector(".macro.cal").textContent = `${Math.round(meal.calories)} kcal`;
  node.querySelector(".macro.protein").textContent = `${meal.protein.toFixed(1)}g protein`;
  node.querySelector(".macro.carbs").textContent = `${meal.carbs.toFixed(1)}g carbs`;
  node.querySelector(".macro.fat").textContent = `${meal.fat.toFixed(1)}g fat`;
  node.querySelector(".meal-ingredients").textContent = meal.ingredients;
  return node;
}

function renderCards(cardType, cards) {
  if (!cards) return;

  if (cardType === "exercise" && Array.isArray(cards) && cards.length) {
    const wrap = document.createElement("div");
    wrap.className = "card-grid";
    cards.forEach((ex) => wrap.appendChild(buildExerciseCard(ex)));
    const row = document.createElement("div");
    row.className = "chat-row bot";
    row.innerHTML = `<div class="avatar">⚡</div>`;
    row.appendChild(wrap);
    chatWindow.appendChild(row);
  }

  if (cardType === "diet" && cards && typeof cards === "object") {
    Object.entries(cards).forEach(([slot, meals]) => {
      if (!meals.length) return;
      const section = document.createElement("div");
      section.className = "chat-row bot";
      const inner = document.createElement("div");
      inner.style.width = "100%";
      const title = document.createElement("div");
      title.className = "weekly-day-title";
      title.textContent = slot.charAt(0).toUpperCase() + slot.slice(1);
      inner.appendChild(title);
      const grid = document.createElement("div");
      grid.className = "card-grid";
      meals.forEach((m) => grid.appendChild(buildMealCard(m)));
      inner.appendChild(grid);
      section.innerHTML = `<div class="avatar">⚡</div>`;
      section.appendChild(inner);
      chatWindow.appendChild(section);
    });
  }

  if (cardType === "weekly_plan" && Array.isArray(cards)) {
    cards.forEach((day) => {
      const section = document.createElement("div");
      section.className = "chat-row bot";
      const inner = document.createElement("div");
      inner.style.width = "100%";
      const title = document.createElement("div");
      title.className = "weekly-day-title";
      title.textContent = day.day;
      const sub = document.createElement("div");
      sub.className = "weekly-day-sub";
      sub.textContent = day.title;
      inner.appendChild(title);
      inner.appendChild(sub);
      if (day.exercises && day.exercises.length) {
        const grid = document.createElement("div");
        grid.className = "card-grid";
        day.exercises.forEach((ex) => grid.appendChild(buildExerciseCard(ex)));
        inner.appendChild(grid);
      }
      section.innerHTML = `<div class="avatar">⚡</div>`;
      section.appendChild(inner);
      chatWindow.appendChild(section);
    });
  }

  scrollToBottom();
}

async function sendMessage(text) {
  addBubble("user", text);
  addTyping();
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });
    const data = await res.json();
    removeTyping();
    addBubble("bot", data.reply.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>"));
    renderCards(data.card_type, data.cards);
  } catch (err) {
    removeTyping();
    addBubble("bot", "Something went wrong reaching the server. Please try again.");
  }
}

chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = chatInput.value.trim();
  if (!text) return;
  chatInput.value = "";
  sendMessage(text);
});

// Auto-send if a quick-prompt query string was passed in, e.g. /chat?q=I want a bigger chest
const params = new URLSearchParams(window.location.search);
if (params.get("q")) {
  sendMessage(params.get("q"));
}
