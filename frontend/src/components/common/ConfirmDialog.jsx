import React, { useEffect } from "react";
import "./ConfirmDialog.css";

const ConfirmDialog = ({
    isOpen,
    title = "Confirm Action",
    message = "Are you sure you want to proceed?",
    confirmText = "Confirm",
    cancelText = "Cancel",
    isDestructive = true,
    loading = false,
    onConfirm,
    onCancel,
}) => {
    useEffect(() => {
        const handleKeyDown = (e) => {
            if (e.key === "Escape" && isOpen && !loading) {
                onCancel();
            }
        };
        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, [isOpen, loading, onCancel]);

    if (!isOpen) return null;

    return (
        <div className="confirm-dialog-backdrop" onClick={!loading ? onCancel : undefined}>
            <div
                className="confirm-dialog-modal"
                role="dialog"
                aria-modal="true"
                aria-labelledby="confirm-dialog-title"
                onClick={(e) => e.stopPropagation()}
            >
                <div className="confirm-dialog-header">
                    <span className={`confirm-dialog-icon ${isDestructive ? "destructive" : "warning"}`}>
                        {isDestructive ? "⚠️" : "ℹ️"}
                    </span>
                    <h3 id="confirm-dialog-title">{title}</h3>
                </div>

                <div className="confirm-dialog-body">
                    <p>{message}</p>
                </div>

                <div className="confirm-dialog-actions">
                    <button
                        type="button"
                        className="btn-dialog-cancel"
                        onClick={onCancel}
                        disabled={loading}
                    >
                        {cancelText}
                    </button>
                    <button
                        type="button"
                        className={`btn-dialog-confirm ${isDestructive ? "btn-danger" : "btn-primary"}`}
                        onClick={onConfirm}
                        disabled={loading}
                    >
                        {loading ? "Processing..." : confirmText}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ConfirmDialog;
