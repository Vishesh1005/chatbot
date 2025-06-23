document.addEventListener("DOMContentLoaded", () => {
  const chatBox = document.getElementById("chat-area");
  const chatForm = document.getElementById("chat-form");
  const userInput = document.getElementById("user-input");

  chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const message = userInput.value.trim();
    if (!message) return;

    addMessage("user", message);
    userInput.value = "";

    try {
      const res = await fetch("https://Vishesh1005-chatbot.hf.space/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: message }) // FIXED: 'text' → 'message' to match FastAPI input
      });

      const data = await res.json();

      // ✅ Add response text
      if (data.response) {
        addMessage("bot", data.response);
      }

      // ✅ Add image if present
      if (data.image) {
        const img = document.createElement("img");
        img.src = data.image;
        img.alt = "Response image";
        img.classList.add("chat-image");
        chatBox.appendChild(img);
        chatBox.scrollTop = chatBox.scrollHeight;
      }
    } catch (err) {
      addMessage("bot", "⚠️ Server error. Please try again later.");
    }
  });

  // ✅ Enter key sends message
  userInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      chatForm.dispatchEvent(new Event("submit"));
    }
  });

  // ✅ Append a message to chat
  function addMessage(sender, text) {
    const msgDiv = document.createElement("div");
    msgDiv.className = sender === "user" ? "user-message" : "bot-message";
    msgDiv.textContent = text;
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
  }
});
