import React, { useState } from 'react'
import {
  Paper,
  Typography,
  Box,
  TextField,
  Button,
  Card,
  CardContent,
  Divider,
  Chip,
  Alert,
  List,
  ListItem,
  ListItemText,
  IconButton,
  CircularProgress
} from '@mui/material'
import {
  Send as SendIcon,
  Clear as ClearIcon,
  ContentCopy as CopyIcon
} from '@mui/icons-material'
import { KingdomAPI, ChatRequest, ChatResponse } from '../services/api'

interface ChatTesterProps {
  onNewWorkflow: (workflow: any) => void
}

interface ChatMessage {
  id: string
  request: ChatRequest
  response?: ChatResponse
  timestamp: Date
  loading?: boolean
  error?: string
}

const ChatTester: React.FC<ChatTesterProps> = ({ onNewWorkflow }) => {
  const [sender, setSender] = useState('test_user')
  const [receiver, setReceiver] = useState('kingdom')
  const [forum, setForum] = useState('general')
  const [message, setMessage] = useState('')
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)

  const predefinedMessages = [
    {
      label: 'General Greeting',
      message: 'Hello! How are you today?',
      forum: 'general'
    },
    {
      label: 'Math Question - Basic',
      message: 'What is 15 + 25 * 2?',
      forum: 'math_help'
    },
    {
      label: 'Math Question - Equation',
      message: 'Can you solve the equation: 2x + 5 = 15?',
      forum: 'math_help'
    },
    {
      label: 'Math Question - Complex',
      message: 'Calculate the derivative of x² + 3x - 7',
      forum: 'math_help'
    },
    {
      label: 'General Question',
      message: 'What is the capital of France?',
      forum: 'trivia'
    },
    {
      label: 'Help Request',
      message: 'I need help with understanding how this system works',
      forum: 'support'
    }
  ]

  const sendMessage = async () => {
    if (!message.trim()) return

    const request: ChatRequest = {
      sender,
      receiver,
      forum,
      message: message.trim()
    }

    const chatMessage: ChatMessage = {
      id: `msg_${Date.now()}`,
      request,
      timestamp: new Date(),
      loading: true
    }

    setChatHistory(prev => [chatMessage, ...prev])
    setIsLoading(true)

    try {
      const response = await KingdomAPI.sendChatMessage(request)
      
      // Update the message with response
      setChatHistory(prev => 
        prev.map(msg => 
          msg.id === chatMessage.id 
            ? { ...msg, response, loading: false }
            : msg
        )
      )

      // Notify parent about new workflow
      onNewWorkflow({
        workflow_id: response.workflow_id,
        started_at: response.timestamp,
        first_agent: response.agent_used,
        status: 'completed'
      })

      // Clear form
      setMessage('')
      
    } catch (error) {
      console.error('Failed to send message:', error)
      setChatHistory(prev => 
        prev.map(msg => 
          msg.id === chatMessage.id 
            ? { ...msg, loading: false, error: 'Failed to send message' }
            : msg
        )
      )
    } finally {
      setIsLoading(false)
    }
  }

  const usePredefinedMessage = (predefinedMsg: any) => {
    setMessage(predefinedMsg.message)
    setForum(predefinedMsg.forum)
  }

  const clearHistory = () => {
    setChatHistory([])
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  const copyPostmanExample = () => {
    const example = {
      method: 'POST',
      url: 'http://localhost:8765/api/chat',
      headers: {
        'Content-Type': 'application/json'
      },
      body: {
        sender,
        receiver,
        forum,
        message
      }
    }
    copyToClipboard(JSON.stringify(example, null, 2))
  }

  return (
    <Box className="fade-in">
      <Typography variant="h4" gutterBottom>
        Chat Tester
      </Typography>

      <Box sx={{ display: 'flex', gap: 3, height: 'calc(100vh - 200px)' }}>
        {/* Input Form */}
        <Paper sx={{ width: 400, p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Send Test Message
          </Typography>

          <Box sx={{ mb: 2 }}>
            <TextField
              fullWidth
              label="Sender"
              value={sender}
              onChange={(e) => setSender(e.target.value)}
              size="small"
              sx={{ mb: 2 }}
            />
            
            <TextField
              fullWidth
              label="Receiver"
              value={receiver}
              onChange={(e) => setReceiver(e.target.value)}
              size="small"
              sx={{ mb: 2 }}
            />
            
            <TextField
              fullWidth
              label="Forum/Channel"
              value={forum}
              onChange={(e) => setForum(e.target.value)}
              size="small"
              sx={{ mb: 2 }}
            />
            
            <TextField
              fullWidth
              label="Message"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              multiline
              rows={3}
              size="small"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                  sendMessage()
                }
              }}
            />
          </Box>

          <Box sx={{ display: 'flex', gap: 1, mb: 3 }}>
            <Button
              variant="contained"
              onClick={sendMessage}
              disabled={isLoading || !message.trim()}
              startIcon={isLoading ? <CircularProgress size={16} /> : <SendIcon />}
              fullWidth
            >
              Send Message
            </Button>
            <IconButton onClick={copyPostmanExample} title="Copy Postman Example">
              <CopyIcon />
            </IconButton>
          </Box>

          <Divider sx={{ mb: 2 }} />

          <Typography variant="h6" gutterBottom>
            Quick Test Messages
          </Typography>
          
          <List dense>
            {predefinedMessages.map((msg, index) => (
              <ListItem
                key={index}
                button
                onClick={() => usePredefinedMessage(msg)}
                sx={{ 
                  border: 1, 
                  borderColor: 'divider', 
                  borderRadius: 1, 
                  mb: 1 
                }}
              >
                <ListItemText
                  primary={msg.label}
                  secondary={
                    <Box>
                      <Typography variant="caption" display="block">
                        Forum: {msg.forum}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        "{msg.message.slice(0, 50)}..."
                      </Typography>
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>

          <Alert severity="info" sx={{ mt: 2 }}>
            <Typography variant="caption">
              Tip: Use Ctrl+Enter to send messages quickly
            </Typography>
          </Alert>
        </Paper>

        {/* Chat History */}
        <Paper sx={{ flex: 1, p: 2, display: 'flex', flexDirection: 'column' }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">
              Chat History ({chatHistory.length})
            </Typography>
            <IconButton onClick={clearHistory} disabled={chatHistory.length === 0}>
              <ClearIcon />
            </IconButton>
          </Box>

          <Box sx={{ flex: 1, overflow: 'auto' }}>
            {chatHistory.length === 0 ? (
              <Box sx={{ 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center', 
                height: '100%',
                color: 'text.secondary'
              }}>
                <Typography>No messages sent yet. Try one of the predefined messages!</Typography>
              </Box>
            ) : (
              chatHistory.map((chat) => (
                <Card key={chat.id} sx={{ mb: 2, border: 1, borderColor: 'divider' }}>
                  <CardContent>
                    {/* Request */}
                    <Box sx={{ mb: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'between', alignItems: 'center', mb: 1 }}>
                        <Typography variant="subtitle2" color="primary.main">
                          📤 Request
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {chat.timestamp.toLocaleTimeString()}
                        </Typography>
                      </Box>
                      
                      <Box sx={{ display: 'flex', gap: 1, mb: 1, flexWrap: 'wrap' }}>
                        <Chip label={`From: ${chat.request.sender}`} size="small" variant="outlined" />
                        <Chip label={`To: ${chat.request.receiver}`} size="small" variant="outlined" />
                        <Chip label={`Forum: ${chat.request.forum}`} size="small" variant="outlined" />
                      </Box>
                      
                      <Paper sx={{ p: 2, bgcolor: 'grey.50', border: 1, borderColor: 'grey.200' }}>
                        <Typography variant="body2">
                          "{chat.request.message}"
                        </Typography>
                      </Paper>
                    </Box>

                    {/* Response */}
                    <Box>
                      <Typography variant="subtitle2" color="secondary.main" gutterBottom>
                        📥 Response
                      </Typography>
                      
                      {chat.loading ? (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 2 }}>
                          <CircularProgress size={20} />
                          <Typography variant="body2" color="text.secondary">
                            Processing message...
                          </Typography>
                        </Box>
                      ) : chat.error ? (
                        <Alert severity="error" sx={{ mt: 1 }}>
                          {chat.error}
                        </Alert>
                      ) : chat.response ? (
                        <Box>
                          <Box sx={{ display: 'flex', gap: 1, mb: 1, flexWrap: 'wrap' }}>
                            <Chip 
                              label={`Agent: ${chat.response.agent_used}`} 
                              size="small" 
                              color="success" 
                            />
                            <Chip 
                              label={`Workflow: ${chat.response.workflow_id.split('_').pop()}`} 
                              size="small" 
                              color="primary" 
                            />
                            <IconButton 
                              size="small" 
                              onClick={() => copyToClipboard(chat.response!.workflow_id)}
                              title="Copy Workflow ID"
                            >
                              <CopyIcon fontSize="small" />
                            </IconButton>
                          </Box>
                          
                          <Paper sx={{ p: 2, bgcolor: 'success.light', color: 'success.contrastText' }}>
                            <Typography variant="body2">
                              {chat.response.response}
                            </Typography>
                          </Paper>
                        </Box>
                      ) : null}
                    </Box>
                  </CardContent>
                </Card>
              ))
            )}
          </Box>
        </Paper>
      </Box>
    </Box>
  )
}

export default ChatTester