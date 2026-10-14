import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, TextareaHTMLAttributes } from 'react'
import { LoaderCircle } from 'lucide-react'
import { forwardRef } from 'react'
import { cn } from '../lib/utils'

export function Button({ variant = 'primary', loading, className, children, ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' | 'ghost' | 'danger'; loading?: boolean }) { return <button className={cn('button', `button-${variant}`, className)} disabled={loading || props.disabled} {...props}>{loading && <LoaderCircle size={16} className="spin" />}{children}</button> }
export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(function Input(props, ref) { return <input className="field-input" ref={ref} {...props} /> })
export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(function Textarea(props, ref) { return <textarea className="field-input field-textarea" ref={ref} {...props} /> })
export function Panel({ children, className }: { children: ReactNode; className?: string }) { return <section className={cn('panel', className)}>{children}</section> }
export function PageHeader({ eyebrow, title, description, action }: { eyebrow: string; title: string; description: string; action?: ReactNode }) { return <div className="page-header"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{description}</p></div>{action}</div> }
export function StatCard({ label, value, detail, accent = 'indigo' }: { label: string; value: string | number; detail: string; accent?: 'indigo' | 'teal' | 'amber' | 'rose' }) { return <div className="stat-card"><div className={`stat-orb orb-${accent}`} /><div><span>{label}</span><strong>{value}</strong><small>{detail}</small></div></div> }
export function Field({ label, error, hint, children }: { label: string; error?: string; hint?: string; children: ReactNode }) { return <label className="field"><span>{label}</span>{children}{hint && !error && <small className="field-hint">{hint}</small>}{error && <small className="field-error">{error}</small>}</label> }
