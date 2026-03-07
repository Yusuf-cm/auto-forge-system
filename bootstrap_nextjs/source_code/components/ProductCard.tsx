// components/ProductCard.tsx
// Individual product card with add-to-cart functionality.
// Demonstrates: typed props, onClick handler, toast feedback on action,
// hover state via useState, conditional rendering for out-of-stock.

'use client'

import { useState } from 'react'
import { Product } from '../types'
import { formatPrice } from '../lib/products'

interface ProductCardProps {
  product: Product
  onAddToCart: (product: Product) => void
}

export default function ProductCard({ product, onAddToCart }: ProductCardProps) {
  const [isHovered, setIsHovered] = useState(false)
  const [justAdded, setJustAdded] = useState(false)

  const handleAddToCart = () => {
    if (!product.inStock) return
    onAddToCart(product)
    setJustAdded(true)
    setTimeout(() => setJustAdded(false), 1500)
  }

  return (
    <article
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{
        backgroundColor: 'var(--surface)',
        border: `1px solid ${isHovered ? 'var(--accent)' : 'rgba(204, 255, 0, 0.15)'}`,
        padding: '2rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '1rem',
        transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
        boxShadow: isHovered
          ? '0 0 30px rgba(204, 255, 0, 0.08)'
          : '0 0 20px rgba(204, 255, 0, 0.03)',
      }}
    >
      {/* ── Category tag ──────────────────────────────────────── */}
      <span style={{
        fontFamily: "'Inter', sans-serif",
        fontSize: '0.75rem',
        fontWeight: 700,
        color: 'var(--accent)',
        textTransform: 'uppercase',
        letterSpacing: '0.1em',
      }}>
        {product.category}
      </span>

      {/* ── Name ──────────────────────────────────────────────── */}
      <h3 style={{
        fontFamily: "'Inter', sans-serif",
        fontSize: '1.125rem',
        fontWeight: 700,
        color: 'var(--text)',
        margin: 0,
        lineHeight: 1.3,
      }}>
        {product.name}
      </h3>

      {/* ── Description ───────────────────────────────────────── */}
      <p style={{
        color: 'var(--text-muted)',
        fontSize: '0.9375rem',
        lineHeight: 1.6,
        margin: 0,
        flex: 1,
      }}>
        {product.description}
      </p>

      {/* ── Price + CTA ───────────────────────────────────────── */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginTop: 'auto',
      }}>
        <span style={{
          fontFamily: "'Bebas Neue', sans-serif",
          fontSize: '1.5rem',
          color: 'var(--accent)',
        }}>
          {formatPrice(product.price)}
        </span>

        <button
          onClick={handleAddToCart}
          disabled={!product.inStock || justAdded}
          aria-label={`Add ${product.name} to cart`}
          style={{
            background: justAdded
              ? 'rgba(204, 255, 0, 0.3)'
              : product.inStock
                ? 'var(--accent)'
                : 'rgba(255,255,255,0.1)',
            color: justAdded || !product.inStock ? 'rgba(26,26,26,0.5)' : 'var(--bg)',
            border: 'none',
            padding: '10px 20px',
            fontFamily: "'Inter', sans-serif",
            fontWeight: 700,
            fontSize: '0.8125rem',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            cursor: product.inStock && !justAdded ? 'pointer' : 'not-allowed',
            transition: 'all 0.2s ease',
            minWidth: '120px',
          }}
        >
          {justAdded ? 'Added ✓' : product.inStock ? 'Add to Cart' : 'Sold Out'}
        </button>
      </div>
    </article>
  )
}
