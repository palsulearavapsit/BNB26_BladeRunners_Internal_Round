export const config = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') || '',
  supabaseUrl: import.meta.env.VITE_SUPABASE_URL || '',
  supabaseAnonKey: import.meta.env.VITE_SUPABASE_ANON_KEY || '',
}

export const hasSupabaseConfig = Boolean(
  config.supabaseUrl
    && config.supabaseAnonKey
    && config.supabaseUrl !== 'https://your-project.supabase.co'
    && config.supabaseAnonKey !== 'your-anon-key',
)
