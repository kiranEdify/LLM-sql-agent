import React, { useState, useEffect, useRef } from "react";
import { Box, Typography, TextField, IconButton, Avatar, Paper, CircularProgress } from "@mui/material";
import SendIcon from "@mui/icons-material/Send";
import axios from "axios";
import PersonIcon from "@mui/icons-material/Person";
import SupportAgentIcon from "@mui/icons-material/SupportAgent";
import DeleteIcon from "@mui/icons-material/Delete";

const ChatUI = () => {
    const [messages, setMessages] = useState([
      { role: "assistant", content: "Hi, How may I help you?", timestamp: new Date().toLocaleTimeString() },
    ]);
    const [currentMessage, setCurrentMessage] = useState("");
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef(null);

    useEffect(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, loading]);

    const sendMessage = async () => {
      if (!currentMessage.trim()) return;
      const newMessages = [...messages, { role: "user", content: currentMessage, timestamp: new Date().toLocaleTimeString() }];
      setMessages(newMessages);
      setCurrentMessage("");
      setLoading(true);

      try {
        const response = await axios.post("http://localhost:8000/chat", {
          message: currentMessage,
          history: messages,
        });
        setMessages([...newMessages, { role: "assistant", content: response.data.response, timestamp: new Date().toLocaleTimeString() }]);
      } catch (error) {
        console.error("Error sending message:", error);
      } finally {
        setLoading(false);
      }
    };

    const clearChat = () => {
      setMessages([{ role: "assistant", content: "Hi, How may I help you?", timestamp: new Date().toLocaleTimeString() }]);
    };

    return (
      <Box
        sx={{
          height: "90vh",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: "#f5f5f5",
          padding: "20px",
          overflow: "hidden", // Prevents scrolling issue
        }}
      >
        <Paper elevation={3} sx={{ 
          width: "70%",
          maxWidth: "1200px",
          borderRadius: "10px",
          padding: "20px",
          height: "100vh", 
          display: "flex",
          // flex:1,
          flexDirection: "column", 
          overflow: "hidden"

          }}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6" gutterBottom>
              {/* Chatbot - <Typography component="span" color="primary" fontWeight="bold">qwen2.5:32b</Typography> */}
              Chatbot - <Typography component="span" color="primary" fontWeight="bold">GPT-4o-mini:8b</Typography>
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
              flex: 1,
              overflowY: "auto",
              minHeight: "0px", // Prevents overall page scrolling
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
                <Box
                  sx={{
                    backgroundColor: msg.role === "user" ? "#e3f2fd" : "#d1c4e9",
                    borderRadius: msg.role === "user" ? "18px 18px 5px 18px" : "18px 18px 18px 5px", // Adjusted for correct styling
                    padding: "10px 15px",
                    maxWidth: "75%",
                    position: "relative",
                  }}
                >
                  <Typography>{msg.content}</Typography>
                  <Typography
                    sx={{
                      fontSize: "0.75rem",
                      color: "gray",
                      textAlign: "right",
                      marginTop: "5px",
                    }}
                  >
                    {msg.timestamp}
                  </Typography>
                </Box>
                {msg.role === "user" && <Avatar sx={{ bgcolor: "purple", color: "white", marginLeft: 1 }}><PersonIcon/></Avatar>}
              </Box>
            ))}
            {loading && (
              <Box display="flex" justifyContent="center" mt={2}>
                <CircularProgress size={24} />
              </Box>
            )}
            <div ref={messagesEndRef} />
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
