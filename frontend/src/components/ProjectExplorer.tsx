import { useState, useEffect, useCallback, useRef } from "react";
import {
  FolderOpen,
  FileCode,
  FileText,
  Download,
  RefreshCw,
  ChevronRight,
  ChevronDown,
  File,
  Copy,
  Check,
} from "lucide-react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";

const API_URL = "http://localhost:8000";

interface ProjectFile {
  name: string;
  size: number;
}

interface Project {
  name: string;
  files: ProjectFile[];
}

interface ProjectExplorerProps {
  /** Bumped externally whenever the agent creates/edits a file */
  refreshTrigger: number;
}

function getLanguage(filename: string): string {
  const ext = filename.split(".").pop() || "";
  const map: Record<string, string> = {
    py: "python",
    js: "javascript",
    ts: "typescript",
    json: "json",
    md: "markdown",
    txt: "text",
    env: "bash",
    example: "bash",
    yml: "yaml",
    yaml: "yaml",
  };
  return map[ext] || "text";
}

function getFileIcon(filename: string) {
  if (filename.endsWith(".py")) return <FileCode className="h-4 w-4 text-yellow-400" />;
  if (filename.endsWith(".json")) return <FileCode className="h-4 w-4 text-amber-400" />;
  if (filename.endsWith(".md")) return <FileText className="h-4 w-4 text-blue-400" />;
  if (filename.endsWith(".txt")) return <FileText className="h-4 w-4 text-[var(--color-text-muted)]" />;
  return <File className="h-4 w-4 text-[var(--color-text-muted)]" />;
}

export function ProjectExplorer({ refreshTrigger }: ProjectExplorerProps) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [hasFetched, setHasFetched] = useState(false);
  const [expandedProject, setExpandedProject] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<{
    project: string;
    filename: string;
  } | null>(null);
  const [fileContent, setFileContent] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const selectedFileRef = useRef(selectedFile);
  selectedFileRef.current = selectedFile;

  const loadFile = useCallback(async (project: string, filename: string) => {
    setLoading(true);
    setSelectedFile({ project, filename });
    try {
      const res = await fetch(
        `${API_URL}/api/projects/${encodeURIComponent(project)}/files/${encodeURIComponent(filename)}`
      );
      const data = await res.json();
      setFileContent(data.content || "");
    } catch {
      setFileContent("Error loading file");
    }
    setLoading(false);
  }, []);

  const fetchProjects = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/projects`);
      const data = await res.json();
      const newProjects: Project[] = data.projects || [];
      console.log("[ProjectExplorer] Loaded", newProjects.length, "projects");
      setProjects(newProjects);
      setHasFetched(true);

      // Auto-expand latest project and auto-select agent.py
      if (newProjects.length > 0) {
        const latest = newProjects[newProjects.length - 1];
        setExpandedProject((prev) => prev || latest.name);
        if (!selectedFileRef.current && latest.files.some((f) => f.name === "agent.py")) {
          loadFile(latest.name, "agent.py");
        }
      }
    } catch (e) {
      console.error("[ProjectExplorer] Error loading projects:", e);
    }
  }, [loadFile]);

  // Fetch on mount and when refreshTrigger changes
  useEffect(() => {
    fetchProjects();
  }, [refreshTrigger, fetchProjects]);

  // Poll every 5s as backup
  useEffect(() => {
    const interval = setInterval(fetchProjects, 5000);
    return () => clearInterval(interval);
  }, [fetchProjects]);

  // Re-fetch selected file when agent edits it
  useEffect(() => {
    if (selectedFileRef.current && refreshTrigger > 0) {
      loadFile(selectedFileRef.current.project, selectedFileRef.current.filename);
    }
  }, [refreshTrigger, loadFile]);

  const handleDownload = (project: string, filename: string) => {
    window.open(
      `${API_URL}/api/projects/${encodeURIComponent(project)}/download/${encodeURIComponent(filename)}`,
      "_blank"
    );
  };

  const handleCopy = async () => {
    await navigator.clipboard.writeText(fileContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (projects.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4 p-8 text-center">
        <FolderOpen className="h-12 w-12 text-[var(--color-border)]" />
        <div>
          <p className="text-sm font-medium text-[var(--color-text-muted)]">
            {hasFetched ? "No projects generated yet" : "Loading projects..."}
          </p>
          <p className="mt-1 text-xs text-[var(--color-text-muted)] opacity-60">
            {hasFetched
              ? "Chat with the agent to create your first project"
              : "Fetching from http://localhost:8000/api/projects"}
          </p>
          <button
            onClick={fetchProjects}
            className="mt-4 rounded-lg bg-indigo-500 px-3 py-1.5 text-xs text-white hover:bg-indigo-600"
          >
            Reload
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col bg-[var(--color-bg)]">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3">
        <div className="flex items-center gap-2">
          <FolderOpen className="h-4 w-4 text-indigo-400" />
          <span className="text-sm font-semibold text-white">Projects</span>
          <span className="rounded-full bg-indigo-500/20 px-2 py-0.5 text-xs text-indigo-400">
            {projects.length}
          </span>
        </div>
        <button
          onClick={fetchProjects}
          className="rounded-lg p-1.5 text-[var(--color-text-muted)] transition-colors hover:bg-[var(--color-surface-2)] hover:text-white"
        >
          <RefreshCw className="h-3.5 w-3.5" />
        </button>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* File tree */}
        <div className="w-56 shrink-0 overflow-y-auto border-r border-[var(--color-border)] bg-[var(--color-surface)]">
          {projects.map((project) => (
            <div key={project.name}>
              {/* Project folder */}
              <button
                onClick={() =>
                  setExpandedProject(
                    expandedProject === project.name ? null : project.name
                  )
                }
                className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm transition-colors hover:bg-[var(--color-surface-2)]"
              >
                {expandedProject === project.name ? (
                  <ChevronDown className="h-3 w-3 text-[var(--color-text-muted)]" />
                ) : (
                  <ChevronRight className="h-3 w-3 text-[var(--color-text-muted)]" />
                )}
                <FolderOpen className="h-4 w-4 text-amber-400" />
                <span className="truncate font-medium text-white">
                  {project.name}
                </span>
              </button>

              {/* Files */}
              {expandedProject === project.name && (
                <div className="animate-fade-in">
                  {project.files.map((file) => (
                    <button
                      key={file.name}
                      onClick={() =>
                        loadFile(project.name, file.name)
                      }
                      className={`flex w-full items-center gap-2 py-1.5 pl-9 pr-3 text-left text-xs transition-colors ${
                        selectedFile?.project === project.name &&
                        selectedFile?.filename === file.name
                          ? "bg-indigo-500/15 text-indigo-300"
                          : "text-[var(--color-text-muted)] hover:bg-[var(--color-surface-2)] hover:text-white"
                      }`}
                    >
                      {getFileIcon(file.name)}
                      <span className="truncate">{file.name}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* File content viewer */}
        <div className="flex flex-1 flex-col overflow-hidden">
          {selectedFile ? (
            <>
              {/* File header */}
              <div className="flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2">
                <div className="flex items-center gap-2">
                  {getFileIcon(selectedFile.filename)}
                  <span className="text-xs font-medium text-white">
                    {selectedFile.project}/{selectedFile.filename}
                  </span>
                </div>
                <div className="flex items-center gap-1">
                  <button
                    onClick={handleCopy}
                    className="flex items-center gap-1 rounded-lg px-2 py-1 text-xs text-[var(--color-text-muted)] transition-colors hover:bg-[var(--color-surface-2)] hover:text-white"
                  >
                    {copied ? (
                      <>
                        <Check className="h-3 w-3 text-emerald-400" /> Copied!
                      </>
                    ) : (
                      <>
                        <Copy className="h-3 w-3" /> Copy
                      </>
                    )}
                  </button>
                  <button
                    onClick={() =>
                      handleDownload(selectedFile.project, selectedFile.filename)
                    }
                    className="flex items-center gap-1 rounded-lg px-2 py-1 text-xs text-[var(--color-text-muted)] transition-colors hover:bg-[var(--color-surface-2)] hover:text-white"
                  >
                    <Download className="h-3 w-3" /> Download
                  </button>
                </div>
              </div>

              {/* Code */}
              <div className="flex-1 overflow-auto">
                {loading ? (
                  <div className="flex h-full items-center justify-center">
                    <span className="text-xs text-[var(--color-text-muted)]">
                      Loading...
                    </span>
                  </div>
                ) : (
                  <SyntaxHighlighter
                    language={getLanguage(selectedFile.filename)}
                    style={vscDarkPlus}
                    customStyle={{
                      margin: 0,
                      padding: "1rem",
                      fontSize: "0.75rem",
                      lineHeight: "1.7",
                      background: "var(--color-bg)",
                      minHeight: "100%",
                    }}
                    showLineNumbers
                  >
                    {fileContent}
                  </SyntaxHighlighter>
                )}
              </div>
            </>
          ) : (
            <div className="flex h-full flex-col items-center justify-center gap-3 text-center">
              <FileCode className="h-10 w-10 text-[var(--color-border)]" />
              <p className="text-xs text-[var(--color-text-muted)]">
                Select a file to preview
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
