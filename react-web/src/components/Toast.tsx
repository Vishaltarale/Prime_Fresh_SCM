import { createContext, useCallback, useContext, useState, type ReactNode } from 'react';

type ToastKind = 'success' | 'error' | 'info';
interface ToastMessage { id: number; kind: ToastKind; text: string; }

interface ToastContextValue {
  show: (text: string, kind?: ToastKind) => void;
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const show = useCallback((text: string, kind: ToastKind = 'info') => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { id, kind, text }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 4000);
  }, []);

  return (
    <ToastContext.Provider value={{ show }}>
      {children}
      <div style={styles.stack}>
        {toasts.map((t) => (
          <div key={t.id} style={{ ...styles.toast, ...kindStyles[t.kind] }}>
            {t.text}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within ToastProvider');
  return ctx;
}

const kindStyles: Record<ToastKind, React.CSSProperties> = {
  success: { background: 'var(--color-success)' },
  error: { background: 'var(--color-danger)' },
  info: { background: 'var(--color-primary)' },
};

const styles: Record<string, React.CSSProperties> = {
  stack: {
    position: 'fixed',
    top: 16,
    right: 16,
    display: 'flex',
    flexDirection: 'column',
    gap: 8,
    zIndex: 1000,
  },
  toast: {
    color: 'var(--color-text-inverse)',
    padding: '12px 16px',
    borderRadius: 'var(--radius-md)',
    boxShadow: 'var(--shadow-md)',
    fontSize: 14,
    minWidth: 240,
    animation: 'none',
  },
};
