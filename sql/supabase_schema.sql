-- TVU Analytics Platform schema
create extension if not exists "pgcrypto";

create table if not exists public.app_users (
  id uuid primary key default gen_random_uuid(),
  email text unique not null,
  full_name text not null,
  password_hash text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.analysis_results (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.app_users(id) on delete cascade,
  text text not null,
  sentiment text not null,
  confidence double precision not null,
  model text not null,
  raw_response jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.report_history (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.app_users(id) on delete cascade,
  title text not null,
  summary text not null,
  metrics jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_analysis_user_created_at
  on public.analysis_results(user_id, created_at desc);

create index if not exists idx_report_user_created_at
  on public.report_history(user_id, created_at desc);
