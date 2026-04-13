import { useState, useCallback, useRef } from "react";

const API_URL = "http://localhost:8000";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
}

/** Every event that happens during agent execution */
export interface ActivityEvent {
  id: string;
  timestamp: number;
  type:
    | "thinking"      // Agent is generating tokens
    | "tool_start"    // Tool call initiated
    | "tool_end"      // Tool call completed
    | "sensor_start"  // Sensor started
    | "sensor_pass"   // Sensor passed
    | "sensor_fail"   // Sensor found issues
    | "correction"    // Agent is fixing an issue (edit_file after sensor_fail)
    | "file_changed"  // A file was created or modified
    | "error"         // An error occurred
    | "done";         // Turn completed
  tool?: string;
  category?: "tool" | "sensor" | "integration";
  input?: string;
  output?: string;
  status?: "running" | "done" | "pass" | "fail";
}

export interface ToolEvent {
  tool: string;
  category?: "tool" | "sensor" | "integration";
  input?: string;
  output?: string;
  status: "running" | "done";
  sensorStatus?: "pass" | "fail";
}

interface UseChatReturn {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  activeTools: ToolEvent[];
  activityLog: ActivityEvent[];
  projectRefreshTrigger: number;
  templateId: string;
  setTemplateId: (id: string) => void;
  personaId: string;
  stackId: string;
  skillIds: string[];
  projectTypeId: string;
  setPersonaAndSkills: (personaId: string, skillIds: string[], projectTypeId?: string) => void;
  setPersonaStack: (personaId: string, stackId: string) => void;
  submit: (text: string) => void;
}

const SENSOR_NAMES = new Set([
  "run_linter", "validate_structure", "check_directives",
  "review_code", "harness_status", "read_harness_rules",
  "update_harness_rules", "read_agents_md", "update_agents_md",
  "scan_drift", "validate_before_write", "create_sdd", "get_sdd",
]);

const FILE_WRITE_TOOLS = new Set(["write_file", "edit_file", "generate_agent_code"]);

let eventCounter = 0;
function nextId() {
  return `evt-${++eventCounter}-${Date.now()}`;
}

export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTools, setActiveTools] = useState<ToolEvent[]>([]);
  const [activityLog, setActivityLog] = useState<ActivityEvent[]>([]);
  const [projectRefreshTrigger, setProjectRefreshTrigger] = useState(0);
  const [personaId, setPersonaIdState] = useState("deepagent_generator");
  const [stackId, setStackIdState] = useState("agnostic");
  const [skillIds, setSkillIdsState] = useState<string[]>([]);
  const [projectTypeId, setProjectTypeIdState] = useState<string>("custom");
  const threadIdRef = useRef<string | null>(null);
  const streamingContentRef = useRef("");
  const lastSensorFailRef = useRef<string | null>(null);
  const thinkingEventIdRef = useRef<string | null>(null);
  const pendingToolEventsRef = useRef<Map<string, string>>(new Map());

  function pushActivity(event: Omit<ActivityEvent, "id" | "timestamp">) {
    const full: ActivityEvent = { ...event, id: nextId(), timestamp: Date.now() };
    setActivityLog((prev) => [...prev, full]);
    return full.id;
  }

  const setPersonaStack = useCallback((newPersonaId: string, newStackId: string) => {
    setPersonaIdState(newPersonaId);
    setStackIdState(newStackId);
    setMessages([]);
    setActivityLog([]);
    setActiveTools([]);
    threadIdRef.current = null;
    setError(null);
    lastSensorFailRef.current = null;
  }, []);

  const setPersonaAndSkills = useCallback(
    (newPersonaId: string, newSkillIds: string[], newProjectTypeId?: string) => {
      setPersonaIdState(newPersonaId);
      setSkillIdsState(newSkillIds);
      if (newProjectTypeId !== undefined) {
        setProjectTypeIdState(newProjectTypeId);
      }
      setMessages([]);
      setActivityLog([]);
      setActiveTools([]);
      threadIdRef.current = null;
      setError(null);
      lastSensorFailRef.current = null;
    },
    []
  );

  const setTemplateId = useCallback((id: string) => {
    // Legacy — keeps stack unchanged
    setPersonaIdState(id);
    setMessages([]);
    setActivityLog([]);
    setActiveTools([]);
    threadIdRef.current = null;
    setError(null);
    lastSensorFailRef.current = null;
  }, []);

  const submit = useCallback(
    (text: string) => {
      if (!text.trim() || isLoading) return;

      const userMsg: ChatMessage = {
        id: `user-${Date.now()}`,
        role: "user",
        content: text,
      };
      const assistantId = `assistant-${Date.now()}`;
      setMessages((prev) => [
        ...prev,
        userMsg,
        { id: assistantId, role: "assistant", content: "" },
      ]);
      setIsLoading(true);
      setError(null);
      setActiveTools([]);
      streamingContentRef.current = "";
      thinkingEventIdRef.current = null;
      pendingToolEventsRef.current.clear();

      fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          thread_id: threadIdRef.current,
          persona_id: personaId,
          skill_ids: skillIds,
          project_type_id: projectTypeId,
        }),
      })
        .then(async (response) => {
          if (!response.ok) throw new Error(`Server error: ${response.status}`);
          const reader = response.body?.getReader();
          if (!reader) throw new Error("No response body");

          const decoder = new TextDecoder();
          let buffer = "";

          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop() || "";

            let currentEvent = "";
            for (const line of lines) {
              if (line.startsWith("event:")) {
                currentEvent = line.slice(6).trim();
              } else if (line.startsWith("data:") && currentEvent) {
                try {
                  const data = JSON.parse(line.slice(5).trim());
                  handleSSEEvent(currentEvent, data, assistantId);
                } catch { /* ignore */ }
                currentEvent = "";
              }
            }
          }
        })
        .catch((err) => {
          setError(err.message);
          pushActivity({ type: "error", output: err.message });
        })
        .finally(() => {
          setIsLoading(false);
          setActiveTools([]);
          pushActivity({ type: "done" });
        });
    },
    [isLoading, personaId, skillIds, projectTypeId]
  );

  function handleSSEEvent(event: string, data: any, assistantId: string) {
    switch (event) {
      case "metadata":
        threadIdRef.current = data.thread_id;
        break;

      case "token": {
        // First token = start "thinking" activity
        if (!thinkingEventIdRef.current) {
          thinkingEventIdRef.current = pushActivity({
            type: "thinking",
            status: "running",
          });
        }
        streamingContentRef.current += data.content;
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantId
              ? { ...msg, content: streamingContentRef.current }
              : msg
          )
        );
        break;
      }

      case "tool_start": {
        // End thinking phase
        if (thinkingEventIdRef.current) {
          setActivityLog((prev) =>
            prev.map((e) =>
              e.id === thinkingEventIdRef.current
                ? { ...e, status: "done" }
                : e
            )
          );
          thinkingEventIdRef.current = null;
        }

        const isSensor = data.category === "sensor" || SENSOR_NAMES.has(data.tool);
        const isCorrection =
          data.tool === "edit_file" && lastSensorFailRef.current !== null;

        // Create event and track its ID by tool name
        const evtType = isCorrection
          ? "correction"
          : isSensor
          ? "sensor_start"
          : "tool_start";

        const evtId = pushActivity({
          type: evtType,
          tool: data.tool,
          category: data.category || (isSensor ? "sensor" : "tool"),
          input: data.input,
          status: "running",
        });

        // Track which event ID belongs to this tool call
        pendingToolEventsRef.current.set(data.tool, evtId);

        setActiveTools((prev) => [
          ...prev,
          {
            tool: data.tool,
            category: data.category || (isSensor ? "sensor" : "tool"),
            input: data.input,
            status: "running",
          },
        ]);
        break;
      }

      case "tool_end": {
        const isSensor = data.category === "sensor" || SENSOR_NAMES.has(data.tool);
        const sensorStatus = data.sensor_status as "pass" | "fail" | undefined;
        const isCorrection =
          data.tool === "edit_file" && lastSensorFailRef.current !== null;

        // Find the pending event ID for this tool
        const pendingId = pendingToolEventsRef.current.get(data.tool);
        pendingToolEventsRef.current.delete(data.tool);

        // Determine the final event type and status
        let finalType: ActivityEvent["type"];
        let finalStatus: ActivityEvent["status"];

        if (isCorrection) {
          finalType = "correction";
          finalStatus = "done";
        } else if (isSensor && sensorStatus === "fail") {
          finalType = "sensor_fail";
          finalStatus = "fail";
          lastSensorFailRef.current = data.tool;
        } else if (isSensor && sensorStatus === "pass") {
          const wasCorrected = lastSensorFailRef.current === data.tool;
          finalType = "sensor_pass";
          finalStatus = wasCorrected ? "done" : "pass";
          if (wasCorrected) lastSensorFailRef.current = null;
        } else {
          finalType = "tool_end";
          finalStatus = "done";
        }

        // UPDATE the existing event instead of creating a new one
        if (pendingId) {
          setActivityLog((prev) =>
            prev.map((e) =>
              e.id === pendingId
                ? { ...e, type: finalType, output: data.output, status: finalStatus }
                : e
            )
          );
        } else {
          // Fallback: create new event if no pending found
          pushActivity({
            type: finalType,
            tool: data.tool,
            category: data.category,
            output: data.output,
            status: finalStatus,
          });
        }

        // File changed notification
        if (FILE_WRITE_TOOLS.has(data.tool)) {
          pushActivity({ type: "file_changed", tool: data.tool });
          setProjectRefreshTrigger((prev) => prev + 1);
        }

        setActiveTools((prev) =>
          prev.map((t) =>
            t.tool === data.tool && t.status === "running"
              ? { ...t, output: data.output, status: "done", sensorStatus }
              : t
          )
        );
        break;
      }

      case "message_complete":
        if (thinkingEventIdRef.current) {
          setActivityLog((prev) =>
            prev.map((e) =>
              e.id === thinkingEventIdRef.current
                ? { ...e, status: "done" }
                : e
            )
          );
          thinkingEventIdRef.current = null;
        }
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantId ? { ...msg, content: data.content } : msg
          )
        );
        break;

      case "file_changed":
        setProjectRefreshTrigger((prev) => prev + 1);
        break;

      case "error":
        pushActivity({ type: "error", output: data.message });
        setError(data.message);
        break;
    }
  }

  return {
    messages,
    isLoading,
    error,
    activeTools,
    activityLog,
    projectRefreshTrigger,
    templateId: personaId,
    setTemplateId,
    personaId,
    stackId,
    skillIds,
    projectTypeId,
    setPersonaAndSkills,
    setPersonaStack,
    submit,
  };
}
