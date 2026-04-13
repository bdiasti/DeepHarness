import { useState, useEffect, useRef } from "react";
import {
  Bot, Layers, Building2, ClipboardList, ShieldCheck, Code, Smartphone,
  Cloud, Check, Search, Zap, Lock, Sparkles, Info, Scroll,
} from "lucide-react";

const API_URL = "";

interface PersonaInfo {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  required_skills: string[];
  recommended_skills: string[];
}

interface SkillInfo {
  id: string;
  name: string;
  category: string;
  description: string;
}

interface ProjectTypeInfo {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  mandatory_stack: string[];
  constitution: string;
}

interface Props {
  activeProjectType: string;
  activePersona: string;
  activeSkills: string[];
  onApply: (projectTypeId: string, personaId: string, skillIds: string[]) => void;
}

const ICON_MAP: Record<string, any> = {
  bot: Bot,
  layers: Layers,
  building: Building2,
  "clipboard-list": ClipboardList,
  "shield-check": ShieldCheck,
  code: Code,
  cloud: Cloud,
  smartphone: Smartphone,
};

const CATEGORY_LABELS: Record<string, string> = {
  frontend: "Frontend",
  backend: "Backend",
  mobile: "Mobile",
  database: "Database",
  architecture: "Arquitetura",
  methodology: "Metodologia",
  testing: "Testes",
  devops: "DevOps",
};

const CATEGORY_COLORS: Record<string, string> = {
  frontend: "#06b6d4",
  backend: "#3b82f6",
  mobile: "#a855f7",
  database: "#f97316",
  architecture: "#8b5cf6",
  methodology: "#f59e0b",
  testing: "#10b981",
  devops: "#06b6d4",
};

// Fetch persona directives for tooltip
async function fetchPersonaDetails(personaId: string): Promise<string> {
  try {
    // We use the persona's directives inline from the api response
    return "";
  } catch {
    return "";
  }
}

function DirectivesTooltip({ persona }: { persona: PersonaInfo }) {
  return (
    <div className="absolute left-full top-0 z-50 ml-2 w-72 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-3 shadow-xl">
      <h4 className="mb-2 flex items-center gap-2 text-xs font-bold text-white">
        <Info className="h-3 w-3" />
        {persona.name}
      </h4>
      <p className="mb-2 text-[11px] text-[var(--color-text-muted)]">{persona.description}</p>
      {persona.required_skills.length > 0 && (
        <div className="mb-2">
          <p className="mb-1 text-[10px] font-semibold uppercase text-amber-400">
            <Lock className="mr-1 inline h-2.5 w-2.5" />
            Required skills
          </p>
          <div className="flex flex-wrap gap-1">
            {persona.required_skills.map((s) => (
              <span key={s} className="rounded bg-amber-500/10 px-1.5 py-0.5 text-[10px] text-amber-400">
                {s.split("/")[1]}
              </span>
            ))}
          </div>
        </div>
      )}
      {persona.recommended_skills.length > 0 && (
        <div>
          <p className="mb-1 text-[10px] font-semibold uppercase text-violet-400">
            <Sparkles className="mr-1 inline h-2.5 w-2.5" />
            Recommended
          </p>
          <div className="flex flex-wrap gap-1">
            {persona.recommended_skills.map((s) => (
              <span key={s} className="rounded bg-violet-500/10 px-1.5 py-0.5 text-[10px] text-violet-400">
                {s.split("/")[1]}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export function TemplateSelector({
  activeProjectType,
  activePersona,
  activeSkills,
  onApply,
}: Props) {
  const [projectTypes, setProjectTypes] = useState<ProjectTypeInfo[]>([]);
  const [personas, setPersonas] = useState<PersonaInfo[]>([]);
  const [skillsByCategory, setSkillsByCategory] = useState<Record<string, SkillInfo[]>>({});
  const [selectedProjectType, setSelectedProjectType] = useState(activeProjectType);
  const [selectedPersona, setSelectedPersona] = useState(activePersona);
  const [selectedSkills, setSelectedSkills] = useState<Set<string>>(new Set(activeSkills));
  const [search, setSearch] = useState("");
  const [hoveredPersona, setHoveredPersona] = useState<string | null>(null);
  const [showConstitution, setShowConstitution] = useState(false);

  useEffect(() => {
    setSelectedProjectType(activeProjectType);
    setSelectedPersona(activePersona);
    setSelectedSkills(new Set(activeSkills));
  }, [activeProjectType, activePersona, activeSkills]);

  useEffect(() => {
    console.log("[Selector] fetching...");
    fetch(`${API_URL}/api/project-types`)
      .then((r) => r.json())
      .then((d) => {
        console.log("[Selector] project-types:", d.project_types?.length);
        setProjectTypes(d.project_types || []);
      })
      .catch((e) => console.error("[Selector] project-types ERR:", e));
    fetch(`${API_URL}/api/personas`)
      .then((r) => r.json())
      .then((d) => {
        console.log("[Selector] personas:", d.personas?.length);
        setPersonas(d.personas || []);
      })
      .catch((e) => console.error("[Selector] personas ERR:", e));
    fetch(`${API_URL}/api/skills-library`)
      .then((r) => r.json())
      .then((d) => {
        console.log("[Selector] skills:", Object.keys(d.by_category || {}).length, "categories");
        setSkillsByCategory(d.by_category || {});
      })
      .catch((e) => console.error("[Selector] skills ERR:", e));
  }, []);

  const currentProjectType = projectTypes.find((pt) => pt.id === selectedProjectType);
  const currentPersona = personas.find((p) => p.id === selectedPersona);
  const mandatoryStack = new Set(currentProjectType?.mandatory_stack || []);
  const requiredSet = new Set(currentPersona?.required_skills || []);
  const recommendedSet = new Set(currentPersona?.recommended_skills || []);

  const prevPersonaRef = useRef(selectedPersona);
  const prevProjectTypeRef = useRef(selectedProjectType);

  useEffect(() => {
    const personaChanged = prevPersonaRef.current !== selectedPersona;
    const projectChanged = prevProjectTypeRef.current !== selectedProjectType;
    if ((personaChanged || projectChanged) && currentPersona) {
      const auto = new Set<string>();
      // Mandatory from project type
      if (currentProjectType) {
        currentProjectType.mandatory_stack.forEach((s) => auto.add(s));
      }
      // Required from persona
      currentPersona.required_skills.forEach((s) => auto.add(s));
      // Recommended from persona
      currentPersona.recommended_skills.forEach((s) => auto.add(s));
      // Keep user's extras
      selectedSkills.forEach((s) => auto.add(s));
      setSelectedSkills(auto);
      prevPersonaRef.current = selectedPersona;
      prevProjectTypeRef.current = selectedProjectType;
    }
  }, [selectedPersona, selectedProjectType, currentPersona, currentProjectType]);

  const toggleSkill = (id: string) => {
    if (requiredSet.has(id) || mandatoryStack.has(id)) return;
    setSelectedSkills((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const apply = () => {
    onApply(selectedProjectType, selectedPersona, Array.from(selectedSkills));
  };

  const filterSkill = (s: SkillInfo) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return s.name.toLowerCase().includes(q) || s.description.toLowerCase().includes(q);
  };

  const totalSkills = Object.values(skillsByCategory).flat().length;

  if (projectTypes.length === 0 || personas.length === 0) {
    return (
      <div className="p-8 text-center">
        <p className="text-sm text-[var(--color-text-muted)]">Loading...</p>
        <p className="mt-2 text-xs opacity-60">
          project_types: {projectTypes.length} | personas: {personas.length} | skills: {Object.keys(skillsByCategory).length}
        </p>
        <p className="mt-2 text-xs opacity-60">
          If stuck: restart `python server.py` and hard refresh browser
        </p>
      </div>
    );
  }

  return (
    <div className="p-4">
      {/* Info do Project Type atual (ja selecionado no header) */}
      {currentProjectType && currentProjectType.id !== "custom" && (
        <div className="mb-4 flex items-center gap-2 rounded-lg border border-amber-500/30 bg-amber-500/5 p-2.5">
          <Scroll className="h-4 w-4 shrink-0 text-amber-400" />
          <div className="flex-1 text-xs">
            <span className="font-semibold text-white">Project: {currentProjectType.name}</span>
            <span className="ml-2 text-[var(--color-text-muted)]">
              ({currentProjectType.mandatory_stack.length} mandatory skills from constitution)
            </span>
          </div>
          <button
            onClick={() => setShowConstitution(!showConstitution)}
            className="rounded px-2 py-0.5 text-[10px] text-amber-400 hover:bg-amber-500/10"
          >
            {showConstitution ? "Hide" : "View"} Constitution
          </button>
        </div>
      )}
      {showConstitution && currentProjectType && currentProjectType.constitution && (
        <div className="mb-4 max-h-48 overflow-y-auto rounded-lg border border-amber-500/30 bg-amber-500/5 p-3">
          <pre className="whitespace-pre-wrap text-[10px] leading-relaxed text-[var(--color-text-muted)]">
            {currentProjectType.constitution}
          </pre>
        </div>
      )}

      {/* STEP 1: PERSONA */}
      <div className="mb-5">
        <h3 className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
          <span className="flex h-4 w-4 items-center justify-center rounded-full bg-indigo-500 text-[9px] text-white">1</span>
          Persona (hover for directives)
        </h3>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
          {personas.map((p) => {
            const Icon = ICON_MAP[p.icon] || Bot;
            const active = p.id === selectedPersona;
            return (
              <div
                key={p.id}
                className="relative"
                onMouseEnter={() => setHoveredPersona(p.id)}
                onMouseLeave={() => setHoveredPersona(null)}
              >
                <button
                  onClick={() => setSelectedPersona(p.id)}
                  className={`relative flex w-full items-center gap-2 rounded-lg border p-2.5 text-left transition-all ${
                    active
                      ? "border-2 bg-[var(--color-surface-2)]"
                      : "border-[var(--color-border)] bg-[var(--color-surface)] hover:bg-[var(--color-surface-2)]"
                  }`}
                  style={{ borderColor: active ? p.color : undefined }}
                >
                  {active && (
                    <div className="absolute right-1.5 top-1.5 flex h-4 w-4 items-center justify-center rounded-full" style={{ backgroundColor: p.color }}>
                      <Check className="h-2.5 w-2.5 text-white" />
                    </div>
                  )}
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg" style={{ backgroundColor: `${p.color}20`, color: p.color }}>
                    <Icon className="h-4 w-4" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <h4 className="text-xs font-semibold text-white">{p.name}</h4>
                    <p className="truncate text-[10px] text-[var(--color-text-muted)]">{p.description}</p>
                  </div>
                </button>
                {hoveredPersona === p.id && <DirectivesTooltip persona={p} />}
              </div>
            );
          })}
        </div>
      </div>

      {/* STEP 3: SKILLS */}
      <div className="mb-4">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
            <span className="flex h-4 w-4 items-center justify-center rounded-full bg-indigo-500 text-[9px] text-white">2</span>
            Extra Skills
            <span className="rounded-full bg-indigo-500/20 px-2 py-0.5 text-[10px] text-indigo-400">
              {selectedSkills.size}/{totalSkills}
            </span>
            <span className="flex items-center gap-1 text-[10px] normal-case text-amber-400">
              <Lock className="h-2.5 w-2.5" /> locked
            </span>
            <span className="flex items-center gap-1 text-[10px] normal-case text-violet-400">
              <Sparkles className="h-2.5 w-2.5" /> recommended
            </span>
          </h3>
          <div className="relative">
            <Search className="absolute left-2 top-1.5 h-3 w-3 text-[var(--color-text-muted)]" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search skill..."
              className="w-48 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] py-1 pl-7 pr-2 text-xs text-white outline-none focus:border-indigo-500/40"
            />
          </div>
        </div>

        <div className="space-y-3">
          {Object.keys(skillsByCategory).sort().map((cat) => {
            const items = skillsByCategory[cat].filter(filterSkill);
            if (items.length === 0) return null;
            const catColor = CATEGORY_COLORS[cat] || "#6366f1";
            return (
              <div key={cat}>
                <div className="mb-1.5 flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full" style={{ backgroundColor: catColor }} />
                  <span className="text-[11px] font-semibold text-white">
                    {CATEGORY_LABELS[cat] || cat}
                  </span>
                  <span className="text-[10px] text-[var(--color-text-muted)]">({items.length})</span>
                </div>
                <div className="grid grid-cols-2 gap-1.5 sm:grid-cols-3 md:grid-cols-4">
                  {items.map((s) => {
                    const checked = selectedSkills.has(s.id);
                    const isMandatory = mandatoryStack.has(s.id);
                    const isRequired = requiredSet.has(s.id);
                    const isLocked = isMandatory || isRequired;
                    const isRecommended = recommendedSet.has(s.id);
                    const lockReason = isMandatory
                      ? "Required by project type"
                      : isRequired
                      ? "Required by this persona"
                      : isRecommended
                      ? "Recommended"
                      : "";
                    return (
                      <button
                        key={s.id}
                        onClick={() => toggleSkill(s.id)}
                        disabled={isLocked}
                        title={lockReason}
                        className={`group flex items-center gap-2 rounded-lg border px-2.5 py-1.5 text-left transition-all ${
                          isLocked
                            ? "cursor-not-allowed border-amber-500/40 bg-amber-500/10"
                            : checked
                            ? "border-indigo-500/60 bg-indigo-500/10"
                            : isRecommended
                            ? "border-violet-500/30 bg-[var(--color-surface)] hover:bg-[var(--color-surface-2)]"
                            : "border-[var(--color-border)] bg-[var(--color-surface)] hover:bg-[var(--color-surface-2)]"
                        }`}
                      >
                        <div
                          className={`flex h-4 w-4 shrink-0 items-center justify-center rounded border transition-colors ${
                            isLocked
                              ? "border-amber-400 bg-amber-500"
                              : checked
                              ? "border-indigo-400 bg-indigo-500"
                              : "border-[var(--color-border)]"
                          }`}
                        >
                          {isLocked ? (
                            <Lock className="h-2.5 w-2.5 text-white" />
                          ) : checked ? (
                            <Check className="h-3 w-3 text-white" />
                          ) : null}
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="flex items-center gap-1 text-[11px] font-medium text-white">
                            {s.name}
                            {isRecommended && !isLocked && (
                              <Sparkles className="h-2.5 w-2.5 text-violet-400" />
                            )}
                          </p>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Apply */}
      <div className="sticky bottom-0 flex items-center justify-between rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-3">
        <div className="text-xs text-[var(--color-text-muted)]">
          <span className="font-medium text-white">
            {currentProjectType?.name}
          </span>
          <span className="mx-2">→</span>
          <span className="font-medium text-white">{currentPersona?.name}</span>
          {selectedSkills.size > 0 && <span className="ml-2">+ {selectedSkills.size} skills</span>}
        </div>
        <button
          onClick={apply}
          className="flex items-center gap-2 rounded-lg bg-indigo-500 px-4 py-2 text-xs font-medium text-white transition-colors hover:bg-indigo-600"
        >
          <Zap className="h-3.5 w-3.5" />
          Apply
        </button>
      </div>
    </div>
  );
}
