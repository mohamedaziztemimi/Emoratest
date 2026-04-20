"use client";

import { useState, useCallback } from "react";

// ── Types ────────────────────────────────────────────────────────

import type { Modification, ModificationType, SelectedElement, CSSProperties } from "./EditorFrame";

export interface ElementInspectorProps {
  element: SelectedElement | null;
  onModify: (mod: Modification) => void;
  modifications: Modification[];
}

interface TabProps {
  label: string;
  active: boolean;
  onClick: () => void;
}

// ── Tab Component ────────────────────────────────────────────────

function Tab({ label, active, onClick }: TabProps) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
        active
          ? "bg-[hsl(var(--card))] text-[hsl(var(--foreground))] border-b-2 border-[hsl(var(--border))]"
          : "bg-transparent text-[hsl(var(--muted-foreground))] hover:bg-[hsl(var(--muted))]/50"
      }`}
    >
      {label}
    </button>
  );
}

// ── ElementInspector Component ───────────────────────────────────

export default function ElementInspector({
  element,
  onModify,
  modifications,
}: ElementInspectorProps) {
  const [activeTab, setActiveTab] = useState<"content" | "styles" | "visibility" | "advanced">("content");
  const [contentValue, setContentValue] = useState(element?.innerText || "");
  const [cssInput, setCssInput] = useState("");

  // Styles state
  const [fontSize, setFontSize] = useState(element?.styles?.["font-size"] || 16);
  const [fontWeight, setFontWeight] = useState(element?.styles?.["font-weight"] || "normal");
  const [color, setColor] = useState(element?.styles?.["color"] || "#000000");
  const [padding, setPadding] = useState(element?.styles?.["padding"] || "0");
  const [borderRadius, setBorderRadius] = useState(element?.styles?.["border-radius"] || "0");
  const [textAlign, setTextAlign] = useState(element?.styles?.["text-align"] || "left");

  // Visibility state
  const [visible, setVisible] = useState(true);
  const [opacity, setOpacity] = useState(100);

  // Changes badge count
  const changesCount = modifications.filter(
    (m) => m.selector === element?.selector
  ).length;

  // Handle content change
  const handleContentChange = useCallback((value: string) => {
    setContentValue(value);
    if (element) {
      onModify({
        selector: element.selector,
        type: "text",
        value,
        originalValue: element.innerText || "",
        timestamp: Date.now(),
      });
    }
  }, [element, onModify]);

  // Handle style change
  const handleStyleChange = useCallback((property: string, value: string) => {
    onModify({
      selector: element.selector,
      type: "style",
      value: `${property}: ${value}`,
      originalValue: "",
      timestamp: Date.now(),
    });
  }, [element, onModify]);

  // Handle CSS input
  const handleCssInputChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setCssInput(e.target.value);
  }, []);

  const handleCssApply = useCallback(() => {
    if (!element) return;

    try {
      // Parse CSS (simple parser)
      const cssProps: CSSProperties = {};
      cssInput.split(";").forEach((rule) => {
        const [prop, value] = rule.split(":").map((s) => s.trim());
        if (prop && value) {
          cssProps[prop.trim()] = value.trim();
        }
      });

      // Apply each property
      Object.entries(cssProps).forEach(([prop, value]) => {
        onModify({
          selector: element.selector,
          type: "style",
          value: `${prop}: ${value}`,
          originalValue: "",
          timestamp: Date.now(),
        });
      });
    } catch (err) {
      console.error("Invalid CSS:", err);
    }
  }, [element, cssInput, onModify]);

  // Handle visibility toggle
  const handleVisibilityToggle = useCallback(() => {
    setVisible(!visible);
    onModify({
      selector: element.selector,
      type: "visibility",
      value: visible ? "visible" : "hidden",
      originalValue: visible ? "visible" : "hidden",
      timestamp: Date.now(),
    });
  }, [element, visible, onModify]);

  // Handle opacity slider
  const handleOpacityChange = useCallback((value: number) => {
    setOpacity(value);
    onModify({
      selector: element.selector,
      type: "style",
      value: `opacity: ${value / 100}`,
      originalValue: `${opacity / 100}`,
      timestamp: Date.now(),
    });
  }, [element, onModify]);

  // Handle undo (last change for this element)
  const handleUndo = useCallback(() => {
    const elementMods = modifications.filter((m) => m.selector === element?.selector);
    if (elementMods.length > 0) {
      const lastMod = elementMods[elementMods.length - 1];
      onModify({
        selector: element.selector,
        type: lastMod.type,
        value: lastMod.originalValue,
        timestamp: Date.now(),
      });
    }
  }, [element, modifications, onModify]);

  if (!element) {
    return (
      <div className="flex flex-col h-full items-center justify-center p-8 text-[hsl(var(--muted-foreground))]">
        <svg className="w-16 h-16 mx-auto mb-4 text-[hsl(var(--muted-foreground))]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 00-3 0m-3 0 3 3 0 0 003h3m-3-3 0 003-3 0 0 012m0 3-3 0 3-3 0 0 003h3M3 3 0 3 3m0 0 3 3-0 003M3 3 0 0 012m0 3-3 0 0 003M3 3 0 0 012M9 3 3 0 0 0000.012m0-3 3 0 0 003M3 3 0 0 012m0 3 3 0 0 003M3 3 0 0 003" />
        </svg>
        <h3 className="text-lg font-semibold">No Element Selected</h3>
        <p className="text-sm text-[hsl(var(--muted-foreground))]">
          Click on an element in the editor to view and edit its properties.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-[hsl(var(--card))] overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-[hsl(var(--border))]">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-lg font-bold text-[hsl(var(--foreground))]">Element Inspector</h2>
          {changesCount > 0 && (
            <span className="bg-[hsl(var(--primary))] text-white text-xs font-semibold px-2 py-1 rounded-full">
              {changesCount} change{changesCount !== 1 ? "s" : ""}
            </span>
          )}
        </div>
        <div className="text-xs text-[hsl(var(--muted-foreground))] font-mono">
          {element?.selector || "No selector"}
        </div>
      </div>

      {/* Undo Button */}
      {changesCount > 0 && (
        <div className="p-2 border-b border-[hsl(var(--border))]">
          <button
            onClick={handleUndo}
            className="w-full px-4 py-2 bg-[hsl(var(--muted))] text-[hsl(var(--foreground))] hover:bg-[hsl(var(--accent))] rounded-lg transition-colors flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h6a3 3 0 003 3 0v-6a3 3 0 002 3 3 0 002-3 3 0 002.5l2 2 2a4 4 0 003 3 3 0 012M6 11a4 4 0 000 3 3 3 0 0-002.5 2 2 2z" />
            </svg>
            <span className="text-sm">Undo last change</span>
          </button>
        </div>
      )}

      {/* Content Tab */}
      {activeTab === "content" && (
        <div className="p-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-[hsl(var(--foreground))] mb-2">
              Inner Text
            </label>
            <textarea
              value={contentValue}
              onChange={handleContentChange}
              className="w-full h-40 px-3 py-2 border border-[hsl(var(--border))] rounded-lg bg-[hsl(var(--background))] text-[hsl(var(--foreground))] resize-none"
              placeholder="Enter text content..."
            />
            <p className="text-xs text-[hsl(var(--muted-foreground))] mt-1">
              Character count: {contentValue.length}
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-[hsl(var(--foreground))] mb-2">
              Inner HTML
            </label>
            <textarea
              value={element?.innerHTML || ""}
              onChange={(e) => handleContentChange(e.target.value)}
              className="w-full h-40 px-3 py-2 border border-[hsl(var(--border))] rounded-lg bg-[hsl(var(--background))] text-[hsl(var(--foreground))] resize-none"
              placeholder="Enter HTML content..."
            />
          </div>
        </div>
      )}

      {/* Styles Tab */}
      {activeTab === "styles" && (
        <div className="p-4 space-y-6">
          {/* Font Size */}
          <div>
            <label className="block text-sm font-medium text-[hsl(var(--foreground))] mb-2">
              Font Size (px)
            </label>
            <input
              type="range"
              min="8"
              max="72"
              value={fontSize}
              onChange={(e) => handleStyleChange("font-size", e.target.value)}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-[hsl(var(--muted-foreground))]">
              <span>8</span>
              <span>{fontSize}</span>
              <span>72</span>
            </div>
          </div>

          {/* Font Weight */}
          <div>
            <label className="block text-sm font-medium text-[hsl(var(--foreground))] mb-2">
              Font Weight
            </label>
            <select
              value={fontWeight}
              onChange={(e) => handleStyleChange("font-weight", e.target.value)}
              className="w-full px-3 py-2 border border-[hsl(var(--border))] rounded-lg bg-[hsl(var(--background))] text-[hsl(var(--foreground))]"
            >
              <option value="normal">Normal</option>
              <option value="bold">Bold</option>
              <option value="600">Semi-Bold</option>
            </select>
          </div>

          {/* Text Color */}
          <div>
            <label className="block text-sm font-medium text-[hsl(var(--foreground))] mb-2">
              Text Color
            </label>
            <div className="flex items-center gap-2">
              <input
                type="color"
                value={color}
                onChange={(e) => handleStyleChange("color", e.target.value)}
                className="w-12 h-10 rounded border-0 cursor-pointer"
              />
              <input
                type="text"
                value={color}
                onChange={(e) => handleStyleChange("color", e.target.value)}
                className="flex-1 px-2 py-1 border border-[hsl(var(--border))] rounded bg-[hsl(var(--background))] text-[hsl(var(--foreground))] text-xs"
                placeholder="#000000"
              />
            </div>
          </div>

          {/* Padding */}
          <div>
            <label className="block text-sm font-medium text-[hsl(var(--foreground))] mb-2">
              Padding (px)
            </label>
            <div className="flex gap-2">
              {[0, 4, 8, 12, 16, 24, 32].map((val) => (
                <button
                  key={val}
                  onClick={() => handleStyleChange("padding", val.toString())}
                  className={`w-10 h-10 rounded border transition-colors ${
                    padding === val
                      ? "bg-[hsl(var(--primary))] border-[hsl(var(--primary))] text-white"
                      : "bg-[hsl(var(--background))] border-[hsl(var(--border))] hover:border-[hsl(var(--primary))]"
                  }`}
                  title={`${val}px`}
                >
                  {val}
                </button>
              ))}
            </div>
            <input
              type="number"
              min="0"
              max="64"
              value={padding}
              onChange={(e) => handleStyleChange("padding", e.target.value)}
              className="w-20 px-2 py-1 border border-[hsl(var(--border))] rounded-lg bg-[hsl(var(--background))] text-[hsl(var(--foreground))] text-sm"
            />
          </div>

          {/* Border Radius */}
          <div>
            <label className="block text-sm font-medium text-[hsl(var(--foreground))] mb-2">
              Border Radius (px)
            </label>
            <div className="flex gap-2">
              {[0, 4, 8, 12, 16, 24].map((val) => (
                <button
                  key={val}
                  onClick={() => handleStyleChange("border-radius", val.toString())}
                  className={`w-10 h-10 rounded-full transition-colors ${
                    borderRadius === val
                      ? "bg-[hsl(var(--primary))] border-[hsl(var(--primary))]"
                      : "bg-[hsl(var(--background))] border-[hsl(var(--border))] hover:border-[hsl(var(--primary))]"
                  }`}
                  style={{ borderRadius: `${val}px` }}
                />
              ))}
            </div>
            <input
              type="number"
              min="0"
              max="50"
              value={borderRadius}
              onChange={(e) => handleStyleChange("border-radius", e.target.value)}
              className="w-20 px-2 py-1 border border-[hsl(var(--border))] rounded-lg bg-[hsl(var(--background))] text-[hsl(var(--foreground))] text-sm"
            />
          </div>

          {/* Text Align */}
          <div>
            <label className="block text-sm font-medium text-[hsl(var(--foreground))] mb-2">
              Text Align
            </label>
            <select
              value={textAlign}
              onChange={(e) => handleStyleChange("text-align", e.target.value)}
              className="w-full px-3 py-2 border border-[hsl(var(--border))] rounded-lg bg-[hsl(var(--background))] text-[hsl(var(--foreground))]"
            >
              <option value="left">Left</option>
              <option value="center">Center</option>
              <option value="right">Right</option>
            </select>
          </div>
        </div>
      )}

      {/* Visibility Tab */}
      {activeTab === "visibility" && (
        <div className="p-4 space-y-6">
          {/* Show/Hide Toggle */}
          <div className="flex items-center justify-between mb-6">
            <label className="text-sm font-medium text-[hsl(var(--foreground))]">
              Visibility
            </label>
            <button
              onClick={handleVisibilityToggle}
              className={`px-4 py-2 rounded-lg transition-colors ${
                visible
                  ? "bg-[hsl(var(--primary))] text-white"
                  : "bg-[hsl(var(--muted))] text-[hsl(var(--foreground))] hover:bg-[hsl(var(--accent))]"
              }`}
            >
              {visible ? "Visible" : "Hidden"}
            </button>
          </div>

          {/* Opacity Slider */}
          <div>
            <label className="block text-sm font-medium text-[hsl(var(--foreground))] mb-2">
              Opacity
            </label>
            <input
              type="range"
              min="0"
              max="100"
              value={opacity}
              onChange={(e) => handleOpacityChange(e.target.value)}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-[hsl(var(--muted-foreground))]">
              <span>{opacity}%</span>
            </div>
          </div>
        </div>
      )}

      {/* Advanced Tab */}
      {activeTab === "advanced" && (
        <div className="p-4 space-y-4">
          <label className="block text-sm font-medium text-[hsl(var(--foreground))] mb-2">
            Raw CSS
          </label>
          <textarea
            value={cssInput}
            onChange={handleCssInputChange}
            className="w-full h-40 px-3 py-2 border border-[hsl(var(--border))] rounded-lg bg-[hsl(var(--background))] font-mono text-xs"
            placeholder="selector { property: value; }"
          />
          <button
            onClick={handleCssApply}
            className="w-full mt-2 px-4 py-2 bg-[hsl(var(--primary))] text-white rounded-lg hover:bg-[hsl(var(--primary-dark))] transition-colors"
            disabled={!cssInput.trim()}
          >
            Apply CSS
          </button>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="flex border-t border-[hsl(var(--border))]">
        <Tab label="Content" active={activeTab === "content"} onClick={() => setActiveTab("content")} />
        <Tab label="Styles" active={activeTab === "styles"} onClick={() => setActiveTab("styles")} />
        <Tab label="Visibility" active={activeTab === "visibility"} onClick={() => setActiveTab("visibility")} />
        <Tab label="Advanced" active={activeTab === "advanced"} onClick={() => setActiveTab("advanced")} />
      </div>
    </div>
  );
}
