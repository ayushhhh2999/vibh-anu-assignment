import { Plus, RefreshCw, Users, Workflow } from 'lucide-react'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { api } from '../../api/client'
import { useLeads } from '../useLeads'
import { useToast } from '../../app/providers'
import { Button, Field, Input, PageHeader, Panel, StatCard } from '../../components/ui'
import { LeadTable } from '../../components/leads/LeadTable'
import { errorMessage } from '../../lib/utils'
import { zodResolver } from '@hookform/resolvers/zod'

const schema = z.object({ name: z.string().min(2, 'Use at least 2 characters.').max(100, 'Keep the name under 100 characters.'), contact_number: z.string().min(7, 'Use at least 7 characters.').max(20, 'Keep the contact number under 20 characters.') })
type Values = z.infer<typeof schema>
export function MarketingPage() {
  const { leads, isLoading, isError, refresh } = useLeads(); const { push } = useToast(); const [showForm, setShowForm] = useState(false); const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<Values>({ resolver: zodResolver(schema) })
  const create = async (values: Values) => { try { await api.createLead(values); await refresh(); reset(); setShowForm(false); push('success', 'Lead created and sent to Communication.'); } catch (error) { push('error', errorMessage(error, 'Lead creation failed.')) } }
  const statusCount = (status: string) => leads.filter((lead) => lead.status === status).length
  return <><PageHeader eyebrow="Marketing desk" title="Create momentum." description="Capture new opportunities and keep an eye on the handoffs you started." action={<div className="header-actions"><Button variant="ghost" onClick={() => void refresh()}><RefreshCw size={16} />Refresh</Button><Button onClick={() => setShowForm((value) => !value)}><Plus size={17} />New lead</Button></div>} />
    <div className="stats-grid"><StatCard label="Leads created" value={leads.length} detail="Visible from the backend" accent="indigo" /><StatCard label="In communication" value={statusCount('communication')} detail="Awaiting enrichment" accent="teal" /><StatCard label="In motion" value={leads.filter((lead) => lead.status && lead.status !== 'communication').length} detail="Advanced through workflow" accent="amber" /><StatCard label="Workspace state" value={isLoading ? 'Syncing' : 'Live'} detail="Server-backed queue" accent="rose" /></div>
    {showForm && <Panel className="form-panel"><div className="panel-heading"><div><div className="eyebrow">New record</div><h2>Create a lead</h2><p>Only the information needed to start the controlled handoff.</p></div><button className="close-text" onClick={() => setShowForm(false)}>Close</button></div><form className="inline-form" onSubmit={handleSubmit(create)}><Field label="Customer / lead name" error={errors.name?.message}><Input autoFocus placeholder="e.g. Arjun Mehta" {...register('name')} /></Field><Field label="Contact number" error={errors.contact_number?.message}><Input placeholder="7–20 characters" {...register('contact_number')} /></Field><Button type="submit" loading={isSubmitting}>Create lead</Button></form></Panel>}
    <div className="section-heading"><div><div className="eyebrow">Your pipeline</div><h2>Leads you submitted</h2></div><span className="section-note"><Users size={15} />{leads.length} records</span></div>
    {isError ? <Panel className="error-panel"><Workflow size={18} /><div><strong>Could not load the Marketing queue.</strong><p>Check that the FastAPI backend is running and the API URL is correct.</p></div><Button variant="secondary" onClick={() => void refresh()}>Try again</Button></Panel> : isLoading ? <Panel className="loading-panel"><RefreshCw size={18} className="spin" />Loading your live queue…</Panel> : <LeadTable leads={leads} />}
  </>
}
