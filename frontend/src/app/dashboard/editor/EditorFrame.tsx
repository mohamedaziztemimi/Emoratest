"use client";

import { useEffect, useRef, useState, useCallback, forwardRef } from "react";

// ── Types ────────────────────────────────────────────────────────

export type EditorMode = "select" | "preview";

export type ModificationType = "text" | "style" | "visibility" | "html";

export interface CSSProperties {
  [key: string]: string | number;
}

export interface SelectedElement {
  selector: string;
  tagName: string;
  innerText?: string;
  innerHTML?: string;
  styles: CSSProperties;
  rect: DOMRect;
}

export interface Modification {
  selector: string;
  type: ModificationType;
  value: string;
  originalValue: string;
  timestamp: number;
}

export interface EditorFrameProps {
  url: string;
  mode: EditorMode;
  onElementSelect: (el: SelectedElement) => void;
  modifications: Modification[];
  onApplyModifications: (mods: Modification[]) => void;
}

// ── Constants ────────────────────────────────────────────────────────

const DEVICE_SIZES = {
  mobile: { width: 375, height: 812, name: "Mobile (375px)" },
  tablet: { width: 768, height: 1024, name: "Tablet (768px)" },
  desktop: { width: 1280, height: 800, name: "Desktop (1280px)" },
} as const;

type DeviceKey = keyof typeof DEVICE_SIZES;

const INJECTED_SCRIPT = `
(function() {
  const overlay = document.createElement('div');
  overlay.id = 'emoratest-editor-overlay';
  overlay.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; bottom: 0; pointer-events: none; z-index: 9999;';
  document.body.appendChild(overlay);

  window.EmoraTestEditor = {
    highlightElement: function(selector) {
      document.querySelectorAll(selector).forEach(el => {
        el.style.outline = '2px solid #3B82F6';
        el.style.outlineOffset = '-2px';
        el.style.cursor = 'pointer';
      });
    },
    removeHighlight: function() {
      document.querySelectorAll('[data-emoratest-highlighted]').forEach(el => {
        el.style.outline = el.getAttribute('data-original-outline') || '';
        el.style.cursor = '';
        el.removeAttribute('data-emoratest-highlighted');
      });
    },
    applyStyles: function(selector, styles) {
      document.querySelectorAll(selector).forEach(el => {
        Object.entries(styles).forEach(([prop, value]) => {
          if (prop.startsWith('--')) {
            el.style.setProperty(prop, String(value));
          } else {
            el.style[prop as any] = String(value);
          }
        });
      });
    },
    applyVisibility: function(selector, visible) {
      document.querySelectorAll(selector).forEach(el => {
        el.style.display = visible ? '' : 'none';
      });
    },
    applyContent: function(selector, type, value) {
      document.querySelectorAll(selector).forEach(el => {
        if (type === 'text') {
          el.innerText = value;
        } else if (type === 'html') {
          el.innerHTML = value;
        }
      });
    }
  };
})();
`;

// ── EditorFrame Component ────────────────────────────────────────────

interface EditorFrameInternal {
  sendMessage: (message: any) => void;
}

const EditorFrameInternal = forwardRef<HTMLIFrameElement, EditorFrameInternal & EditorFrameProps>(
  ({ url, mode, onElementSelect, modifications, onApplyModifications }, ref) => {
    const [iframeLoaded, setIframeLoaded] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [currentDevice, setCurrentDevice] = useState<DeviceKey>("desktop");
    const iframeRef = useRef<HTMLIFrameElement>(null);

    const sendMessage = useCallback((message: any) => {
      if (iframeRef.current?.contentWindow) {
        iframeRef.current.contentWindow.postMessage(message, '*');
      }
    }, []);

    useEffect(() => {
      sendMessage({ type: 'SET_MODE', mode });
    }, [mode, sendMessage]);

    useEffect(() => {
      const handleMessage = (event: MessageEvent) => {
        if (event.source !== iframeRef.current?.contentWindow) return;

        const { type, data } = event.data;
        if (type === 'ELEMENT_SELECTED' && data) {
          onElementSelect(data);
        } else if (type === 'MODIFICATIONS_APPLIED' && data) {
          onApplyModifications(data);
        }
      };

      window.addEventListener('message', handleMessage);
      return () => window.removeEventListener('message', handleMessage);
    }, [onElementSelect, onApplyModifications]);

    // Inject script when iframe loads
    useEffect(() => {
      if (iframeLoaded && iframeRef.current?.contentWindow) {
        const script = document.createElement('script');
        script.textContent = INJECTED_SCRIPT;
        iframeRef.current.contentDocument?.head.appendChild(script);

        // Add click handler for element selection
        const clickHandlerScript = document.createElement('script');
        clickHandlerScript.textContent = `
          document.body.addEventListener('click', function(e) {
            if (window.parent.postMessage && '${mode}' === 'select') {
              const target = e.target;
              const computedStyle = window.getComputedStyle(target);
              const rect = target.getBoundingClientRect();
              window.parent.postMessage({
                type: 'ELEMENT_SELECTED',
                data: {
                  selector: generateSelector(target),
                  tagName: target.tagName.toLowerCase(),
                  innerText: target.innerText?.substring(0, 200),
                  innerHTML: target.innerHTML?.substring(0, 500),
                  styles: {
                    'font-size': computedStyle.fontSize,
                    'font-weight': computedStyle.fontWeight,
                    'color': computedStyle.color,
                    'padding': computedStyle.padding,
                    'border-radius': computedStyle.borderRadius,
                    'text-align': computedStyle.textAlign,
                  },
                  rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height }
                }
              }, '*');
              e.preventDefault();
            }
          }, true);

          function generateSelector(el) {
            if (el.id) return '#' + el.id;
            if (el.className) return '.' + el.className.split(' ').join('.');
            return el.tagName.toLowerCase();
          }
        `;
        iframeRef.current.contentDocument?.body.appendChild(clickHandlerScript);
      }
    }, [iframeLoaded, mode]);

    const handleLoad = () => {
      setIframeLoaded(true);
      setError(null);
    };

    const handleError = () => {
      setError("Failed to load page. This site may block iframe embedding.");
    };

    const handleReload = useCallback(() => {
      setIframeLoaded(false);
      setError(null);
    }, []);

    const handleDeviceChange = useCallback((device: DeviceKey) => {
      setCurrentDevice(device);
      setIframeLoaded(false);
    }, []);

    const deviceSize = DEVICE_SIZES[currentDevice];

    return (
      <div className="relative flex-1 bg-[hsl(var(--muted))] rounded-lg overflow-hidden border border-[hsl(var(--border))] flex items-center justify-center">
        {error && (
          <div className="absolute inset-0 bg-red-50/90 flex items-center justify-center z-20">
            <div className="text-center p-8">
              <svg className="w-12 h-12 mx-auto mb-4 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h-4m4 4h4m-4-4h4m0 4v-6a3 3 0 00-3 0m0 0 3 0 0 003h3m-3 3 0 0 003" />
              </svg>
              <h3 className="text-lg font-bold text-red-900">Iframe Blocked</h3>
              <p className="text-red-800 mt-2">{error}</p>
              <p className="text-sm text-red-700 mt-4">
                This website may block iframe embedding. Try using a proxy or check CORS settings.
              </p>
            </div>
          </div>
        )}

        {!error && (
          <>
            {/* Device Size Toggle */}
            <div className="absolute top-4 right-4 flex gap-2 bg-white/90 rounded-lg shadow-lg border border-[hsl(var(--border))] z-10">
              <button
                onClick={handleReload}
                className="p-2 hover:bg-[hsl(var(--muted))] rounded-md transition-colors"
                title="Reload Page"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </button>

              {(Object.keys(DEVICE_SIZES) as DeviceKey[]).map((key) => (
                <button
                  key={key}
                  onClick={() => handleDeviceChange(key)}
                  className={`px-3 py-1 text-sm rounded-md transition-colors ${
                    currentDevice === key
                      ? "bg-[hsl(var(--primary))] text-white"
                      : "hover:bg-[hsl(var(--muted))]"
                  }`}
                  title={DEVICE_SIZES[key].name}
                >
                  {key === 'mobile' ? 'M' : key === 'tablet' ? 'T' : 'D'}
                </button>
              ))}
            </div>

            {/* Iframe Container */}
            <div
              style={{
                width: deviceSize.width + 'px',
                height: deviceSize.height + 'px',
                maxWidth: '100%',
                maxHeight: '100%',
              }}
            >
              <iframe
                ref={iframeRef}
                src={url}
                key={`${currentDevice}-${iframeLoaded}`} // Force reload on device change
                sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-modals"
                className="w-full h-full border-0 bg-white shadow-xl"
                onLoad={handleLoad}
                onError={handleError}
                title="Target Website"
              />
            </div>
          </>
        )}
      </div>
    );
  }
);

EditorFrameInternal.displayName = 'EditorFrameInternal';

export default EditorFrameInternal;
