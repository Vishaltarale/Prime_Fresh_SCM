import { ActivityIndicator, View } from 'react-native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import type { AuthStackParamList, AppStackParamList } from './types';
import { useAuth } from '../context/AuthContext';
import { LoginScreen } from '../screens/auth/LoginScreen';
import { RegisterScreen } from '../screens/auth/RegisterScreen';
import { DashboardScreen } from '../screens/DashboardScreen';
import { GrnListScreen } from '../screens/grn/GrnListScreen';
import { GrnCreateScreen } from '../screens/grn/GrnCreateScreen';
import { GrnDetailScreen } from '../screens/grn/GrnDetailScreen';
import { EntityListScreen } from '../screens/entities/EntityListScreen';
import { EntityFormScreen } from '../screens/entities/EntityFormScreen';
import { OrderListScreen } from '../screens/orders/OrderListScreen';
import { OrderCreateScreen } from '../screens/orders/OrderCreateScreen';
import { OrderDetailScreen } from '../screens/orders/OrderDetailScreen';
import { CategoryListScreen } from '../screens/catalog/CategoryListScreen';
import { SubcategoryListScreen } from '../screens/catalog/SubcategoryListScreen';
import { UomListScreen } from '../screens/catalog/UomListScreen';
import { ProductListScreen } from '../screens/catalog/ProductListScreen';
import { ProductCreateScreen } from '../screens/catalog/ProductCreateScreen';
import { ReportListScreen } from '../screens/reports/ReportListScreen';
import { ProfileScreen } from '../screens/ProfileScreen';
import { colors } from '../theme';

const AuthStack = createNativeStackNavigator<AuthStackParamList>();
const AppStack = createNativeStackNavigator<AppStackParamList>();

function AuthNavigator() {
  return (
    <AuthStack.Navigator screenOptions={{ headerShown: false }}>
      <AuthStack.Screen name="Login" component={LoginScreen} />
      <AuthStack.Screen name="Register" component={RegisterScreen} />
    </AuthStack.Navigator>
  );
}

function AppNavigator() {
  return (
    <AppStack.Navigator screenOptions={{ headerShown: false }}>
      <AppStack.Screen name="Dashboard" component={DashboardScreen} />
      <AppStack.Screen name="GrnList" component={GrnListScreen} />
      <AppStack.Screen name="GrnCreate" component={GrnCreateScreen} />
      <AppStack.Screen name="GrnDetail" component={GrnDetailScreen} />
      <AppStack.Screen name="EntityList" component={EntityListScreen} />
      <AppStack.Screen name="EntityForm" component={EntityFormScreen} />
      <AppStack.Screen name="OrderList" component={OrderListScreen} />
      <AppStack.Screen name="OrderCreate" component={OrderCreateScreen} />
      <AppStack.Screen name="OrderDetail" component={OrderDetailScreen} />
      <AppStack.Screen name="CategoryList" component={CategoryListScreen} />
      <AppStack.Screen name="SubcategoryList" component={SubcategoryListScreen} />
      <AppStack.Screen name="UomList" component={UomListScreen} />
      <AppStack.Screen name="ProductList" component={ProductListScreen} />
      <AppStack.Screen name="ProductCreate" component={ProductCreateScreen} />
      <AppStack.Screen name="ReportList" component={ReportListScreen} />
      <AppStack.Screen name="Profile" component={ProfileScreen} />
    </AppStack.Navigator>
  );
}

export function RootNavigator() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.background }}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  return user ? <AppNavigator /> : <AuthNavigator />;
}
