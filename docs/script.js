// script.js
const form = document.getElementById("chat-form");
const input = document.getElementById("user-input");
const chatArea = document.getElementById("chat-area");
const endChatBtn = document.getElementById("end-chat-btn");

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const userText = input.value.trim();
  if (!userText) return;

  chatArea.innerHTML += `<div class="user-message">${userText}</div>`;
  input.value = "";

  try {
    const res = await fetch("https://Vishesh1005-chatbot.hf.space/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ text: userText })
    });

    const data = await res.json();
    const reply = typeof data.response === "string"
      ? data.response
      : JSON.stringify(data.response);

    chatArea.innerHTML += `<div class="bot-message">${reply}</div>`;
    chatArea.scrollTop = chatArea.scrollHeight;

  } catch (err) {
    console.error("❌ Chat error:", err);
    chatArea.innerHTML += `<div class="bot-message">❌ Server error</div>`;
  }
});

endChatBtn.addEventListener("click", () => {
  window.location.href = "form.html";
});
