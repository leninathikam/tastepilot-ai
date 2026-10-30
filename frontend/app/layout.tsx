import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = {title:'TastePilot — A day that feels like you', description:'Cultural intelligence for thoughtful days out. Discover, inspect and revise your plan.'};
export default function Layout({children}:{children:React.ReactNode}) {return <html lang="en"><body>{children}</body></html>;}
