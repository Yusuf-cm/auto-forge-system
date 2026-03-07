// components/Cart.tsx
// Slide-out cart drawer with item management.
// Demonstrates: conditional rendering, list rendering with keys,
// quantity controls, remove items, running total, empty state.
// The cart receives state and dispatch from the parent via props —
// this is the correct pattern: state lives at the top, components receive it.

'use client'

import { CartItem } from '../types'
import { getCartTotal, getCartCount } from '../lib/cart'
import { formatPrice } from '../lib/products'

interface CartProps {
  items: CartItem[]
  isOpen: boolean
  onClose: () => void
  onRemove: (productId: string) => void
  onUpdateQuantity: (productId: string, quantity: number) => void
  onClear: () => void
}

export default function Cart({
  items,
  isOpen,
  onClose,
  onRemove,
  onUpdateQuantity,
  onClear,
}: CartProps) {
  const total = getCartTotal(items)
  const count = getCartCount(items)

  if (!isOpen) return null

  return (
    <>
      {/* ── Backdrop ──────────────────────────────────────────── */}
      <div
        onClick={onClose}
        style={{
          position: 'fixed',
          inset: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.7)',
          zIndex: 200,
        }}
      />

      {/* ── Drawer ────────────────────────────────────────────── */}
      <aside style={{
        position: 'fixed',
        top: 0,
        right: 0,
        bottom: 0,
        width: '100%',
        maxWidth: '420px',
        backgroundColor: 'var(--surface)',
        borderLeft: '1px solid rgba(204, 255, 0, 0.2)',
        zIndex: 201,
        display: 'flex',
        flexDirection: 'column',
        overflowY: 'auto',
      }}>

        {/* ── Header ──────────────────────────────────────────── */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '1.5rem 2rem',
          borderBottom: '1px solid rgba(204, 255, 0, 0.15)',
        }}>
          <h2 style={{
            fontFamily: "'Bebas Neue', sans-serif",
            fontSize: '1.5rem',
            color: 'var(--accent)',
            margin: 0,
          }}>
            Your Cart {count > 0 ? `(${count})` : ''}
          </h2>
          <button
            onClick={onClose}
            aria-label="Close cart"
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-muted)',
              fontSize: '1.5rem',
              cursor: 'pointer',
              lineHeight: 1,
            }}
          >
            ×
          </button>
        </div>

        {/* ── Empty state ──────────────────────────────────────── */}
        {items.length === 0 ? (
          <div style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '3rem 2rem',
            textAlign: 'center',
          }}>
            <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
              Your cart is empty.
            </p>
            <button
              onClick={onClose}
              style={{
                background: 'var(--accent)',
                color: 'var(--bg)',
                border: 'none',
                padding: '12px 32px',
                fontFamily: "'Inter', sans-serif",
                fontWeight: 700,
                fontSize: '0.875rem',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                cursor: 'pointer',
              }}
            >
              Continue Shopping
            </button>
          </div>
        ) : (
          <>
            {/* ── Items list ──────────────────────────────────── */}
            <div style={{ flex: 1, padding: '1.5rem 2rem', overflowY: 'auto' }}>
              {items.map(item => (
                <div
                  key={item.product.id}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.75rem',
                    paddingBottom: '1.5rem',
                    marginBottom: '1.5rem',
                    borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <div>
                      <p style={{
                        fontFamily: "'Inter', sans-serif",
                        fontWeight: 700,
                        color: 'var(--text)',
                        margin: 0,
                        marginBottom: '0.25rem',
                      }}>
                        {item.product.name}
                      </p>
                      <p style={{
                        color: 'var(--accent)',
                        fontSize: '0.875rem',
                        fontWeight: 700,
                        margin: 0,
                      }}>
                        {formatPrice(item.product.price)}
                      </p>
                    </div>
                    <button
                      onClick={() => onRemove(item.product.id)}
                      aria-label={`Remove ${item.product.name}`}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: 'var(--text-muted)',
                        cursor: 'pointer',
                        fontSize: '1.25rem',
                        lineHeight: 1,
                        alignSelf: 'flex-start',
                      }}
                    >
                      ×
                    </button>
                  </div>

                  {/* ── Quantity controls ─────────────────────── */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      border: '1px solid rgba(204, 255, 0, 0.3)',
                    }}>
                      <button
                        onClick={() => onUpdateQuantity(item.product.id, item.quantity - 1)}
                        aria-label="Decrease quantity"
                        style={{
                          background: 'transparent',
                          border: 'none',
                          color: 'var(--text)',
                          width: '36px',
                          height: '36px',
                          cursor: 'pointer',
                          fontSize: '1.25rem',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}
                      >
                        −
                      </button>
                      <span style={{
                        padding: '0 1rem',
                        color: 'var(--text)',
                        fontFamily: "'Inter', sans-serif",
                        fontWeight: 700,
                        minWidth: '40px',
                        textAlign: 'center',
                      }}>
                        {item.quantity}
                      </span>
                      <button
                        onClick={() => onUpdateQuantity(item.product.id, item.quantity + 1)}
                        aria-label="Increase quantity"
                        style={{
                          background: 'transparent',
                          border: 'none',
                          color: 'var(--text)',
                          width: '36px',
                          height: '36px',
                          cursor: 'pointer',
                          fontSize: '1.25rem',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}
                      >
                        +
                      </button>
                    </div>
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                      Subtotal: {formatPrice(item.product.price * item.quantity)}
                    </span>
                  </div>
                </div>
              ))}
            </div>

            {/* ── Footer: total + actions ──────────────────────── */}
            <div style={{
              padding: '1.5rem 2rem',
              borderTop: '1px solid rgba(204, 255, 0, 0.15)',
            }}>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                marginBottom: '1.5rem',
              }}>
                <span style={{
                  fontFamily: "'Inter', sans-serif",
                  fontWeight: 700,
                  color: 'var(--text)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                }}>
                  Total
                </span>
                <span style={{
                  fontFamily: "'Bebas Neue', sans-serif",
                  fontSize: '1.5rem',
                  color: 'var(--accent)',
                }}>
                  {formatPrice(total)}
                </span>
              </div>

              <button
                style={{
                  width: '100%',
                  background: 'var(--accent)',
                  color: 'var(--bg)',
                  border: 'none',
                  padding: '16px',
                  fontFamily: "'Inter', sans-serif",
                  fontWeight: 700,
                  fontSize: '0.875rem',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  cursor: 'pointer',
                  marginBottom: '0.75rem',
                  transition: 'background 0.2s',
                }}
              >
                Checkout
              </button>

              <button
                onClick={onClear}
                style={{
                  width: '100%',
                  background: 'transparent',
                  color: 'var(--text-muted)',
                  border: '1px solid rgba(255,255,255,0.15)',
                  padding: '12px',
                  fontFamily: "'Inter', sans-serif",
                  fontWeight: 600,
                  fontSize: '0.8125rem',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  cursor: 'pointer',
                }}
              >
                Clear Cart
              </button>
            </div>
          </>
        )}
      </aside>
    </>
  )
}
