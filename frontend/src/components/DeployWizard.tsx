import { useState, useEffect } from "react";
import {
  X, Rocket, Container, GitBranch, FileCheck, FileX, Zap,
  Loader2, CheckCircle2, AlertTriangle, ChevronRight, Wand2, Package,
} from "lucide-react";

const API = "";

interface Props {
  onClose: () => void;
  onAnalyzeError?: (message: string) => void;
}

interface Project {
  name: string;
}

interface TargetInfo {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  ready: boolean;
  missing: string[];
  present: string[];
  required_artifacts: string[];
}

interface DeployCheck {
  project: string;
  detected_stack: string;
  artifacts: Record<string, { path: string; exists: boolean; size: number }>;
  targets: Record<string, TargetInfo>;
}

const ICONS: Record<string, any> = {
  container: Container,
  rocket: Rocket,
  "git-branch": GitBranch,
};

export function DeployWizard({ onClose, onAnalyzeError }: Props) {
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<string>("");
  const [check, setCheck] = useState<DeployCheck | null>(null);
  const [selectedTarget, setSelectedTarget] = useState<string>("");
  const [generating, setGenerating] = useState<string | null>(null);
  const [deploying, setDeploying] = useState(false);
  const [deployResult, setDeployResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch(`${API}/api/projects`)
      .then((r) => r.json())
      .then((d) => setProjects((d.projects || []).map((p: any) => ({ name: p.name }))))
      .catch(() => {});
  }, []);

  const loadCheck = (project: string) => {
    setLoading(true);
    fetch(`${API}/api/projects/${encodeURIComponent(project)}/deploy-check`)
      .then((r) => r.json())
      .then((d) => setCheck(d))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  const selectProjectAndNext = (name: string) => {
    setSelectedProject(name);
    loadCheck(name);
    setStep(2);
  };

  const generate = async (artifact: string) => {
    setGenerating(artifact);
    try {
      await fetch(
        `${API}/api/projects/${encodeURIComponent(selectedProject)}/generate-artifact/${encodeURIComponent(artifact)}`,
        { method: "POST" }
      );
      loadCheck(selectedProject);
    } finally {
      setGenerating(null);
    }
  };

  const generateAllMissing = async () => {
    if (!check || !selectedTarget) return;
    const missing = check.targets[selectedTarget].missing;
    setGenerating("all");
    for (const a of missing) {
      await fetch(
        `${API}/api/projects/${encodeURIComponent(selectedProject)}/generate-artifact/${encodeURIComponent(a)}`,
        { method: "POST" }
      );
    }
    loadCheck(selectedProject);
    setGenerating(null);
  };

  const doDeploy = async () => {
    if (!selectedTarget) return;
    setDeploying(true);
    setDeployResult(null);
    try {
      const res = await fetch(
        `${API}/api/projects/${encodeURIComponent(selectedProject)}/execute-deploy/${selectedTarget}`,
        { method: "POST" }
      );
      const data = await res.json();
      setDeployResult(data);
    } catch (e: any) {
      setDeployResult({ error: e.message });
    }
    setDeploying(false);
  };

  const currentTarget = check && selectedTarget ? check.targets[selectedTarget] : null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center bg-black/60 backdrop-blur-sm animate-fade-in"
      onClick={onClose}
    >
      <div
        className="mt-12 max-h-[90vh] w-full max-w-4xl overflow-y-auto rounded-xl border border-[var(--color-border)] bg-[var(--color-bg)] shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 flex items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-surface)] px-5 py-3">
          <div className="flex items-center gap-3">
            <Rocket className="h-5 w-5 text-emerald-400" />
            <h2 className="text-sm font-semibold text-white">Deploy Wizard</h2>
            {/* Step indicator */}
            <div className="ml-4 flex items-center gap-1 text-[10px] text-[var(--color-text-muted)]">
              <StepPill n={1} label="Project" active={step === 1} done={step > 1} />
              <ChevronRight className="h-3 w-3" />
              <StepPill n={2} label="Artifacts" active={step === 2} done={step > 2} />
              <ChevronRight className="h-3 w-3" />
              <StepPill n={3} label="Deploy" active={step === 3} />
            </div>
          </div>
          <button onClick={onClose} className="rounded p-1 text-[var(--color-text-muted)] hover:bg-[var(--color-surface-2)] hover:text-white">
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5">
          {/* STEP 1 — Select Project */}
          {step === 1 && (
            <div>
              <h3 className="mb-3 text-sm font-medium text-white">Select the project to deploy</h3>
              {projects.length === 0 ? (
                <p className="text-xs text-[var(--color-text-muted)]">No projects available.</p>
              ) : (
                <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 md:grid-cols-3">
                  {projects.map((p) => (
                    <button
                      key={p.name}
                      onClick={() => selectProjectAndNext(p.name)}
                      className="flex items-center gap-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-3 text-left transition-all hover:border-emerald-500/40 hover:bg-[var(--color-surface-2)]"
                    >
                      <Package className="h-5 w-5 shrink-0 text-emerald-400" />
                      <span className="truncate text-sm font-medium text-white">{p.name}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* STEP 2 — Check Artifacts + Select Target */}
          {step === 2 && check && (
            <div>
              <div className="mb-4 flex items-center gap-3 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-3">
                <Package className="h-5 w-5 text-emerald-400" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-white">{check.project}</p>
                  <p className="text-[11px] text-[var(--color-text-muted)]">
                    Detected stack: <span className="text-indigo-400">{check.detected_stack}</span>
                  </p>
                </div>
                <button
                  onClick={() => setStep(1)}
                  className="text-xs text-[var(--color-text-muted)] hover:text-white"
                >
                  Change
                </button>
              </div>

              <h3 className="mb-3 text-sm font-medium text-white">Choose deploy type</h3>
              <div className="space-y-2">
                {Object.values(check.targets).map((t) => {
                  const Icon = ICONS[t.icon] || Container;
                  const active = selectedTarget === t.id;
                  return (
                    <button
                      key={t.id}
                      onClick={() => setSelectedTarget(t.id)}
                      className={`flex w-full items-center gap-3 rounded-lg border p-3 text-left transition-all ${
                        active
                          ? "border-2 bg-[var(--color-surface-2)]"
                          : "border-[var(--color-border)] bg-[var(--color-surface)] hover:bg-[var(--color-surface-2)]"
                      }`}
                      style={{ borderColor: active ? t.color : undefined }}
                    >
                      <div
                        className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg"
                        style={{ backgroundColor: `${t.color}20`, color: t.color }}
                      >
                        <Icon className="h-5 w-5" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-semibold text-white">{t.name}</p>
                          {t.ready ? (
                            <span className="rounded-full bg-emerald-500/15 px-2 py-0.5 text-[10px] font-medium text-emerald-400">
                              Ready
                            </span>
                          ) : (
                            <span className="rounded-full bg-amber-500/15 px-2 py-0.5 text-[10px] font-medium text-amber-400">
                              {t.missing.length} missing
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-[var(--color-text-muted)]">{t.description}</p>
                      </div>
                    </button>
                  );
                })}
              </div>

              {/* Artifact checklist for selected target */}
              {currentTarget && (
                <div className="mt-4 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-3">
                  <div className="mb-2 flex items-center justify-between">
                    <h4 className="text-xs font-semibold uppercase text-[var(--color-text-muted)]">
                      Required artifacts
                    </h4>
                    {currentTarget.missing.length > 0 && (
                      <button
                        onClick={generateAllMissing}
                        disabled={generating !== null}
                        className="flex items-center gap-1.5 rounded-lg bg-indigo-500 px-3 py-1 text-[11px] font-medium text-white hover:bg-indigo-600 disabled:opacity-40"
                      >
                        {generating === "all" ? (
                          <Loader2 className="h-3 w-3 animate-spin" />
                        ) : (
                          <Wand2 className="h-3 w-3" />
                        )}
                        Generate all missing
                      </button>
                    )}
                  </div>
                  <div className="space-y-1">
                    {currentTarget.required_artifacts.map((a) => {
                      const present = currentTarget.present.includes(a);
                      return (
                        <div
                          key={a}
                          className={`flex items-center justify-between rounded px-2.5 py-1.5 text-xs ${
                            present ? "bg-emerald-500/5" : "bg-amber-500/5"
                          }`}
                        >
                          <div className="flex items-center gap-2">
                            {present ? (
                              <FileCheck className="h-3.5 w-3.5 text-emerald-400" />
                            ) : (
                              <FileX className="h-3.5 w-3.5 text-amber-400" />
                            )}
                            <span className={present ? "text-white" : "text-[var(--color-text-muted)]"}>
                              {a}
                            </span>
                          </div>
                          <button
                            onClick={() => generate(a)}
                            disabled={generating !== null}
                            className={`flex items-center gap-1 rounded px-2 py-0.5 text-[10px] transition-colors disabled:opacity-40 ${
                              present
                                ? "bg-amber-500/20 text-amber-400 hover:bg-amber-500/30"
                                : "bg-indigo-500/20 text-indigo-400 hover:bg-indigo-500/30"
                            }`}
                          >
                            {generating === a ? (
                              <Loader2 className="h-3 w-3 animate-spin" />
                            ) : (
                              <Wand2 className="h-3 w-3" />
                            )}
                            {present ? "Regenerate" : "Generate"}
                          </button>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Next button */}
              <div className="mt-4 flex justify-end">
                <button
                  onClick={() => setStep(3)}
                  disabled={!selectedTarget || !currentTarget?.ready}
                  className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-xs font-medium text-white transition-colors hover:bg-emerald-700 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  Next
                  <ChevronRight className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          )}

          {/* STEP 3 — Execute */}
          {step === 3 && currentTarget && (
            <div>
              <div className="mb-4 rounded-lg border border-emerald-500/30 bg-emerald-500/5 p-4">
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="h-6 w-6 text-emerald-400" />
                  <div>
                    <p className="text-sm font-semibold text-white">Ready to deploy</p>
                    <p className="text-[11px] text-[var(--color-text-muted)]">
                      {check?.project} → {currentTarget.name}
                    </p>
                  </div>
                </div>
              </div>

              {!deployResult && !deploying && (
                <button
                  onClick={doDeploy}
                  className="flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-emerald-600 to-emerald-500 py-3 text-sm font-semibold text-white transition-colors hover:from-emerald-700 hover:to-emerald-600"
                >
                  <Zap className="h-4 w-4" />
                  Execute Deploy
                </button>
              )}

              {deploying && (
                <div className="flex items-center justify-center gap-3 rounded-lg bg-[var(--color-surface)] p-8">
                  <Loader2 className="h-5 w-5 animate-spin text-emerald-400" />
                  <span className="text-sm text-white">Deploying... this may take a few minutes</span>
                </div>
              )}

              {deployResult && (
                <div className={`rounded-lg border p-4 ${
                  deployResult.success || deployResult.code === 0
                    ? "border-emerald-500/30 bg-emerald-500/5"
                    : "border-red-500/30 bg-red-500/5"
                }`}>
                  <div className="mb-2 flex items-center gap-2">
                    {deployResult.success || deployResult.code === 0 ? (
                      <>
                        <CheckCircle2 className="h-5 w-5 text-emerald-400" />
                        <p className="text-sm font-semibold text-emerald-400">Deploy completed</p>
                      </>
                    ) : (
                      <>
                        <AlertTriangle className="h-5 w-5 text-red-400" />
                        <p className="text-sm font-semibold text-red-400">Deploy error</p>
                      </>
                    )}
                  </div>
                  {deployResult.stdout && (
                    <details className="mt-2">
                      <summary className="cursor-pointer text-[11px] text-[var(--color-text-muted)] hover:text-white">
                        stdout
                      </summary>
                      <pre className="mt-1 max-h-40 overflow-auto rounded bg-[var(--color-bg)] p-2 text-[10px] text-[var(--color-text-muted)]">
                        {deployResult.stdout}
                      </pre>
                    </details>
                  )}
                  {deployResult.stderr && (
                    <details className="mt-2">
                      <summary className="cursor-pointer text-[11px] text-red-400 hover:text-red-300">
                        stderr
                      </summary>
                      <pre className="mt-1 max-h-40 overflow-auto rounded bg-[var(--color-bg)] p-2 text-[10px] text-red-400">
                        {deployResult.stderr}
                      </pre>
                    </details>
                  )}
                  <div className="mt-3 flex items-center gap-2">
                    {!(deployResult.success || deployResult.code === 0) && onAnalyzeError && (
                      <button
                        onClick={() => {
                          const errorText = [
                            deployResult.stderr,
                            deployResult.stdout,
                          ].filter(Boolean).join("\n").slice(-3000);
                          const msg = `O deploy do projeto "${selectedProject}" no target "${selectedTarget}" falhou. Analise o erro abaixo, identifique a causa, corrija os arquivos do projeto (Dockerfile, package.json, etc), rode os sensors, e me avise quando estiver pronto pra tentar de novo.\n\n\`\`\`\n${errorText}\n\`\`\``;
                          onAnalyzeError(msg);
                          onClose();
                        }}
                        className="flex items-center gap-1.5 rounded-lg bg-violet-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-violet-700"
                      >
                        <Wand2 className="h-3.5 w-3.5" />
                        Analyze with Harness
                      </button>
                    )}
                    <button
                      onClick={() => doDeploy()}
                      className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-emerald-700"
                    >
                      <Zap className="h-3.5 w-3.5" />
                      Try again
                    </button>
                    <button
                      onClick={() => {
                        setDeployResult(null);
                        setStep(1);
                        setSelectedProject("");
                        setSelectedTarget("");
                      }}
                      className="rounded-lg border border-[var(--color-border)] px-3 py-1.5 text-xs text-[var(--color-text-muted)] hover:text-white"
                    >
                      New deploy
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {loading && !check && (
            <div className="flex items-center justify-center p-8">
              <Loader2 className="h-5 w-5 animate-spin text-[var(--color-text-muted)]" />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function StepPill({ n, label, active, done }: { n: number; label: string; active?: boolean; done?: boolean }) {
  return (
    <div
      className={`flex items-center gap-1 rounded-full px-2 py-0.5 ${
        active
          ? "bg-emerald-500/20 text-emerald-400"
          : done
          ? "bg-emerald-500/10 text-emerald-500"
          : "bg-[var(--color-surface-2)] text-[var(--color-text-muted)]"
      }`}
    >
      <span className="flex h-3.5 w-3.5 items-center justify-center rounded-full bg-current text-[8px] text-[var(--color-bg)]">
        {n}
      </span>
      {label}
    </div>
  );
}
