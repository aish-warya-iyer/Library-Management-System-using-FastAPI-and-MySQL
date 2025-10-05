import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  fetchConversations,
  fetchMessages,
  sendMessage,
  setCurrentConversation,
} from "./chatSlice";

export default function Chat() {
  const dispatch = useDispatch();
  const { conversations, messages, currentId, error } = useSelector((s) => s.chat);
  const [text, setText] = useState("");

  useEffect(() => {
    dispatch(fetchConversations());
  }, [dispatch]);

  useEffect(() => {
    if (currentId) dispatch(fetchMessages(currentId));
  }, [currentId, dispatch]);

  const submit = async (e) => {
    e.preventDefault();
    if (!text.trim()) return;
    await dispatch(sendMessage({ conversation_id: currentId, message: text }));
    setText("");
  };

  return (
    <div className="card" style={{ display: "grid", gap: 12 }}>
      <h2 style={{ marginTop: 0 }}>💬 LLM Chat</h2>

      {/* select conversation */}
      <div className="row" style={{ flexWrap: "wrap", gap: 8 }}>
        {conversations.map((c) => (
          <button
            key={c.id}
            onClick={() => dispatch(setCurrentConversation(c.id))}
            className={c.id === currentId ? "badge" : "secondary"}
          >
            {c.title || `Chat ${c.id}`}
          </button>
        ))}
        <button onClick={() => dispatch(setCurrentConversation(null))}>
          ➕ New
        </button>
      </div>

      {/* messages */}
      <div
        style={{
          background: "#0f172a",
          borderRadius: 10,
          padding: 12,
          maxHeight: 300,
          overflowY: "auto",
        }}
      >
        {messages.map((m, i) => (
          <p key={i}>
            <strong style={{ color: m.role === "assistant" ? "#22d3ee" : "#f9fafb" }}>
              {m.role === "assistant" ? "AI:" : "You:"}
            </strong>{" "}
            {m.content}
          </p>
        ))}
        {messages.length === 0 && <p style={{ opacity: 0.6 }}>No messages yet.</p>}
      </div>

      {error && <p className="error">Error: {error}</p>}

      <form onSubmit={submit} className="row">
        <input
          placeholder="Type your message..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          style={{ flex: 1 }}
        />
        <button type="submit">Send</button>
      </form>
    </div>
  );
}
