import { Eye, EyeOff, LockKeyhole, Mail, ShieldCheck, Sparkles } from 'lucide-react'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useNavigate } from 'react-router-dom'
import { z } from 'zod'
import { api, authStore } from '../../api/client'
import { useAuth } from '../../app/auth'
import { dashboardForRole } from '../../app/routes'
import { Button, Field, Input } from '../../components/ui'
import { useToast } from '../../app/providers'
import { zodResolver } from '@hookform/resolvers/zod'

const schema = z.object({ email: z.string().email('Enter a valid work email.'), password: z.string().min(1, 'Password is required.') })
type FormValues = z.infer<typeof schema>
export function LoginPage() {
  const navigate = useNavigate(); const { push } = useToast(); const { signIn } = useAuth(); const [showPassword, setShowPassword] = useState(false); const [serverError, setServerError] = useState('')
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: { email: '', password: '' } })
  const submit = async (values: FormValues) => { setServerError(''); try { const result = await api.login(values); authStore.set(result.access_token); const user = await api.me(); signIn(result.access_token, user); push('success', `Signed in as ${user.name || user.email}.`); navigate(dashboardForRole(user.role), { replace: true }) } catch (error) { authStore.clear(); setServerError(error instanceof Error ? error.message : 'Unable to sign in. Check your credentials.') } }
  return <div className="login-page"><div className="login-art"><div className="login-brand"><div className="brand-mark"><span /></div><strong>Vibh-Anu</strong></div><div className="login-art-copy"><div className="eyebrow light">Lead operations platform</div><h1>Move every lead forward, with confidence.</h1><p>One accountable workspace for the teams that turn first contact into a claimed opportunity.</p></div><div className="login-art-footer"><span><ShieldCheck size={16} />Backend-authorized workflow</span><span>v1.0 · Internal use</span></div></div><main className="login-card-wrap"><div className="login-card"><div className="mobile-login-brand"><div className="brand-mark"><span /></div><strong>Vibh-Anu</strong></div><div className="login-heading"><div className="spark-icon"><Sparkles size={17} /></div><div><div className="eyebrow">Secure workspace</div><h2>Good to see you.</h2><p>Sign in with your departmental account to continue.</p></div></div><form onSubmit={handleSubmit(submit)}><Field label="Work email" error={errors.email?.message}><div className="input-icon"><Mail size={17} /><Input type="email" autoComplete="username" placeholder="you@vibhanu.com" {...register('email')} /></div></Field><Field label="Password" error={errors.password?.message}><div className="input-icon"><LockKeyhole size={17} /><Input type={showPassword ? 'text' : 'password'} autoComplete="current-password" placeholder="Enter your password" {...register('password')} /><button className="input-action" type="button" onClick={() => setShowPassword((value) => !value)} aria-label={showPassword ? 'Hide password' : 'Show password'}>{showPassword ? <EyeOff size={17} /> : <Eye size={17} />}</button></div></Field>{serverError && <div className="form-error" role="alert">{serverError}</div>}<Button type="submit" loading={isSubmitting} className="login-button">Sign in to workspace</Button></form><p className="login-footnote"><ShieldCheck size={14} /> Access is controlled by your Vibh-Anu role</p></div></main></div>
}
