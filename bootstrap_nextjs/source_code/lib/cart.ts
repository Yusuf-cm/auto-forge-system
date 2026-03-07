// lib/cart.ts
// Cart reducer and localStorage persistence.
// This pattern MUST be used for all stateful operations.
// useReducer + localStorage = persistent client state without a database.

import { CartState, CartAction, CartItem } from '../types'

export const CART_STORAGE_KEY = 'autoforge_cart'

export const initialCartState: CartState = {
  items: [],
  isOpen: false,
}

export function cartReducer(state: CartState, action: CartAction): CartState {
  switch (action.type) {

    case 'ADD_ITEM': {
      const existing = state.items.find(
        item => item.product.id === action.product.id
      )
      if (existing) {
        return {
          ...state,
          items: state.items.map(item =>
            item.product.id === action.product.id
              ? { ...item, quantity: item.quantity + 1 }
              : item
          ),
        }
      }
      return {
        ...state,
        items: [...state.items, { product: action.product, quantity: 1 }],
      }
    }

    case 'REMOVE_ITEM':
      return {
        ...state,
        items: state.items.filter(item => item.product.id !== action.productId),
      }

    case 'UPDATE_QUANTITY': {
      if (action.quantity <= 0) {
        return {
          ...state,
          items: state.items.filter(item => item.product.id !== action.productId),
        }
      }
      return {
        ...state,
        items: state.items.map(item =>
          item.product.id === action.productId
            ? { ...item, quantity: action.quantity }
            : item
        ),
      }
    }

    case 'CLEAR_CART':
      return { ...state, items: [] }

    case 'TOGGLE_CART':
      return { ...state, isOpen: !state.isOpen }

    case 'LOAD_CART':
      return { ...state, items: action.items }

    default:
      return state
  }
}

// Cart total item count — shown in nav badge
export function getCartCount(items: CartItem[]): number {
  return items.reduce((total, item) => total + item.quantity, 0)
}

// Cart subtotal
export function getCartTotal(items: CartItem[]): number {
  return items.reduce(
    (total, item) => total + item.product.price * item.quantity,
    0
  )
}

// Persist cart to localStorage
export function saveCartToStorage(items: CartItem[]): void {
  try {
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(items))
  } catch {
    // localStorage may be unavailable in SSR — fail silently
  }
}

// Load cart from localStorage on app init
export function loadCartFromStorage(): CartItem[] {
  try {
    const stored = localStorage.getItem(CART_STORAGE_KEY)
    return stored ? JSON.parse(stored) : []
  } catch {
    return []
  }
}
