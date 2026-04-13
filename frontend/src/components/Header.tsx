import { useEffect, useState } from "react";
import { Bot, ChevronDown, Sparkles, Rocket, Layers, Package } from "lucide-react";

const PERSONA_NAMES: Record<string, string> = {
  deepagent_generator: "DeepAgent Generator",
  architect: "Software Architect",
  product_owner: "Product Owner",
  qa_engineer: "QA Engineer",
  developer: "Developer",
  devops: "DevOps / SRE",
};

const PERSONA_COLORS: Record<string, string> = {
  deepagent_generator: "#6366f1",
  architect: "#8b5cf6",
  product_owner: "#f59e0b",
  qa_engineer: "#10b981",
  developer: "#ec4899",
  devops: "#06b6d4",
};

interface ProjectTypeOpt {
  id: string;
  name: string;
  color: string;
}

interface HeaderProps {
  templateId: string;
  skillCount: number;
  projectTypeId: string;
  onProjectTypeChange: (id: string) => void;
  onToggleTemplates: () => void;
  onDeploy: () => void;
}

export function Header({
  templateId,
  skillCount,
  projectTypeId,
  onProjectTypeChange,
  onToggleTemplates,
  onDeploy,
}: HeaderProps) {
  const [projectTypes, setProjectTypes] = useState<ProjectTypeOpt[]>([]);

  useEffect(() => {
    fetch("/api/project-types")
      .then((r) => r.json())
      .then((d) => setProjectTypes(d.project_types || []))
      .catch(() => {});
  }, []);

  const personaColor = PERSONA_COLORS[templateId] || "#6366f1";
  const personaName = PERSONA_NAMES[templateId] || templateId;
  const currentProject = projectTypes.find((p) => p.id === projectTypeId);
  const projectColor = currentProject?.color || "#64748b";

  return (
    <header className="flex items-center gap-3 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-6 py-3">
      <div className="flex items-center gap-2">
        <div
          className="flex h-9 w-9 items-center justify-center rounded-lg"
          style={{ background: `linear-gradient(135deg, ${projectColor}, ${personaColor})` }}
        >
          <Bot className="h-5 w-5 text-white" />
        </div>
        <div>
          <h1 className="text-lg font-semibold leading-tight text-white">
            DeepHarness
          </h1>
          <p className="text-xs text-[var(--color-text-muted)]">
            Engineering Platform
          </p>
        </div>
      </div>

      {/* Project Type select */}
      <div className="ml-6 flex items-center gap-1.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-2)] px-2.5 py-1">
        <Package className="h-3.5 w-3.5" style={{ color: projectColor }} />
        <select
          value={projectTypeId}
          onChange={(e) => onProjectTypeChange(e.target.value)}
          className="cursor-pointer bg-transparent text-sm text-white outline-none"
        >
          {projectTypes.map((pt) => (
            <option key={pt.id} value={pt.id} className="bg-[var(--color-surface)]">
              {pt.name}
            </option>
          ))}
        </select>
      </div>

      {/* Persona + Skills combo button */}
      <button
        onClick={onToggleTemplates}
        className="flex items-center gap-2 rounded-lg border border-[var(--color-border)] px-3 py-1.5 text-sm transition-all hover:bg-[var(--color-surface-2)]"
      >
        <div className="flex items-center gap-1.5">
          <div className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: personaColor }} />
          <span className="font-medium text-white">{personaName}</span>
        </div>
        {skillCount > 0 && (
          <>
            <span className="text-[var(--color-text-muted)]">+</span>
            <div className="flex items-center gap-1.5">
              <Layers className="h-3 w-3 text-indigo-400" />
              <span className="text-[var(--color-text-muted)]">
                {skillCount} skill{skillCount > 1 ? "s" : ""}
              </span>
            </div>
          </>
        )}
        <ChevronDown className="h-3.5 w-3.5 text-[var(--color-text-muted)]" />
      </button>

      <div className="ml-auto flex items-center gap-3">
        {/* Deploy button — opens wizard */}
        <button
          onClick={onDeploy}
          className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-1.5 text-xs font-medium text-white transition-all hover:bg-emerald-700"
        >
          <Rocket className="h-3.5 w-3.5" />
          Deploy
        </button>

        <div className="flex items-center gap-2 rounded-full bg-[var(--color-surface-2)] px-3 py-1.5">
          <Sparkles className="h-3.5 w-3.5 text-violet-400" />
          <span className="text-xs font-medium text-violet-300">
            Powered by Deep Agents
          </span>
        </div>
      </div>
    </header>
  );
}
