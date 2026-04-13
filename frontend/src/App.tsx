import { useState, useEffect, useCallback } from "react";
import {
  Activity,
  FolderOpen,
  Plug,
  Rocket,
  ClipboardList,
} from "lucide-react";
import { useChat } from "./lib/useChat";
import { Header } from "./components/Header";
import { ChatPanel } from "./components/ChatPanel";
import { ActivityPanel } from "./components/ActivityPanel";
import { ProjectExplorer } from "./components/ProjectExplorer";
import { TemplateSelector } from "./components/TemplateSelector";
import { BoardPanel } from "./components/BoardPanel";
import { DeployWizard } from "./components/DeployWizard";

type RightTab = "activity" | "files" | "board" | "integrations";

export default function App() {
  const {
    messages,
    isLoading,
    error,
    activityLog,
    projectRefreshTrigger,
    templateId,
    personaId,
    stackId,
    skillIds,
    projectTypeId,
    setPersonaAndSkills,
    submit,
  } = useChat();

  const [showTemplates, setShowTemplates] = useState(false);
  const [showDeploy, setShowDeploy] = useState(false);
  const [rightTab, setRightTab] = useState<RightTab>("activity");

  // Count integration events for badge
  const integrationEvents = activityLog.filter(
    (e) => e.category === "integration"
  ).length;

  return (
    <div className="flex h-screen flex-col overflow-hidden">
      <Header
        templateId={templateId}
        skillCount={skillIds.length}
        projectTypeId={projectTypeId}
        onProjectTypeChange={(pt) => setPersonaAndSkills(personaId, skillIds, pt)}
        onToggleTemplates={() => setShowTemplates(!showTemplates)}
        onDeploy={() => setShowDeploy(true)}
      />

      {showDeploy && (
        <DeployWizard
          onClose={() => setShowDeploy(false)}
          onAnalyzeError={(msg) => submit(msg)}
        />
      )}

      {showTemplates && (
        <div
          className="fixed inset-0 z-50 flex items-start justify-center bg-black/60 backdrop-blur-sm animate-fade-in"
          onClick={() => setShowTemplates(false)}
        >
          <div
            className="mt-16 max-h-[85vh] w-full max-w-5xl overflow-y-auto rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="sticky top-0 flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3">
              <h2 className="text-sm font-semibold text-white">
                Select Persona + Skills
              </h2>
              <button
                onClick={() => setShowTemplates(false)}
                className="rounded-lg p-1 text-[var(--color-text-muted)] hover:bg-[var(--color-surface-2)] hover:text-white"
              >
                ✕
              </button>
            </div>
            <TemplateSelector
              activeProjectType={projectTypeId}
              activePersona={personaId}
              activeSkills={skillIds}
              onApply={(pt, p, skills) => {
                setPersonaAndSkills(p, skills, pt);
                setShowTemplates(false);
              }}
            />
          </div>
        </div>
      )}

      {error && (
        <div className="border-b border-red-500/30 bg-red-500/10 px-6 py-2 text-sm text-red-400">
          {error}
        </div>
      )}

      <main className="flex flex-1 overflow-hidden">
        {/* LEFT: Chat */}
        <div className="flex w-[45%] flex-col border-r border-[var(--color-border)]">
          <ChatPanel
            messages={messages}
            isLoading={isLoading}
            onSubmit={submit}
          />
        </div>

        {/* RIGHT: Tabs */}
        <div className="flex w-[55%] flex-col">
          <div className="flex border-b border-[var(--color-border)] bg-[var(--color-surface)]">
            <button
              onClick={() => setRightTab("activity")}
              className={`flex items-center gap-2 px-5 py-2.5 text-xs font-medium transition-colors ${
                rightTab === "activity"
                  ? "border-b-2 border-violet-500 text-violet-400"
                  : "text-[var(--color-text-muted)] hover:text-white"
              }`}
            >
              <Activity className="h-3.5 w-3.5" />
              Mission Control
              {activityLog.length > 0 && (
                <span className="rounded-full bg-violet-500/20 px-1.5 py-0.5 text-[10px]">
                  {activityLog.length}
                </span>
              )}
            </button>
            <button
              onClick={() => setRightTab("files")}
              className={`flex items-center gap-2 px-5 py-2.5 text-xs font-medium transition-colors ${
                rightTab === "files"
                  ? "border-b-2 border-indigo-500 text-indigo-400"
                  : "text-[var(--color-text-muted)] hover:text-white"
              }`}
            >
              <FolderOpen className="h-3.5 w-3.5" />
              Projetos
            </button>
            <button
              onClick={() => setRightTab("board")}
              className={`flex items-center gap-2 px-5 py-2.5 text-xs font-medium transition-colors ${
                rightTab === "board"
                  ? "border-b-2 border-amber-500 text-amber-400"
                  : "text-[var(--color-text-muted)] hover:text-white"
              }`}
            >
              <ClipboardList className="h-3.5 w-3.5" />
              Board
            </button>
            <button
              onClick={() => setRightTab("integrations")}
              className={`flex items-center gap-2 px-5 py-2.5 text-xs font-medium transition-colors ${
                rightTab === "integrations"
                  ? "border-b-2 border-orange-500 text-orange-400"
                  : "text-[var(--color-text-muted)] hover:text-white"
              }`}
            >
              <Plug className="h-3.5 w-3.5" />
              Integrations
              {integrationEvents > 0 && (
                <span className="rounded-full bg-orange-500/20 px-1.5 py-0.5 text-[10px]">
                  {integrationEvents}
                </span>
              )}
            </button>
          </div>

          <div className="flex-1 overflow-hidden">
            {rightTab === "activity" ? (
              <ActivityPanel events={activityLog} isLoading={isLoading} />
            ) : rightTab === "files" ? (
              <ProjectExplorer refreshTrigger={projectRefreshTrigger} />
            ) : rightTab === "board" ? (
              <BoardPanel />
            ) : (
              <IntegrationPanel onSubmit={submit} />
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

/* ---- Inline Integration Panel ---- */

import {
  CheckCircle2 as Check2,
  XCircle as XC,
  Loader2 as Spin,
  AlertTriangle as Warn,
  RefreshCw,
} from "lucide-react";

const API = "http://localhost:8000";

// Maps integration name to health check key
const HEALTH_KEYS: Record<string, string> = {
  "Task Manager": "task_manager",
  "Azure DevOps": "_config",
  "GitLab": "git",
  "Vault (Secrets)": "vault",
  "SonarQube": "sonarqube",
  "Semgrep (SAST)": "semgrep",
  "Playwright": "playwright",
  "Flyway (DB)": "postgres",
  "CI/CD Pipeline": "_builtin",
  "Docker Registry": "registry",
  "Docker": "docker",
  "K3s (Staging)": "kubectl",
  "K8s (Producao)": "kubectl",
  "Grafana + Prometheus": "grafana",
  "Notificacoes": "ntfy",
  "Feature Flags": "flagsmith",
};

type HealthMap = Record<string, { status: string; error?: string; output?: string }>;

function StatusDot({ status }: { status: string }) {
  if (status === "online") return <Check2 className="h-3.5 w-3.5 text-emerald-400" />;
  if (status === "offline") return <XC className="h-3.5 w-3.5 text-red-400" />;
  if (status === "not_installed") return <Warn className="h-3.5 w-3.5 text-amber-400" />;
  if (status === "error") return <XC className="h-3.5 w-3.5 text-red-400" />;
  if (status === "_builtin") return <Check2 className="h-3.5 w-3.5 text-emerald-400" />;
  if (status === "loading") return <Spin className="h-3.5 w-3.5 animate-spin text-[var(--color-text-muted)]" />;
  return <div className="h-2.5 w-2.5 rounded-full bg-[var(--color-text-muted)] opacity-40" />;
}

function statusLabel(status: string): string {
  if (status === "online" || status === "_builtin") return "Online";
  if (status === "offline") return "Offline";
  if (status === "not_installed") return "Nao instalado";
  if (status === "error") return "Erro";
  if (status === "loading") return "Verificando...";
  return "Desconhecido";
}

function statusColor(status: string): string {
  if (status === "online" || status === "_builtin") return "text-emerald-400";
  if (status === "offline" || status === "error") return "text-red-400";
  if (status === "not_installed") return "text-amber-400";
  return "text-[var(--color-text-muted)]";
}

function IntegrationPanel({ onSubmit }: { onSubmit: (msg: string) => void }) {
  const [health, setHealth] = useState<HealthMap>({});
  const [loading, setLoading] = useState(false);

  const fetchHealth = useCallback(() => {
    setLoading(true);
    fetch(`${API}/api/integrations/health`)
      .then((r) => r.json())
      .then((data) => {
        const h = data.integrations || {};
        console.log("[Integrations Health]", h);
        setHealth(h);
      })
      .catch((e) => console.error("[Integrations Health Error]", e))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchHealth();
    // Re-check every 30s
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, [fetchHealth]);

  function getStatus(integName: string): string {
    const key = HEALTH_KEYS[integName];
    if (!key) return "unknown";
    if (key === "_builtin") return "_builtin";
    if (key === "_config") return "offline";
    // If we haven't loaded health yet, show loading
    if (Object.keys(health).length === 0) return "loading";
    return health[key]?.status || "unknown";
  }

  function getError(integName: string): string {
    const key = HEALTH_KEYS[integName];
    if (!key || key.startsWith("_")) return "";
    return health[key]?.error || "";
  }

  const integrations = [
    { name: "Task Manager", color: "#f59e0b", tools: ["task_create_item", "task_board", "task_create_sprint"], description: "Gerenciamento de tarefas e sprints (built-in)", section: "Plan", category: "task_management" },
    { name: "Azure DevOps", color: "#0078D4", tools: ["azdo_create_work_item", "azdo_get_board"], description: "Work items, sprints e boards via Azure DevOps", section: "Plan", category: "task_management" },
    { name: "GitLab", color: "#FC6D26", tools: ["git_init", "git_commit", "git_push", "git_create_mr"], description: "Versionamento de codigo com Git", section: "Develop", category: "version_control" },
    { name: "Vault (Secrets)", color: "#FFD814", tools: ["vault_setup", "vault_store_secret", "vault_generate_env"], description: "HashiCorp Vault local (docker)", section: "Develop", category: "secrets" },
    { name: "SonarQube", color: "#4E9BCD", tools: ["sonar_scan", "sonar_quality_gate", "sonar_issues"], description: "Quality gate — code smells, bugs, vulnerabilidades", section: "Review", category: "quality" },
    { name: "Semgrep (SAST)", color: "#2B2B2B", tools: ["security_scan", "security_report"], description: "Security scanning — OWASP, SAST automatizado", section: "Review", category: "security" },
    { name: "Playwright", color: "#2EAD33", tools: ["e2e_run_tests", "e2e_show_report", "e2e_init"], description: "Testes E2E automatizados", section: "Test", category: "testing" },
    { name: "Flyway (DB)", color: "#CC0200", tools: ["db_create_migration", "db_migrate", "db_status"], description: "Migracoes de banco versionadas", section: "Test", category: "database" },
    { name: "CI/CD Pipeline", color: "#FC6D26", tools: ["cicd_generate_pipeline", "cicd_validate_pipeline"], description: "Gerar .gitlab-ci.yml automaticamente", section: "Build", category: "cicd" },
    { name: "Docker Registry", color: "#2496ED", tools: ["registry_setup", "registry_push", "registry_list"], description: "Registro local de imagens", section: "Build", category: "registry" },
    { name: "Docker", color: "#2496ED", tools: ["docker_build", "docker_run", "docker_compose_up"], description: "Deploy local com containers", section: "Deploy", category: "deploy_local" },
    { name: "K3s (Staging)", color: "#FFC61C", tools: ["k3s_deploy", "k3s_status", "k3s_rollback"], description: "Deploy staging com K3s", section: "Deploy", category: "deploy_staging" },
    { name: "K8s (Producao)", color: "#326CE5", tools: ["k8s_deploy", "k8s_status", "k8s_scale"], description: "Deploy producao com Kubernetes", section: "Deploy", category: "deploy_production" },
    { name: "Grafana + Prometheus", color: "#F46800", tools: ["monitoring_setup", "monitoring_start", "monitoring_check_alerts"], description: "Monitoramento com dashboards e alertas", section: "Monitor", category: "monitoring" },
    { name: "Notificacoes", color: "#611f69", tools: ["notify_send", "notify_setup", "notify_on_deploy"], description: "Alertas via Slack, Teams ou Ntfy", section: "Monitor", category: "notifications" },
    { name: "Feature Flags", color: "#6633FF", tools: ["flag_setup", "flag_create", "flag_toggle", "flag_list"], description: "Flagsmith local (docker)", section: "Monitor", category: "feature_flags" },
  ];

  const onlineCount = integrations.filter((i) => {
    const s = getStatus(i.name);
    return s === "online" || s === "_builtin";
  }).length;

  return (
    <div className="flex h-full flex-col bg-[var(--color-bg)]">
      <div className="flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3">
        <div className="flex items-center gap-2">
          <Plug className="h-4 w-4 text-orange-400" />
          <span className="text-sm font-semibold text-white">Integrations</span>
          <span className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] font-medium text-emerald-400">
            {onlineCount}/{integrations.length} online
          </span>
        </div>
        <button
          onClick={fetchHealth}
          disabled={loading}
          className="rounded-lg p-1.5 text-[var(--color-text-muted)] transition-colors hover:bg-[var(--color-surface-2)] hover:text-white disabled:opacity-30"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {["Plan", "Develop", "Review", "Test", "Build", "Deploy", "Monitor"].map((section) => {
          const items = integrations.filter((i) => i.section === section);
          if (!items.length) return null;
          return (
            <div key={section} className="mb-5">
              <h3 className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
                <div className="h-px flex-1 bg-[var(--color-border)]" />
                {section}
                <div className="h-px flex-1 bg-[var(--color-border)]" />
              </h3>
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                {items.map((integ) => {
                  const st = getStatus(integ.name);
                  const err = getError(integ.name);
                  return (
                    <div
                      key={integ.name}
                      className={`rounded-lg border p-3 transition-all ${
                        st === "online" || st === "_builtin"
                          ? "border-emerald-500/20 bg-[var(--color-surface)]"
                          : st === "offline" || st === "error"
                          ? "border-red-500/20 bg-[var(--color-surface)]"
                          : "border-[var(--color-border)] bg-[var(--color-surface)]"
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        <div
                          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg"
                          style={{ backgroundColor: `${integ.color}20`, color: integ.color }}
                        >
                          <Plug className="h-4 w-4" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <h4 className="text-xs font-semibold text-white">{integ.name}</h4>
                            <StatusDot status={st} />
                            <span className={`text-[10px] font-medium ${statusColor(st)}`}>
                              {statusLabel(st)}
                            </span>
                          </div>
                          <p className="truncate text-[10px] text-[var(--color-text-muted)]">{integ.description}</p>
                        </div>
                      </div>
                      {/* Error message */}
                      {err && (st === "offline" || st === "error" || st === "not_installed") && (
                        <div className="mt-1.5 rounded bg-red-500/10 px-2 py-1 text-[10px] text-red-400">
                          {err.slice(0, 120)}
                        </div>
                      )}
                      {/* Tools */}
                      <div className="mt-2 flex flex-wrap gap-1">
                        {integ.tools.slice(0, 3).map((t) => (
                          <span key={t} className="rounded-full bg-[var(--color-surface-2)] px-2 py-0.5 text-[9px] text-[var(--color-text-muted)]">{t}</span>
                        ))}
                        {integ.tools.length > 3 && (
                          <span className="rounded-full bg-[var(--color-surface-2)] px-2 py-0.5 text-[9px] text-[var(--color-text-muted)]">+{integ.tools.length - 3}</span>
                        )}
                      </div>
                      {/* Deploy button */}
                      {integ.category.startsWith("deploy") && (st === "online" || st === "_builtin") && (
                        <button
                          onClick={() => onSubmit(`deploy the current project to ${integ.category.replace("deploy_", "")}`)}
                          className="mt-2 flex w-full items-center justify-center gap-1.5 rounded-lg py-1.5 text-[11px] font-medium text-white transition-all hover:opacity-90"
                          style={{ backgroundImage: `linear-gradient(135deg, ${integ.color}, ${integ.color}cc)` }}
                        >
                          <Rocket className="h-3 w-3" />
                          Deploy
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
