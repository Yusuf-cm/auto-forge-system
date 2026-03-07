// components/Nav.tsx
// Navigation with mobile toggle, scroll-spy active state, and cart counter.
// Demonstrates: useState for mobile menu, useEffect for scroll detection,
// smooth scroll on link click, cart item count badge.
// Every site MUST have a Nav component — never inline navigation in page.tsx.

'use client'

import { useState, useEffect } from 'react'
import { CartItem, NavItem } from '../types'
import { getCartCount } from '../lib/cart'

interface NavProps {
  items: NavItem[]
  cartItems: CartItem[]
  onCartToggle: () => void
  siteName: string
}

export default function Nav({ items, cartItems, onCartToggle, siteName }: NavProps) {
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const [activeSection, setActiveSection] = useState('')
  const [isScrolled, setIsScrolled] = useState(false)

  const cartCount = getCartCount(cartItems)

  // ── Scroll detection: nav background + active section ──────
  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20)

      // Find which section is in view
      const sections = items.map(item => item.href.replace('#', ''))
      for (const section of sections) {
        const el = document.getElementById(section)
        if (el) {
          const rect = el.getBoundingClientRect()
          if (rect.top <= 100 && rect.bottom >= 100) {
            setActiveSection(section)
            break
          }
        }
      }
    }

    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [items])

  // ── Smooth scroll to section ────────────────────────────────
  const handleNavClick = (e: React.MouseEvent<HTMLAnchorElement>, href: string) => {
    if (href.startsWith('#')) {
      e.preventDefault()
      const target = document.getElementById(href.replace('#', ''))
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' })
        setIsMenuOpen(false)
      }
    }
  }

  return (
    <nav
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 100,
        backgroundColor: isScrolled ? 'rgba(26, 26, 26, 0.95)' : 'transparent',
        borderBottom: isScrolled ? '1px solid rgba(204, 255, 0, 0.2)' : 'none',
        backdropFilter: isScrolled ? 'blur(10px)' : 'none',
        transition: 'all 0.3s ease',
        padding: '1rem 2rem',
      }}
    >
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>

        {/* ── Logo ─────────────────────────────────────────── */}
        <span style={{
          fontFamily: "'Bebas Neue', sans-serif",
          fontSize: '1.5rem',
          color: 'var(--accent)',
          letterSpacing: '0.1em',
        }}>
          {siteName}
        </span>

        {/* ── Desktop nav links ─────────────────────────────── */}
        <div className="desktop-nav" style={{ display: 'flex', gap: '2rem', alignItems: 'center' }}>
          {items.map(item => (
            <a
              key={item.href}
              href={item.href}
              onClick={e => handleNavClick(e, item.href)}
              style={{
                color: activeSection === item.href.replace('#', '')
                  ? 'var(--accent)'
                  : 'var(--text-muted)',
                fontFamily: "'Inter', sans-serif",
                fontSize: '0.875rem',
                fontWeight: 600,
                textDecoration: 'none',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                transition: 'color 0.2s ease',
              }}
            >
              {item.label}
            </a>
          ))}

          {/* ── Cart button ─────────────────────────────────── */}
          <button
            onClick={onCartToggle}
            style={{
              background: 'transparent',
              border: '1px solid var(--accent)',
              color: 'var(--accent)',
              padding: '8px 16px',
              fontFamily: "'Inter', sans-serif",
              fontSize: '0.875rem',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            Cart
            {cartCount > 0 && (
              <span style={{
                background: 'var(--accent)',
                color: 'var(--bg)',
                borderRadius: '50%',
                width: '20px',
                height: '20px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '0.75rem',
                fontWeight: 700,
              }}>
                {cartCount}
              </span>
            )}
          </button>
        </div>

        {/* ── Mobile hamburger ──────────────────────────────── */}
        <button
          className="mobile-menu-btn"
          onClick={() => setIsMenuOpen(!isMenuOpen)}
          aria-label={isMenuOpen ? 'Close menu' : 'Open menu'}
          style={{
            background: 'transparent',
            border: 'none',
            color: 'var(--text)',
            cursor: 'pointer',
            display: 'none',
            flexDirection: 'column',
            gap: '5px',
            padding: '4px',
          }}
        >
          <span style={{
            display: 'block', width: '24px', height: '2px',
            background: 'currentColor',
            transform: isMenuOpen ? 'rotate(45deg) translate(5px, 5px)' : 'none',
            transition: 'transform 0.2s',
          }} />
          <span style={{
            display: 'block', width: '24px', height: '2px',
            background: 'currentColor',
            opacity: isMenuOpen ? 0 : 1,
            transition: 'opacity 0.2s',
          }} />
          <span style={{
            display: 'block', width: '24px', height: '2px',
            background: 'currentColor',
            transform: isMenuOpen ? 'rotate(-45deg) translate(5px, -5px)' : 'none',
            transition: 'transform 0.2s',
          }} />
        </button>
      </div>

      {/* ── Mobile menu dropdown ──────────────────────────────── */}
      {isMenuOpen && (
        <div style={{
          backgroundColor: 'var(--bg)',
          borderTop: '1px solid rgba(204, 255, 0, 0.2)',
          padding: '1.5rem 2rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '1rem',
        }}>
          {items.map(item => (
            <a
              key={item.href}
              href={item.href}
              onClick={e => handleNavClick(e, item.href)}
              style={{
                color: 'var(--text)',
                fontFamily: "'Inter', sans-serif",
                fontSize: '1rem',
                fontWeight: 600,
                textDecoration: 'none',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}
            >
              {item.label}
            </a>
          ))}
          <button
            onClick={() => { onCartToggle(); setIsMenuOpen(false) }}
            style={{
              background: 'var(--accent)',
              color: 'var(--bg)',
              border: 'none',
              padding: '12px',
              fontFamily: "'Inter', sans-serif",
              fontWeight: 700,
              fontSize: '0.875rem',
              textTransform: 'uppercase',
              cursor: 'pointer',
            }}
          >
            Cart {cartCount > 0 ? `(${cartCount})` : ''}
          </button>
        </div>
      )}
    </nav>
  )
}
