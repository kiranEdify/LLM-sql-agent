import React, { useState } from "react";
import { Box, Typography, TextField, IconButton, Avatar, Paper , CircularProgress } from "@mui/material";
import SendIcon from "@mui/icons-material/Send";
import axios from "axios";
import SupportAgentIcon from '@mui/icons-material/SupportAgent';
import FaceIcon from '@mui/icons-material/Face';
import PersonIcon from '@mui/icons-material/Person';

const ChatUI = () => {
  const [messages, setMessages] = useState([
    { role: "assistant", content: "Hi, How may I help you?" },
  ]);
  const [currentMessage, setCurrentMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    console.log(currentMessage)
    if (!currentMessage.trim()) return;
    const newMessages = [...messages, { role: "user", content: currentMessage }];
    setMessages(newMessages);
    setCurrentMessage("");
    setLoading(true);

    console.log(newMessages)
    try {
      const response = await axios.post("http://localhost:8000/chat", {
        message: currentMessage,
        history: messages,
      });
      console.log("api-resp",response)
      setMessages([...newMessages, { role: "assistant", content: response.data.response }]);
    } catch (error) {
      console.error("Error sending message:", error);
    } finally {
        setLoading(false);
      }
  };

  return (
    <Box
      sx={{
        height: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        backgroundColor: "#f5f5f5",
        padding: "20px",
      }}
    >
      <Paper elevation={3} sx={{ width: "60%", borderRadius: "10px", padding: "20px" }}>
        <Typography variant="h6" gutterBottom>
          Hello,
        </Typography>
        <Typography variant="h4" color="primary" fontWeight="bold" gutterBottom>
          How can we assist you?
        </Typography>

        <Box
          sx={{
            backgroundColor: "white",
            borderRadius: "10px",
            padding: "10px",
            height: "400px",
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
