const form = document.getElementById("chat-form");
const input = document.getElementById("user-input");
const chatArea = document.getElementById("chat-area");

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const userText = input.value.trim();
  if (!userText) return;

  // Show user message
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
    console.log("📦 Response from backend:", data);

    const reply = typeof data.response === "string"
      ? data.response
      : JSON.stringify(data.response);

    chatArea.innerHTML += `<div class="bot-message">${reply}</div>`;

  } catch (err) {
    console.error("❌ Chat error:", err);
    chatArea.innerHTML += `<div class="bot-message">❌ Server error</div>`;
  }
  document.getElementById("end-chat-btn").addEventListener("click", () => {
  window.location.href = "form.html";  // Redirect to form page
});

});
