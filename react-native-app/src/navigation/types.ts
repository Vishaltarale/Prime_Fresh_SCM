export type AuthStackParamList = {
  Login: undefined;
  Register: undefined;
};

export type AppStackParamList = {
  Dashboard: undefined;
  GrnList: undefined;
  GrnCreate: undefined;
  GrnDetail: { id: string };
  EntityList: { entity: string; label: string };
  EntityForm: { entity: string; label: string; id?: string };
  OrderList: undefined;
  OrderCreate: undefined;
  OrderDetail: { id: string };
  CategoryList: undefined;
  SubcategoryList: undefined;
  UomList: undefined;
  ProductList: undefined;
  ProductCreate: undefined;
  ReportList: undefined;
  Profile: undefined;
};
