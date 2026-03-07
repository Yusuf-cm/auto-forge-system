// lib/products.ts
// Product data and helper functions.
// In a real project this would fetch from an API or CMS.
// For now: static data with TypeScript types enforced.
// The Weaver MUST put all data here, never inline in components.

import { Product } from '../types'

export const PRODUCTS: Product[] = [
  {
    id: 'voltage-espresso',
    name: 'Voltage Espresso',
    description: 'Dark roast with notes of dark chocolate and brown sugar. Built for espresso machines and those who mean business.',
    price: 18.00,
    category: 'espresso',
    inStock: true,
    tags: ['dark', 'espresso', 'bold'],
  },
  {
    id: 'dark-matter-cold-brew',
    name: 'Dark Matter Cold Brew',
    description: 'Ultra-coarse grind for 24hr cold extraction. Smooth, low-acid, and hits different at 6am.',
    price: 22.00,
    category: 'cold-brew',
    inStock: true,
    tags: ['cold-brew', 'smooth', 'low-acid'],
  },
  {
    id: 'reactor-blend',
    name: 'Reactor Blend',
    description: 'Complex, full-bodied blend engineered for all-day output. Three origins, one result: sustained energy without the crash.',
    price: 20.00,
    category: 'blend',
    inStock: true,
    tags: ['blend', 'full-bodied', 'all-day'],
  },
]

export function getProductById(id: string): Product | undefined {
  return PRODUCTS.find(p => p.id === id)
}

export function getProductsByCategory(category: string): Product[] {
  return PRODUCTS.filter(p => p.category === category)
}

export function formatPrice(price: number): string {
  return `$${price.toFixed(2)}`
}
