interface DeleteModalProps {
  isOpen: boolean;
  title: string;
  description: string;
  itemName?: string;
  isLoading?: boolean;
  confirmLabel?: string;
  onCancel: () => void;
  onConfirm: () => void;
}

export function DeleteModal({
  isOpen,
  title,
  description,
  itemName,
  isLoading = false,
  confirmLabel = "Delete",
  onCancel,
  onConfirm,
}: DeleteModalProps) {
  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onCancel}
        style={{
          position: "fixed",
          inset: 0,
          background: "rgba(0, 0, 0, 0.4)",
          backdropFilter: "blur(4px)",
          zIndex: 50,
        }}
      />

      {/* Modal */}
      <div
        style={{
          position: "fixed",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          background: "white",
          borderRadius: "20px",
          padding: "32px",
          width: "440px",
          maxWidth: "calc(100vw - 48px)",
          zIndex: 51,
          boxShadow: "0 20px 60px rgba(0, 0, 0, 0.15)",
        }}
      >
        {/* Warning icon */}
        <div
          style={{
            width: "48px",
            height: "48px",
            borderRadius: "50%",
            background: "#FEF2F2",
            color: "#EF4444",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            margin: "0 auto 16px auto",
            fontSize: "24px",
            fontWeight: "700",
          }}
        >
          !
        </div>

        {/* Title */}
        <h3
          style={{
            fontSize: "20px",
            fontWeight: "700",
            color: "#111318",
            textAlign: "center",
            margin: "0 0 8px 0",
          }}
        >
          {title}
        </h3>

        {/* Description */}
        <p
          style={{
            fontSize: "14px",
            color: "#6B7280",
            textAlign: "center",
            lineHeight: "1.6",
            margin: "0 0 24px 0",
          }}
        >
          {description}
          {itemName && (
            <span
              style={{
                display: "block",
                marginTop: "8px",
                fontWeight: "500",
                color: "#111318",
              }}
            >
              &ldquo;{itemName}&rdquo;
            </span>
          )}
        </p>

        {/* Buttons */}
        <div style={{ display: "flex", gap: "12px" }}>
          {/* Cancel button */}
          <button
            onClick={onCancel}
            disabled={isLoading}
            style={{
              flex: 1,
              background: "white",
              border: "1.5px solid #E5E7EB",
              color: "#374151",
              borderRadius: "10px",
              padding: "12px",
              fontSize: "14px",
              fontWeight: "500",
              cursor: isLoading ? "not-allowed" : "pointer",
              opacity: isLoading ? 0.6 : 1,
            }}
          >
            Cancel
          </button>

          {/* Confirm button */}
          <button
            onClick={onConfirm}
            disabled={isLoading}
            style={{
              flex: 1,
              background: "#EF4444",
              color: "white",
              border: "none",
              borderRadius: "10px",
              padding: "12px",
              fontSize: "14px",
              fontWeight: "600",
              cursor: isLoading ? "not-allowed" : "pointer",
              opacity: isLoading ? 0.7 : 1,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "8px",
            }}
          >
            {isLoading ? (
              <>
                <svg
                  style={{ animation: "spin 1s linear infinite", width: "16px", height: "16px" }}
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" strokeOpacity="0.25" />
                  <path fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                {`${confirmLabel}...`}
              </>
            ) : (
              confirmLabel
            )}
          </button>
        </div>
      </div>

      <style jsx>{`
        @keyframes spin {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }
      `}</style>
    </>
  );
}
