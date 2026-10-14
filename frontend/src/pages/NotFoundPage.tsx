import { Link } from 'react-router-dom'
import { Button } from '../components/ui'
export function NotFoundPage() { return <div className="route-loading"><div className="eyebrow">404 · Not found</div><h1>This page moved elsewhere.</h1><p>Use the workspace navigation to return to your authorized dashboard.</p><Link to="/"><Button>Back to workspace</Button></Link></div> }
