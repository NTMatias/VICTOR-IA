begin;
insert into auth.users(id,aud,role,email,created_at,updated_at) values ('a0100000-0000-4000-8000-000000000001','authenticated','authenticated','audit-one@example.invalid',now(),now()),('a0100000-0000-4000-8000-000000000002','authenticated','authenticated','audit-two@example.invalid',now(),now());
set local role authenticated;
select set_config('request.jwt.claim.sub','a0100000-0000-4000-8000-000000000001',true);
do $$begin
 if (select count(*) from public.profiles)<>1 then raise exception 'Profile isolation failed';end if;
 if public.is_victor_admin() then raise exception 'Unexpected admin';end if;
 if (select count(*) from public.login_events)<>0 then raise exception 'Events exposed';end if;
 begin insert into victor_private.admins(user_id) values('a0100000-0000-4000-8000-000000000001'); raise exception 'Privilege escalation possible';exception when insufficient_privilege then null;end;
end$$;
select public.record_victor_login('7.0.0');
select public.record_victor_login('7.0.0');
reset role;
do $$begin if (select count(*) from public.login_events where user_id='a0100000-0000-4000-8000-000000000001')<>1 then raise exception 'Login recording failed';end if;end$$;
rollback;
select 'PASS: isolated profiles, hidden events, denied admin escalation, recorded login; fictional test data rolled back' as validation;
