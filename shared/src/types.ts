export type StaffRole = 'Admin' | 'Inventory Officer' | 'Warehouse Manager';
export type ExternalRole = 'Customer' | 'Supplier' | 'Farmer';
export type Role = StaffRole | ExternalRole;

export interface User {
  id: string;
  full_name: string;
  email: string;
  phone: string;
  role: Role;
  created_at: string;
}

export interface RegisterInput {
  full_name: string;
  email: string;
  phone: string;
  password: string;
  role: Role;
  // Only required when role is Customer/Supplier/Farmer — the linked
  // business entity is created from these in the same call.
  address?: string;
  city?: string;
  state?: string;
  district?: string;
  village?: string;
  company_name?: string;
}

export interface MyProfile {
  user: User;
  entity: Record<string, string> | null;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface NamedRef {
  id: string;
  name: string;
}

export interface ProductRef extends NamedRef {
  sku: string;
  uom: string;
  price_per_unit: number;
}

export type GrnStatus = 'Draft' | 'Confirmed' | 'Rejected';
export type GrnSourceType = 'Supplier' | 'Farmer';

export interface GrnItem {
  product: string;
  product_name?: string;
  ordered_qty: number;
  received_qty: number;
  loss_qty?: number;
  loss_reason?: string;
  unit_price: number;
  uom: string;
  remarks: string;
  line_total?: number;
}

export interface GrnRef {
  id: string;
  name: string;
}

export interface Grn {
  id: string;
  grn_number: string;
  grn_date: string;
  source_type: GrnSourceType;
  supplier: GrnRef | null;
  farmer: GrnRef | null;
  purchase_order: { id: string; po_number: string } | null;
  warehouse: GrnRef;
  items: GrnItem[];
  total_amount: number;
  status: GrnStatus;
  received_by: string;
  notes: string;
  created_at: string;
}

// ── Purchase Orders ────────────────────────────────────────────────────

export type PoStatus = 'Draft' | 'Sent' | 'Awaiting Approval' | 'Confirmed' | 'Rejected';

export interface PoItem {
  product: string;
  product_name: string;
  ordered_qty: number;
  proposed_price: number;
  confirmed_price: number | null;
  received_qty: number;
  loss_qty: number;
  remaining_qty: number;
  line_total_confirmed: number;
  line_total_received: number;
}

export interface PurchaseOrder {
  id: string;
  po_number: string;
  supplier: { id: string; name: string; email: string };
  warehouse: NamedRef;
  items: PoItem[];
  status: PoStatus;
  notes: string;
  created_by: string;
  approved_by: string;
  proposed_total: number;
  confirmed_total: number;
  received_total: number;
  created_at: string;
  sent_at: string | null;
  responded_at: string | null;
  confirmed_at: string | null;
  email_sent?: boolean;
  email_error?: string;
}

export interface PoConfirmedForGrn {
  id: string;
  po_number: string;
  supplier: NamedRef;
  warehouse: NamedRef;
  items: PoItem[];
}

export interface PoPaymentEntry {
  kind: 'Payment' | 'Refund';
  amount: number;
  method: string;
  reason: string;
  recorded_by: string;
  date: string;
}

export interface PoPaymentSummary {
  po: string;
  total_amount: number;
  amount_paid: number;
  balance: number;
  status: 'Unpaid' | 'Partially Paid' | 'Fully Paid';
  history: PoPaymentEntry[];
}

// ── Generic entity CRUD (Employee/Farmer/Supplier/Customer/Warehouse) ──

export type EntityFieldType = 'text' | 'email' | 'date' | 'select' | 'textarea' | 'bool';

export interface EntityField {
  name: string;
  label: string;
  type: EntityFieldType;
  required: boolean;
  choices?: string[];
}

export interface EntityMeta {
  entity: string;
  label: string;
  fields: EntityField[];
}

export type EntityRecord = { id: string } & Record<string, string | boolean | undefined>;

export const ENTITY_TYPES = ['employee', 'farmer', 'supplier', 'customer', 'warehouse'] as const;
export type EntityType = (typeof ENTITY_TYPES)[number];

// ── Dashboard ──────────────────────────────────────────────────────────

export interface DashboardSummary {
  counts: {
    orders: number;
    products: number;
    warehouses: number;
    employees: number;
    farmers: number;
    suppliers: number;
    customers: number;
    low_stock_products: number;
  };
  total_revenue: number;
  order_status_breakdown: Array<{ status: string; count: number }>;
  inventory_by_category: Array<{ category: string; quantity: number }>;
  stock_by_warehouse: Array<{ warehouse: string; quantity: number }>;
  recent_orders: Array<{ id: string; customer_name: string; status: string; total_amount: number; order_date: string | null }>;
}

// ── Analytics ──────────────────────────────────────────────────────────

export interface NameValue {
  name: string;
  value: number;
}

export interface Candle {
  month: string;
  open: number;
  close: number;
  high: number;
  low: number;
  count: number;
}

export interface AnalyticsSummary {
  sales_candles: Candle[];
  purchase_order_candles: Candle[];
  order_status_distribution: NameValue[];
  category_stock_distribution: NameValue[];
  warehouse_stock_distribution: NameValue[];
  payment_status_distribution: NameValue[];
  top_products_by_value: NameValue[];
  supplier_spend_distribution: NameValue[];
  supplier_qty_distribution: NameValue[];
}

// ── Reports ────────────────────────────────────────────────────────────

export type ReportType = 'inventory' | 'orders' | 'suppliers' | 'warehouses' | 'sales' | 'low-stock';

// ── Notifications ──────────────────────────────────────────────────────

export type NotificationCategory = 'low_stock' | 'po_status' | 'grn_status' | 'payment_status' | 'general';
export type NotificationSeverity = 'info' | 'warning' | 'critical';

export interface AppNotification {
  id: string;
  category: NotificationCategory;
  severity: NotificationSeverity;
  title: string;
  message: string;
  warehouse: NamedRef | null;
  product: NamedRef | null;
  po_id: string | null;
  grn_id: string | null;
  resolved: boolean;
  is_read: boolean;
  created_at: string;
}

export interface NotificationList {
  results: AppNotification[];
  unread_count: number;
}

export interface ReportData {
  title: string;
  headers: string[];
  rows: Array<Array<string | number>>;
  summary?: string;
  /** Parallel to `rows` — lets the UI open a detail modal per row (PO for Purchase Orders/Supplier Payments, warehouse for Warehouses). */
  row_meta?: Array<{ po_id: string } | { warehouse_id: string } | null>;
  /** Per-PO product line items — the export views' "Details" tab/sheet; not rendered in the on-screen table. */
  details?: Array<{ po_number: string; supplier: string; headers: string[]; rows: Array<Array<string | number>> }>;
}

export interface WarehouseStockItem {
  product: string;
  sku: string;
  quantity_available: number;
  price_per_unit: number;
  is_low: boolean;
}

export interface WarehouseStockDetail {
  warehouse: { id: string; name: string; city: string };
  threshold: number;
  items: WarehouseStockItem[];
}

// ── Catalog (Category/Subcategory/UOM/Conversion/Product) ─────────────────

export interface Category {
  id: string;
  name: string;
  description: string;
}

export interface Subcategory {
  id: string;
  name: string;
  category: NamedRef;
}

export interface UomRecord {
  id: string;
  name: string;
  description: string;
}

export interface Conversion {
  id: string;
  from_uom: NamedRef;
  to_uom: NamedRef;
  factor: number;
}

export type ProductSourceType = 'supplier' | 'farmer';

// One line per warehouse the product has actually been received into (via a
// confirmed GRN) — a product can carry stock in several warehouses at once,
// each with its own quantity and landed cost.
export interface ProductStockLine {
  warehouse: NamedRef;
  quantity_available: number;
  price_per_unit: number | null;
}

export interface CatalogProduct {
  id: string;
  name: string;
  sku: string;
  category: NamedRef | null;
  subcategory: NamedRef | null;
  uom: NamedRef | null;
  price_per_unit: number;
  /** Per-warehouse breakdown — empty until a GRN has been confirmed for this product. */
  stock: ProductStockLine[];
  /** Sum of stock[].quantity_available across all warehouses. */
  quantity_available: number;
  description: string;
  source_type: ProductSourceType | null;
  supplier: NamedRef | null;
  farmer: NamedRef | null;
  created_at: string;
}

// ── Orders ──────────────────────────────────────────────────────────────

export type OrderStatus = 'Pending' | 'Processing' | 'Completed' | 'Cancelled';
export type PaymentStatus = 'Paid' | 'Unpaid';

export interface OrderItem {
  product_name: string;
  quantity: number;
  price: number;
  uom: string;
  line_total: number;
}

export interface Order {
  id: string;
  customer_name: string;
  order_date: string;
  status: OrderStatus;
  payment_status: PaymentStatus;
  delivery_address: string;
  created_by: string;
  warehouse: NamedRef | null;
  total_amount: number;
  items: OrderItem[];
}

export interface OrderItemInput {
  product: string;
  quantity: number;
  price: number;
  uom: string;
}

export interface OrderCreateInput {
  customer_name: string;
  delivery_address: string;
  warehouse: string;
  items: OrderItemInput[];
}

export interface GrnCreateInput {
  source_type: GrnSourceType;
  supplier?: string;
  farmer?: string;
  purchase_order?: string;
  warehouse: string;
  notes?: string;
  items: Array<Pick<GrnItem, 'product' | 'ordered_qty' | 'received_qty' | 'loss_qty' | 'loss_reason' | 'unit_price' | 'uom' | 'remarks'>>;
}
