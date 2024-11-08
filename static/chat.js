function sendImage() {
    const imageInput = document.getElementById("image-input");
    const file = imageInput.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("image", file);

    fetch("/send_image", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.response) {
            addMessageToChatBox("bot", data.response);
        }
        // Display the uploaded image at the top
        const chatImage = document.getElementById("chat-image");
        chatImage.src = URL.createObjectURL(file);
    })
    .catch(error => console.error("Error:", error));
}

function addMessageToChatBox(sender, message) {
    const chatContainer = document.getElementById("chat-container");
    const messageElement = document.createElement("div");

    if (sender === "user") {
        messageElement.className = "message user-message";
        messageElement.innerText = "나: " + message;  // User's message
    } else {
        messageElement.className = "message bot-message";
        messageElement.innerText = "봇: " + message;  // Bot's message
    }

    chatContainer.appendChild(messageElement);
}
