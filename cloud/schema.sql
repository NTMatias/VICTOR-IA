-- Run as project owner in Supabase SQL editor. No service-role key belongs in VICTOR.
begin;
create schema if not exists victor_private;
revoke all on schema victor_private from public,anon,authenticated;
create table if not exists victor_private.admins(user_id uuid primary key references auth.users(id) on delete cascade);
alter table victor_private.admins enable row level security;
revoke all on victor_private.admins from public,anon,authenticated;

create or replace function public.is_victor_admin() returns boolean
language sql stable security definer set search_path=''
as $$select exists(select 1 from victor_private.admins where user_id=auth.uid())$$;
revoke all on function public.is_victor_admin() from public;
grant execute on function public.is_victor_admin() to authenticated;

create table if not exists public.profiles(
 id uuid primary key references auth.users(id) on delete cascade,
 email text not null,
 created_at timestamptz not null default now(),
 last_login_at timestamptz,
 app_version text
);
alter table public.profiles enable row level security;
revoke all on public.profiles from anon,authenticated;
grant select on public.profiles to authenticated;
drop policy if exists victor_profile_read on public.profiles;
create policy victor_profile_read on public.profiles for select to authenticated
using(id=auth.uid() or public.is_victor_admin());

create table if not exists public.login_events(
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null references public.profiles(id) on delete cascade,
 occurred_at timestamptz not null default now(),
 app_version text not null
);
alter table public.login_events enable row level security;
revoke all on public.login_events from anon,authenticated;
grant select on public.login_events to authenticated;
drop policy if exists victor_admin_access_log on public.login_events;
create policy victor_admin_access_log on public.login_events for select to authenticated using(public.is_victor_admin());

create or replace function victor_private.new_profile() returns trigger
language plpgsql security definer set search_path=''
as $$begin insert into public.profiles(id,email) values(new.id,coalesce(new.email,''));return new;end;$$;
revoke all on function victor_private.new_profile() from public,anon,authenticated;
drop trigger if exists victor_new_profile on auth.users;
create trigger victor_new_profile after insert on auth.users for each row execute function victor_private.new_profile();
insert into public.profiles(id,email,created_at) select id,coalesce(email,''),created_at from auth.users on conflict(id) do nothing;

create or replace function public.record_victor_login(app_version text) returns void
language plpgsql security definer set search_path=''
as $$begin
 if auth.uid() is null then raise exception 'Authentication required';end if;
 if app_version is null or length(app_version)>64 or app_version !~ '^[0-9A-Za-z.+_-]+$' then raise exception 'Invalid version';end if;
 if exists(select 1 from public.profiles where id=auth.uid() and last_login_at>now()-interval '1 minute') then return;end if;
 update public.profiles set last_login_at=now(),app_version=record_victor_login.app_version where id=auth.uid();
 insert into public.login_events(user_id,app_version) values(auth.uid(),record_victor_login.app_version);
end;$$;
revoke all on function public.record_victor_login(text) from public;
grant execute on function public.record_victor_login(text) to authenticated;
commit;

-- Promote ONLY the owner's verified auth.users UUID, after registration, in SQL editor:
-- insert into victor_private.admins(user_id) values('OWNER-AUTH-USER-UUID');
-- Client-editable metadata is never used to assign administrator privileges.
