import { useEffect, useState, type ReactNode } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import type { Role } from '@shared/types';
import { ENTITY_NAV, ROLE_ACCESS } from '@shared/constants';
import { useAuth } from '../context/AuthContext';
import { Dropdown, DropdownItem } from './Dropdown';
import { NotificationBell } from './NotificationBell';
import logoFull from '../assets/logo-full.png';
import logoIcon from '../assets/logo-icon.png';

interface NavItem {
  label: string;
  path: string;
  icon: string;
  roles?: Role[];
}

const STAFF_ROLES: Role[] = ['Admin', 'Inventory Officer', 'Warehouse Manager'];
const SIDEBAR_WIDTH = 240;
const APPBAR_HEIGHT = 64;
const MOBILE_BREAKPOINT = 900;

// Single role-aware nav config replacing the old app's two separate
// hardcoded user/admin sidebars. Two entries can point at the same path
// (e.g. GRN vs "My Deliveries") — role filtering below ensures only one
// ever renders for a given user.
const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', path: '/', icon: '🏠', roles: ROLE_ACCESS.dashboard },
  { label: 'Purchase Orders', path: '/purchase-orders', icon: '📝', roles: ROLE_ACCESS.purchaseOrders },
  { label: 'GRN', path: '/grn', icon: '📦', roles: ROLE_ACCESS.grn },
  { label: 'My Deliveries', path: '/grn', icon: '🚚', roles: ROLE_ACCESS.myDeliveries },
  { label: 'All Orders', path: '/orders/all', icon: '📋', roles: ROLE_ACCESS.orders },
  { label: 'My Orders', path: '/orders', icon: '🧾', roles: ROLE_ACCESS.myOrders },
  ...ENTITY_NAV.map((e) => ({ label: e.label, path: `/entities/${e.entity}`, icon: e.icon, roles: ROLE_ACCESS.registrations })),
  { label: 'Categories', path: '/catalog/categories', icon: '🗂️', roles: ROLE_ACCESS.catalogManage },
  { label: 'Subcategories', path: '/catalog/subcategories', icon: '📁', roles: ROLE_ACCESS.catalogManage },
  { label: 'Units of Measurement', path: '/catalog/uom', icon: '📐', roles: ROLE_ACCESS.catalogManage },
  { label: 'Products', path: '/catalog/products', icon: '🛒', roles: ROLE_ACCESS.catalogManage },
  { label: 'Reports', path: '/reports', icon: '📊', roles: ROLE_ACCESS.reports },
  { label: 'Analytics', path: '/analytics', icon: '📈', roles: ROLE_ACCESS.analytics },
  { label: 'My Profile', path: '/profile', icon: '👤' },
];

function useIsMobile() {
  const [isMobile, setIsMobile] = useState(() => window.innerWidth < MOBILE_BREAKPOINT);
  useEffect(() => {
    function onResize() {
      setIsMobile(window.innerWidth < MOBILE_BREAKPOINT);
    }
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);
  return isMobile;
}

export function AppLayout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const isMobile = useIsMobile();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const items = NAV_ITEMS.filter((item) => !item.roles || (user && item.roles.includes(user.role)));
  const isStaff = user && STAFF_ROLES.includes(user.role);

  // Close the mobile drawer on every navigation.
  useEffect(() => {
    setSidebarOpen(false);
  }, [location.pathname]);

  const sidebarVisible = isMobile ? sidebarOpen : true;

  return (
    <div>
      {isMobile && sidebarOpen && (
        <div onClick={() => setSidebarOpen(false)} style={overlayStyle} />
      )}

      {/* Sidebar and header are both position:fixed against the viewport —
          they never sit inside a scrolling container, so they stay pinned
          no matter how tall any given page's content is. Only the content
          wrapper below scrolls (via normal document flow). */}
      <aside
        style={{
          ...sidebarStyle,
          transform: sidebarVisible ? 'translateX(0)' : 'translateX(-100%)',
        }}
      >
        <div style={{ padding: '18px 20px', display: 'flex', justifyContent: 'center', flexShrink: 0 }}>
          <div className="logo-badge" style={logoBadgeStyle}>
            <img src={logoFull} alt="Prime Fresh" style={{ display: 'block', height: 30, width: 'auto', margin: '0 auto' }} />
          </div>
        </div>
        <nav className="sidebar-nav" style={{ flex: 1, padding: '4px 12px 12px', overflowY: 'auto' }}>
          {items.map((item) => (
            <NavLink
              key={item.label}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) => `nav-link-app${isActive ? ' active' : ''}`}
              style={({ isActive }) => navLinkStyle(isActive)}
            >
              <span>{item.icon}</span> {item.label}
            </NavLink>
          ))}
        </nav>
        <div style={{ padding: 16, borderTop: '1px solid rgba(255,255,255,0.12)', flexShrink: 0 }}>
          <div style={{ color: '#fff', fontSize: 13, fontWeight: 600 }}>{user?.full_name}</div>
          <div style={{ color: 'rgba(255,255,255,0.6)', fontSize: 12 }}>{user?.role}{!isStaff && ' (Partner Portal)'}</div>
        </div>
      </aside>

      <header style={{ ...navbarStyle, left: isMobile ? 0 : SIDEBAR_WIDTH }}>
        {isMobile ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <button
              onClick={() => setSidebarOpen((o) => !o)}
              aria-label="Toggle navigation"
              className="btn-app"
              style={hamburgerStyle}
            >
              ☰
            </button>
            <img src={logoIcon} alt="Prime Fresh" className="logo-badge" style={{ height: 28, width: 'auto' }} />
          </div>
        ) : (
          <div />
        )}
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          {isStaff && <NotificationBell />}
          <Dropdown trigger={<span style={{ fontWeight: 600, fontSize: 14 }}>{user?.full_name} ▾</span>}>
            <DropdownItem onClick={() => navigate('/profile')}>My Profile</DropdownItem>
            <DropdownItem onClick={() => { logout(); navigate('/login'); }}>Sign out</DropdownItem>
          </Dropdown>
        </div>
      </header>

      <main
        key={location.pathname}
        className="page-enter"
        style={{
          ...mainStyle,
          marginLeft: isMobile ? 0 : SIDEBAR_WIDTH,
        }}
      >
        {children}
      </main>
    </div>
  );
}

const sidebarStyle: React.CSSProperties = {
  position: 'fixed',
  top: 0,
  left: 0,
  bottom: 0,
  width: SIDEBAR_WIDTH,
  background: 'linear-gradient(180deg, var(--color-primary-dark), var(--color-primary))',
  display: 'flex',
  flexDirection: 'column',
  zIndex: 300,
  transition: 'transform 0.2s ease',
};

const logoBadgeStyle: React.CSSProperties = {
  background: '#fff',
  borderRadius: 'var(--radius-md)',
  padding: '8px 16px',
  boxShadow: 'var(--shadow-sm)',
  display: 'inline-flex',
  alignItems: 'center',
};

const overlayStyle: React.CSSProperties = {
  position: 'fixed',
  inset: 0,
  background: 'rgba(15, 23, 42, 0.5)',
  zIndex: 250,
};

const navbarStyle: React.CSSProperties = {
  position: 'fixed',
  top: 0,
  right: 0,
  height: APPBAR_HEIGHT,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: '0 24px',
  background: 'linear-gradient(90deg, var(--color-primary-light), var(--color-primary) 45%, var(--color-primary-dark))',
  color: '#fff',
  boxShadow: '0 2px 8px rgba(121, 134, 203, 0.18)',
  zIndex: 200,
};

const hamburgerStyle: React.CSSProperties = {
  background: 'transparent',
  border: 'none',
  fontSize: 22,
  lineHeight: 1,
  cursor: 'pointer',
  color: '#fff',
  padding: 4,
};

const mainStyle: React.CSSProperties = {
  padding: 'var(--space-lg)',
  paddingTop: `calc(${APPBAR_HEIGHT}px + var(--space-lg))`,
  minHeight: '100vh',
  background: 'var(--color-bg)',
  boxSizing: 'border-box',
};

function navLinkStyle(isActive: boolean): React.CSSProperties {
  // Only set `background` for the active state — leaving it unset (rather
  // than 'transparent') for inactive links lets the CSS :hover rule in
  // index.css actually take effect, since inline styles always beat
  // stylesheet rules regardless of specificity/pseudo-classes.
  return isActive
    ? { color: 'var(--color-primary-dark)', background: '#fff' }
    : { color: 'rgba(255,255,255,0.85)' };
}
