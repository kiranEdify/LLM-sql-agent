import React, { useState, useEffect, useRef } from "react";
import { Box, Typography, TextField, IconButton, Avatar, Paper, CircularProgress, Select, MenuItem, FormControl } from "@mui/material";
import SendIcon from "@mui/icons-material/Send";
import axios from "axios";
import PersonIcon from "@mui/icons-material/Person";
import SupportAgentIcon from "@mui/icons-material/SupportAgent";
import DeleteIcon from "@mui/icons-material/Delete";

const models = [
    "qwen2.5:32b",
    "llama3.1",
    // "deepseek-r1:32b",
    // "deepseek-r1:8b",
    // "qwen2.5:14b",
    // "qwen2.5:32b",
    // "qwen2.5:72b",
    // "qwen2.5",
    // "mistral",
    // "llama3.1:70b",
    // "gemma2:27b",
    // "falcon:40b"
];

const users = {
  "Alice":1,
  "Bob":2
}


const ChatUI = () => {
  const [messages, setMessages] = useState([
    { role: "assistant", content: "Hi, How may I help you?", timestamp: new Date().toLocaleTimeString() },
  ]);
  const [currentMessage, setCurrentMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState(models[0]);
  const [selectedUser, setSelectedUser] = useState(users.Alice);
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
        user_msg: currentMessage,
        history: messages,
        model: selectedModel,
        context:`customer id : ${selectedUser}`
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
    <Box sx={{ height: "90vh", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", backgroundColor: "#f5f5f5", padding: "20px", overflow: "hidden" }}>
      <Paper elevation={3} sx={{width: { xs: "100%", sm: "90%", md: "50%", }, maxWidth: "1200px", borderRadius: "12px", padding: "20px", height: "100vh", display: "flex", flexDirection: "column", overflow: "hidden" }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Box display="flex" alignItems="center">
            <Typography variant="h6" fontWeight={600} >
              Chatbot -
            </Typography>
            <FormControl size="small"  sx={{ ml: 1, minWidth: 140,  }}>
              <Select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                displayEmpty
                sx={{ fontWeight: "bold", color: "#1976d2", backgroundColor: "transparent", boxShadow: "none", '.MuiOutlinedInput-notchedOutline': { border: 0 } }}
              >
                {models.map((model) => (
                  <MenuItem key={model} value={model}>{model}</MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl size="small"  sx={{ ml: 1, minWidth: 140,  }}>
            <Select
                value={selectedUser}
                onChange={(e) => setSelectedUser(e.target.value)}
                displayEmpty
                sx={{ fontWeight: "bold", color: "#1976d2", backgroundColor: "transparent", boxShadow: "none", '.MuiOutlinedInput-notchedOutline': { border: 0 } }}
              >
                 {Object.entries(users).map(([name, id]) => (
                    <MenuItem key={id} value={id}>
                      {name}
                    </MenuItem>
                  ))}
              </Select>
             
            </FormControl>
          </Box>
          <IconButton color="error" onClick={clearChat}>
            <DeleteIcon />
          </IconButton>
        </Box>

        <Box sx={{ backgroundColor: "white", borderRadius: "10px", padding: "10px", flex: 1, overflowY: "auto", minHeight: "0px" }}>
          {messages.map((msg, index) => (
            <Box key={index} display="flex" alignItems="center" justifyContent={msg.role === "user" ? "flex-end" : "flex-start"} mb={2}>
              {msg.role === "assistant" && <Avatar sx={{ bgcolor: "black", color: "white", marginRight: 1 }}><SupportAgentIcon/></Avatar>}
              <Box sx={{ backgroundColor: msg.role === "user" ? "#e3f2fd" : "#d1c4e9", borderRadius: msg.role === "user" ? "18px 18px 5px 18px" : "18px 18px 18px 5px", padding: "10px 15px", maxWidth: "75%", position: "relative" }}>
                <Typography><div dangerouslySetInnerHTML={{ __html: msg.content }} /></Typography>
                <Typography sx={{ fontSize: "0.75rem", color: "gray", textAlign: "right", marginTop: "5px" }}>
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
