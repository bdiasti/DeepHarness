import { useEffect, useRef, useState } from "react";
import {
  Brain,
  Wrench,
  Shield,
  CheckCircle2,
  XCircle,
  Loader2,
  Pencil,
  FilePlus,
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  Activity,
  Zap,
  GitBranch,
  Container,
  TestTube2,
  Rocket,
  ClipboardList,
  Plug,
} from "lucide-react";
import type { ActivityEvent } from "../lib/useChat";

interface ActivityPanelProps {
  events: ActivityEvent[];
  isLoading: boolean;
}

const TOOL_LABELS: Record<string, string> = {
  run_linter: "Linter",
  validate_structure: "Structure",
  check_directives: "Directives",
  review_code: "Code Review",
  harness_status: "Harness Status",
  read_harness_rules: "Custom Rules",
  update_harness_rules: "Update Rules",
  read_agents_md: "Project Context",
  update_agents_md: "Save Context",
  scan_drift: "Detect Drift",
  validate_before_write: "Pre-validation",
  create_sdd: "Create SDD (Plan)",
  get_sdd: "Read SDD",
  write_file: "Create File",
  edit_file: "Edit File",
  read_file: "Read File",
  ls: "List",
  glob: "Search",
  grep: "Grep",
  write_todos: "Plan",
  generate_agent_code: "Generate Agent",
  validate_agent_config: "Validate Config",
  list_available_models: "Models",
  list_available_tools: "Tools",
  list_middleware_options: "Middleware",
  list_projects: "Projects",
  task: "Delegate SubAgent",
  // Integrations: Git
  git_init: "Git Init",
  git_commit: "Git Commit",
  git_push: "Git Push",
  git_create_branch: "Git Branch",
  git_diff: "Git Diff",
  git_log: "Git Log",
  git_status: "Git Status",
  git_create_mr: "Merge Request",
  // Integrations: Docker
  docker_build: "Docker Build",
  docker_run: "Docker Run",
  docker_stop: "Docker Stop",
  docker_logs: "Docker Logs",
  docker_status: "Docker Status",
  docker_compose_up: "Compose Up",
  docker_compose_down: "Compose Down",
  // Integrations: Tasks
  task_create_item: "Create Task",
  task_list_items: "List Tasks",
  task_update_item: "Update Task",
  task_create_sprint: "Create Sprint",
  task_list_sprints: "List Sprints",
  task_board: "Board",
  task_link_commit: "Link Commit",
  // Integrations: Azure DevOps
  azdo_create_work_item: "AzDO: Create Item",
  azdo_list_work_items: "AzDO: List",
  azdo_update_work_item: "AzDO: Update",
  azdo_get_sprints: "AzDO: Sprints",
  azdo_get_board: "AzDO: Board",
  azdo_link_commit: "AzDO: Link Commit",
  // Integrations: Playwright
  e2e_run_tests: "E2E: Run Tests",
  e2e_run_single_test: "E2E: Single Test",
  e2e_show_report: "E2E: Report",
  e2e_list_tests: "E2E: List",
  e2e_init: "E2E: Initialize",
  // Integrations: K3s/K8s
  k3s_deploy: "K3s Deploy (Staging)",
  k3s_status: "K3s Status",
  k3s_logs: "K3s Logs",
  k3s_rollback: "K3s Rollback",
  k8s_deploy: "K8s Deploy (Prod)",
  k8s_status: "K8s Status",
  k8s_logs: "K8s Logs",
  k8s_scale: "K8s Scale",
  k8s_rollback: "K8s Rollback",
  // SonarQube
  sonar_scan: "Sonar Scan",
  sonar_quality_gate: "Quality Gate",
  sonar_issues: "Sonar Issues",
  sonar_setup: "Sonar Setup",
  // CI/CD
  cicd_generate_pipeline: "Generate Pipeline",
  cicd_validate_pipeline: "Validate Pipeline",
  cicd_add_stage: "Add Stage",
  cicd_show_pipeline: "View Pipeline",
  // Notifications
  notify_send: "Notify",
  notify_setup: "Configure Notification",
  notify_test: "Test Notification",
  notify_on_deploy: "Notify Deploy",
  notify_on_test_fail: "Notify Failure",
  // Monitoring
  monitoring_setup: "Setup Monitoring",
  monitoring_status: "Monitoring Status",
  monitoring_start: "Start Monitoring",
  monitoring_stop: "Stop Monitoring",
  monitoring_check_alerts: "Check Alerts",
  monitoring_add_dashboard: "Add Dashboard",
  // Vault
  vault_setup: "Setup Vault",
  vault_store_secret: "Store Secret",
  vault_get_secret: "Read Secret",
  vault_list_secrets: "List Secrets",
  vault_generate_env: "Generate .env",
  // Flyway
  db_create_migration: "Create Migration",
  db_migrate: "Run Migration",
  db_status: "DB Status",
  db_rollback: "DB Rollback",
  db_list_migrations: "List Migrations",
  // Registry
  registry_setup: "Setup Registry",
  registry_push: "Push Image",
  registry_list: "List Images",
  registry_tag: "Tag Image",
  registry_status: "Registry Status",
  // Semgrep
  security_scan: "Security Scan",
  security_report: "Security Report",
  security_fix_suggestions: "Security Fixes",
  security_setup: "Setup Security",
  // Flagsmith
  flag_setup: "Setup Flags",
  flag_create: "Create Flag",
  flag_toggle: "Toggle Flag",
  flag_list: "List Flags",
  flag_generate_sdk_code: "SDK Code",
  // Integration management
  integration_status: "Integrations Status",
  configure_integration: "Configure Integration",
  deploy: "Deploy",
};

function getIntegrationIcon(tool: string) {
  if (tool?.startsWith("git_")) return GitBranch;
  if (tool?.startsWith("docker_") || tool?.startsWith("compose_")) return Container;
  if (tool?.startsWith("e2e_")) return TestTube2;
  if (tool?.startsWith("k3s_") || tool?.startsWith("k8s_")) return Rocket;
  if (tool?.startsWith("task_") || tool?.startsWith("azdo_")) return ClipboardList;
  if (tool?.startsWith("sonar_")) return Shield;
  if (tool?.startsWith("cicd_")) return Rocket;
  if (tool?.startsWith("notify_")) return Activity;
  if (tool?.startsWith("monitoring_")) return Activity;
  if (tool?.startsWith("vault_")) return Shield;
  if (tool?.startsWith("db_")) return Container;
  if (tool?.startsWith("registry_")) return Container;
  if (tool?.startsWith("security_")) return Shield;
  if (tool?.startsWith("flag_")) return Plug;
  if (tool === "deploy") return Rocket;
  return Plug;
}

function getEventConfig(event: ActivityEvent) {
  // Integration events get special treatment
  if (event.category === "integration") {
    const Icon = getIntegrationIcon(event.tool || "");
    return {
      icon: Icon,
      label: TOOL_LABELS[event.tool || ""] || event.tool || "Integration",
      color: "text-orange-400",
      bg: "bg-orange-500/10",
      border: "border-orange-500/20",
    };
  }

  switch (event.type) {
    case "thinking":
      return {
        icon: Brain,
        label: "Reasoning...",
        color: "text-indigo-400",
        bg: "bg-indigo-500/10",
        border: "border-indigo-500/20",
      };
    case "tool_start":
      return {
        icon: Wrench,
        label: TOOL_LABELS[event.tool || ""] || event.tool || "Tool",
        color: "text-cyan-400",
        bg: "bg-cyan-500/10",
        border: "border-cyan-500/20",
      };
    case "tool_end":
      return {
        icon: Wrench,
        label: TOOL_LABELS[event.tool || ""] || event.tool || "Tool",
        color: "text-cyan-400",
        bg: "bg-cyan-500/10",
        border: "border-cyan-500/20",
      };
    case "sensor_start":
      return {
        icon: Shield,
        label: `Sensor: ${TOOL_LABELS[event.tool || ""] || event.tool}`,
        color: "text-violet-400",
        bg: "bg-violet-500/10",
        border: "border-violet-500/20",
      };
    case "sensor_pass":
      return {
        icon: CheckCircle2,
        label: `${TOOL_LABELS[event.tool || ""] || event.tool}`,
        color: "text-emerald-400",
        bg: "bg-emerald-500/10",
        border: "border-emerald-500/20",
      };
    case "sensor_fail":
      return {
        icon: XCircle,
        label: `${TOOL_LABELS[event.tool || ""] || event.tool}`,
        color: "text-red-400",
        bg: "bg-red-500/10",
        border: "border-red-500/20",
      };
    case "correction":
      return {
        icon: Pencil,
        label: "Auto-correcting...",
        color: "text-amber-400",
        bg: "bg-amber-500/10",
        border: "border-amber-500/20",
      };
    case "file_changed":
      return {
        icon: FilePlus,
        label: "File modified",
        color: "text-sky-400",
        bg: "bg-sky-500/10",
        border: "border-sky-500/20",
      };
    case "error":
      return {
        icon: AlertTriangle,
        label: "Error",
        color: "text-red-400",
        bg: "bg-red-500/10",
        border: "border-red-500/20",
      };
    case "done":
      return {
        icon: Zap,
        label: "Completed",
        color: "text-emerald-400",
        bg: "bg-emerald-500/10",
        border: "border-emerald-500/20",
      };
    default:
      return {
        icon: Activity,
        label: event.type,
        color: "text-[var(--color-text-muted)]",
        bg: "bg-[var(--color-surface-2)]",
        border: "border-[var(--color-border)]",
      };
  }
}

function getStatusBadge(event: ActivityEvent) {
  if (event.status === "running") {
    return (
      <span className="flex items-center gap-1 rounded-full bg-indigo-500/15 px-2 py-0.5 text-[10px] font-medium text-indigo-400">
        <Loader2 className="h-2.5 w-2.5 animate-spin" />
        running
      </span>
    );
  }
  if (event.type === "sensor_pass") {
    const wasCorrected = event.status === "done";
    return (
      <span
        className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${
          wasCorrected
            ? "bg-amber-500/15 text-amber-400"
            : "bg-emerald-500/15 text-emerald-400"
        }`}
      >
        {wasCorrected ? "FIXED" : "PASS"}
      </span>
    );
  }
  if (event.type === "sensor_fail") {
    return (
      <span className="rounded-full bg-red-500/15 px-2 py-0.5 text-[10px] font-semibold text-red-400">
        FAIL
      </span>
    );
  }
  return null;
}

function extractFirstLine(output?: string): string {
  if (!output) return "";
  const line = output.split("\n").find((l) => l.trim().length > 0) || "";
  return line.trim().slice(0, 80);
}

function EventRow({ event }: { event: ActivityEvent }) {
  const [expanded, setExpanded] = useState(false);
  const config = getEventConfig(event);
  const Icon = config.icon;
  const hasOutput = event.output && event.output.length > 0;
  const isRunning = event.status === "running";

  // Skip file_changed and done from detailed view — they're just markers
  if (event.type === "file_changed" || event.type === "done") {
    return (
      <div className="flex items-center gap-2 py-1 pl-3 text-[11px] text-[var(--color-text-muted)] opacity-60">
        <Icon className="h-3 w-3" />
        <span>{config.label}</span>
      </div>
    );
  }

  return (
    <div
      className={`rounded-lg border ${config.border} ${config.bg} transition-all ${
        isRunning ? "animate-pulse-glow" : ""
      }`}
    >
      <button
        onClick={() => hasOutput && setExpanded(!expanded)}
        className="flex w-full items-center gap-2.5 px-3 py-2 text-left"
        disabled={!hasOutput}
      >
        {/* Timeline dot */}
        <div className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-md ${config.bg}`}>
          {isRunning ? (
            <Loader2 className={`h-3.5 w-3.5 animate-spin ${config.color}`} />
          ) : (
            <Icon className={`h-3.5 w-3.5 ${config.color}`} />
          )}
        </div>

        {/* Content */}
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className={`text-xs font-medium ${config.color}`}>
              {config.label}
            </span>
            {getStatusBadge(event)}
          </div>
          {/* Preview of input/output */}
          {event.input && !expanded && (
            <p className="mt-0.5 truncate text-[11px] text-[var(--color-text-muted)] opacity-70">
              {event.input.slice(0, 60)}
            </p>
          )}
          {hasOutput && !expanded && event.type !== "thinking" && (
            <p className="mt-0.5 truncate text-[11px] text-[var(--color-text-muted)] opacity-70">
              {extractFirstLine(event.output)}
            </p>
          )}
        </div>

        {/* Expand arrow */}
        {hasOutput && (
          <div className="shrink-0 text-[var(--color-text-muted)]">
            {expanded ? (
              <ChevronDown className="h-3.5 w-3.5" />
            ) : (
              <ChevronRight className="h-3.5 w-3.5" />
            )}
          </div>
        )}
      </button>

      {/* Expanded output */}
      {expanded && hasOutput && (
        <div className="border-t border-[var(--color-border)] px-3 py-2">
          <pre className="max-h-48 overflow-auto whitespace-pre-wrap text-[11px] leading-relaxed text-[var(--color-text-muted)]">
            {event.output}
          </pre>
        </div>
      )}
    </div>
  );
}

export function ActivityPanel({ events, isLoading }: ActivityPanelProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events]);

  // Stats
  const sensorPasses = events.filter((e) => e.type === "sensor_pass").length;
  const sensorFails = events.filter((e) => e.type === "sensor_fail").length;
  const corrections = events.filter((e) => e.type === "correction").length;
  const toolCalls = events.filter((e) => e.type === "tool_start" || e.type === "tool_end").length;

  return (
    <div className="flex h-full flex-col bg-[var(--color-bg)]">
      {/* Header with stats */}
      <div className="flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3">
        <div className="flex items-center gap-2">
          <Activity className="h-4 w-4 text-violet-400" />
          <span className="text-sm font-semibold text-white">
            Mission Control
          </span>
          {isLoading && (
            <Loader2 className="h-3.5 w-3.5 animate-spin text-indigo-400" />
          )}
        </div>
        {events.length > 0 && (
          <div className="flex items-center gap-3 text-[11px]">
            {sensorPasses > 0 && (
              <span className="flex items-center gap-1 text-emerald-400">
                <CheckCircle2 className="h-3 w-3" />
                {sensorPasses}
              </span>
            )}
            {sensorFails > 0 && (
              <span className="flex items-center gap-1 text-red-400">
                <XCircle className="h-3 w-3" />
                {sensorFails}
              </span>
            )}
            {corrections > 0 && (
              <span className="flex items-center gap-1 text-amber-400">
                <Pencil className="h-3 w-3" />
                {corrections}
              </span>
            )}
            <span className="text-[var(--color-text-muted)]">
              {events.length} events
            </span>
          </div>
        )}
      </div>

      {/* Timeline */}
      <div className="flex-1 overflow-y-auto px-3 py-3">
        {events.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center gap-3 text-center">
            <Activity className="h-10 w-10 text-[var(--color-border)]" />
            <div>
              <p className="text-sm font-medium text-[var(--color-text-muted)]">
                No activity yet
              </p>
              <p className="mt-1 text-xs text-[var(--color-text-muted)] opacity-60">
                Send a message to see the agent working
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-2">
            {events.map((event) => (
              <EventRow key={event.id} event={event} />
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </div>
    </div>
  );
}
