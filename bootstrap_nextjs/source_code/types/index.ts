// types/index.ts
// All TypeScript interfaces for the application.
// Every piece of data in the app has a type defined here.
// The Weaver MUST define types before building components.

export interface Product {
  id: string
  name: string
  description: string
  price: number
  category: string
  inStock: boolean
  tags: string[]
}

export interface CartItem {
  product: Product
  quantity: number
}

export interface CartState {
  items: CartItem[]
  isOpen: boolean
}

export type CartAction =
  | { type: 'ADD_ITEM'; product: Product }
  | { type: 'REMOVE_ITEM'; productId: string }
  | { type: 'UPDATE_QUANTITY'; productId: string; quantity: number }
  | { type: 'CLEAR_CART' }
  | { type: 'TOGGLE_CART' }
  | { type: 'LOAD_CART'; items: CartItem[] }

export interface ContactFormData {
  name: string
  email: string
  message: string
}

export interface ContactFormState {
  status: 'idle' | 'loading' | 'success' | 'error'
  message: string
}

export interface NavItem {
  label: string
  href: string
}

export interface SiteConfig {
  name: string
  tagline: string
  description: string
  nav: NavItem[]
}
