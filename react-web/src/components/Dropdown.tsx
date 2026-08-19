import { useEffect, useRef, useState, type ReactNode } from 'react';

interface DropdownProps {
  trigger: ReactNode;
  children: ReactNode;
  align?: 'left' | 'right';
}

export function Dropdown({ trigger, children, align = 'right' }: DropdownProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener('mousedown', onClickOutside);
    return () => document.removeEventListener('mousedown', onClickOutside);
  }, []);

  return (
    <div ref={ref} style={{ position: 'relative', display: 'inline-block' }}>
      <div onClick={() => setOpen((o) => !o)} style={{ cursor: 'pointer' }}>
        {trigger}
      </div>
      {open && (
        <div
          className="dropdown-enter"
          style={{
            position: 'absolute',
            top: '100%',
            marginTop: 6,
            [align]: 0,
            background: 'var(--color-surface)',
            color: 'var(--color-text)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-md)',
            boxShadow: 'var(--shadow-md)',
            minWidth: 180,
            zIndex: 500,
            overflow: 'hidden',
          }}
          onClick={() => setOpen(false)}
        >
          {children}
        </div>
      )}
    </div>
  );
}

export function DropdownItem({ children, onClick }: { children: ReactNode; onClick?: () => void }) {
  return (
    <div
      onClick={onClick}
      style={{ padding: '10px 14px', fontSize: 14, cursor: 'pointer', transition: 'background 0.15s var(--ease-out), padding-left 0.15s var(--ease-out)' }}
      onMouseOver={(e) => (e.currentTarget.style.paddingLeft = '18px')}
      onMouseOut={(e) => (e.currentTarget.style.paddingLeft = '14px')}
      onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--color-bg)')}
      onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
    >
      {children}
    </div>
  );
}
