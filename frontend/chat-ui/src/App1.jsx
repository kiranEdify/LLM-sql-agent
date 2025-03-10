import React, { useState } from "react";
import { Box, Typography, TextField, IconButton, Avatar, Paper, CircularProgress } from "@mui/material";
import SendIcon from "@mui/icons-material/Send";
import axios from "axios";
import PersonIcon from '@mui/icons-material/Person';
import SupportAgentIcon from '@mui/icons-material/SupportAgent';
import DeleteIcon from '@mui/icons-material/Delete';

const ChatUI = () => {
  const [messages, setMessages] = useState([
    { role: "assistant", content: "Hi, How may I help you?" },
  ]);
  const [currentMessage, setCurrentMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!currentMessage.trim()) return;
    const newMessages = [...messages, { role: "user", content: currentMessage }];
    setMessages(newMessages);
    setCurrentMessage("");
    setLoading(true);

    try {
      const response = await axios.post("http://localhost:8000/chat", {
        message: currentMessage,
        history: messages,
      });
      setMessages([...newMessages, { role: "assistant", content: response.data.response }]);
    } catch (error) {
      console.error("Error sending message:", error);
    } finally {
      setLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([{ role: "assistant", content: "Hi, How may I help you?" }]);
  };

  return (
    <Box
      sx={{
        height: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: "#f5f5f5",
        padding: "20px",
        overflow: "hidden", // Prevents overall scrollbar
      }}
    >
      <Paper elevation={3} sx={{ width: { xs: "95%", sm: "80%", md: "70%", lg: "60%" }, maxWidth: "800px", borderRadius: "10px", padding: "20px" }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6" gutterBottom>
                Chatbot 
                {" - "}
                <Typography variant="p" color="primary" fontWeight="bold" gutterBottom>
                qwen2.5:32b
                </Typography>
            </Typography>
            <IconButton color="error" onClick={clearChat}>
                <DeleteIcon />
            </IconButton>
        </Box>
        

        <Box
          sx={{
            backgroundColor: "white",
            borderRadius: "10px",
            padding: "10px",
            height: "60vh",
            minHeight: "300px",
            overflowY: "auto",
          }}
        >
          {messages.map((msg, index) => (
            <Box
              key={index}
              display="flex"
              alignItems="center"
              justifyContent={msg.role === "user" ? "flex-end" : "flex-start"}
              mb={2}
            >
              {msg.role === "assistant" && <Avatar sx={{ bgcolor: "black", color: "white", marginRight: 1 }}><SupportAgentIcon/></Avatar>}
              <Typography
                sx={{
                  backgroundColor: msg.role === "user" ? "#e3f2fd" : "#d1c4e9",
                  borderRadius: "10px",
                  padding: "10px",
                }}
              >
                {msg.content}
              </Typography>
              {msg.role === "user" && <Avatar sx={{ bgcolor: "purple", color: "white", marginLeft: 1 }}><PersonIcon/></Avatar>}
            </Box>
          ))}
          {loading && (
            <Box display="flex" justifyContent="center" mt={2}>
              <CircularProgress size={24} />
            </Box>
          )}
        </Box>

        <Box display="flex" alignItems="center" mt={2}>
          <TextField
            fullWidth
            variant="outlined"
            placeholder="Ask me anything..."
            value={currentMessage}
            onChange={(e) => setCurrentMessage(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          />
          <IconButton color="primary" sx={{ marginLeft: 1 }} onClick={sendMessage} disabled={loading}>
            <SendIcon />
          </IconButton>
        </Box>
      </Paper>
    </Box>
  );
};

export default ChatUI;
