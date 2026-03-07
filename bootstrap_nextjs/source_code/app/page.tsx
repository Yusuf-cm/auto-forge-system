// app/page.tsx
// Root page — the orchestrator.
// THIS IS THE MOST IMPORTANT PATTERN IN THE BOOTSTRAP:
// State lives here. Components receive state + dispatch as props.
// No state in leaf components. No prop drilling beyond one level.
// The Weaver MUST follow this pattern in all generated sites.

'use client'

import { useReducer, useEffect } from 'react'
import { cartReducer, initialCartState, saveCartToStorage, loadCartFromStorage } from '../lib/cart'
import { PRODUCTS } from '../lib/products'
import { Product } from '../types'
import Nav from '../components/Nav'
import Cart from '../components/Cart'
import ProductCard from '../components/ProductCard'
import ContactForm from '../components/ContactForm'

// ── Site configuration ──────────────────────────────────────
// Replace these values for each project — never hardcode in JSX.
const SITE_CONFIG = {
  name: 'VOLT COFFEE',
  tagline: 'FUEL THE GRIND',
  subtitle: 'Single-origin beans. Precision roasting. 48hr delivery. Built for people who treat performance as a lifestyle.',
  stats: [
    { value: '472mg', label: 'Caffeine Per Bag' },
    { value: 'Single-Origin', label: 'Sourced Direct' },
    { value: '48hr', label: 'Roast-to-Ship' },
  ],
  nav: [
    { label: 'Roasts', href: '#roasts' },
    { label: 'Process', href: '#process' },
    { label: 'Reviews', href: '#reviews' },
    { label: 'Contact', href: '#contact' },
  ],
}

export default function Home() {
  // ── Cart state managed with useReducer ─────────────────────
  // useReducer is the correct pattern for complex state with multiple
  // actions. Never use multiple useState calls for related state.
  const [cartState, dispatch] = useReducer(cartReducer, initialCartState)

  // ── Persist cart to localStorage ───────────────────────────
  // Load on mount, save on every change.
  useEffect(() => {
    const stored = loadCartFromStorage()
    if (stored.length > 0) {
      dispatch({ type: 'LOAD_CART', items: stored })
    }
  }, [])

  useEffect(() => {
    saveCartToStorage(cartState.items)
  }, [cartState.items])

  // ── Cart action handlers ────────────────────────────────────
  const handleAddToCart = (product: Product) => {
    dispatch({ type: 'ADD_ITEM', product })
  }

  const handleRemoveFromCart = (productId: string) => {
    dispatch({ type: 'REMOVE_ITEM', productId })
  }

  const handleUpdateQuantity = (productId: string, quantity: number) => {
    dispatch({ type: 'UPDATE_QUANTITY', productId, quantity })
  }

  const handleClearCart = () => {
    dispatch({ type: 'CLEAR_CART' })
  }

  const handleCartToggle = () => {
    dispatch({ type: 'TOGGLE_CART' })
  }

  return (
    <>
      {/* ── Navigation ──────────────────────────────────────── */}
      <Nav
        items={SITE_CONFIG.nav}
        cartItems={cartState.items}
        onCartToggle={handleCartToggle}
        siteName={SITE_CONFIG.name}
      />

      {/* ── Cart drawer ─────────────────────────────────────── */}
      <Cart
        items={cartState.items}
        isOpen={cartState.isOpen}
        onClose={handleCartToggle}
        onRemove={handleRemoveFromCart}
        onUpdateQuantity={handleUpdateQuantity}
        onClear={handleClearCart}
      />

      <main>

        {/* ── HERO ──────────────────────────────────────────── */}
        <section
          id="hero"
          style={{
            minHeight: '100vh',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            textAlign: 'center',
            padding: '8rem 2rem 4rem',
            backgroundColor: 'var(--bg)',
            boxShadow: 'inset 0 0 200px rgba(204, 255, 0, 0.04)',
          }}
        >
          <p style={{
            fontFamily: "'Inter', sans-serif",
            fontSize: '0.75rem',
            fontWeight: 700,
            letterSpacing: '0.3em',
            textTransform: 'uppercase',
            color: 'var(--text-muted)',
            marginBottom: '1.5rem',
          }}>
            Premium Specialty Coffee
          </p>

          <h1 style={{
            fontFamily: "'Bebas Neue', sans-serif",
            fontSize: 'clamp(4rem, 10vw, 8rem)',
            lineHeight: 1,
            letterSpacing: '-0.02em',
            color: 'var(--accent)',
            marginBottom: '1.5rem',
          }}>
            {SITE_CONFIG.tagline}
          </h1>

          <p style={{
            color: 'var(--text-muted)',
            fontSize: '1.125rem',
            lineHeight: 1.7,
            maxWidth: '520px',
            marginBottom: '3rem',
          }}>
            {SITE_CONFIG.subtitle}
          </p>

          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', justifyContent: 'center' }}>
            <a
              href="#roasts"
              onClick={e => {
                e.preventDefault()
                document.getElementById('roasts')?.scrollIntoView({ behavior: 'smooth' })
              }}
              style={{
                display: 'inline-block',
                background: 'var(--accent)',
                color: 'var(--bg)',
                padding: '16px 40px',
                fontFamily: "'Inter', sans-serif",
                fontWeight: 700,
                fontSize: '0.875rem',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                textDecoration: 'none',
                transition: 'background 0.2s',
              }}
            >
              Shop Roasts
            </a>
            <a
              href="#contact"
              onClick={e => {
                e.preventDefault()
                document.getElementById('contact')?.scrollIntoView({ behavior: 'smooth' })
              }}
              style={{
                display: 'inline-block',
                background: 'transparent',
                color: 'var(--accent)',
                border: '1px solid var(--accent)',
                padding: '16px 40px',
                fontFamily: "'Inter', sans-serif",
                fontWeight: 700,
                fontSize: '0.875rem',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                textDecoration: 'none',
              }}
            >
              Get in Touch
            </a>
          </div>
        </section>

        {/* ── STATS BAR ───────────────────────────────────────── */}
        <div style={{
          backgroundColor: 'var(--surface)',
          borderTop: '1px solid rgba(204, 255, 0, 0.2)',
          borderBottom: '1px solid rgba(204, 255, 0, 0.2)',
          padding: '2.5rem 2rem',
        }}>
          <div style={{
            maxWidth: '1200px',
            margin: '0 auto',
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: '2rem',
            textAlign: 'center',
          }}>
            {SITE_CONFIG.stats.map(stat => (
              <div key={stat.label}>
                <span style={{
                  display: 'block',
                  fontFamily: "'Bebas Neue', sans-serif",
                  fontSize: '2rem',
                  color: 'var(--accent)',
                  lineHeight: 1,
                  marginBottom: '0.25rem',
                }}>
                  {stat.value}
                </span>
                <span style={{
                  fontFamily: "'Inter', sans-serif",
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  color: 'var(--text-muted)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.1em',
                }}>
                  {stat.label}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* ── PRODUCTS ────────────────────────────────────────── */}
        <section id="roasts" style={{
          maxWidth: '1200px',
          margin: '0 auto',
          padding: '80px 2rem',
        }}>
          <h2 style={{
            fontFamily: "'Bebas Neue', sans-serif",
            fontSize: '2.5rem',
            color: 'var(--text)',
            marginBottom: '0.5rem',
          }}>
            Our Roasts
          </h2>
          <p style={{
            color: 'var(--text-muted)',
            marginBottom: '3rem',
            fontFamily: "'Inter', sans-serif",
          }}>
            Every bag roasted to order. Dispatched within 48 hours.
          </p>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '1.5rem',
          }}>
            {PRODUCTS.map(product => (
              <ProductCard
                key={product.id}
                product={product}
                onAddToCart={handleAddToCart}
              />
            ))}
          </div>
        </section>

        {/* ── PROCESS ─────────────────────────────────────────── */}
        <section id="process" style={{
          backgroundColor: '#111111',
          padding: '80px 0',
        }}>
          <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 2rem' }}>
            <h2 style={{
              fontFamily: "'Bebas Neue', sans-serif",
              fontSize: '2.5rem',
              color: 'var(--text)',
              marginBottom: '3rem',
            }}>
              The Process
            </h2>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              gap: '1.5rem',
            }}>
              {[
                { num: '01', title: 'We Source', body: 'Direct relationships with farms in Ethiopia, Colombia, and Guatemala. Every lot cupped before purchase.' },
                { num: '02', title: 'We Roast', body: 'Small-batch roasting in our facility. Every batch profiled, logged, and approved before it ships.' },
                { num: '03', title: 'We Ship', body: 'Roasted-to-order and dispatched within 48 hours. Arrives at peak freshness, not from a warehouse.' },
              ].map(step => (
                <div key={step.num} style={{
                  backgroundColor: 'var(--surface)',
                  border: '1px solid rgba(204, 255, 0, 0.12)',
                  padding: '2rem',
                }}>
                  <p style={{
                    fontFamily: "'Bebas Neue', sans-serif",
                    fontSize: '3rem',
                    color: 'rgba(204, 255, 0, 0.2)',
                    lineHeight: 1,
                    marginBottom: '0.5rem',
                  }}>
                    {step.num}
                  </p>
                  <p style={{
                    fontFamily: "'Inter', sans-serif",
                    fontSize: '1rem',
                    fontWeight: 700,
                    color: 'var(--accent)',
                    marginBottom: '0.5rem',
                  }}>
                    {step.title}
                  </p>
                  <p style={{
                    color: 'var(--text-muted)',
                    fontSize: '0.9375rem',
                    lineHeight: 1.6,
                  }}>
                    {step.body}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── TESTIMONIALS ────────────────────────────────────── */}
        <section id="reviews" style={{
          maxWidth: '1200px',
          margin: '0 auto',
          padding: '80px 2rem',
        }}>
          <h2 style={{
            fontFamily: "'Bebas Neue', sans-serif",
            fontSize: '2.5rem',
            color: 'var(--text)',
            marginBottom: '3rem',
          }}>
            What They Say
          </h2>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '1.5rem',
          }}>
            {[
              { quote: 'Switched from a major brand three months ago. My morning output went up noticeably. The Reactor Blend is the only thing on my desk.', author: 'Marcus T., Product Lead' },
              { quote: "I don't write reviews. I'm writing this one. The Dark Matter cold brew is the best I've had outside of Tokyo.", author: 'Priya K., Engineer' },
              { quote: 'Volt is what coffee should be — precise, clean, no nonsense. The packaging alone tells you these people are serious.', author: 'James O., Founder' },
            ].map(item => (
              <blockquote key={item.author} style={{
                backgroundColor: 'var(--surface)',
                borderLeft: '4px solid var(--accent)',
                border: '1px solid rgba(204, 255, 0, 0.15)',
                borderLeft: '4px solid var(--accent)',
                padding: '2rem',
                margin: 0,
              }}>
                <p style={{
                  color: 'var(--text)',
                  fontStyle: 'italic',
                  lineHeight: 1.7,
                  marginBottom: '1rem',
                  fontFamily: "'Inter', sans-serif",
                  fontSize: '0.9375rem',
                }}>
                  &ldquo;{item.quote}&rdquo;
                </p>
                <cite style={{
                  color: 'var(--accent)',
                  fontFamily: "'Inter', sans-serif",
                  fontSize: '0.8125rem',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  fontStyle: 'normal',
                }}>
                  — {item.author}
                </cite>
              </blockquote>
            ))}
          </div>
        </section>

        {/* ── CONTACT ─────────────────────────────────────────── */}
        <section id="contact" style={{
          backgroundColor: 'var(--surface)',
          borderTop: '1px solid rgba(204, 255, 0, 0.2)',
          padding: '80px 0',
        }}>
          <div style={{
            maxWidth: '640px',
            margin: '0 auto',
            padding: '0 2rem',
          }}>
            <h2 style={{
              fontFamily: "'Bebas Neue', sans-serif",
              fontSize: '2.5rem',
              color: 'var(--text)',
              marginBottom: '0.5rem',
            }}>
              Get in Touch
            </h2>
            <p style={{
              color: 'var(--text-muted)',
              marginBottom: '2.5rem',
              fontFamily: "'Inter', sans-serif",
            }}>
              Wholesale inquiries, trade accounts, or just want to talk coffee.
              We respond within 24 hours.
            </p>
            <ContactForm />
          </div>
        </section>

      </main>

      {/* ── FOOTER ──────────────────────────────────────────────── */}
      <footer style={{
        backgroundColor: '#0D0D0D',
        borderTop: '1px solid rgba(255,255,255,0.06)',
        padding: '2rem',
        textAlign: 'center',
      }}>
        <p style={{
          fontFamily: "'Inter', sans-serif",
          fontSize: '0.8125rem',
          color: 'var(--text-muted)',
        }}>
          © {new Date().getFullYear()} {SITE_CONFIG.name}. Built by AutoForge.
        </p>
      </footer>
    </>
  )
}
