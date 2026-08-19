import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import type { Role } from '@shared/types';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ToastProvider } from './components/Toast';
import { ProtectedRoute } from './components/ProtectedRoute';
import { AppLayout } from './components/AppLayout';
import { LoginPage } from './pages/auth/LoginPage';
import { RegisterPage } from './pages/auth/RegisterPage';
import { DashboardPage } from './pages/DashboardPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { ProfilePage } from './pages/ProfilePage';
import { GrnListPage } from './pages/grn/GrnListPage';
import { GrnCreatePage } from './pages/grn/GrnCreatePage';
import { GrnDetailPage } from './pages/grn/GrnDetailPage';
import { EntityListPage } from './pages/entities/EntityListPage';
import { CategoryPage } from './pages/catalog/CategoryPage';
import { SubcategoryPage } from './pages/catalog/SubcategoryPage';
import { UomPage } from './pages/catalog/UomPage';
import { ProductPage } from './pages/catalog/ProductPage';
import { ReportsPage } from './pages/ReportsPage';
import { OrderDashPage } from './pages/orders/OrderDashPage';
import { OrderCreatePage } from './pages/orders/OrderCreatePage';
import { OrderDetailPage } from './pages/orders/OrderDetailPage';
import { PoListPage } from './pages/po/PoListPage';
import { PoCreatePage } from './pages/po/PoCreatePage';
import { PoDetailPage } from './pages/po/PoDetailPage';
import { PoPublicResponsePage } from './pages/po/PoPublicResponsePage';

function Protected({ children, roles }: { children: React.ReactNode; roles?: Role[] }) {
  return (
    <ProtectedRoute roles={roles}>
      <AppLayout>{children}</AppLayout>
    </ProtectedRoute>
  );
}

// "/" means something different per role: the full Dashboard for staff who
// manage the business, and each partner role's own landing page otherwise —
// there's no generic aggregate view that makes sense to show a Customer.
function Home() {
  const { user } = useAuth();
  if (!user) return null;
  if (user.role === 'Admin' || user.role === 'Warehouse Manager') return <DashboardPage />;
  if (user.role === 'Inventory Officer') return <Navigate to="/grn" replace />;
  if (user.role === 'Customer') return <Navigate to="/orders" replace />;
  if (user.role === 'Supplier' || user.role === 'Farmer') return <Navigate to="/grn" replace />;
  return <Navigate to="/profile" replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ToastProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/po-response/:token" element={<PoPublicResponsePage />} />
            <Route path="/" element={<Protected><Home /></Protected>} />
            <Route path="/profile" element={<Protected><ProfilePage /></Protected>} />

            <Route path="/grn" element={<Protected roles={['Admin', 'Inventory Officer', 'Warehouse Manager', 'Supplier', 'Farmer']}><GrnListPage /></Protected>} />
            <Route path="/grn/new" element={<Protected roles={['Admin', 'Inventory Officer', 'Warehouse Manager']}><GrnCreatePage /></Protected>} />
            <Route path="/grn/:id" element={<Protected roles={['Admin', 'Inventory Officer', 'Warehouse Manager', 'Supplier', 'Farmer']}><GrnDetailPage /></Protected>} />

            <Route path="/purchase-orders" element={<Protected roles={['Admin', 'Inventory Officer', 'Warehouse Manager']}><PoListPage /></Protected>} />
            <Route path="/purchase-orders/new" element={<Protected roles={['Admin', 'Inventory Officer', 'Warehouse Manager']}><PoCreatePage /></Protected>} />
            <Route path="/purchase-orders/:id" element={<Protected roles={['Admin', 'Inventory Officer', 'Warehouse Manager']}><PoDetailPage /></Protected>} />

            <Route path="/entities/:entity" element={<Protected roles={['Admin']}><EntityListPage /></Protected>} />

            <Route path="/catalog/categories" element={<Protected roles={['Admin', 'Inventory Officer', 'Warehouse Manager']}><CategoryPage /></Protected>} />
            <Route path="/catalog/subcategories" element={<Protected roles={['Admin', 'Inventory Officer', 'Warehouse Manager']}><SubcategoryPage /></Protected>} />
            <Route path="/catalog/uom" element={<Protected roles={['Admin', 'Inventory Officer', 'Warehouse Manager']}><UomPage /></Protected>} />
            <Route path="/catalog/products" element={<Protected roles={['Admin', 'Inventory Officer', 'Warehouse Manager']}><ProductPage /></Protected>} />

            <Route path="/reports" element={<Protected roles={['Admin', 'Warehouse Manager']}><ReportsPage /></Protected>} />
            <Route path="/reports/:type" element={<Protected roles={['Admin', 'Warehouse Manager']}><ReportsPage /></Protected>} />

            <Route path="/analytics" element={<Protected roles={['Admin', 'Warehouse Manager']}><AnalyticsPage /></Protected>} />

            <Route path="/orders" element={<Protected roles={['Admin', 'Warehouse Manager', 'Customer']}><OrderDashPage /></Protected>} />
            <Route path="/orders/all" element={<Protected roles={['Admin', 'Warehouse Manager']}><OrderDashPage allOrders /></Protected>} />
            <Route path="/orders/new" element={<Protected roles={['Admin', 'Warehouse Manager', 'Customer']}><OrderCreatePage /></Protected>} />
            <Route path="/orders/:id" element={<Protected roles={['Admin', 'Warehouse Manager', 'Customer']}><OrderDetailPage /></Protected>} />
          </Routes>
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
