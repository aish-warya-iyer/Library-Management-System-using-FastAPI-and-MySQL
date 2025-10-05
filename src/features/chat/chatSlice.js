import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import api from "../../lib/api";

// send a message → backend → LLM → reply
export const sendMessage = createAsyncThunk(
  "chat/sendMessage",
  async ({ conversation_id, message }, { rejectWithValue }) => {
    try {
      const res = await api.post("/ai/chat", { conversation_id, message });
      return res.data; // { conversation_id, reply }
    } catch (err) {
      return rejectWithValue(err.response?.data || { detail: "Chat failed" });
    }
  }
);

export const fetchConversations = createAsyncThunk(
  "chat/fetchConversations",
  async (_, { rejectWithValue }) => {
    try {
      const res = await api.get("/ai/conversations");
      return res.data;
    } catch (err) {
      return rejectWithValue(err.response?.data || { detail: "Fetch failed" });
    }
  }
);

export const fetchMessages = createAsyncThunk(
  "chat/fetchMessages",
  async (conversation_id, { rejectWithValue }) => {
    try {
      const res = await api.get(`/ai/conversations/${conversation_id}/messages`);
      return res.data;
    } catch (err) {
      return rejectWithValue(err.response?.data || { detail: "Fetch failed" });
    }
  }
);

const chatSlice = createSlice({
  name: "chat",
  initialState: {
    conversations: [],
    messages: [],
    currentId: null,
    status: "idle",
    error: null,
  },
  reducers: {
    setCurrentConversation: (s, a) => {
      s.currentId = a.payload;
      s.messages = [];
    },
  },
  extraReducers: (b) => {
    b.addCase(fetchConversations.fulfilled, (s, a) => {
      s.conversations = a.payload;
    });
    b.addCase(fetchMessages.fulfilled, (s, a) => {
      s.messages = a.payload;
    });
    b.addCase(sendMessage.fulfilled, (s, a) => {
      const { conversation_id, reply } = a.payload;
      // append user + assistant messages for live UI
      s.messages.push({ role: "user", content: a.meta.arg.message });
      s.messages.push({ role: "assistant", content: reply });
      s.currentId = conversation_id;
    });
    b.addMatcher(
      (a) => a.type.endsWith("rejected"),
      (s, a) => (s.error = a.payload?.detail || "Error")
    );
  },
});

export const { setCurrentConversation } = chatSlice.actions;
export default chatSlice.reducer;
