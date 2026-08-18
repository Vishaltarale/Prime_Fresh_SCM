import type { Role, StaffRole, ExternalRole, GrnStatus, GrnSourceType } from './types';

export const STAFF_ROLES: StaffRole[] = ['Admin', 'Inventory Officer', 'Warehouse Manager'];
export const EXTERNAL_ROLES: ExternalRole[] = ['Customer', 'Supplier', 'Farmer'];
export const ROLES: Role[] = [...STAFF_ROLES, ...EXTERNAL_ROLES];
export const GRN_STATUSES: GrnStatus[] = ['Draft', 'Confirmed', 'Rejected'];
export const GRN_SOURCE_TYPES: GrnSourceType[] = ['Supplier', 'Farmer'];

// Module access matrix — used by both the web sidebar and route guards.
export const ROLE_ACCESS = {
  dashboard: ['Admin', 'Warehouse Manager'] as Role[],
  grn: ['Admin', 'Inventory Officer', 'Warehouse Manager'] as Role[],
  myDeliveries: ['Supplier', 'Farmer'] as Role[],
  catalogManage: ['Admin', 'Inventory Officer', 'Warehouse Manager'] as Role[],
  orders: ['Admin', 'Warehouse Manager'] as Role[],
  myOrders: ['Customer'] as Role[],
  registrations: ['Admin'] as Role[],
  reports: ['Admin', 'Warehouse Manager'] as Role[],
  // Purchase Orders: same "admin or inventory manager or warehouse provider" group as GRN.
  purchaseOrders: ['Admin', 'Inventory Officer', 'Warehouse Manager'] as Role[],
};

export const REGISTER_PROFILE_FIELDS: Record<string, string[]> = {
  Customer: ['address', 'city', 'state'],
  Supplier: ['company_name', 'address', 'state', 'district'],
  Farmer: ['address', 'village', 'district', 'state'],
};

export const API_ENDPOINTS = {
  register: '/auth/register/',
  login: '/auth/login/',
  refresh: '/auth/refresh/',
  me: '/auth/me/',
  myProfile: '/auth/profile/',
  warehouses: '/warehouses/',
  suppliers: '/suppliers/',
  farmers: '/farmers/',
  products: '/products/',
  grnList: '/grn/',
  grnDetail: (id: string) => `/grn/${id}/`,
  grnConfirm: (id: string) => `/grn/${id}/confirm/`,
  grnReject: (id: string) => `/grn/${id}/reject/`,

  purchaseOrders: '/purchase-orders/',
  poConfirmedForGrn: '/purchase-orders/confirmed/',
  poDetail: (id: string) => `/purchase-orders/${id}/`,
  poSend: (id: string) => `/purchase-orders/${id}/send/`,
  poConfirm: (id: string) => `/purchase-orders/${id}/confirm/`,
  poReject: (id: string) => `/purchase-orders/${id}/reject/`,
  poPayments: (id: string) => `/purchase-orders/${id}/payments/`,
  poRefund: (id: string) => `/purchase-orders/${id}/refund/`,
  poPublic: (token: string) => `/po-response/${token}/`,

  entityMeta: (entity: string) => `/entities/${entity}/meta/`,
  entityList: (entity: string) => `/entities/${entity}/`,
  entityDetail: (entity: string, id: string) => `/entities/${entity}/${id}/`,

  categories: '/catalog/categories/',
  categoryDetail: (id: string) => `/catalog/categories/${id}/`,
  subcategories: '/catalog/subcategories/',
  subcategoryDetail: (id: string) => `/catalog/subcategories/${id}/`,
  catalogUom: '/catalog/uom/',
  catalogUomDetail: (id: string) => `/catalog/uom/${id}/`,
  conversions: '/catalog/conversions/',
  conversionDetail: (id: string) => `/catalog/conversions/${id}/`,
  catalogProducts: '/catalog/products/',
  catalogProductDetail: (id: string) => `/catalog/products/${id}/`,

  orders: '/orders/',
  orderDetail: (id: string) => `/orders/${id}/`,
  orderInvoice: (id: string) => `/orders/${id}/invoice/`,

  dashboard: '/dashboard/',

  report: (type: string) => `/reports/${type}/`,
  reportExportPdf: (type: string) => `/reports/${type}/export/pdf/`,
  reportExportExcel: (type: string) => `/reports/${type}/export/excel/`,
} as const;

export const ORDER_STATUSES = ['Pending', 'Processing', 'Completed', 'Cancelled'] as const;
export const PAYMENT_STATUSES = ['Paid', 'Unpaid'] as const;

export const ENTITY_NAV: Array<{ entity: string; label: string; icon: string }> = [
  { entity: 'employee', label: 'Employees', icon: '🧑‍💼' },
  { entity: 'farmer', label: 'Farmers', icon: '🌾' },
  { entity: 'supplier', label: 'Suppliers', icon: '🚚' },
  { entity: 'customer', label: 'Customers', icon: '🧾' },
  { entity: 'warehouse', label: 'Warehouses', icon: '🏬' },
];

export const REPORT_NAV: Array<{ type: string; label: string; icon: string }> = [
  { type: 'inventory', label: 'Inventory', icon: '📦' },
  { type: 'orders', label: 'Orders', icon: '🧾' },
  { type: 'suppliers', label: 'Suppliers', icon: '🚚' },
  { type: 'warehouses', label: 'Warehouses', icon: '🏬' },
  { type: 'sales', label: 'Sales', icon: '💰' },
  { type: 'low-stock', label: 'Low Stock', icon: '⚠️' },
  { type: 'purchase-orders', label: 'Purchase Orders', icon: '📝' },
  { type: 'po-payments', label: 'Supplier Payments', icon: '💳' },
];

export const PO_STATUSES = ['Draft', 'Sent', 'Awaiting Approval', 'Confirmed', 'Rejected'] as const;
export const LOSS_REASONS = ['', 'Damaged', 'Short-shipped', 'Lost', 'Other'] as const;
