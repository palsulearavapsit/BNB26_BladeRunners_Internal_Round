import { createClient } from '@supabase/supabase-js'
import { config, hasSupabaseConfig } from './config'

export const supabase = hasSupabaseConfig
  ? createClient(config.supabaseUrl, config.supabaseAnonKey, {
      auth: { persistSession: false, autoRefreshToken: true, detectSessionInUrl: true },
    })
  : null
