import { useState, useRef, useCallback, useEffect } from "react";

const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8000/ws/research";

const AGENTS = [
  {
    id: "Planner",
    label: "Planner",
    icon: "⬡",
    desc: "Breaks down your question into 3 focused sub-tasks",
    color: "#00d4ff",
  },
  {
    id: "Researcher",
    label: "Researcher",
    icon: "⬡",
    desc: "Searches the web for each sub-task",
    color: "#ff6b35",
  },
  {
    id: "Synthesizer",
    label: "Synthesizer",
    icon: "⬡",
    desc: "Merges all findings into a final answer",
    color: "#a855f7",
  },
];

function AgentNode({ agent, status, message, subtaskId }) {
  const isRunning = status === "running";
  const isDone = status === "done";

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: "10px",
        position: "relative",
      }}
    >
      {/* Hex node */}
      <div
        style={{
          width: 96,
          height: 96,
          position: "relative",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {/* Pulse ring when running */}
        {isRunning && (
          <div
            style={{
              position: "absolute",
              inset: -8,
              borderRadius: "50%",
              border: `2px solid ${agent.color}`,
              animation: "pulse-ring 1.2s ease-out infinite",
            }}
          />
        )}
        <svg width="96" height="96" viewBox="0 0 96 96">
          <polygon
            points="48,4 88,26 88,70 48,92 8,70 8,26"
            fill={isDone ? agent.color + "22" : isRunning ? agent.color + "15" : "#0a0a0f"}
            stroke={isDone || isRunning ? agent.color : "#2a2a3a"}
            strokeWidth={isDone ? 2 : isRunning ? 2 : 1.5}
            style={{ transition: "all 0.4s ease" }}
          />
        </svg>
        <span
          style={{
            position: "absolute",
            fontSize: 28,
            filter: isDone || isRunning ? `drop-shadow(0 0 8px ${agent.color})` : "none",
            transition: "filter 0.4s ease",
          }}
        >
          {isDone ? "✓" : agent.icon}
        </span>
      </div>

      {/* Label */}
      <div style={{ textAlign: "center" }}>
        <div
          style={{
            fontFamily: "'Space Mono', monospace",
            fontSize: 13,
            fontWeight: 700,
            color: isDone || isRunning ? agent.color : "#555",
            letterSpacing: "0.08em",
            transition: "color 0.3s",
          }}
        >
          {agent.label}
        </div>
        {message && (
          <div
            style={{
              fontFamily: "'Space Mono', monospace",
              fontSize: 10,
              color: "#666",
              marginTop: 4,
              maxWidth: 120,
              lineHeight: 1.4,
            }}
          >
            {message}
          </div>
        )}
        {subtaskId && (
          <div
            style={{
              display: "inline-block",
              background: agent.color + "22",
              border: `1px solid ${agent.color}44`,
              borderRadius: 4,
              padding: "2px 6px",
              fontSize: 9,
              color: agent.color,
              marginTop: 4,
              fontFamily: "'Space Mono', monospace",
            }}
          >
            task {subtaskId}/3
          </div>
        )}
      </div>
    </div>
  );
}

function Connector({ active, color }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 4,
        paddingBottom: 30,
      }}
    >
      {[0, 1, 2, 3, 4].map((i) => (
        <div
          key={i}
          style={{
            width: 6,
            height: 6,
            borderRadius: "50%",
            background: active ? color : "#2a2a3a",
            animation: active ? `dot-flow 1s ${i * 0.15}s ease-in-out infinite` : "none",
            transition: "background 0.4s",
          }}
        />
      ))}
    </div>
  );
}

function FindingsPanel({ events }) {
  const researchEvents = events.filter(
    (e) => e.agent === "Researcher" && e.status === "done" && e.data
  );
  const synthEvent = events.find(
    (e) => e.agent === "Synthesizer" && e.status === "done" && e.data
  );
  const planEvent = events.find(
    (e) => e.agent === "Planner" && e.status === "done" && e.data
  );

  if (!planEvent && !researchEvents.length && !synthEvent) return null;

  return (
    <div style={{ marginTop: 40, display: "flex", flexDirection: "column", gap: 16 }}>
      {/* Subtasks */}
      {planEvent?.data?.subtasks && (
        <div
          style={{
            background: "#0d0d18",
            border: "1px solid #1a1a2e",
            borderRadius: 12,
            padding: "16px 20px",
          }}
        >
          <div
            style={{
              fontFamily: "'Space Mono', monospace",
              fontSize: 11,
              color: "#00d4ff",
              letterSpacing: "0.1em",
              marginBottom: 12,
            }}
          >
            PLAN — 3 SUB-TASKS
          </div>
          {planEvent.data.subtasks.map((t) => (
            <div
              key={t.id}
              style={{
                display: "flex",
                gap: 10,
                marginBottom: 8,
                alignItems: "flex-start",
              }}
            >
              <span
                style={{
                  fontFamily: "'Space Mono', monospace",
                  fontSize: 10,
                  color: "#00d4ff88",
                  minWidth: 16,
                  paddingTop: 2,
                }}
              >
                {t.id}.
              </span>
              <span
                style={{
                  fontFamily: "'Space Mono', monospace",
                  fontSize: 11,
                  color: "#888",
                  lineHeight: 1.6,
                }}
              >
                {t.query}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Research findings */}
      {researchEvents.map((e, i) => (
        <div
          key={i}
          style={{
            background: "#0d0d18",
            border: "1px solid #1a1a2e",
            borderLeft: "3px solid #ff6b35",
            borderRadius: 12,
            padding: "16px 20px",
            animation: "fade-up 0.4s ease",
          }}
        >
          <div
            style={{
              fontFamily: "'Space Mono', monospace",
              fontSize: 11,
              color: "#ff6b35",
              letterSpacing: "0.1em",
              marginBottom: 8,
            }}
          >
            RESEARCH {i + 1} — {e.data.query}
          </div>
          <div
            style={{
              fontFamily: "'Space Mono', monospace",
              fontSize: 11,
              color: "#777",
              lineHeight: 1.7,
            }}
          >
            {e.data.summary}
          </div>
        </div>
      ))}

      {/* Final answer */}
      {synthEvent?.data && (
        <div
          style={{
            background: "#0d0d18",
            border: "1px solid #a855f744",
            borderRadius: 12,
            padding: "20px 24px",
            animation: "fade-up 0.5s ease",
          }}
        >
          <div
            style={{
              fontFamily: "'Space Mono', monospace",
              fontSize: 11,
              color: "#a855f7",
              letterSpacing: "0.1em",
              marginBottom: 16,
            }}
          >
            ✦ FINAL ANSWER
          </div>
          <div
            style={{
              fontFamily: "Georgia, serif",
              fontSize: 14,
              color: "#ccc",
              lineHeight: 1.8,
              whiteSpace: "pre-wrap",
            }}
          >
            {synthEvent.data.answer}
          </div>
          {synthEvent.data.key_takeaways?.length > 0 && (
            <div style={{ marginTop: 20 }}>
              <div
                style={{
                  fontFamily: "'Space Mono', monospace",
                  fontSize: 10,
                  color: "#a855f7",
                  letterSpacing: "0.1em",
                  marginBottom: 10,
                }}
              >
                KEY TAKEAWAYS
              </div>
              {synthEvent.data.key_takeaways.map((t, i) => (
                <div
                  key={i}
                  style={{
                    display: "flex",
                    gap: 10,
                    marginBottom: 6,
                    alignItems: "flex-start",
                  }}
                >
                  <span style={{ color: "#a855f7", fontSize: 12 }}>→</span>
                  <span
                    style={{
                      fontFamily: "'Space Mono', monospace",
                      fontSize: 11,
                      color: "#888",
                      lineHeight: 1.6,
                    }}
                  >
                    {t}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [question, setQuestion] = useState("");
  const [events, setEvents] = useState([]);
  const [agentStates, setAgentStates] = useState({});
  const [isRunning, setIsRunning] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const wsRef = useRef(null);

  useEffect(() => {
    return () => {
      if (wsRef.current && wsRef.current.readyState <= WebSocket.OPEN) {
        wsRef.current.close();
      }
    };
  }, []);

  const handleRun = useCallback(() => {
    if (!question.trim() || isRunning) return;

    setEvents([]);
    setAgentStates({});
    setIsComplete(false);
    setIsRunning(true);
    setErrorMessage("");

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      ws.send(JSON.stringify({ question: question.trim() }));
    };

    ws.onmessage = (msg) => {
      const event = JSON.parse(msg.data);
      setEvents((prev) => [...prev, event]);

      if (event.agent !== "system") {
        setAgentStates((prev) => ({
          ...prev,
          [event.agent]: {
            status: event.status,
            message: event.message,
            subtaskId: event.subtask_id,
          },
        }));
      }

      if (event.agent === "system" && event.status === "error") {
        setErrorMessage(event.message || "The backend reported an error.");
        setIsRunning(false);
        setIsComplete(false);
        return;
      }

      if (event.status === "complete") {
        setIsRunning(false);
        setIsComplete(true);
      }
    };

    ws.onerror = () => {
      setErrorMessage(
        "Could not connect to the backend WebSocket. Make sure the FastAPI server is running on ws://localhost:8000/ws/research."
      );
      setIsRunning(false);
      setIsComplete(false);
    };

    ws.onclose = (event) => {
      if (!isComplete && !errorMessage && event.code !== 1000) {
        setErrorMessage("The connection closed before the research run finished.");
      }
      setIsRunning(false);
    };
  }, [question, isRunning, isComplete, errorMessage]);

  // Check which connectors should be active
  const plannerDone = agentStates["Planner"]?.status === "done";
  const researcherActive =
    agentStates["Researcher"]?.status === "running" ||
    agentStates["Researcher"]?.status === "done";
  const researcherDone = agentStates["Researcher"]?.status === "done" &&
    !agentStates["Synthesizer"];
  const synthActive =
    agentStates["Synthesizer"]?.status === "running" ||
    agentStates["Synthesizer"]?.status === "done";

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap');

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
          background: #05050d;
          color: #ccc;
          min-height: 100vh;
          font-family: 'Space Mono', monospace;
        }

        @keyframes pulse-ring {
          0% { transform: scale(1); opacity: 0.8; }
          100% { transform: scale(1.5); opacity: 0; }
        }

        @keyframes dot-flow {
          0%, 100% { opacity: 0.2; transform: scale(0.8); }
          50% { opacity: 1; transform: scale(1.2); }
        }

        @keyframes fade-up {
          from { opacity: 0; transform: translateY(12px); }
          to { opacity: 1; transform: translateY(0); }
        }

        @keyframes scan {
          0% { background-position: 0 0; }
          100% { background-position: 0 40px; }
        }

        textarea:focus { outline: none; }
        textarea::placeholder { color: #333; }
      `}</style>

      <div
        style={{
          minHeight: "100vh",
          background: "radial-gradient(ellipse at 20% 20%, #0a0a1f 0%, #05050d 60%)",
          padding: "40px 24px 80px",
          maxWidth: 780,
          margin: "0 auto",
        }}
      >
        {/* Header */}
        <div style={{ marginBottom: 48 }}>
          <div
            style={{
              fontFamily: "'Space Mono', monospace",
              fontSize: 10,
              color: "#333",
              letterSpacing: "0.2em",
              marginBottom: 12,
            }}
          >
            MICROSOFT BUILD AI · AGENT SWARMS · THEME 05
          </div>
          <h1
            style={{
              fontFamily: "'Space Mono', monospace",
              fontSize: 28,
              fontWeight: 700,
              color: "#eee",
              lineHeight: 1.2,
              marginBottom: 8,
            }}
          >
            Research<span style={{ color: "#00d4ff" }}>Swarm</span>
          </h1>
          <p
            style={{
              fontFamily: "'Space Mono', monospace",
              fontSize: 11,
              color: "#444",
              lineHeight: 1.6,
            }}
          >
            3-agent orchestration · Planner → Researcher × 3 → Synthesizer
          </p>
        </div>

        {/* Input */}
        <div
          style={{
            background: "#0a0a15",
            border: "1px solid #1e1e30",
            borderRadius: 12,
            padding: 20,
            marginBottom: 40,
          }}
        >
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a research question..."
            rows={3}
            style={{
              width: "100%",
              background: "transparent",
              border: "none",
              fontFamily: "'Space Mono', monospace",
              fontSize: 13,
              color: "#ccc",
              resize: "none",
              lineHeight: 1.7,
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter" && e.metaKey) handleRun();
            }}
          />
          <div
            style={{
              display: "flex",
              justifyContent: "flex-end",
              marginTop: 12,
            }}
          >
            <button
              onClick={handleRun}
              disabled={isRunning || !question.trim()}
              style={{
                background: isRunning ? "#111" : "#00d4ff",
                color: isRunning ? "#444" : "#000",
                border: "none",
                borderRadius: 8,
                padding: "10px 24px",
                fontFamily: "'Space Mono', monospace",
                fontSize: 11,
                fontWeight: 700,
                letterSpacing: "0.08em",
                cursor: isRunning ? "not-allowed" : "pointer",
                transition: "all 0.2s",
              }}
            >
              {isRunning ? "RUNNING..." : "LAUNCH SWARM ⬡"}
            </button>
          </div>
        </div>

        {/* Orchestration graph */}
        {Object.keys(agentStates).length > 0 && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 16,
              padding: "32px 0",
              borderTop: "1px solid #111",
              borderBottom: "1px solid #111",
              marginBottom: 0,
              overflowX: "auto",
            }}
          >
            <AgentNode
              agent={AGENTS[0]}
              status={agentStates["Planner"]?.status}
              message={agentStates["Planner"]?.message}
            />
            <Connector active={plannerDone || researcherActive} color="#00d4ff" />
            <AgentNode
              agent={AGENTS[1]}
              status={agentStates["Researcher"]?.status}
              message={agentStates["Researcher"]?.message}
              subtaskId={agentStates["Researcher"]?.subtaskId}
            />
            <Connector active={synthActive} color="#ff6b35" />
            <AgentNode
              agent={AGENTS[2]}
              status={agentStates["Synthesizer"]?.status}
              message={agentStates["Synthesizer"]?.message}
            />
          </div>
        )}

        {errorMessage && (
          <div
            style={{
              marginTop: 24,
              background: "#1a0d12",
              border: "1px solid #5c1f2f",
              borderRadius: 12,
              padding: "16px 18px",
            }}
          >
            <div
              style={{
                fontFamily: "'Space Mono', monospace",
                fontSize: 11,
                color: "#ff6b8b",
                letterSpacing: "0.1em",
                marginBottom: 8,
              }}
            >
              RUN ERROR
            </div>
            <div
              style={{
                fontFamily: "'Space Mono', monospace",
                fontSize: 11,
                color: "#d2a8b3",
                lineHeight: 1.7,
                whiteSpace: "pre-wrap",
              }}
            >
              {errorMessage}
            </div>
          </div>
        )}

        {!errorMessage && isComplete && events.length > 0 && (
          <div
            style={{
              marginTop: 24,
              fontFamily: "'Space Mono', monospace",
              fontSize: 10,
              color: "#3b8",
              letterSpacing: "0.08em",
            }}
          >
            RUN COMPLETE
          </div>
        )}

        {/* Findings */}
        <FindingsPanel events={events} />

        {/* Idle state - agent descriptions */}
        {Object.keys(agentStates).length === 0 && (
          <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
            {AGENTS.map((agent) => (
              <div
                key={agent.id}
                style={{
                  flex: 1,
                  minWidth: 160,
                  background: "#0a0a15",
                  border: "1px solid #111",
                  borderRadius: 10,
                  padding: "16px",
                }}
              >
                <div
                  style={{
                    fontFamily: "'Space Mono', monospace",
                    fontSize: 11,
                    color: agent.color,
                    fontWeight: 700,
                    marginBottom: 8,
                    letterSpacing: "0.06em",
                  }}
                >
                  {agent.label}
                </div>
                <div
                  style={{
                    fontFamily: "'Space Mono', monospace",
                    fontSize: 10,
                    color: "#444",
                    lineHeight: 1.6,
                  }}
                >
                  {agent.desc}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
