import { useState, useEffect, useCallback, useRef } from "react";
import {
  RefreshCw,
  ClipboardList,
  Plus,
  X,
  Trash2,
  GitCommit,
  AlertTriangle,
  Loader2,
  MoreVertical,
} from "lucide-react";

const API = "http://localhost:8000";
const TASK_API = "http://localhost:8100";

interface WorkItem {
  id: string;
  project: string;
  title: string;
  description: string;
  item_type: string;
  status: string;
  priority: string;
  assigned_to: string;
  tags: string;
  commits: { commit_hash: string; message: string }[];
}

interface BoardColumn {
  status: string;
  items: WorkItem[];
  count: number;
}

interface BoardData {
  project: string;
  columns: BoardColumn[];
  total: number;
}

interface Sprint {
  id: string;
  name: string;
  status: string;
  goal: string;
  item_count: number;
}

interface Project {
  name: string;
}

const COLUMNS = [
  { status: "todo", label: "To Do", color: "#94a3b8", border: "border-slate-500/30" },
  { status: "in_progress", label: "In Progress", color: "#6366f1", border: "border-indigo-500/30" },
  { status: "review", label: "Review", color: "#f59e0b", border: "border-amber-500/30" },
  { status: "done", label: "Done", color: "#10b981", border: "border-emerald-500/30" },
];

const PRIORITIES = [
  { value: "P0", label: "P0", color: "bg-red-500" },
  { value: "P1", label: "P1", color: "bg-orange-500" },
  { value: "P2", label: "P2", color: "bg-blue-500" },
  { value: "P3", label: "P3", color: "bg-slate-500" },
];

const TYPES = ["task", "bug", "story", "epic"];

// ═══════════════════════════════════════════
// Card
// ═══════════════════════════════════════════

function Card({
  item,
  onUpdate,
  onDelete,
  onDragStart,
}: {
  item: WorkItem;
  onUpdate: (id: string, data: Partial<WorkItem>) => void;
  onDelete: (id: string) => void;
  onDragStart: (id: string) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(item.title);
  const [editDesc, setEditDesc] = useState(item.description);
  const [showMenu, setShowMenu] = useState(false);

  const priorityColor =
    PRIORITIES.find((p) => p.value === item.priority)?.color || "bg-slate-500";

  const handleSave = () => {
    if (editTitle.trim() && (editTitle !== item.title || editDesc !== item.description)) {
      onUpdate(item.id, { title: editTitle.trim(), description: editDesc });
    }
    setEditing(false);
  };

  return (
    <div
      draggable
      onDragStart={(e) => {
        e.dataTransfer.effectAllowed = "move";
        onDragStart(item.id);
      }}
      className="group relative cursor-grab rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-2.5 shadow-sm transition-all hover:border-indigo-500/40 hover:shadow-md active:cursor-grabbing"
    >
      {/* Priority bar */}
      <div className={`absolute left-0 top-0 h-full w-1 rounded-l-lg ${priorityColor}`} />

      {editing ? (
        <div className="space-y-2 pl-2">
          <input
            value={editTitle}
            onChange={(e) => setEditTitle(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSave();
              if (e.key === "Escape") setEditing(false);
            }}
            autoFocus
            className="w-full rounded border border-indigo-500/40 bg-[var(--color-bg)] px-2 py-1 text-xs text-white outline-none"
          />
          <textarea
            value={editDesc}
            onChange={(e) => setEditDesc(e.target.value)}
            placeholder="Description..."
            rows={2}
            className="w-full resize-none rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-2 py-1 text-[10px] text-[var(--color-text-muted)] outline-none focus:border-indigo-500/40"
          />
          <div className="flex gap-1">
            <button
              onClick={handleSave}
              className="rounded bg-indigo-500 px-2 py-1 text-[10px] font-medium text-white hover:bg-indigo-600"
            >
              Save
            </button>
            <button
              onClick={() => setEditing(false)}
              className="rounded px-2 py-1 text-[10px] text-[var(--color-text-muted)] hover:text-white"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <div className="pl-2">
          <div className="flex items-start gap-1.5">
            <span
              className={`mt-0.5 shrink-0 rounded px-1.5 py-0.5 text-[9px] font-bold leading-none text-white ${priorityColor}`}
            >
              {item.priority}
            </span>
            <p
              className="flex-1 text-xs font-medium leading-snug text-white"
              onClick={() => setEditing(true)}
            >
              {item.title}
            </p>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setShowMenu(!showMenu);
              }}
              className="opacity-0 transition-opacity group-hover:opacity-100"
            >
              <MoreVertical className="h-3 w-3 text-[var(--color-text-muted)]" />
            </button>
          </div>

          {item.description && (
            <p className="mt-1 line-clamp-2 text-[10px] leading-relaxed text-[var(--color-text-muted)]">
              {item.description}
            </p>
          )}

          <div className="mt-1.5 flex items-center gap-1.5">
            <span className="rounded-full bg-[var(--color-surface-2)] px-1.5 py-0.5 text-[9px] text-[var(--color-text-muted)]">
              {item.item_type}
            </span>
            {item.assigned_to && (
              <span className="flex h-4 w-4 items-center justify-center rounded-full bg-violet-500/20 text-[8px] font-bold text-violet-400">
                {item.assigned_to[0]?.toUpperCase()}
              </span>
            )}
            {item.commits?.length > 0 && (
              <span className="ml-auto flex items-center gap-0.5 text-[9px] text-emerald-400">
                <GitCommit className="h-2.5 w-2.5" />
                {item.commits.length}
              </span>
            )}
          </div>
        </div>
      )}

      {showMenu && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setShowMenu(false)}
          />
          <div className="absolute right-1 top-7 z-20 w-40 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-1 shadow-xl">
            <p className="px-2 py-1 text-[10px] font-semibold text-[var(--color-text-muted)]">
              Priority
            </p>
            {PRIORITIES.map((p) => (
              <button
                key={p.value}
                onClick={() => {
                  onUpdate(item.id, { priority: p.value });
                  setShowMenu(false);
                }}
                className="flex w-full items-center gap-2 rounded px-2 py-1 text-[11px] text-white hover:bg-[var(--color-surface-2)]"
              >
                <div className={`h-2 w-2 rounded-full ${p.color}`} />
                {p.label}
              </button>
            ))}
            <p className="mt-1 px-2 py-1 text-[10px] font-semibold text-[var(--color-text-muted)]">
              Type
            </p>
            {TYPES.map((t) => (
              <button
                key={t}
                onClick={() => {
                  onUpdate(item.id, { item_type: t });
                  setShowMenu(false);
                }}
                className="flex w-full items-center gap-2 rounded px-2 py-1 text-[11px] capitalize text-white hover:bg-[var(--color-surface-2)]"
              >
                {t}
              </button>
            ))}
            <div className="my-1 border-t border-[var(--color-border)]" />
            <button
              onClick={() => {
                if (confirm(`Delete "${item.title}"?`)) onDelete(item.id);
                setShowMenu(false);
              }}
              className="flex w-full items-center gap-2 rounded px-2 py-1 text-[11px] text-red-400 hover:bg-red-500/10"
            >
              <Trash2 className="h-3 w-3" />
              Delete
            </button>
          </div>
        </>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════
// Add Card Form
// ═══════════════════════════════════════════

function AddCardForm({
  onAdd,
  onCancel,
}: {
  onAdd: (title: string, priority: string) => void;
  onCancel: () => void;
}) {
  const [title, setTitle] = useState("");
  const [priority, setPriority] = useState("P2");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = () => {
    if (title.trim()) {
      onAdd(title.trim(), priority);
      setTitle("");
    }
  };

  return (
    <div className="rounded-lg border border-indigo-500/40 bg-[var(--color-surface)] p-2">
      <input
        ref={inputRef}
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") handleSubmit();
          if (e.key === "Escape") onCancel();
        }}
        placeholder="Card title..."
        className="w-full rounded bg-[var(--color-bg)] px-2 py-1.5 text-xs text-white outline-none"
      />
      <div className="mt-2 flex items-center gap-1">
        <select
          value={priority}
          onChange={(e) => setPriority(e.target.value)}
          className="rounded border border-[var(--color-border)] bg-[var(--color-bg)] px-1.5 py-0.5 text-[10px] text-white outline-none"
        >
          {PRIORITIES.map((p) => (
            <option key={p.value} value={p.value}>
              {p.label}
            </option>
          ))}
        </select>
        <button
          onClick={handleSubmit}
          className="ml-auto rounded bg-indigo-500 px-3 py-1 text-[11px] font-medium text-white hover:bg-indigo-600"
        >
          Add
        </button>
        <button
          onClick={onCancel}
          className="rounded p-1 text-[var(--color-text-muted)] hover:text-white"
        >
          <X className="h-3 w-3" />
        </button>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════
// Column
// ═══════════════════════════════════════════

function Column({
  config,
  column,
  onAdd,
  onUpdate,
  onDelete,
  onDragStart,
  onDrop,
}: {
  config: typeof COLUMNS[0];
  column: BoardColumn;
  onAdd: (status: string, title: string, priority: string) => void;
  onUpdate: (id: string, data: Partial<WorkItem>) => void;
  onDelete: (id: string) => void;
  onDragStart: (id: string) => void;
  onDrop: (status: string) => void;
}) {
  const [adding, setAdding] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        onDrop(config.status);
      }}
      className={`flex min-w-[260px] flex-1 flex-col rounded-xl border-2 transition-all ${
        dragOver ? "border-indigo-500 bg-indigo-500/5" : `${config.border} bg-[var(--color-surface-2)]/30`
      }`}
    >
      {/* Header */}
      <div className="flex items-center gap-2 border-b border-[var(--color-border)] px-3 py-2.5">
        <div
          className="h-2.5 w-2.5 rounded-full"
          style={{ backgroundColor: config.color }}
        />
        <span className="text-xs font-bold uppercase tracking-wider" style={{ color: config.color }}>
          {config.label}
        </span>
        <span className="ml-auto rounded-full bg-[var(--color-surface)] px-2 py-0.5 text-[10px] font-semibold text-[var(--color-text-muted)]">
          {column.count}
        </span>
      </div>

      {/* Cards */}
      <div className="flex-1 space-y-2 overflow-y-auto p-2">
        {column.items.length === 0 && !adding && (
          <div className="flex h-20 items-center justify-center rounded-lg border border-dashed border-[var(--color-border)] text-[10px] text-[var(--color-text-muted)] opacity-40">
            Drag cards here
          </div>
        )}
        {column.items.map((item) => (
          <Card
            key={item.id}
            item={item}
            onUpdate={onUpdate}
            onDelete={onDelete}
            onDragStart={onDragStart}
          />
        ))}
        {adding && (
          <AddCardForm
            onAdd={(title, priority) => {
              onAdd(config.status, title, priority);
              setAdding(false);
            }}
            onCancel={() => setAdding(false)}
          />
        )}
      </div>

      {/* Add button */}
      <div className="border-t border-[var(--color-border)] p-1.5">
        <button
          onClick={() => setAdding(true)}
          disabled={adding}
          className="flex w-full items-center justify-center gap-1.5 rounded-lg py-1.5 text-[11px] font-medium text-[var(--color-text-muted)] transition-colors hover:bg-[var(--color-surface)] hover:text-white disabled:opacity-30"
        >
          <Plus className="h-3 w-3" />
          Add card
        </button>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════
// Board Panel
// ═══════════════════════════════════════════

export function BoardPanel() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<string>("");
  const [sprints, setSprints] = useState<Sprint[]>([]);
  const [selectedSprint, setSelectedSprint] = useState<string>("");
  const [board, setBoard] = useState<BoardData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const draggedIdRef = useRef<string | null>(null);

  // Fetch projects
  useEffect(() => {
    fetch(`${API}/api/projects`)
      .then((r) => r.json())
      .then((data) => {
        const projs = (data.projects || []).map((p: any) => ({ name: p.name }));
        setProjects(projs);
        if (projs.length > 0 && !selectedProject) {
          setSelectedProject(projs[0].name);
        }
      })
      .catch(() => {});
  }, []);

  // Fetch sprints
  useEffect(() => {
    if (!selectedProject) return;
    fetch(`${TASK_API}/api/sprints?project=${encodeURIComponent(selectedProject)}`)
      .then((r) => r.json())
      .then((data) => setSprints(Array.isArray(data) ? data : []))
      .catch(() => setSprints([]));
  }, [selectedProject]);

  // Fetch board
  const fetchBoard = useCallback(() => {
    if (!selectedProject) return;
    setLoading(true);
    setError("");
    let url = `${TASK_API}/api/board?project=${encodeURIComponent(selectedProject)}`;
    if (selectedSprint) url += `&sprint_id=${selectedSprint}`;

    fetch(url)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((data) => setBoard(data))
      .catch((e) => {
        setError(
          e.message.includes("fetch") || e.message.includes("Failed")
            ? "Task Manager offline. Start it with: docker compose -f docker-compose.infra.yml up task-manager -d"
            : e.message
        );
        setBoard(null);
      })
      .finally(() => setLoading(false));
  }, [selectedProject, selectedSprint]);

  useEffect(() => {
    fetchBoard();
    const interval = setInterval(fetchBoard, 15000);
    return () => clearInterval(interval);
  }, [fetchBoard]);

  // Actions
  const handleAdd = async (status: string, title: string, priority: string) => {
    try {
      await fetch(`${TASK_API}/api/items`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          project: selectedProject,
          title,
          priority,
          status,
          sprint_id: selectedSprint || null,
        }),
      });
      fetchBoard();
    } catch (e) {
      console.error(e);
    }
  };

  const handleUpdate = async (id: string, data: Partial<WorkItem>) => {
    try {
      await fetch(`${TASK_API}/api/items/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      fetchBoard();
    } catch (e) {
      console.error(e);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await fetch(`${TASK_API}/api/items/${id}`, { method: "DELETE" });
      fetchBoard();
    } catch (e) {
      console.error(e);
    }
  };

  const handleDrop = (newStatus: string) => {
    const id = draggedIdRef.current;
    if (id) {
      handleUpdate(id, { status: newStatus });
      draggedIdRef.current = null;
    }
  };

  return (
    <div className="flex h-full flex-col bg-[var(--color-bg)]">
      {/* Header */}
      <div className="flex items-center gap-3 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3">
        <ClipboardList className="h-4 w-4 text-amber-400" />
        <span className="text-sm font-semibold text-white">Board</span>

        <select
          value={selectedProject}
          onChange={(e) => {
            setSelectedProject(e.target.value);
            setSelectedSprint("");
          }}
          className="ml-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-2)] px-2 py-1 text-xs text-white outline-none"
        >
          <option value="">Select a project</option>
          {projects.map((p) => (
            <option key={p.name} value={p.name}>
              {p.name}
            </option>
          ))}
        </select>

        {sprints.length > 0 && (
          <select
            value={selectedSprint}
            onChange={(e) => setSelectedSprint(e.target.value)}
            className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-2)] px-2 py-1 text-xs text-white outline-none"
          >
            <option value="">All sprints</option>
            {sprints.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name} ({s.item_count})
              </option>
            ))}
          </select>
        )}

        <div className="ml-auto flex items-center gap-3">
          {board && (
            <span className="text-[11px] text-[var(--color-text-muted)]">
              {board.total} cards
            </span>
          )}
          <button
            onClick={fetchBoard}
            disabled={loading}
            className="rounded-lg p-1.5 text-[var(--color-text-muted)] transition-colors hover:bg-[var(--color-surface-2)] hover:text-white"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 border-b border-red-500/20 bg-red-500/10 px-4 py-2 text-xs text-red-400">
          <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
          {error}
        </div>
      )}

      {/* Board */}
      <div className="flex-1 overflow-x-auto overflow-y-hidden">
        {board ? (
          <div className="flex h-full gap-3 p-3">
            {COLUMNS.map((config) => {
              const col = board.columns.find((c) => c.status === config.status) || {
                status: config.status,
                items: [],
                count: 0,
              };
              return (
                <Column
                  key={config.status}
                  config={config}
                  column={col}
                  onAdd={handleAdd}
                  onUpdate={handleUpdate}
                  onDelete={handleDelete}
                  onDragStart={(id) => {
                    draggedIdRef.current = id;
                  }}
                  onDrop={handleDrop}
                />
              );
            })}
          </div>
        ) : !error ? (
          <div className="flex h-full items-center justify-center">
            {loading ? (
              <Loader2 className="h-6 w-6 animate-spin text-[var(--color-text-muted)]" />
            ) : (
              <div className="text-center">
                <ClipboardList className="mx-auto h-10 w-10 text-[var(--color-border)]" />
                <p className="mt-2 text-xs text-[var(--color-text-muted)]">
                  {projects.length === 0
                    ? "Create a project in the chat first"
                    : "Select a project"}
                </p>
              </div>
            )}
          </div>
        ) : null}
      </div>
    </div>
  );
}
