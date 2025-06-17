document.addEventListener("DOMContentLoaded", () => {
  const chatBox = document.getElementById("chatBox");
  const chatForm = document.getElementById("chatForm");
  const userInput = document.getElementById("userInput");
  const endChatBtn = document.getElementById("endChatBtn");

  // Send message on form submit
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
        body: JSON.stringify({ message }),
      });
      const data = await res.json();
      addMessage("bot", data.response);
    } catch (err) {
      addMessage("bot", "Server error. Please try again later.");
    }
  });

  // Allow pressing Enter to send
  userInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      chatForm.dispatchEvent(new Event("submit"));
    }
  });

  // End Chat and show form
  endChatBtn.addEventListener("click", () => {
    window.location.href = "form.html";
  });

  function addMessage(sender, text) {
    const msgDiv = document.createElement("div");
    msgDiv.className = sender === "user" ? "user-message" : "bot-message";
    msgDiv.textContent = text;
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
  }
});
