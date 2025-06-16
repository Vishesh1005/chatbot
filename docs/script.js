const form = document.getElementById("chat-form");
const input = document.getElementById("user-input");
const chatArea = document.getElementById("chat-area");

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const userText = input.value.trim();
  if (!userText) return;

  chatArea.innerHTML += `<div class="user-message"><strong>You:</strong> ${userText}</div>`;
  chatArea.scrollTop = chatArea.scrollHeight;
  input.value = "";

  try {
    const res = await fetch("https://Vishesh1005-chatbot.hf.space/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: userText })
    });

    const data = await res.json();
    const reply = typeof data.response === "string" ? data.response : JSON.stringify(data.response);

    chatArea.innerHTML += `<div class="bot-message"><strong>Bot:</strong> ${reply}</div>`;
    chatArea.scrollTop = chatArea.scrollHeight;

  } catch (err) {
    chatArea.innerHTML += `<div class="bot-message">❌ Server error</div>`;
  }
});

document.getElementById("end-chat-btn").addEventListener("click", () => {
  window.location.href = "form.html";
});

input.addEventListener("keypress", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    form.dispatchEvent(new Event("submit"));
  }
  const res = await fetch("/submit-form", {
  method: "POST",
  headers: { "Content-Type": "application/x-www-form-urlencoded" },
  body: new URLSearchParams({ name, email, phone })
});

});
