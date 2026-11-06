import {
  ScreeningSession,
  CustomerRecord,
  EyewearProduct,
  EyewearOrder,
  ReferralRecord,
  UserProfile,
} from '@optiguide/shared';
import { INITIAL_PRODUCTS, INITIAL_CUSTOMERS, INITIAL_ORDERS, INITIAL_REFERRALS } from './mockData';

const STORAGE_KEYS = {
  SCREENINGS: 'optiguide_screenings',
  CUSTOMERS: 'optiguide_customers',
  PRODUCTS: 'optiguide_products',
  ORDERS: 'optiguide_orders',
  REFERRALS: 'optiguide_referrals',
  CURRENT_USER: 'optiguide_current_user',
  ACTIVE_SESSION: 'optiguide_active_session',
};

export const getStoredScreenings = (): ScreeningSession[] => {
  try {
    const raw = localStorage.getItem(STORAGE_KEYS.SCREENINGS);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
};

export const saveScreeningSession = (session: ScreeningSession) => {
  try {
    const sessions = getStoredScreenings();
    const existingIndex = sessions.findIndex((s) => s.id === session.id);
    if (existingIndex >= 0) {
      sessions[existingIndex] = session;
    } else {
      sessions.unshift(session);
    }
    localStorage.setItem(STORAGE_KEYS.SCREENINGS, JSON.stringify(sessions));
    localStorage.setItem(STORAGE_KEYS.ACTIVE_SESSION, JSON.stringify(session));
  } catch (err) {
    console.error('Failed to save screening session:', err);
  }
};

export const getActiveSession = (): ScreeningSession | null => {
  try {
    const raw = localStorage.getItem(STORAGE_KEYS.ACTIVE_SESSION);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
};

export const getStoredCustomers = (): CustomerRecord[] => {
  try {
    const raw = localStorage.getItem(STORAGE_KEYS.CUSTOMERS);
    return raw ? JSON.parse(raw) : INITIAL_CUSTOMERS;
  } catch {
    return INITIAL_CUSTOMERS;
  }
};

export const saveCustomer = (customer: CustomerRecord) => {
  const customers = getStoredCustomers();
  const existing = customers.findIndex((c) => c.id === customer.id);
  if (existing >= 0) {
    customers[existing] = customer;
  } else {
    customers.unshift(customer);
  }
  localStorage.setItem(STORAGE_KEYS.CUSTOMERS, JSON.stringify(customers));
};

export const getStoredProducts = (): EyewearProduct[] => {
  try {
    const raw = localStorage.getItem(STORAGE_KEYS.PRODUCTS);
    return raw ? JSON.parse(raw) : INITIAL_PRODUCTS;
  } catch {
    return INITIAL_PRODUCTS;
  }
};

export const saveProduct = (product: EyewearProduct) => {
  const products = getStoredProducts();
  const existing = products.findIndex((p) => p.id === product.id);
  if (existing >= 0) {
    products[existing] = product;
  } else {
    products.unshift(product);
  }
  localStorage.setItem(STORAGE_KEYS.PRODUCTS, JSON.stringify(products));
};

export const getStoredOrders = (): EyewearOrder[] => {
  try {
    const raw = localStorage.getItem(STORAGE_KEYS.ORDERS);
    return raw ? JSON.parse(raw) : INITIAL_ORDERS;
  } catch {
    return INITIAL_ORDERS;
  }
};

export const saveOrder = (order: EyewearOrder) => {
  const orders = getStoredOrders();
  const existing = orders.findIndex((o) => o.id === order.id);
  if (existing >= 0) {
    orders[existing] = order;
  } else {
    orders.unshift(order);
  }
  localStorage.setItem(STORAGE_KEYS.ORDERS, JSON.stringify(orders));
};

export const getStoredReferrals = (): ReferralRecord[] => {
  try {
    const raw = localStorage.getItem(STORAGE_KEYS.REFERRALS);
    return raw ? JSON.parse(raw) : INITIAL_REFERRALS;
  } catch {
    return INITIAL_REFERRALS;
  }
};

export const saveReferral = (referral: ReferralRecord) => {
  const referrals = getStoredReferrals();
  const existing = referrals.findIndex((r) => r.id === referral.id);
  if (existing >= 0) {
    referrals[existing] = referral;
  } else {
    referrals.unshift(referral);
  }
  localStorage.setItem(STORAGE_KEYS.REFERRALS, JSON.stringify(referrals));
};

export const getCurrentUser = (): UserProfile | null => {
  try {
    const raw = localStorage.getItem(STORAGE_KEYS.CURRENT_USER);
    if (raw) return JSON.parse(raw);
    // Default guest profile
    return {
      id: 'usr-guest',
      email: 'guest@optiguide.org',
      fullName: 'Guest Visitor',
      role: 'guest',
      preferredLanguage: 'en',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
  } catch {
    return null;
  }
};

export const setCurrentUser = (user: UserProfile | null) => {
  if (user) {
    localStorage.setItem(STORAGE_KEYS.CURRENT_USER, JSON.stringify(user));
  } else {
    localStorage.removeItem(STORAGE_KEYS.CURRENT_USER);
  }
};

