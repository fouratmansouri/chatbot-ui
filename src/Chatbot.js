import React, { useState } from "react";
import { motion } from "framer-motion";
import { MessageSquare, X } from "lucide-react";

const Chatbot = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [loading, setLoading] = useState(false); // To show loading indicator

  const toggleChat = () => {
    setIsOpen(!isOpen);
  };

  const handleSend = async () => {
    if (inputValue.trim()) {
      // Add user's message to chat
      setMessages([...messages, { sender: "user", text: inputValue }]);
      setInputValue("");
      setLoading(true); // Start loading

      try {
        // Send user query to FastAPI backend
        const response = await fetch("http://127.0.0.1:3000/query/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ question: inputValue }),
        });

        const data = await response.json();
        if (data.answer) {
          // Add bot's response to chat
          setMessages((prevMessages) => [
            ...prevMessages,
            { sender: "bot", text: data.answer },
          ]);
        } else {
          setMessages((prevMessages) => [
            ...prevMessages,
            { sender: "bot", text: "Sorry, I couldn't find an answer." },
          ]);
        }
      } catch (error) {
        console.error("Error fetching response:", error);
        setMessages((prevMessages) => [
          ...prevMessages,
          { sender: "bot", text: "Sorry, there was an error processing your request." },
        ]);
      } finally {
        setLoading(false); // End loading
      }
    }
  };

  const handleKeyPress = (event) => {
    if (event.key === "Enter") {
      handleSend();
    }
  };

  return (
    <div>
      {/* Conditionally render the Chat Toggle Button */}
      {!isOpen && (
        <button className="chat-toggle" onClick={toggleChat}>
          <MessageSquare size={24} />
        </button>
      )}

      {/* Chat Window */}
      <motion.div
        initial={{ x: "100%" }}
        animate={{ x: isOpen ? "0%" : "100%" }}
        transition={{ duration: 0.3 }}
        className={`chat-window ${isOpen ? "open" : ""}`}
      >
        {/* Chat Header */}
        <div className="chat-header">
          <h2>Chatbot</h2>
          <button className="close-btn" onClick={toggleChat}>
            <X size={24} />
          </button>
        </div>

        {/* Chat Messages */}
        <div className="chat-messages">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`message ${message.sender === "user" ? "user" : "bot"}`}
            >
              {message.text}
            </div>
          ))}
          {loading && <div className="loading">Bot is typing...</div>} {/* Loading indicator */}
        </div>

        {/* Chat Input */}
        <div className="chat-input">
          <input
            type="text"
            placeholder="Type a message..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress} // Add this to listen for Enter key
          />
          <button onClick={handleSend}>Send</button>
        </div>
      </motion.div>
    </div>
  );
};

export default Chatbot;