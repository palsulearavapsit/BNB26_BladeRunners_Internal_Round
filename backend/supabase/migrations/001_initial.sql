create table if not exists public.analyses (
  id uuid primary key,
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  filename text not null,
  modality text not null check (modality in ('image','video','audio','text','document')),
  label text not null,
  confidence numeric not null check (confidence >= 0 and confidence <= 1),
  result jsonb not null,
  created_at timestamptz not null default now()
);
alter table public.analyses enable row level security;
do $$ begin
  create policy "Users can read their analyses" on public.analyses
    for select using (auth.uid() = user_id);
exception when duplicate_object then null;
end $$;
create or replace function public.delete_my_account()
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  if auth.uid() is null then
    raise exception 'Not authenticated';
  end if;
  delete from auth.users where id = auth.uid();
end;
$$;
revoke all on function public.delete_my_account() from public;
grant execute on function public.delete_my_account() to authenticated;
do $$ begin
  create policy "Users can insert their analyses" on public.analyses
    for insert with check (auth.uid() = user_id);
exception when duplicate_object then null;
end $$;
