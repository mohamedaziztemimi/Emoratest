"use client";

import { useState, useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";

// ── Components ────────────────────────────────────────────────────────

import EditorFrame, {
  EditorMode,
  Modification,
  SelectedElement,
} from "./EditorFrame";
import ElementInspector from "./ElementInspector";

// ── Types ────────────────────────────────────────────────────────

interface ExperimentVariant {
  id: string;
  name: string;
  modifications: Modification[];
  trafficAllocation: number;
}

// ── Page Component ────────────────────────────────────────────────

export default function EditorPage() {
  const router = useRouter();

  // Editor state
  const [mode, setMode] = useState<EditorMode>("select");
  const [selectedElement, setSelectedElement] = useState<SelectedElement | null>(null);
  const [modifications, setModifications] = useState<Modification[]>([]);
  const [url, setUrl] = useState("https://example.com");
  const [urlInput, setUrlInput] = useState("https://example.com");

  // Experiment state
  const [experimentName, setExperimentName] = useState("Untitled Experiment");
  const [activeVariant, setActiveVariant] = useState(0);
  const [variants, setVariants] = useState<ExperimentVariant[]>([
    { id: "control", name: "Control", modifications: [], trafficAllocation: 50 },
    { id: "variant-1", name: "Variant 1", modifications: [], trafficAllocation: 50 },
  ]);
  const [showPublishDialog, setShowPublishDialog] = useState(false);
  const [saving, setSaving] = useState(false);

  // Load URL
  const handleLoadUrl = useCallback(() => {
    if (urlInput.trim()) {
      setUrl(urlInput);
      setModifications([]);
      setSelectedElement(null);
    }
  }, [urlInput]);

  // Handle element selection
  const handleElementSelect = useCallback((el: SelectedElement) => {
    setSelectedElement(el);
  }, []);

  // Handle modification
  const handleModify = useCallback((mod: Modification) => {
    setModifications((prev) => [...prev, mod]);

    // Also update active variant's modifications
    setVariants((prev) => {
      const updated = [...prev];
      updated[activeVariant].modifications = [...updated[activeVariant].modifications, mod];
      return updated;
    });
  }, [activeVariant]);

  // Apply modifications from a variant
  const handleApplyModifications = useCallback((mods: Modification[]) => {
    setModifications(mods);
  }, []);

  // Switch variant
  const handleSwitchVariant = useCallback((index: number) => {
    setActiveVariant(index);
    setModifications(variants[index].modifications);
    setSelectedElement(null);
  }, [variants]);

  // Add new variant
  const handleAddVariant = useCallback(() => {
    const newId = `variant-${variants.length + 1}`;
    setVariants((prev) => [
      ...prev,
      { id: newId, name: `Variant ${variants.length + 1}`, modifications: [], trafficAllocation: 0 },
    ]);
  }, [variants.length]);

  // Remove variant
  const handleRemoveVariant = useCallback((index: number) => {
    if (variants.length <= 2) return; // Keep at least 2 variants
    setVariants((prev) => prev.filter((_, i) => i !== index));
    if (activeVariant >= variants.length - 1) {
      setActiveVariant(variants.length - 2);
    }
  }, [variants.length, activeVariant]);

  // Update variant name
  const handleUpdateVariantName = useCallback((index: number, name: string) => {
    setVariants((prev) => {
      const updated = [...prev];
      updated[index].name = name;
      return updated;
    });
  }, []);

  // Update traffic allocation
  const handleUpdateTraffic = useCallback((index: number, value: number) => {
    setVariants((prev) => {
      const updated = [...prev];
      updated[index].trafficAllocation = value;
      return updated;
    });
  }, []);

  // Clear modifications
  const handleClearModifications = useCallback(() => {
    setModifications([]);
    setVariants((prev) => {
      const updated = [...prev];
      updated[activeVariant].modifications = [];
      return updated;
    });
  }, [activeVariant]);

  // Publish experiment
  const handlePublish = useCallback(async () => {
    setSaving(true);
    try {
      // Feature pending: Call API to save and publish experiment
      // Backend endpoint: POST /api/v1/experiments/{id}/publish
      await new Promise((resolve) => setTimeout(resolve, 1000));
      setShowPublishDialog(false);
      router.push("/dashboard/experiments");
    } catch (err) {
      console.error("Failed to publish experiment:", err);
    } finally {
      setSaving(false);
    }
  }, [router]);

  // Calculate total modifications count
  const totalModifications = useMemo(() => {
    return variants.reduce((sum, v) => sum + v.modifications.length, 0);
  }, [variants]);

  // Calculate traffic allocation total
  const totalTraffic = useMemo(() => {
    return variants.reduce((sum, v) => sum + v.trafficAllocation, 0);
  }, [variants]);

  return (
    <div className="flex flex-col h-screen bg-[hsl(var(--background))]">
      {/* Header */}
      <header className="px-6 py-3 border-b border-[hsl(var(--border))] bg-[hsl(var(--card))] flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.back()}
            className="p-2 hover:bg-[hsl(var(--muted))] rounded-md transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>

          <div>
            <input
              type="text"
              value={experimentName}
              onChange={(e) => setExperimentName(e.target.value)}
              className="text-lg font-bold bg-transparent border-none focus:outline-none focus:ring-2 focus:ring-[hsl(var(--primary))] rounded px-2 -ml-2"
            />
            <div className="text-xs text-[hsl(var(--muted-foreground))]">
              {totalModifications} modification{totalModifications !== 1 ? "s" : ""}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Mode Toggle */}
          <div className="flex bg-[hsl(var(--muted))] rounded-lg p-1">
            <button
              onClick={() => setMode("select")}
              className={`px-4 py-2 rounded-md text-sm transition-colors ${
                mode === "select"
                  ? "bg-[hsl(var(--primary))] text-white"
                  : "bg-transparent text-[hsl(var(--foreground))]"
              }`}
            >
              Select
            </button>
            <button
              onClick={() => setMode("preview")}
              className={`px-4 py-2 rounded-md text-sm transition-colors ${
                mode === "preview"
                  ? "bg-[hsl(var(--primary))] text-white"
                  : "bg-transparent text-[hsl(var(--foreground))]"
              }`}
            >
              Preview
            </button>
          </div>

          {/* Actions */}
          <button
            onClick={handleClearModifications}
            className="px-4 py-2 text-sm border border-[hsl(var(--border))] rounded-lg hover:bg-[hsl(var(--muted))] transition-colors"
          >
            Clear Changes
          </button>
          <button
            onClick={() => setShowPublishDialog(true)}
            className="px-4 py-2 text-sm bg-[hsl(var(--primary))] text-white rounded-lg hover:bg-[hsl(var(--primary-dark))] transition-colors"
          >
            Publish
          </button>
        </div>
      </header>

      {/* URL Input Bar */}
      <div className="px-6 py-3 border-b border-[hsl(var(--border))] bg-[hsl(var(--card))] flex items-center gap-4">
        <div className="flex-1 flex items-center gap-2">
          <svg className="w-5 h-5 text-[hsl(var(--muted-foreground))]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
          </svg>
          <input
            type="text"
            value={urlInput}
            onChange={(e) => setUrlInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleLoadUrl()}
            placeholder="https://yourwebsite.com"
            className="flex-1 px-3 py-2 border border-[hsl(var(--border))] rounded-lg bg-[hsl(var(--background))] text-[hsl(var(--foreground))] focus:outline-none focus:ring-2 focus:ring-[hsl(var(--primary))]"
          />
          <button
            onClick={handleLoadUrl}
            className="px-4 py-2 bg-[hsl(var(--primary))] text-white rounded-lg hover:bg-[hsl(var(--primary-dark))] transition-colors"
          >
            Load
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Variants */}
        <div className="w-64 bg-[hsl(var(--card))] border-r border-[hsl(var(--border))] flex flex-col">
          <div className="p-4 border-b border-[hsl(var(--border))]">
            <h2 className="text-sm font-semibold text-[hsl(var(--foreground))] mb-2">Variants</h2>
            <div className="text-xs text-[hsl(var(--muted-foreground))]">
              Traffic: {totalTraffic}% allocated
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-2 space-y-2">
            {variants.map((variant, index) => (
              <div
                key={variant.id}
                onClick={() => handleSwitchVariant(index)}
                className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                  activeVariant === index
                    ? "border-[hsl(var(--primary))] bg-[hsl(var(--primary))]/5"
                    : "border-[hsl(var(--border))] hover:border-[hsl(var(--border))]"
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <input
                    type="text"
                    value={variant.name}
                    onChange={(e) => handleUpdateVariantName(index, e.target.value)}
                    onClick={(e) => e.stopPropagation()}
                    className="text-sm font-medium bg-transparent border-none focus:outline-none focus:ring-1 focus:ring-[hsl(var(--primary))] rounded px-1 -ml-1"
                  />
                  {variants.length > 2 && index > 0 && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRemoveVariant(index);
                      }}
                      className="p-1 hover:bg-red-100 rounded text-[hsl(var(--muted-foreground))] hover:text-red-600"
                    >
                      <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  )}
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-[hsl(var(--muted-foreground))]">
                    {variant.modifications.length} change{variant.modifications.length !== 1 ? "s" : ""}
                  </span>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={variant.trafficAllocation}
                    onChange={(e) => handleUpdateTraffic(index, parseInt(e.target.value) || 0)}
                    onClick={(e) => e.stopPropagation()}
                    className="w-12 px-1 py-0.5 border border-[hsl(var(--border))] rounded bg-[hsl(var(--background))] text-center"
                  />
                </div>
              </div>
            ))}
          </div>

          <div className="p-2 border-t border-[hsl(var(--border))]">
            <button
              onClick={handleAddVariant}
              className="w-full px-3 py-2 text-sm border border-dashed border-[hsl(var(--border))] rounded-lg hover:border-[hsl(var(--primary))] hover:bg-[hsl(var(--primary))]/5 transition-colors flex items-center justify-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Add Variant
            </button>
          </div>
        </div>

        {/* Editor Frame */}
        <div className="flex-1 relative">
          <EditorFrame
            ref={null as any}
            url={url}
            mode={mode}
            onElementSelect={handleElementSelect}
            modifications={modifications}
            onApplyModifications={handleApplyModifications}
          />
        </div>

        {/* Right Panel - Element Inspector */}
        <div className="w-80 bg-[hsl(var(--card))] border-l border-[hsl(var(--border))] overflow-hidden">
          <ElementInspector
            element={selectedElement}
            onModify={handleModify}
            modifications={modifications}
          />
        </div>
      </div>

      {/* Publish Dialog */}
      {showPublishDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-[hsl(var(--card))] rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="p-6">
              <h2 className="text-xl font-bold text-[hsl(var(--foreground))] mb-4">
                Publish Experiment
              </h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-[hsl(var(--foreground))] mb-1">
                    Experiment Name
                  </label>
                  <input
                    type="text"
                    value={experimentName}
                    onChange={(e) => setExperimentName(e.target.value)}
                    className="w-full px-3 py-2 border border-[hsl(var(--border))] rounded-lg bg-[hsl(var(--background))] text-[hsl(var(--foreground))]"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-[hsl(var(--foreground))] mb-1">
                    Target URL
                  </label>
                  <input
                    type="text"
                    value={url}
                    readOnly
                    className="w-full px-3 py-2 border border-[hsl(var(--border))] rounded-lg bg-[hsl(var(--muted))] text-[hsl(var(--muted-foreground))]"
                  />
                </div>
                <div className="p-4 bg-[hsl(var(--muted))]/50 rounded-lg">
                  <div className="text-sm text-[hsl(var(--foreground))]">
                    <strong>{variants.length} variant{variants.length !== 1 ? "s" : ""}</strong> with{" "}
                    <strong>{totalModifications} change{totalModifications !== 1 ? "s" : ""}</strong>
                  </div>
                  <div className="text-xs text-[hsl(var(--muted-foreground))] mt-1">
                    Traffic allocation: {totalTraffic}%
                    {totalTraffic !== 100 && ` (missing ${100 - totalTraffic}%)`}
                  </div>
                </div>
              </div>
            </div>
            <div className="px-6 py-4 border-t border-[hsl(var(--border))] flex justify-end gap-3">
              <button
                onClick={() => setShowPublishDialog(false)}
                className="px-4 py-2 text-sm border border-[hsl(var(--border))] rounded-lg hover:bg-[hsl(var(--muted))] transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handlePublish}
                disabled={saving || totalTraffic !== 100}
                className="px-4 py-2 text-sm bg-[hsl(var(--primary))] text-white rounded-lg hover:bg-[hsl(var(--primary-dark))] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving ? "Publishing..." : "Publish Experiment"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
